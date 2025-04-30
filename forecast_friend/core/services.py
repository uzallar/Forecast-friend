import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from requests.exceptions import RequestException
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    @staticmethod
    def get_weather(city_name, date=None):
        """
        Получает погоду для указанного города
        :param city_name: Название города
        :param date: Дата (если None - текущая дата)
        :return: Словарь с данными о погоде
        """
        if date is None:
            date = timezone.now().date()
        
        cache_key = f"weather_{city_name}_{date}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        try:
            # Получаем координаты города
            from .models import City
            city = City.objects.filter(name__iexact=city_name).first()
            if not city or not city.latitude or not city.longitude:
                raise ValueError("Город не найден или не указаны координаты")
            
            # Делаем запрос к API
            url = (
                f"https://api.openweathermap.org/data/2.5/weather?"
                f"lat={city.latitude}&lon={city.longitude}"
                f"&appid={settings.OPENWEATHERMAP_API_KEY}"
                f"&units=metric&lang=ru"
            )
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Форматируем данные
            weather_data = {
                'city': city_name,
                'date': date,
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon'],
            }
            
            # Кешируем результат
            cache.set(cache_key, weather_data, settings.WEATHER_API_CACHE_TIMEOUT)
            return weather_data
            
        except RequestException as e:
            logger.error(f"Ошибка запроса к API погоды: {e}")
            raise ValueError("Сервис погоды временно недоступен")
        except Exception as e:
            logger.error(f"Ошибка при получении погоды: {e}")
            raise ValueError("Не удалось получить данные о погоде")