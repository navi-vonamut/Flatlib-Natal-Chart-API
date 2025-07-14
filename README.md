# Home Assistant Flatlib Astrology Add-on

A lightweight Home Assistant Add-on providing a local Flask-based REST API for calculating **astrological natal charts and transits** using [Flatlib](https://github.com/flatangle/flatlib) and [Swiss Ephemeris](https://www.astro.com/swisseph/).

---

## 🌟 Overview

This add-on spins up a local Flask server within your Home Assistant environment. It acts as a backend for complex astrological computations, offering a reliable API for various Home Assistant automations, integrations with Large Language Models (LLMs), or other external astrology tools. By keeping the computations local, it ensures privacy and faster response times.

---

## 🔮 Features

-   **Natal Chart Calculation:** Get precise positions of classical planets, lunar nodes, Lilith (Syzygy), Pars Fortuna, Ascendant, Midheaven, and house cusps based on birth data.
-   **Natal Aspects:** Calculate aspects between planets in the natal chart.
-   **Transit Chart Calculation:** Determine current planetary positions for any given date and time.
-   **Transit Aspects:** Compute interactive aspects between transit planets and natal chart positions, crucial for daily, monthly, or yearly forecasts.
-   **LLM Integration Ready:** Designed to provide structured astrological data (JSON) directly to LLMs (e.g., GPT, Claude, Ollama) for dynamic, personalized interpretations and guidance.
-   **Seamless Home Assistant Integration:** Easily used within Home Assistant automations, templates, and custom components.
-   **Local & Private:** All computations are performed locally on your Home Assistant server, ensuring your sensitive birth data remains private.
-   **Lightweight & Dockerized:** Built for efficiency and easy deployment within the Home Assistant Add-on ecosystem.

---

## 🚀 Installation

To install this add-on in your Home Assistant instance:

1.  **Add the Add-on Repository:**
    * Click the button below to directly add this repository to your Home Assistant Add-on Store:

        [![Add Repository to Home Assistant](https://my.home-assistant.io/badges/add_repository.svg)](https://my.home-assistant.io/redirect/add_repository/?repository_url=https://github.com/navi-vonamut/Flatlib-Natal-Chart-API)


    * Alternatively, you can manually add the repository:
        * In Home Assistant, navigate to **Settings** > **Add-ons** > **Add-on Store**.
        * Click the three dots in the top right corner and select **"Repositories"**.
        * Enter the URL of this GitHub repository:
            `https://github.com/navi-vonamut/Flatlib-Natal-Chart-AP`
        * Click "Add", then "Close".
2.  **Install the Add-on:**
    * Refresh the Add-on Store page (you might need to refresh your browser).
    * You should now see a new add-on named "**Flatlib Natal Chart API**". Click on it.
    * Click the **"Install"** button.

---

## 🛠️ Configuration

After installation, go to the **"Configuration"** tab of the add-on.

* **`log_level` (Logging Level):** Adjust the verbosity of the add-on's logs. Recommended: `info` for normal operation, `debug` for troubleshooting.

---

## 💡 API Usage

The add-on runs a Flask server, accessible within the Home Assistant Docker network at `http://a0d7b954-flatlib-server:8080`. From outside the Home Assistant host, you'll need to configure port forwarding in the add-on settings (default: 8080/tcp).

### Endpoints:

#### 1. Calculate Natal Chart (`POST /natal`)

Calculates a full natal chart including planets, special objects, angles, houses, and natal aspects.

* **URL:** `http://<ADDON_HOST_IP_OR_NAME>:8080/natal`
* **Content-Type:** `application/json`
* **Request Body (JSON):**
    ```json
    {
      "date": "YYYY-MM-DD",  
      "time": "HH:MM:SS",    
      "tz": "±HH:MM",       
      "lat": LATITUDE,      
      "lon": LONGITUDE      
    }
    ```
    * `date`: Birth date (e.g., "1990-05-03").
    * `time`: Birth time (e.g., "13:20:00").
    * `tz`: Timezone offset from UTC (e.g., "+03:00").
    * `lat`: Birth latitude (e.g., 56.2576).
    * `lon`: Birth longitude (e.g., 43.9827).

* **Example Response (JSON - truncated for brevity):**
    ```json
    {
      "planets": {
        "SUN": { "id": "SUN", "sign": "Taurus", "sign_pos": 12.73, "lon": 42.7302, ... },
        "MOON": { "id": "MOON", "sign": "Virgo", "sign_pos": 1.6, "lon": 151.6033, ... },
        ...
      },
      "special": { ... },
      "angles": { ... },
      "houses": { ... },
      "aspects": [
        { "p1_id": "SUN", "p2_id": "MERCURY", "type": "CONJUNCTION", "orb": 0.9, ... },
        ...
      ]
    }
    ```

#### 2. Calculate Transits (`POST /transits`)

Calculates transit aspects of current planets to natal chart positions.

* **URL:** `http://<ADDON_HOST_IP_OR_NAME>:8080/transits`
* **Content-Type:** `application/json`
* **Request Body (JSON):**
    ```json
    {
      "natal_date": "YYYY-MM-DD",   
      "natal_time": "HH:MM:SS",     
      "natal_tz": "±HH:MM",        
      "natal_lat": LATITUDE,       
      "natal_lon": LONGITUDE,      
      "transit_date": "YYYY-MM-DD", 
      "transit_time": "HH:MM:SS",   
      "transit_tz": "±HH:MM"        
    }
    ```
    * `natal_...`: Birth data (date, time, timezone, latitude, longitude).
    * `transit_...`: Date, time, and timezone for which transit positions should be calculated. Transit latitude/longitude default to natal.

* **Example Response (JSON - truncated for brevity):**
    ```json
    {
      "transit_aspects": [
        { "p1_id": "MARS", "p2_id": "ASC", "type": "OPPOSITION", "orb": 0.9, ... },
        ...
      ],
      "current_transits": {
        "SUN": { "id": "SUN", "sign": "Cancer", "sign_pos": 22.34, "lon": 112.34, ... },
        ...
      }
    }
    ```

#### 3. Health Check (`GET /health`)

Check the status and supported objects of the API.

* **URL:** `http://<ADDON_HOST_IP_OR_NAME>:8080/health`
* **Example Response (JSON):**
    ```json
    {
      "status": "OK",
      "version": "0.1.0",
      "supported_objects": {
        "planets": ["SUN", "MOON", ...],
        "special": ["NORTH_NODE", ...],
        "angles": ["ASC", "MC"],
        "aspects_calculated_for": ["SUN", "MOON", ...]
      }
    }
    ```

#### 4. Test Calculation (`GET /test`)

A simple test endpoint to verify core functionality with predefined data.

* **URL:** `http://<ADDON_HOST_IP_OR_NAME>:8080/test`
* **Example Response (JSON):**
    ```json
    {
      "status": "success",
      "sun_sign": "Taurus",
      "asc_sign": "Libra",
      "house_1_sign": "Libra",
      "test_aspect_count": 1
    }
    ```

---

## 🛠️ Tech Stack

* **Python:** 3.11+
* **`flatlib`:** `0.2.3` (Note: This specific version is used due to compatibility with `pyswisseph` and may have different API calls for aspects compared to newer `flatlib` versions.)
* **`pyswisseph`:** `2.8.0.post1`
* **Flask:** Lightweight web framework for the REST API.

---

## 🧠 Ideal for

* **Smart Home Automations:** Integrate into Home Assistant, Node-RED, or n8n for personalized astrological triggers or insights.
* **Telegram/Discord Bots:** Build bots that can provide astrological readings on demand.
* **Astrological Dashboards:** Create custom dashboards or reports leveraging computed data.
* **Voice Assistants & LLM Interpreters:** Feed structured astrological data to LLMs (like GPT, Claude, or local Ollama instances) for dynamic, human-like interpretations and guidance.

---

## 🐳 Docker Support

This add-on is designed to run within the Home Assistant Docker environment. The Dockerfile is included, allowing you to build and customize the image if needed.

---

## 🤝 Contribution

Contributions are welcome! If you have suggestions or find issues, please open an issue or submit a pull request on GitHub.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
