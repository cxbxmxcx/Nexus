import os

import requests
from dotenv import load_dotenv

load_dotenv()


# @agent_action
def get_weather_for_city(city):
    """Provides real-time weather data for a given city."""
    api_key = os.getenv("OPEN_WEATHER_MAP_API_KEY", None)
    if not api_key:
        return "No OPEN_WEATHER_MAP_API_KEY key found. Please set the WEATHER_API_KEY environment variable to use this function."
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}appid={api_key}&q={city}"
    response = requests.get(complete_url)
    return response.json()
