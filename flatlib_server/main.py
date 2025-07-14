from flask import Flask, request, jsonify
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
from flatlib.aspects import Aspect
import logging

app = Flask(__name__)

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Список поддерживаемых планет (только классические)
PLANET_IDS = [
    const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
    const.JUPITER, const.SATURN
]

# Список поддерживаемых специальных объектов
SPECIAL_OBJECTS = [
    const.NORTH_NODE, const.SOUTH_NODE, 
    const.SYZYGY,  # Черная Луна (Лилит)
    const.PARS_FORTUNA  # Парс Фортуны
]

# Поддерживаемые угловые точки
ANGLE_IDS = [const.ASC, const.MC]

# Основные аспекты для анализа
ASPECT_TYPES = [
    const.NO_ASPECT, const.CONJUNCTION, const.OPPOSITION,
    const.SQUARE, const.TRINE, const.SEXTILE
]

ASPECT_NAMES = {
    const.CONJUNCTION: "Conjunction",
    const.OPPOSITION: "Opposition",
    const.SQUARE: "Square",
    const.TRINE: "Trine",
    const.SEXTILE: "Sextile"
}

def get_planet_data(obj):
    """Извлекает данные для планетарных объектов."""
    # Обработка ретроградности
    is_retrograde = obj.isRetrograde
    if callable(is_retrograde):
        is_retrograde = is_retrograde()
    
    return {
        "id": obj.id,
        "sign": obj.sign,
        "sign_pos": round(obj.signlon, 2),
        "lon": round(obj.lon, 4),
        "lat": round(obj.lat, 4),
        "speed": round(obj.lonspeed, 4),
        "retrograde": bool(is_retrograde)
    }

def get_special_object_data(obj):
    """Извлекает данные для специальных объектов."""
    is_retrograde = obj.isRetrograde
    if callable(is_retrograde):
        is_retrograde = is_retrograde()
    
    return {
        "id": obj.id,
        "sign": obj.sign,
        "sign_pos": round(obj.signlon, 2),
        "lon": round(obj.lon, 4),
        "lat": round(obj.lat, 4),
        "speed": round(obj.lonspeed, 4),
        "retrograde": bool(is_retrograde)
    }

def get_angle_data(obj):
    """Извлекает данные для угловых точек."""
    return {
        "id": obj.id,
        "sign": obj.sign,
        "sign_pos": round(obj.signlon, 2),
        "lon": round(obj.lon, 4)
    }

def get_house_data(house):
    """Извлекает данные для домов."""
    return {
        "id": house.id,
        "sign": house.sign,
        "sign_pos": round(house.signlon, 2),
        "lon": round(house.lon, 4)
    }


def calculate_aspects(chart):
    """Рассчитывает аспекты между всеми объектами карты для flatlib 0.2.3 с расширенными орбами."""
    aspects = []
    all_objects = []
    
    # Собираем все объекты
    object_ids = PLANET_IDS + SPECIAL_OBJECTS + ANGLE_IDS
    for obj_id in object_ids:
        try:
            all_objects.append(chart.get(obj_id))
        except Exception as e:
            app.logger.warning(f"Skipping {obj_id}: {str(e)}")
            continue
    
    # Расширенные орбы для разных типов аспектов
    ORBS = {
        const.CONJUNCTION: 8.0,
        const.OPPOSITION: 8.0,
        const.SQUARE: 6.0,
        const.TRINE: 6.0,
        const.SEXTILE: 4.0
    }
    
    # Углы для каждого типа аспекта
    EXACT_ANGLES = {
        const.CONJUNCTION: 0,
        const.SEXTILE: 60,
        const.SQUARE: 90,
        const.TRINE: 120,
        const.OPPOSITION: 180
    }
    
    # Проверяем аспекты между всеми парами объектов
    for i in range(len(all_objects)):
        for j in range(i + 1, len(all_objects)):
            obj1 = all_objects[i]
            obj2 = all_objects[j]
            
            # Вычисляем угловое расстояние
            distance = abs(obj1.lon - obj2.lon)
            if distance > 180:
                distance = 360 - distance
            
            # Проверяем все возможные аспекты
            for aspect_type, max_orb in ORBS.items():
                exact_angle = EXACT_ANGLES[aspect_type]
                
                # Рассчитываем отклонение от точного аспекта
                orb = abs(distance - exact_angle)
                
                # Корректируем для углов > 180
                if orb > 180:
                    orb = 360 - orb
                
                # Проверяем попадание в орб
                if orb <= max_orb:
                    aspect_name = ASPECT_NAMES.get(aspect_type, f"Unknown-{aspect_type}")
                    aspects.append({
                        "id1": obj1.id,
                        "id2": obj2.id,
                        "type": aspect_name,
                        "difference": round(distance, 4),
                        "orb": round(orb, 4),
                        "exact_angle": exact_angle
                    })
                    break  # Не проверяем другие аспекты для этой пары
    
    return aspects

@app.route('/natal', methods=['POST'])
def natal():
    """
    Основной эндпоинт для расчета натальной карты.
    Принимает JSON с датой, временем и местом рождения.
    """
    # 1. Валидация входных данных
    data = request.json
    required_fields = ['date', 'time', 'tz', 'lat', 'lon']
    if not data or not all(field in data for field in required_fields):
        app.logger.warning("Missing required fields in request.")
        return jsonify({"error": "Missing required fields: date, time, tz, lat, lon"}), 400

    try:
        # 2. Подготовка данных для flatlib
        date_str = data['date'].replace("-", "/")
        dt = Datetime(date_str, data['time'], data['tz'])
        
        lat = float(data['lat'])
        lon = float(data['lon'])
        pos = GeoPos(lat, lon)
        
        app.logger.info(f"Calculating chart for date='{dt}', pos=({lat}, {lon})")
        
        # 3. Расчет карты
        chart = Chart(dt, pos, hsys=const.HOUSES_PLACIDUS)
        
        # 4. Извлечение данных
        result = {}
        
        # Планеты
        planets_data = {}
        for obj_id in PLANET_IDS:
            try:
                obj = chart.get(obj_id)
                planets_data[obj.id] = get_planet_data(obj)
            except Exception as e:
                app.logger.error(f"Error processing planet {obj_id}: {str(e)}")
                planets_data[obj_id] = {"error": str(e)}
        
        result['planets'] = planets_data
        
        # Специальные объекты
        special_data = {}
        for obj_id in SPECIAL_OBJECTS:
            try:
                obj = chart.get(obj_id)
                special_data[obj.id] = get_special_object_data(obj)
            except Exception as e:
                app.logger.error(f"Error processing special object {obj_id}: {str(e)}")
        
        if special_data:  # Добавляем только если есть данные
            result['special'] = special_data

        # Угловые точки
        angles_data = {}
        for obj_id in ANGLE_IDS:
            try:
                obj = chart.get(obj_id)
                angles_data[obj.id] = get_angle_data(obj)
            except Exception as e:
                app.logger.error(f"Error processing angle {obj_id}: {str(e)}")
        
        if angles_data:  # Добавляем только если есть данные
            result['angles'] = angles_data

        # Дома
        houses_data = {}
        try:
            for house in chart.houses: 
                houses_data[f"House {house.id}"] = get_house_data(house)
            result['houses'] = houses_data
        except Exception as e:
            app.logger.error(f"Error processing houses: {str(e)}")
            result['houses'] = {"error": str(e)}
        
        # Аспекты
        try:
            result['aspects'] = calculate_aspects(chart)
        except Exception as e:
            app.logger.error(f"Error calculating aspects: {str(e)}")
            result['aspects'] = {"error": str(e)}
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal error occurred", "details": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности сервера."""
    return jsonify({
        "status": "OK",
        "version": "1.1",  # Обновили версию
        "supported_objects": {
            "planets": PLANET_IDS,
            "special": SPECIAL_OBJECTS,
            "angles": ANGLE_IDS
        },
        "aspect_types": [const.ASPECT_NAMES[t] for t in ASPECT_TYPES if t != const.NO_ASPECT]
    })

@app.route('/test', methods=['GET'])
def test_chart():
    """Тестовый эндпоинт для проверки функциональности."""
    try:
        dt = Datetime('1990/05/03', '13:20:00', '+03:00')
        pos = GeoPos(56.2575, 43.9824)
        chart = Chart(dt, pos, hsys=const.HOUSES_PLACIDUS)
        
        sun = chart.get(const.SUN)
        asc = chart.get(const.ASC)
        
        return jsonify({
            "status": "success",
            "sun_sign": sun.sign,
            "asc_sign": asc.sign,
            "house_1_sign": chart.houses[0].sign,
            "aspects_sample": calculate_aspects(chart)[:3]  # Первые 3 аспекта для теста
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)