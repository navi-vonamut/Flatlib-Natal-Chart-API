import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "flatlib_server"))

import main  # noqa: E402

client = TestClient(main.app)

BIRTH = {
    "date": "1990-05-03",
    "time": "13:20:00",
    "tz": "+03:00",
    "lat": 56.2576,
    "lon": 43.9827,
}


def test_health_version_matches_config():
    config = json.loads((Path(__file__).resolve().parents[1] / "flatlib_server" / "config.json").read_text())
    body = client.get("/health").json()
    assert body["status"] == "OK"
    assert body["version"] == config["version"]


def test_natal_has_all_outer_planets_and_house_keys():
    body = client.post("/natal", json=BIRTH).json()
    for planet in ("Uranus", "Neptune", "Pluto"):
        assert planet in body["planets"], f"{planet} missing from /natal"
    # no double-prefixed keys
    assert all(not key.startswith("House House") for key in body["houses"])
    assert set(body["houses"]) == {f"House{i}" for i in range(1, 13)}


def test_every_body_has_house_number():
    body = client.post("/natal", json=BIRTH).json()
    for group in ("planets", "special"):
        for name, data in body[group].items():
            assert isinstance(data["house"], int), f"{name} has no house"
            assert 1 <= data["house"] <= 12
    assert body["angles"]["Asc"]["house"] == 1


@pytest.mark.parametrize("date_value", ["1990-05-03", "1990/05/03"])
def test_date_formats_accepted_everywhere(date_value):
    birth = {**BIRTH, "date": date_value}
    for path in ("/natal", "/predict/daily", "/predict/monthly", "/predict/yearly"):
        response = client.post(path, json=birth)
        assert response.status_code == 200, f"{path} failed for {date_value}: {response.text[:200]}"


def test_monthly_and_yearly_use_current_date_not_birth_date():
    today = date.today()
    monthly = client.post("/predict/monthly", json=BIRTH).json()
    yearly = client.post("/predict/yearly", json=BIRTH).json()
    assert date.fromisoformat(monthly["target_date"]).year == today.year
    assert date.fromisoformat(yearly["target_date"]).year == today.year + 1


def test_invalid_date_returns_422():
    response = client.post("/predict/daily", json={**BIRTH, "date": "03/05/1990x"})
    assert response.status_code == 422


def test_daily_reports_applying_and_same_planet_transits():
    today = date.today()
    seen_same_planet = False
    seen_applying = False
    for offset in range(0, 30):
        target = (today + timedelta(days=offset)).isoformat()
        transits = client.post("/predict/daily", json={**BIRTH, "target_date": target}).json()["transits"]
        for transit in transits:
            if transit["transit_planet"] == transit["natal_planet"]:
                seen_same_planet = True
            if transit["is_applying"]:
                seen_applying = True
    assert seen_same_planet, "transiting planet to its own natal position is being skipped"
    assert seen_applying, "is_applying is never true"


def test_transits_range_dedupes_and_reports_windows():
    body = client.post("/transits/range", json={**BIRTH, "start_date": "2026-01-01", "end_date": "2026-01-31"}).json()
    assert body["count"] == len(body["transits"]) > 0
    keys = {(t["transit_planet"], t["aspect"], t["natal_planet"]) for t in body["transits"]}
    assert len(keys) == body["count"]
    for entry in body["transits"]:
        assert entry["first_seen"] <= entry["last_seen"]
        assert entry["min_orb"] <= 8.0


def test_synastry_includes_angles():
    other = {**BIRTH, "date": "1992-11-08", "time": "04:45:00"}
    aspects = client.post("/synastry", json={"person1": BIRTH, "person2": other}).json()["synastry_aspects"]
    assert aspects
    assert any("Asc" in (a["person1_object"], a["person2_object"]) for a in aspects)
    assert [a["orb"] for a in aspects] == sorted(a["orb"] for a in aspects)
