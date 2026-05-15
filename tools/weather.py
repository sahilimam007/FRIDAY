import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import config
from tools.location import get_location

def get_weather():
    lat, lon, city = get_location()

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m", "apparent_temperature", "weathercode",
            "windspeed_10m", "relativehumidity_2m", "precipitation"
        ],
        "daily": ["temperature_2m_max", "temperature_2m_min"],
        "timezone": "auto",
        "forecast_days": 1
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    current = data["current"]
    daily = data["daily"]

    code = current["weathercode"]
    descriptions = {
        0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "foggy", 48: "foggy", 51: "light drizzle", 53: "drizzle",
        55: "heavy drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
        71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
        81: "rain showers", 82: "heavy rain showers", 95: "thunderstorm",
        96: "thunderstorm with hail", 99: "thunderstorm with hail"
    }
    desc = descriptions.get(code, "unknown")

    temp     = current["temperature_2m"]
    feels    = current["apparent_temperature"]
    humidity = current["relativehumidity_2m"]
    wind     = current["windspeed_10m"]
    rain     = current["precipitation"]
    high     = daily["temperature_2m_max"][0]
    low      = daily["temperature_2m_min"][0]

    summary = (
        f"Current weather in {city}: {desc}, {temp}°C (feels like {feels}°C). "
        f"Humidity {humidity}%, wind {wind} km/h. "
        f"Today's high {high}°C, low {low}°C. "
        f"Rainfall today: {rain}mm."
    )
    return summary

if __name__ == "__main__":
    print(get_weather())