import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from requests.exceptions import RequestException
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    @staticmethod
    def get_weather(city_name):
        """
        Получает погоду для любого введённого города через API
        """
        cache_key = f"weather_{city_name}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        try:
            # 1. Сначала получаем координаты города
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={settings.OPENWEATHERMAP_API_KEY}"
            geo_response = requests.get(geo_url)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            
            if not geo_data:
                raise ValueError("Город не найден")

            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
            found_city_name = geo_data[0]['name']

            # 2. Получаем погоду по координатам
            weather_url = (
                f"https://api.openweathermap.org/data/2.5/weather?"
                f"lat={lat}&lon={lon}"
                f"&appid={settings.OPENWEATHERMAP_API_KEY}"
                f"&units=metric&lang=ru"
            )
            weather_response = requests.get(weather_url)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            # Форматируем результат
            result = {
                'city': found_city_name,
                'temperature': weather_data['main']['temp'],
                'feels_like': weather_data['main']['feels_like'],
                'humidity': weather_data['main']['humidity'],
                'description': weather_data['weather'][0]['description'],
                'icon': weather_data['weather'][0]['icon'],
            }
            
            cache.set(cache_key, result, settings.WEATHER_API_CACHE_TIMEOUT)
            return result

        except RequestException as e:
            logger.error(f"Ошибка API: {e}")
            raise ValueError("Сервис погоды временно недоступен")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            raise ValueError("Не удалось получить данные о погоде")