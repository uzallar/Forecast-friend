import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from requests.exceptions import RequestException
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class WeatherService:
    @staticmethod
    def get_weather(city_name, date=None):
        """
        Получает текущую погоду или прогноз для указанной даты
        Args:
            city_name: Название города
            date: Дата в формате date (если None - текущая погода)
        Returns:
            Словарь с данными о погоде
        """
        # Кешируем отдельно текущую погоду и прогнозы
        if isinstance(date, str):
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD")
        
    # Кешируем отдельно текущую погоду и прогнозы
        cache_key = f"weather_{city_name}_{date.isoformat() if date else 'current'}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        try:
            # 1. Получаем координаты города
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={settings.OPENWEATHERMAP_API_KEY}"
            geo_response = requests.get(geo_url)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            
            if not geo_data:
                raise ValueError("Город не найден")

            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
            found_city_name = geo_data[0]['name']

            # 2. Определяем тип запроса - текущая погода или прогноз
            if date is None:
                # Текущая погода
                weather_data = WeatherService._get_current_weather(lat, lon)
            else:
                # Прогноз на конкретную дату
                weather_data = WeatherService._get_forecast(lat, lon, date)

            # Форматируем результат
            result = {
                'city': found_city_name,
                'date': date if date else timezone.now().date(),  # Возвращаем объект date, а не строку
                'temperature': weather_data['temp'],
                'feels_like': weather_data.get('feels_like', weather_data['temp']),
                'humidity': weather_data['humidity'],
                'pressure': weather_data.get('pressure', 0),
                'wind_speed': weather_data.get('wind_speed', 0),
                'description': weather_data['weather'][0]['description'],
                'icon': weather_data['weather'][0]['icon'],
            }
            
            # Кешируем на разное время: текущую погоду - на меньшее время
            cache_time = settings.WEATHER_API_CACHE_TIMEOUT // 2 if date else settings.WEATHER_API_CACHE_TIMEOUT
            cache.set(cache_key, result, cache_time)
            return result

        except RequestException as e:
            logger.error(f"Ошибка API: {e}")
            raise ValueError("Сервис погоды временно недоступен")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            raise ValueError("Не удалось получить данные о погоде")

    @staticmethod
    def _get_current_weather(lat, lon):
        """Получает текущую погоду по координатам"""
        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"lat={lat}&lon={lon}"
            f"&appid={settings.OPENWEATHERMAP_API_KEY}"
            f"&units=metric&lang=ru"
        )
        response = requests.get(weather_url)
        response.raise_for_status()
        data = response.json()
        
        return {
            'temp': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'weather': data['weather'],
        }

    @staticmethod
    def _get_forecast(lat, lon, target_date):
        """Получает прогноз на конкретную дату"""
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast?"
            f"lat={lat}&lon={lon}"
            f"&appid={settings.OPENWEATHERMAP_API_KEY}"
            f"&units=metric&lang=ru"
        )
        response = requests.get(forecast_url)
        response.raise_for_status()
        forecast_data = response.json()
        
        # Находим ближайший прогноз к указанной дате
        target_datetime = datetime.combine(target_date, datetime.min.time())
        closest_forecast = None
        min_diff = timedelta.max
        
        for item in forecast_data['list']:
            forecast_datetime = datetime.fromtimestamp(item['dt'])
            time_diff = abs(forecast_datetime - target_datetime)
            
            if time_diff < min_diff:
                min_diff = time_diff
                closest_forecast = item
        
        if not closest_forecast:
            raise ValueError("Прогноз на указанную дату не найден")
        
        return {
            'temp': closest_forecast['main']['temp'],
            'feels_like': closest_forecast['main']['feels_like'],
            'humidity': closest_forecast['main']['humidity'],
            'pressure': closest_forecast['main']['pressure'],
            'wind_speed': closest_forecast['wind']['speed'],
            'weather': closest_forecast['weather'],
        }

def parse_ticket_data(text):
    """
    Парсит текст билета в формате:
    Страна
    Город
    Дата
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) < 3:
        raise ValueError("Файл должен содержать 3 строки: страна, город и дата")
    
    date_formats = [
        '%d.%m.%Y',  # 01.04.2025
        '%d/%m/%Y',   # 01/04/2025
        '%Y-%m-%d',   # 2025-04-01
        '%d %m %Y',   # 01 04 2025
    ]
    
    date = None
    for fmt in date_formats:
        try:
            date = datetime.strptime(lines[2], fmt).date()
            break
        except ValueError:
            continue
    
    if not date:
        raise ValueError(f"Неизвестный формат даты: {lines[2]}")
    
    return {
        'country': lines[0],
        'city': lines[1],
        'date': date
    }