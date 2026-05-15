import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

def get_city_from_coords(lat, lon):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "Jarvis/1.0"},
            timeout=5
        )
        data = r.json()
        city = (data.get("address", {}).get("city") or
                data.get("address", {}).get("town") or
                data.get("address", {}).get("village") or
                "your location")
        return city
    except:
        return "your location"

def get_location():
    """Returns (lat, lon, city) using IP geolocation. Falls back to Kolkata."""
    import config
    try:
        r = requests.get("http://ip-api.com/json/", timeout=5)
        data = r.json()
        if data.get("status") == "success":
            lat = data["lat"]
            lon = data["lon"]
            city = data.get("city", "your location")
            return lat, lon, city
    except:
        pass

    return config.WEATHER_LAT, config.WEATHER_LON, "Kolkata"

if __name__ == "__main__":
    lat, lon, city = get_location()
    print(f"Location: {city} ({lat:.4f}, {lon:.4f})")
