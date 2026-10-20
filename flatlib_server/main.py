"""Home Assistant Flatlib Astrology API.

Local FastAPI backend for natal charts, transits and synastry, built on
flatlib + Swiss Ephemeris.
"""

import logging
from datetime import date as Date, datetime, timedelta
from typing import Any, Dict, List, Optional

from dateutil.relativedelta import relativedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field

from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Keep in sync with config.json
APP_VERSION = "0.3.0"

# --- Flatlib constants ---
PLANET_IDS = [
    const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
    const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
]
SPECIAL_OBJECTS = [
    const.NORTH_NODE, const.SOUTH_NODE,
    const.SYZYGY,
    const.PARS_FORTUNA,
]
# flatlib defaults to LIST_OBJECTS_TRADITIONAL (Sun..Saturn only) - be explicit.
OBJECT_IDS = PLANET_IDS + SPECIAL_OBJECTS
ANGLE_IDS = [const.ASC, const.MC]
ASPECT_TYPES = [
    const.CONJUNCTION, const.OPPOSITION, const.SQUARE, const.TRINE, const.SEXTILE,
]
ASPECT_NAMES = {
    const.CONJUNCTION: "Conjunction",
    const.OPPOSITION: "Opposition",
    const.SQUARE: "Square",
    const.TRINE: "Trine",
    const.SEXTILE: "Sextile",
}
EXACT_ANGLES = {
    const.CONJUNCTION: 0.0,
    const.OPPOSITION: 180.0,
    const.SQUARE: 90.0,
    const.TRINE: 120.0,
    const.SEXTILE: 60.0,
}
TRANSIT_ORBS = {
    const.CONJUNCTION: 8.0,
    const.OPPOSITION: 8.0,
    const.SQUARE: 7.0,
    const.TRINE: 7.0,
    const.SEXTILE: 5.0,
}
NATAL_ASPECT_ORBS = {
    const.CONJUNCTION: 8.0,
    const.OPPOSITION: 8.0,
    const.SQUARE: 6.0,
    const.TRINE: 6.0,
    const.SEXTILE: 4.0,
}

# --- Date helpers ---
_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y")


def parse_date(value: str, field: str = "date") -> Date:
    """Parse an ISO-ish date; accepts 1990-05-03, 1990/05/03, 03.05.1990."""
    text = (value or "").strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise HTTPException(
        status_code=422,
        detail=f"Invalid {field} '{value}': expected YYYY-MM-DD or YYYY/MM/DD",
    )


def flatlib_date(day: Date) -> str:
    return day.strftime("%Y/%m/%d")


# --- Pydantic models ---
_BIRTH_EXAMPLE = {
    "date": "1990-05-03",
    "time": "13:20:00",
    "tz": "+03:00",
    "lat": 56.2576,
    "lon": 43.9827,
}


class BirthData(BaseModel):
    """Birth data used to build a chart."""

    model_config = ConfigDict(json_schema_extra={"example": _BIRTH_EXAMPLE})

    date: str = Field(..., description="Birth date (YYYY-MM-DD or YYYY/MM/DD)")
    time: str = Field(..., description="Birth time (HH:MM:SS)")
    tz: str = Field(..., description="UTC offset of birth place (+HH:MM or -HH:MM)")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class NatalChartRequest(BirthData):
    pass


class DailyPredictionRequest(BirthData):
    target_date: Optional[str] = Field(
        None,
        description="Date to cast transits for (YYYY-MM-DD). Defaults to today.",
    )


class MonthlyPredictionRequest(BirthData):
    target_date: Optional[str] = Field(
        None,
        description="Base date (YYYY-MM-DD). Transits are cast for the 1st of the following month. Defaults to today.",
    )


class YearlyPredictionRequest(BirthData):
    target_date: Optional[str] = Field(
        None,
        description="Base date (YYYY-MM-DD). Transits are cast for Jan 1 of the following year. Defaults to today.",
    )


class Transit(BaseModel):
    """One transit aspect: a transiting body aspecting a natal body."""

    transit_planet: str
    aspect: str
    natal_planet: str
    orb: float
    is_applying: bool = False
    is_exact: bool = False
    transit_sign: Optional[str] = None
    natal_sign: Optional[str] = None
    natal_house: Optional[int] = None


class TransitsResponse(BaseModel):
    target_date: str
    transits: List[Transit] = Field(default_factory=list)


class SynastryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"person1": _BIRTH_EXAMPLE, "person2": _BIRTH_EXAMPLE}}
    )

    person1: BirthData
    person2: BirthData


class RangeRequest(BirthData):
    start_date: str = Field(..., description="Window start (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Window end (YYYY-MM-DD). Defaults to start + 30 days.")
    step_days: int = Field(1, ge=1, le=30, description="Days between samples")


# --- Chart helpers ---
def birth_chart(data: BirthData) -> Chart:
    day = parse_date(data.date, "date")
    try:
        dt = Datetime(flatlib_date(day), data.time, data.tz)
        pos = GeoPos(data.lat, data.lon)
        return Chart(dt, pos, hsys=const.HOUSES_PLACIDUS, IDs=OBJECT_IDS)
    except HTTPException:
        raise
    except Exception as exc:  # flatlib/PySwissEph raise bare exceptions
        logging.error("Error building chart: %s", exc, exc_info=True)
        raise HTTPException(status_code=422, detail=f"Could not build chart: {exc}")


def transit_chart(data: BirthData, target: Date, time_str: str = "12:00:00") -> Chart:
    try:
        dt = Datetime(flatlib_date(target), time_str, data.tz)
        return Chart(dt, GeoPos(data.lat, data.lon), hsys=const.HOUSES_PLACIDUS, IDs=OBJECT_IDS)
    except Exception as exc:
        logging.error("Error building transit chart: %s", exc, exc_info=True)
        raise HTTPException(status_code=422, detail=f"Could not build transit chart: {exc}")


def _is_retrograde(obj: Any) -> bool:
    value = obj.isRetrograde
    return bool(value() if callable(value) else value)


def _speed(obj: Any) -> float:
    return float(getattr(obj, "lonspeed", 0.0) or 0.0)


def house_table(chart: Chart) -> List[Any]:
    """Houses sorted by longitude as [(cusp_lon, house_number), ...]."""
    table = []
    for house in chart.houses:
        digits = "".join(ch for ch in house.id if ch.isdigit())
        if digits:
            table.append((house.lon, int(digits)))
    table.sort()
    return table


def house_of(table: List[Any], lon: float) -> Optional[int]:
    """House number containing an ecliptic longitude (quadrant houses wrap at 0)."""
    if not table:
        return None
    for index, (start, number) in enumerate(table):
        end = table[(index + 1) % len(table)][0]
        if start <= end:
            if start <= lon < end:
                return number
        elif lon >= start or lon < end:
            return number
    return table[-1][1]


def get_body_data(obj: Any, houses: List[Any]) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "sign": obj.sign,
        "sign_pos": round(obj.signlon, 2),
        "lon": round(obj.lon, 4),
        "lat": round(obj.lat, 4),
        "speed": round(_speed(obj), 4),
        "retrograde": _is_retrograde(obj),
        "house": house_of(houses, obj.lon),
    }


def get_angle_data(obj: Any, houses: List[Any]) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "sign": obj.sign,
        "sign_pos": round(obj.signlon, 2),
        "lon": round(obj.lon, 4),
        "house": house_of(houses, obj.lon),
    }


def get_house_data(house: Any) -> Dict[str, Any]:
    return {
        "id": house.id,
        "sign": house.sign,
        "sign_pos": round(house.signlon, 2),
        "lon": round(house.lon, 4),
    }


def _chart_objects(chart: Chart, ids: List[str]) -> List[Any]:
    objects = []
    for obj_id in ids:
        try:
            objects.append(chart.get(obj_id))
        except Exception as exc:
            logging.debug("Object %s unavailable: %s", obj_id, exc)
    return objects


def short_delta(lon1: float, lon2: float) -> float:
    """Signed shortest angular distance from lon2 to lon1, in (-180, 180]."""
    return (lon1 - lon2 + 180.0) % 360.0 - 180.0


def calculate_aspects(chart: Chart) -> List[Dict[str, Any]]:
    """Aspects between all chart bodies and angles."""
    aspects = []
    objects = _chart_objects(chart, PLANET_IDS + SPECIAL_OBJECTS + ANGLE_IDS)

    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            obj1, obj2 = objects[i], objects[j]
            delta = short_delta(obj1.lon, obj2.lon)
            distance = abs(delta)

            for aspect_type, max_orb in NATAL_ASPECT_ORBS.items():
                orb = abs(distance - EXACT_ANGLES[aspect_type])
                if orb <= max_orb:
                    aspects.append({
                        "id1": obj1.id,
                        "id2": obj2.id,
                        "type": ASPECT_NAMES[aspect_type],
                        "difference": round(distance, 4),
                        "orb": round(orb, 4),
                    })
                    break
    return aspects


def compute_transits(natal: Chart, data: BirthData, target: Date,
                     time_str: str = "12:00:00") -> List[Dict[str, Any]]:
    """Transits: transiting bodies aspecting natal bodies and angles.

    A transiting planet aspecting its own natal position (e.g. Sun to natal Sun,
    the annual return) is included - that is one of the most meaningful transits.
    """
    transiting = transit_chart(data, target, time_str)
    natal_targets = _chart_objects(natal, OBJECT_IDS + ANGLE_IDS)
    natal_houses = house_table(natal)

    transits = []
    for trans_obj in _chart_objects(transiting, PLANET_IDS + SPECIAL_OBJECTS):
        for natal_obj in natal_targets:
            delta = short_delta(trans_obj.lon, natal_obj.lon)
            distance = abs(delta)
            # The natal chart is frozen: only the transiting body moves.
            # (Using the natal body's own speed flips the applying flag for
            # same-planet transits, e.g. Sun to natal Sun.)
            rel_speed = _speed(trans_obj)

            for aspect_type, max_orb in TRANSIT_ORBS.items():
                exact_angle = EXACT_ANGLES[aspect_type]
                orb = abs(distance - exact_angle)
                if orb > max_orb:
                    continue

                is_exact = orb < 0.05
                # Excess = how far past the exact angle; applying when it shrinks.
                excess = distance - exact_angle
                rate = (1.0 if delta >= 0 else -1.0) * rel_speed
                is_applying = (not is_exact) and excess * rate < 0

                transits.append({
                    "transit_planet": trans_obj.id,
                    "aspect": ASPECT_NAMES[aspect_type],
                    "natal_planet": natal_obj.id,
                    "orb": round(orb, 2),
                    "is_applying": bool(is_applying),
                    "is_exact": bool(is_exact),
                    "transit_sign": trans_obj.sign,
                    "natal_sign": natal_obj.sign,
                    "natal_house": house_of(natal_houses, natal_obj.lon),
                })
                break

    transits.sort(key=lambda t: (t["orb"], t["transit_planet"], t["natal_planet"]))
    return transits


# --- FastAPI app ---
app = FastAPI(
    title="Flatlib Natal Chart API",
    version=APP_VERSION,
    description="Local astrology API (natal charts, transits, synastry) for Home Assistant.",
)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.post("/natal", response_model=Dict[str, Any])
def get_natal_chart(request: NatalChartRequest):
    """Full natal chart: planets, special points, angles, houses, aspects."""
    chart = birth_chart(request)
    houses = house_table(chart)

    planets = {}
    special = {}
    for obj in _chart_objects(chart, OBJECT_IDS):
        if obj.id in PLANET_IDS:
            planets[obj.id] = get_body_data(obj, houses)
        elif obj.id in SPECIAL_OBJECTS:
            special[obj.id] = get_body_data(obj, houses)

    angles = {}
    for obj in _chart_objects(chart, ANGLE_IDS):
        angles[obj.id] = get_angle_data(obj, houses)

    return {
        "planets": planets,
        "special": special,
        "angles": angles,
        "houses": {house.id: get_house_data(house) for house in chart.houses},
        "aspects": calculate_aspects(chart),
    }


@app.post("/predict/daily", response_model=Dict[str, Any])
def predict_daily(request: DailyPredictionRequest):
    """Transits active on a date (defaults to today)."""
    target = parse_date(request.target_date, "target_date") if request.target_date else Date.today()
    transits = compute_transits(birth_chart(request), request, target)
    response: Dict[str, Any] = {"target_date": target.isoformat(), "transits": transits}
    if not transits:
        response["message"] = "No major transit aspects on this date."
    return response


@app.post("/predict/monthly", response_model=TransitsResponse)
def predict_monthly(request: MonthlyPredictionRequest):
    """Transits cast for the 1st of the month following the base date (default today)."""
    base = parse_date(request.target_date, "target_date") if request.target_date else Date.today()
    target = base.replace(day=1) + relativedelta(months=1)
    transits = compute_transits(birth_chart(request), request, target)
    return {"target_date": target.isoformat(), "transits": transits}


@app.post("/predict/yearly", response_model=TransitsResponse)
def predict_yearly(request: YearlyPredictionRequest):
    """Transits cast for Jan 1 of the year following the base date (default today)."""
    base = parse_date(request.target_date, "target_date") if request.target_date else Date.today()
    target = base.replace(month=1, day=1) + relativedelta(years=1)
    transits = compute_transits(birth_chart(request), request, target)
    return {"target_date": target.isoformat(), "transits": transits}


@app.post("/transits/range", response_model=Dict[str, Any])
def transits_range(request: RangeRequest):
    """Transit aspects active during a window, deduplicated per aspect pair.

    Returns each transit once with the dates it was in orb, the exact-hit dates
    and the tightest orb seen - the useful shape for "what happens this month".
    """
    start = parse_date(request.start_date, "start_date")
    end = parse_date(request.end_date, "end_date") if request.end_date else start + timedelta(days=30)
    if end < start:
        raise HTTPException(status_code=422, detail="end_date must not be before start_date")

    samples = ((end - start).days // request.step_days) + 1
    if samples > 400:
        raise HTTPException(
            status_code=422,
            detail=f"Window too large: {samples} samples (max 400). Widen step_days.",
        )

    natal = birth_chart(request)
    collected: Dict[Any, Dict[str, Any]] = {}
    day = start
    while day <= end:
        for transit in compute_transits(natal, request, day):
            key = (transit["transit_planet"], transit["aspect"], transit["natal_planet"])
            entry = collected.get(key)
            if entry is None:
                entry = {
                    **{k: transit[k] for k in
                       ("transit_planet", "aspect", "natal_planet", "transit_sign",
                        "natal_sign", "natal_house")},
                    "min_orb": transit["orb"],
                    "first_seen": day.isoformat(),
                    "last_seen": day.isoformat(),
                    "exact_dates": [],
                }
                collected[key] = entry
            entry["last_seen"] = day.isoformat()
            if transit["orb"] < entry["min_orb"]:
                entry["min_orb"] = transit["orb"]
            if transit["is_exact"] and day.isoformat() not in entry["exact_dates"]:
                entry["exact_dates"].append(day.isoformat())
        day += timedelta(days=request.step_days)

    entries = sorted(collected.values(), key=lambda e: (e["min_orb"], e["transit_planet"]))
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "step_days": request.step_days,
        "count": len(entries),
        "transits": entries,
    }


@app.post("/synastry", response_model=Dict[str, Any])
def synastry(request: SynastryRequest):
    """Cross-aspects between two natal charts (bodies and angles)."""
    chart1 = birth_chart(request.person1)
    chart2 = birth_chart(request.person2)

    objects1 = _chart_objects(chart1, PLANET_IDS + ANGLE_IDS)
    objects2 = _chart_objects(chart2, PLANET_IDS + ANGLE_IDS)

    aspects = []
    for obj1 in objects1:
        for obj2 in objects2:
            delta = short_delta(obj1.lon, obj2.lon)
            distance = abs(delta)

            for aspect_type, max_orb in TRANSIT_ORBS.items():
                orb = abs(distance - EXACT_ANGLES[aspect_type])
                if orb <= max_orb:
                    aspects.append({
                        "person1_object": obj1.id,
                        "aspect": ASPECT_NAMES[aspect_type],
                        "person2_object": obj2.id,
                        "orb": round(orb, 2),
                    })
                    break

    aspects.sort(key=lambda a: (a["orb"], a["person1_object"], a["person2_object"]))
    return {"synastry_aspects": aspects}


@app.get("/health")
def health_check():
    """Liveness probe plus API capability summary."""
    return {
        "status": "OK",
        "version": APP_VERSION,
        "supported_objects": {
            "planets": PLANET_IDS,
            "special": SPECIAL_OBJECTS,
            "angles": ANGLE_IDS,
        },
        "aspect_types": [ASPECT_NAMES[t] for t in ASPECT_TYPES],
    }
