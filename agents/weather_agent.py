"""
Weather Agent - Provides weather information
"""

import os
import requests
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class WeatherAgent:
    """Handles weather data from WeatherAPI"""
    
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.location = os.getenv("WEATHER_LOCATION", "Mumbai,IN")
        self.base_url = "http://api.weatherapi.com/v1"
        
    async def initialize(self):
        """Verify weather API connection"""
        try:
            if not self.api_key:
                logger.warning("⚠️ WEATHER_API_KEY not set, using mock data")
                return True
                
            weather = await self.get_current_weather()
            if weather.get("condition"):
                logger.info("✅ Weather API connected")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Weather Agent init error: {e}")
            return False
    
    async def get_current_weather(self) -> Dict:
        """Get current weather conditions"""
        
        # Mock data if no API key
        if not self.api_key:
            return {
                "location": "Mumbai, India",
                "temp": 28,
                "feels_like": 30,
                "condition": "Partly Cloudy",
                "humidity": 65,
                "wind_kph": 15,
                "uv_index": 6,
                "last_updated": "2025-01-01 12:00"
            }
        
        try:
            response = requests.get(
                f"{self.base_url}/current.json",
                params={
                    "key": self.api_key,
                    "q": self.location,
                    "aqi": "no"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                current = data['current']
                location = data['location']
                
                return {
                    "location": f"{location['name']}, {location['country']}",
                    "temp": current['temp_c'],
                    "feels_like": current['feelslike_c'],
                    "condition": current['condition']['text'],
                    "humidity": current['humidity'],
                    "wind_kph": current['wind_kph'],
                    "uv_index": current['uv'],
                    "last_updated": current['last_updated']
                }
            
            logger.warning(f"Weather API returned status {response.status_code}")
            return {"error": "Unable to fetch weather"}
            
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return {"error": str(e)}
    
    async def get_forecast(self, days: int = 3) -> List[Dict]:
        """Get weather forecast"""
        
        # Mock data if no API key
        if not self.api_key:
            return [
                {
                    "date": "2025-01-01",
                    "max_temp": 30,
                    "min_temp": 22,
                    "condition": "Sunny",
                    "chance_of_rain": 10,
                    "sunrise": "06:45 AM",
                    "sunset": "06:30 PM"
                }
            ] * days
        
        try:
            response = requests.get(
                f"{self.base_url}/forecast.json",
                params={
                    "key": self.api_key,
                    "q": self.location,
                    "days": days,
                    "aqi": "no"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                forecast_days = []
                
                for day in data['forecast']['forecastday']:
                    forecast_days.append({
                        "date": day['date'],
                        "max_temp": day['day']['maxtemp_c'],
                        "min_temp": day['day']['mintemp_c'],
                        "condition": day['day']['condition']['text'],
                        "chance_of_rain": day['day']['daily_chance_of_rain'],
                        "sunrise": day['astro']['sunrise'],
                        "sunset": day['astro']['sunset']
                    })
                
                return forecast_days
            
            return []
            
        except Exception as e:
            logger.error(f"Forecast fetch error: {e}")
            return []
    
    async def should_schedule_outdoor(self) -> Dict:
        """
        Determine if it's good weather for outdoor activities
        """
        weather = await self.get_current_weather()
        
        if "error" in weather:
            return {
                "recommended": False,
                "reason": "Unable to fetch weather data"
            }
        
        temp = weather.get("temp", 0)
        condition = weather.get("condition", "").lower()
        
        # Good conditions: 18-32°C, not raining
        good_temp = 18 <= temp <= 32
        no_rain = "rain" not in condition and "storm" not in condition
        
        if good_temp and no_rain:
            return {
                "recommended": True,
                "reason": f"Perfect weather! {temp}°C and {weather['condition']}"
            }
        elif not good_temp:
            return {
                "recommended": False,
                "reason": f"Temperature too {'hot' if temp > 32 else 'cold'} ({temp}°C)"
            }
        else:
            return {
                "recommended": False,
                "reason": f"Weather not ideal: {weather['condition']}"
            }