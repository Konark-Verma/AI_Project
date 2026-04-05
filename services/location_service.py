import requests


def get_coordinates(city):
    """Get coordinates for a city using Nominatim (OpenStreetMap API)"""
    try:
        from geopy.geocoders import Nominatim

        geo = Nominatim(user_agent="ai_travel_planner")
        location = geo.geocode(city, timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except Exception as e:
        print(f"Geocoding error: {e}")

    return (20.5937, 78.9629)

def get_weather(city):
    """Fetch real-time weather data from Open-Meteo API (free, no key required)"""
    try:
        coords = get_coordinates(city)
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": coords[0],
            "longitude": coords[1],
            "current": "temperature_2m,weather_code,relative_humidity_2m,weather_description",
            "timezone": "auto"
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            return {
                "temperature": f"{current.get('temperature_2m', 'N/A')}°C",
                "weather": current.get('weather_description', 'Not available'),
                "humidity": f"{current.get('relative_humidity_2m', 'N/A')}%"
            }
    except Exception as e:
        print(f"Weather API error: {e}")
    
    return {"temperature": "N/A", "weather": "Data unavailable", "humidity": "N/A"}

def get_currency_rate(from_currency="USD", to_currency="INR"):
    """Get real exchange rates from Open Exchange Rates or FIXER (free tier available)"""
    try:
        # Using exchangerate-api.com (free tier, 1500 requests/month)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            rate = data.get("rates", {}).get(to_currency, 1)
            return rate
    except Exception as e:
        print(f"Currency API error: {e}")
    return 1.0