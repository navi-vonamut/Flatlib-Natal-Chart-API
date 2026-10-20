# Flatlib Natal Chart API

Home Assistant add-on serving a local FastAPI backend for astrological calculations with
[Flatlib](https://github.com/flatangle/flatlib) and the Swiss Ephemeris. All computation happens
locally; birth data never leaves your network.

-----

## ✨ Features (v0.3.0)

- **Natal chart:** 10 planets (Sun through Pluto), lunar nodes, Lilith (Syzygy), Pars Fortuna,
  Asc/MC, all 12 Placidus cusps, and the **house each body falls in**.
- **Aspects:** major natal aspects (conjunction, opposition, trine, square, sextile) with orbs.
- **Transits:** daily/monthly/yearly snapshots plus `/transits/range` for a window, with
  applying/separating and exact-hit dates.
- **Synastry:** cross-aspects between two charts, including angles.
- **JSON throughout:** shaped for HA REST sensors, template sensors and LLM prompts.

-----

## 🛠️ Configuration

The add-on has no options to configure - start it and call the API.

-----

## 💡 API

Reachable inside the Home Assistant Docker network at `http://a0d7b954-flatlib-server:8080`.
Interactive docs: `/docs` (or open `/`). Health: `/health`.

Every chart request takes the same birth body; `date` accepts `YYYY-MM-DD` or `YYYY/MM/DD`:

```json
{
  "date": "1990-05-03",
  "time": "13:20:00",
  "tz": "+03:00",
  "lat": 56.2576,
  "lon": 43.9827
}
```

### Endpoints

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/natal` | POST | Planets, special points, angles, houses, aspects |
| `/predict/daily` | POST | Transits on `target_date` (default: today) |
| `/predict/monthly` | POST | Transits on the 1st of next month (base: `target_date` or today) |
| `/predict/yearly` | POST | Transits on Jan 1 of next year (base: `target_date` or today) |
| `/transits/range` | POST | Deduplicated transits across `start_date`..`end_date`, with `first_seen`, `last_seen`, `exact_dates`, `min_orb` |
| `/synastry` | POST | `{"person1": {...}, "person2": {...}}` cross-aspects |
| `/health` | GET | Status, version and supported objects |

Each body in `/natal` carries `sign`, `sign_pos` (degrees into sign), `lon`, `lat`, `speed`,
`retrograde` and `house`. Transits carry `transit_planet`, `aspect`, `natal_planet`, `orb`,
`is_applying`, `is_exact`, both signs and the natal `natal_house`.

-----

## ❓ Support

Open an issue in this repository.

-----

## 📄 License

MIT
