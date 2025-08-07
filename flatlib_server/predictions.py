from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.relations import Relation

# Орбы можно вынести в конфиг
# (как сильно может аспект отклоняться от точного значения)
TRANSIT_ORBS = {
    const.CONJUNCTION: 8,
    const.OPPOSITION: 8,
    const.SQUARE: 7,
    const.TRINE: 7,
    const.SEXTILE: 5,
    # и т.д. для минорных аспектов, если нужно
}

def get_transits_for_date(natal_data: dict, target_date: str):
    """
    Рассчитывает транзитные аспекты на конкретную дату.
    
    natal_data: словарь с данными рождения ('date', 'time', 'lat', 'lon')
    target_date: целевая дата в формате 'YYYY/MM/DD'
    """
    
    # 1. Создаем натальную карту
    birth_date = Datetime(natal_data['date'], natal_data['time'])
    birth_pos = GeoPos(natal_data['lat'], natal_data['lon'])
    natal_chart = Chart(birth_date, birth_pos)

    # 2. Создаем транзитную карту на целевую дату (время можно взять полдень)
    # Время не так критично для медленных планет, но для Луны имеет значение
    transit_date = Datetime(target_date, '12:00')
    # Положение на Земле для транзитов не имеет значения, т.к. мы смотрим на планеты
    # Но для расчета домов транзитной карты оно нужно. Можно использовать натальное.
    transit_chart = Chart(transit_date, birth_pos)

    # 3. Находим аспекты между транзитными и натальными планетами
    transits = []
    
    # Мы ищем аспекты от транзитных планет (chart2) к натальным (chart1)
    for transit_obj in transit_chart.objects:
        for natal_obj in natal_chart.objects:
            relation = Relation(transit_obj, natal_obj)
            
            # Проверяем, является ли аспект мажорным и входит ли в наши орбы
            if relation.isMajor() and abs(relation.orb) <= TRANSIT_ORBS.get(relation.aspect.id, 0):
                transits.append({
                    'transit_planet': transit_obj.id,
                    'aspect': relation.aspect.id,
                    'natal_planet': natal_obj.id,
                    'orb': round(relation.orb, 2), # Округляем орб для читаемости
                    'is_applying': relation.isApplying(), # Сходящийся (true) или расходящийся (false) аспект
                })
                
    return transits

from flatlib.charts.progressed import ProgressedChart

def get_progressions_for_year(natal_data: dict, age: int):
    """
    Рассчитывает прогрессивные аспекты на определенный год жизни (возраст).
    
    natal_data: словарь с данными рождения
    age: возраст, на который делаем прогноз
    """
    
    # 1. Создаем натальную карту
    birth_date = Datetime(natal_data['date'], natal_data['time'])
    birth_pos = GeoPos(natal_data['lat'], natal_data['lon'])
    natal_chart = Chart(birth_date, birth_pos)
    
    # 2. Создаем прогрессивную карту
    # 'pd' означает 'progressed date'
    pd = birth_date.add_days(age) 
    prog_chart = ProgressedChart(natal_chart, pd)
    
    # 3. Находим аспекты прогрессивных планет к натальным
    progressions = []
    
    # Орбы для прогрессий обычно берут очень маленькие, ~1 градус
    prog_orb = 1.0
    
    for prog_obj in prog_chart.objects:
        for natal_obj in natal_chart.objects:
            relation = Relation(prog_obj, natal_obj)
            if relation.isMajor() and abs(relation.orb) <= prog_orb:
                progressions.append({
                    'progressed_planet': prog_obj.id,
                    'aspect': relation.aspect.id,
                    'natal_planet': natal_obj.id,
                    'orb': round(relation.orb, 2),
                    'is_applying': relation.isApplying()
                })
                
    return progressions