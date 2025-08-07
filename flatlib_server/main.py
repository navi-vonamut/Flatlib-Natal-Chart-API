import logging
from typing import List, Dict, Any

from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from datetime import datetime
from dateutil.relativedelta import relativedelta

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Константы Flatlib ---
PLANET_IDS = [
    const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
    const.JUPITER, const.SATURN
]
SPECIAL_OBJECTS = [
    const.NORTH_NODE, const.SOUTH_NODE, 
    const.SYZYGY, 
    const.PARS_FORTUNA
]
ANGLE_IDS = [const.ASC, const.MC]
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
TRANSIT_ORBS = {
    const.CONJUNCTION: 8,
    const.OPPOSITION: 8,
    const.SQUARE: 7,
    const.TRINE: 7,
    const.SEXTILE: 5,
}

# --- Pydantic модели ---
class NatalChartRequest(BaseModel):
    date: str = Field(..., description="Дата рождения (YYYY/MM/DD)", example="1990/05/03")
    time: str = Field(..., description="Время рождения (HH:MM:SS)", example="13:20:00")
    tz: str = Field(..., description="Часовой пояс (+HH:MM или -HH:MM)", example="+03:00")
    lat: float = Field(..., description="Широта", example=56.2575)
    lon: float = Field(..., description="Долгота", example=43.9824)

class DailyPredictionRequest(BaseModel):
    date: str = Field(..., description="Дата рождения (YYYY/MM/DD)", example="1990/05/03")
    time: str = Field(..., description="Время рождения (HH:MM:SS)", example="13:20:00")
    tz: str = Field(..., description="Часовой пояс (+HH:MM или -HH:MM)", example="+03:00")
    lat: float = Field(..., description="Широта", example=56.2575)
    lon: float = Field(..., description="Долгота", example=43.9824)
    target_date: str = Field(..., description="Целевая дата для прогноза (YYYY/MM/DD)", example="2025/08/15")

class YearlyPredictionRequest(BaseModel):
    date: str = Field(..., description="Дата рождения (YYYY/MM/DD)", example="1990/05/03")
    time: str = Field(..., description="Время рождения (HH:MM:SS)", example="13:20:00")
    tz: str = Field(..., description="Часовой пояс (+HH:MM или -HH:MM)", example="+03:00")
    lat: float = Field(..., description="Широта", example=56.2575)
    lon: float = Field(..., description="Долгота", example=43.9824)
    age: int = Field(..., description="Возраст, на который делается прогноз", example=35)

class Transit(BaseModel):
    """Модель для описания одного транзитного аспекта."""
    transit_planet: str
    aspect: str
    natal_planet: str
    orb: float
    is_applying: bool = False

class TransitsResponse(BaseModel):
    """Модель для ответа с транзитными аспектами."""
    target_date: str
    transits: List[Transit]
    
class SynastryRequest(BaseModel):
    """Модель для запроса синастрии (две натальные карты)."""
    person1: NatalChartRequest
    person2: NatalChartRequest

# --- Вспомогательные функции ---
def get_planet_data(obj):
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
    return {
        "id": obj.id,
        "sign": obj.sign,
        "sign_pos": round(obj.signlon, 2),
        "lon": round(obj.lon, 4)
    }

def get_house_data(house):
    return {
        "id": house.id,
        "sign": house.sign,
        "sign_pos": round(house.signlon, 2),
        "lon": round(house.lon, 4)
    }

def calculate_aspects(chart):
    """Рассчитывает аспекты между всеми объектами карты."""
    aspects = []
    
    all_objects = []
    for o_id in PLANET_IDS + SPECIAL_OBJECTS + ANGLE_IDS:
        try:
            obj = chart.get(o_id)
            all_objects.append(obj)
        except:
            continue
    
    ORBS = {const.CONJUNCTION: 8.0, const.OPPOSITION: 8.0, const.SQUARE: 6.0, const.TRINE: 6.0, const.SEXTILE: 4.0}
    EXACT_ANGLES = {const.CONJUNCTION: 0, const.SEXTILE: 60, const.SQUARE: 90, const.TRINE: 120, const.OPPOSITION: 180}
    
    for i in range(len(all_objects)):
        for j in range(i + 1, len(all_objects)):
            obj1, obj2 = all_objects[i], all_objects[j]
            distance = abs(obj1.lon - obj2.lon)
            if distance > 180:
                distance = 360 - distance
            
            for aspect_type, max_orb in ORBS.items():
                exact_angle = EXACT_ANGLES[aspect_type]
                orb = abs(distance - exact_angle)
                
                if orb > 180:
                    orb = 360 - orb
                
                if orb <= max_orb:
                    aspect_name = ASPECT_NAMES.get(aspect_type, f"Unknown-{aspect_type}")
                    aspects.append({
                        "id1": obj1.id, "id2": obj2.id, "type": aspect_name,
                        "difference": round(distance, 4), "orb": round(orb, 4)
                    })
                    break
    return aspects
    
def get_transits_for_date(natal_data: dict, target_date: str) -> List[Dict[str, Any]]:
    """
    Рассчитывает транзитные аспекты на конкретную дату, используя старый метод.
    """
    try:
        # 1. Создаём натальную карту
        birth_date = Datetime(natal_data['date'].replace("-", "/"), natal_data['time'], natal_data['tz'])
        birth_pos = GeoPos(natal_data['lat'], natal_data['lon'])
        natal_chart = Chart(birth_date, birth_pos)

        # 2. Создаём транзитную карту на текущую дату
        transit_date = Datetime(target_date.replace("-", "/"), '12:00:00', natal_data['tz'])
        transit_pos = birth_pos
        transit_chart = Chart(transit_date, transit_pos)

        transits = []
        
        # 3. Получаем списки объектов из обеих карт
        natal_objects = natal_chart.objects
        transit_objects = transit_chart.objects

        # 4. Вручную рассчитываем аспекты между транзитными и натальными объектами
        for transit_obj in transit_objects:
            for natal_obj in natal_objects:
                # Проверяем, что это не один и тот же объект в разных картах
                if transit_obj.id == natal_obj.id:
                    continue

                distance = abs(transit_obj.lon - natal_obj.lon)
                if distance > 180:
                    distance = 360 - distance

                for aspect_type, max_orb in TRANSIT_ORBS.items():
                    # Рассчитываем точный угол для каждого аспекта
                    if aspect_type == const.CONJUNCTION:
                        exact_angle = 0
                    elif aspect_type == const.OPPOSITION:
                        exact_angle = 180
                    elif aspect_type == const.SQUARE:
                        exact_angle = 90
                    elif aspect_type == const.TRINE:
                        exact_angle = 120
                    elif aspect_type == const.SEXTILE:
                        exact_angle = 60
                    else:
                        continue # Пропускаем, если аспект не поддерживается

                    orb = abs(distance - exact_angle)
                    
                    if orb <= max_orb:
                        aspect_name = ASPECT_NAMES.get(aspect_type, f"Unknown-{aspect_type}")
                        transits.append({
                            'transit_planet': transit_obj.id,
                            'aspect': aspect_name, # Используем человекочитаемое имя
                            'natal_planet': natal_obj.id,
                            'orb': round(orb, 2),
                            # Упрощенная логика is_applying. Можно доработать
                            'is_applying': False, 
                        })
                        break
        return transits
    except Exception as e:
        # Добавляем логгирование для более детальной информации об ошибке
        logging.error(f"Error in get_transits_for_date: {e}", exc_info=True)
        raise e

# --- FastAPI-приложение ---
app = FastAPI()

@app.post("/natal", response_model=Dict[str, Any])
async def get_natal_chart(request: NatalChartRequest):
    """
    Эндпоинт для расчета натальной карты.
    """
    try:
        date_str = request.date.replace("-", "/")
        dt = Datetime(date_str, request.time, request.tz)
        pos = GeoPos(request.lat, request.lon)
        
        logging.info(f"Calculating chart for date='{dt}', pos=({request.lat}, {request.lon})")
        
        chart = Chart(dt, pos, hsys=const.HOUSES_PLACIDUS)
        
        result = {}
        result['planets'] = {obj.id: get_planet_data(chart.get(obj.id)) for obj in chart.objects if obj.id in PLANET_IDS}
        result['special'] = {obj.id: get_special_object_data(chart.get(obj.id)) for obj in chart.objects if obj.id in SPECIAL_OBJECTS}
        
        angles = {}
        for angle_id in ANGLE_IDS:
            try:
                angle_obj = chart.get(angle_id)
                angles[angle_id] = get_angle_data(angle_obj)
            except Exception as e:
                logging.warning(f"Could not get angle {angle_id}: {e}")
                
        result['angles'] = angles
        
        result['houses'] = {f"House {h.id}": get_house_data(h) for h in chart.houses}
        result['aspects'] = calculate_aspects(chart)
        
        return result
        
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred")


@app.post("/predict/daily", response_model=Dict[str, Any])
async def predict_daily(request: DailyPredictionRequest):
    """
    Эндпоинт для расчета ежедневных транзитов.
    """
    try:
        transits = get_transits_for_date(request.dict(), request.target_date)
        if not transits:
            return {"message": "На указанную дату значимых транзитных аспектов не найдено."}
        return {"target_date": request.target_date, "transits": transits}
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    

# Новый эндпоинт для месячного прогноза
@app.post("/predict/monthly", response_model=TransitsResponse)
async def predict_monthly(request: NatalChartRequest):
    """
    Расчет транзитов на первый день следующего месяца для месячного прогноза.
    """
    try:
        # Получаем дату натальной карты
        natal_datetime = Datetime(request.date.replace("-", "/"), request.time, request.tz)

        # Вычисляем дату следующего месяца
        current_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        next_month_date = current_date.replace(day=1) + relativedelta(months=1)
        target_date_str = next_month_date.strftime("%Y-%m-%d")

        # Получаем транзиты для этой даты
        transits = get_transits_for_date(request.dict(), target_date_str)

        return {"target_date": target_date_str, "transits": transits}
    except Exception as e:
        logging.error(f"Error in predict_monthly: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing monthly prediction.")


# Новый эндпоинт для годового прогноза
@app.post("/predict/yearly", response_model=TransitsResponse)
async def predict_yearly(request: NatalChartRequest):
    """
    Расчет транзитов на 1 января следующего года для годового прогноза.
    """
    try:
        # Получаем дату натальной карты
        natal_datetime = Datetime(request.date.replace("-", "/"), request.time, request.tz)

        # Вычисляем дату следующего года
        current_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        next_year_date = current_date.replace(month=1, day=1) + relativedelta(years=1)
        target_date_str = next_year_date.strftime("%Y-%m-%d")

        # Получаем транзиты для этой даты
        transits = get_transits_for_date(request.dict(), target_date_str)

        return {"target_date": target_date_str, "transits": transits}
    except Exception as e:
        logging.error(f"Error in predict_yearly: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing yearly prediction.")

# Новый эндпоинт для синастрии
@app.post("/synastry", response_model=Dict[str, Any])
async def synastry(request: SynastryRequest):
    """
    Расчет синастрических аспектов между двумя натальными картами.
    """
    try:
        # 1. Создаем натальную карту для первого человека
        person1_date = Datetime(request.person1.date.replace("-", "/"), request.person1.time, request.person1.tz)
        person1_pos = GeoPos(request.person1.lat, request.person1.lon)
        person1_chart = Chart(person1_date, person1_pos)

        # 2. Создаем натальную карту для второго человека
        person2_date = Datetime(request.person2.date.replace("-", "/"), request.person2.time, request.person2.tz)
        person2_pos = GeoPos(request.person2.lat, request.person2.lon)
        person2_chart = Chart(person2_date, person2_pos)

        synastry_aspects = []

        # 3. Рассчитываем аспекты между всеми планетами двух карт
        for obj1 in person1_chart.objects:
            # Используем только основные объекты для синастрии, чтобы избежать избыточности
            if obj1.id not in (PLANET_IDS + ANGLE_IDS):
                continue
            
            for obj2 in person2_chart.objects:
                if obj2.id not in (PLANET_IDS + ANGLE_IDS):
                    continue

                distance = abs(obj1.lon - obj2.lon)
                if distance > 180:
                    distance = 360 - distance

                # Используем стандартные орбисы для синастрии (можно настроить)
                for aspect_type, max_orb in TRANSIT_ORBS.items():
                    if aspect_type == const.NO_ASPECT:
                        continue

                    # Рассчитываем точный угол для каждого аспекта
                    if aspect_type == const.CONJUNCTION:
                        exact_angle = 0
                    elif aspect_type == const.OPPOSITION:
                        exact_angle = 180
                    elif aspect_type == const.SQUARE:
                        exact_angle = 90
                    elif aspect_type == const.TRINE:
                        exact_angle = 120
                    elif aspect_type == const.SEXTILE:
                        exact_angle = 60
                    else:
                        continue

                    orb = abs(distance - exact_angle)
                    if orb <= max_orb:
                        aspect_name = ASPECT_NAMES.get(aspect_type, f"Unknown-{aspect_type}")
                        synastry_aspects.append({
                            'person1_object': obj1.id,
                            'aspect': aspect_name,
                            'person2_object': obj2.id,
                            'orb': round(orb, 2),
                        })

        return {"synastry_aspects": synastry_aspects}

    except Exception as e:
        logging.error(f"Error in synastry: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing synastry.")

@app.get('/health')
def health_check():
    """Проверка работоспособности сервера."""
    return {
        "status": "OK",
        "version": "1.3",
        "supported_objects": {
            "planets": PLANET_IDS,
            "special": SPECIAL_OBJECTS,
            "angles": ANGLE_IDS
        },
        "aspect_types": [ASPECT_NAMES[t] for t in ASPECT_TYPES if t != const.NO_ASPECT]
    }