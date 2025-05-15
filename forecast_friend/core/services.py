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
        Получает прогноз погоды на дату с Open-Meteo, координаты — с OpenWeatherMap.
        """
        if isinstance(date, str):
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD")

        # Кеширование
        cache_key = f"weather_meteo_{city_name}_{date.isoformat() if date else 'today'}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Получаем координаты города через OpenWeatherMap
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={settings.OPENWEATHERMAP_API_KEY}"
        geo_resp = requests.get(geo_url)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        if not geo_data:
            raise ValueError("Город не найден")

        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        found_city_name = geo_data[0]['name']

        # Получаем прогноз с Open-Meteo
        meteo_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,relative_humidity_2m,pressure_msl,windspeed_10m"
            f"&timezone=auto"
        )

        meteo_resp = requests.get(meteo_url)
        meteo_resp.raise_for_status()
        meteo_data = meteo_resp.json()

        # Парсим нужную дату
        target_date = date or timezone.now().date()
        hourly_times = meteo_data["hourly"]["time"]
        temps = meteo_data["hourly"]["temperature_2m"]
        humidities = meteo_data["hourly"]["relative_humidity_2m"]
        pressures = meteo_data["hourly"]["pressure_msl"]
        winds = meteo_data["hourly"]["windspeed_10m"]

        # Отбираем все часы на нужную дату
        filtered = [
            (datetime.fromisoformat(time_str), temp, hum, pres, wind)
            for time_str, temp, hum, pres, wind in zip(hourly_times, temps, humidities, pressures, winds)
            if datetime.fromisoformat(time_str).date() == target_date
        ]

        if not filtered:
            raise ValueError("Нет погодных данных на указанную дату")

        # Вычисляем средние значения
        avg_temp = round(sum(f[1] for f in filtered) / len(filtered), 1)
        avg_hum = round(sum(f[2] for f in filtered) / len(filtered), 0)
        avg_pres = round(sum(f[3] for f in filtered) / len(filtered), 0)
        avg_wind = round(sum(f[4] for f in filtered) / len(filtered), 1)

        result = {
            "city": found_city_name,
            "date": target_date,
            "temperature": avg_temp,
            "feels_like": avg_temp,
            "humidity": avg_hum,
            "pressure": avg_pres,
            "wind_speed": avg_wind,
            "description": "Температура по Open-Meteo",
            "icon": "01d"  # Можешь заменить на своё или убрать
        }

        cache.set(cache_key, result, 60 * 60)  # 1 час кеш
        return result

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