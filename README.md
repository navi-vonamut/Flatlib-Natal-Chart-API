# Home Assistant Flatlib Astrology API

A powerful Home Assistant Add-on providing a local **FastAPI** backend for advanced astrological calculations using [Flatlib](https://github.com/flatangle/flatlib) and [Swiss Ephemeris](https://www.astro.com/swisseph/).

-----

## ✨ Overview

This add-on runs a high-performance **FastAPI server** directly within your Home Assistant environment. It serves as a robust backend for complex astrological computations, offering a reliable and fast API. By performing all calculations locally, it ensures your sensitive personal data remains private and secure.

The add-on is designed to support a wide range of use cases, from simple automations to feeding structured data to Large Language Models (LLMs) for dynamic, personalized interpretations.

-----

## 🚀 Key Features

  - **FastAPI backend**: asynchronous, self-documenting (`/docs`), no external calls.
  - **Natal chart**: 10 planets (Sun through Pluto), lunar nodes, Lilith (Syzygy), Pars Fortuna, Ascendant, Midheaven, all 12 Placidus cusps, plus the **house each body occupies**.
  - **Aspects**: major natal aspects (conjunction, opposition, trine, square, sextile) with orbs.
  - **Transits**: daily / monthly / yearly snapshots, plus a `/transits/range` endpoint for a date window with applying/separating state and exact-hit dates.
  - **Synastry**: cross-aspects between two natal charts, angles included.
  - **LLM ready**: structured JSON for GPT, Claude, Ollama, or HA REST/template sensors.
  - **Local & private**: calculations never leave your network.

### Changes in v0.3.0

  - Lunar nodes, Lilith and Pars Fortuna stay in the chart; **Uranus, Neptune and Pluto are no longer silently dropped** (flatlib defaults to the 7 traditional planets - the chart is now built with an explicit object list).
  - **House placement** returned for every body and angle.
  - House keys are `House1`…`House12` (previously `House House1`…).
  - Transits now include the **natal angles (Asc/MC) as targets** and no longer skip a transiting planet aspecting its own natal position - the annual Sun return, for example, now appears.
  - `is_applying` / `is_exact` are computed from longitudes and speeds instead of being hardcoded.
  - **Fixed:** `/predict/monthly` and `/predict/yearly` cast transits from the birth date instead of the current date; `YYYY/MM/DD` input no longer 500s; `/predict/yearly` no longer ignores its own request model.
  - `/transits/range` added; `GET /` redirects to `/docs`; `/health` reports the real version.

-----

## 🔧 Installation

1.  **Add the Add-on Repository** - add this repository URL to the Home Assistant Add-on Store:
    `https://github.com/Mozburg/Flatlib-Natal-Chart-API`
2.  **Install the Add-on** - find "**Flatlib Natal Chart API**" in the store and click "Install".

-----

## 💻 API Endpoints

The server is reachable inside the Home Assistant Docker network at `http://a0d7b954-flatlib-server:8080`.

All chart requests share one birth-data body. `date` accepts `YYYY-MM-DD` or `YYYY/MM/DD`, `tz` is the
UTC offset of the birth place:

```json
{
  "date": "1990-05-03",
  "time": "13:20:00",
  "tz": "+03:00",
  "lat": 56.2576,
  "lon": 43.9827
}
```

### 1\. Natal Chart (`POST /natal`)

  * **Response:** `planets` (Sun…Pluto), `special` (nodes, Syzygy, Pars Fortuna), `angles` (Asc, MC), `houses` (`House1`…`House12`, Placidus), `aspects`.
  * Every body: `sign`, `sign_pos` (degrees into sign), `lon`, `lat`, `speed`, `retrograde`, `house`.

### 2\. Daily Prediction (`POST /predict/daily`)

  * **Request:** birth data plus optional `target_date` (**defaults to today**).
  * **Response:** `target_date` and `transits`, each with `transit_planet`, `aspect`, `natal_planet`, `orb`, `is_applying`, `is_exact`, `transit_sign`, `natal_sign`, `natal_house`, sorted by tightest orb.

### 3\. Monthly Prediction (`POST /predict/monthly`)

  * **Request:** birth data plus optional `target_date` (base date, defaults to today).
  * **Response:** transits cast for the 1st of the following month.

### 4\. Yearly Prediction (`POST /predict/yearly`)

  * **Request:** birth data plus optional `target_date` (base date, defaults to today).
  * **Response:** transits cast for January 1 of the following year.

### 5\. Transit Range (`POST /transits/range`)

  * **Request:** birth data plus `start_date`, optional `end_date` (default start + 30 days) and `step_days` (default 1).
  * **Response:** each aspect pair once, with `first_seen`, `last_seen`, `exact_dates` and `min_orb` - the shape you want for "what happens this month".

### 6\. Synastry (`POST /synastry`)

  * **Request:**
    ```json
    {
      "person1": { "date": "1990-05-03", "time": "13:20:00", "tz": "+03:00", "lat": 56.2576, "lon": 43.9827 },
      "person2": { "date": "1992-11-08", "time": "04:45:00", "tz": "+03:00", "lat": 56.2576, "lon": 43.9827 }
    }
    ```
  * **Response:** `synastry_aspects` (`person1_object`, `aspect`, `person2_object`, `orb`), sorted by orb.

### 7\. Health (`GET /health`)

  * Returns `status`, `version` and the supported planets, special points, angles and aspect types.

-----

## 🧪 Tests

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python flatlib==0.2.3 pyswisseph==2.8.0.post1 fastapi python-dateutil httpx pytest
.venv/bin/python -m pytest tests/ -q
```

-----

## 🛠️ Tech Stack

  * **Python:** 3.11
  * **`fastapi`** + **`uvicorn`**: the backend server
  * **`flatlib`**: `0.2.3`
  * **`pyswisseph`**: `2.8.0.post1`

-----

## 🤝 Contribution

Contributions are welcome! Open an issue or a pull request on GitHub.

-----

## 📄 License

MIT
