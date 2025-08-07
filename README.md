# Home Assistant Flatlib Astrology API

A powerful Home Assistant Add-on providing a local **FastAPI** backend for advanced astrological calculations using [Flatlib](https://github.com/flatangle/flatlib) and [Swiss Ephemeris](https://www.astro.com/swisseph/).

-----

## ✨ Overview

This add-on runs a high-performance **FastAPI server** directly within your Home Assistant environment. It serves as a robust backend for complex astrological computations, offering a reliable and fast API. By performing all calculations locally, it ensures your sensitive personal data remains private and secure.

The add-on is designed to support a wide range of use cases, from simple automations to feeding structured data to Large Language Models (LLMs) for dynamic, personalized interpretations.

-----

## 🚀 Key Features (v0.2.0)

  - **Backend Migration to FastAPI**: The server has been completely rewritten from Flask to FastAPI, offering significantly improved performance, asynchronous support, and modern API documentation.
  - **Natal Chart Calculation**: Get a complete natal chart, including planets, lunar nodes, Lilith (Syzygy), Pars Fortuna, Ascendant, Midheaven, and house cusps.
  - **Daily, Monthly, & Yearly Horoscopes**: New API endpoints to calculate **transits** and **predictions** for specific dates, months, or years.
  - **Synastry Calculation**: An all-new endpoint to calculate compatibility between two natal charts.
  - **LLM Integration Ready**: Designed to provide structured astrological data (JSON) directly to LLMs (e.g., GPT, Claude, Ollama) for personalized interpretations.
  - **Local & Private**: All computations are performed locally on your Home Assistant server, ensuring sensitive birth data never leaves your network.

-----

## 🔧 Installation

To install this add-on in your Home Assistant instance:

1.  **Add the Add-on Repository:**
      - Click the button below to add this repository to your Home Assistant Add-on Store:
        [](https://www.google.com/search?q=%5Bhttps://my.home-assistant.io/redirect/supervisor_add_addon_repository/%3Frepository_url%3Dhttps%253A%252F%252Fgithub.com%252Fnavi-vonamut%252FFlatlib-Natal-Chart-AP%5D\(https://my.home-assistant.io/redirect/supervisor_add_addon_repository/%3Frepository_url%3Dhttps%253A%252F%252Fgithub.com%252Fnavi-vonamut%252FFlatlib-Natal-Chart-AP\))
      - Or, manually add the repository URL: `https://github.com/navi-vonamut/Flatlib-Natal-Chart-AP`
2.  **Install the Add-on:**
      - In the Add-on Store, find "**Flatlib Astrology API**" and click "Install".

-----

## 💻 API Endpoints

The FastAPI server is accessible within the Home Assistant Docker network at `http://a0d7b954-flatlib-server:8080`.

### 1\. Calculate Natal Chart (`POST /natal`)

  * **Request:**
    ```json
    {
      "date": "YYYY-MM-DD",
      "time": "HH:MM:SS",
      "tz": "±HH:MM",
      "lat": LATITUDE,
      "lon": LONGITUDE
    }
    ```
  * **Response:** A JSON object with all natal chart data, including planets, houses, angles, and aspects.

### 2\. Daily Prediction (`POST /predict/daily`)

  * **Request:** Same body as `/natal` plus a `target_date`.
    ```json
    {
      "date": "1990-05-03",
      "time": "13:20:00",
      "tz": "+03:00",
      "lat": 56.2576,
      "lon": 43.9827,
      "target_date": "2025-08-07"
    }
    ```
  * **Response:** Daily astrological predictions based on current transits.

### 3\. Monthly Prediction (`POST /predict/monthly`)

  * **Request:** Same as `/predict/daily`.
  * **Response:** Monthly predictions and transit data.

### 4\. Yearly Prediction (`POST /predict/yearly`)

  * **Request:** Same as `/predict/daily`.
  * **Response:** Yearly predictions and transit data.

### 5\. Synastry (`POST /synastry`)

  * **Request:**
    ```json
    {
      "chart1": { /* natal chart data for person 1 */ },
      "chart2": { /* natal chart data for person 2 */ }
    }
    ```
  * **Response:** Compatibility analysis between the two charts.

-----

## 🛠️ Tech Stack

  * **Python:** 3.11+
  * **`fastapi`**: The high-performance backend server.
  * **`flatlib`**: `0.2.3`
  * **`pyswisseph`**: `2.8.0.post1`

-----

## 🤝 Contribution

Contributions are welcome\! If you have suggestions or find issues, please open an issue or submit a pull request on GitHub.

-----

## 📄 License

This project is licensed under the [MIT License](https://www.google.com/search?q=LICENSE).