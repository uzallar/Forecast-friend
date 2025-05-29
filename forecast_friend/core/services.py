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
        Получает прогноз погоды на дату с Open-Meteo, используя дневной forecast.
        """
        if isinstance(date, str):
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD")

        target_date = date or timezone.now().date()
        cache_key = f"weather_meteo_daily_{city_name}_{target_date.isoformat()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Получаем координаты города через OpenWeatherMap
        try:
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={settings.OPENWEATHERMAP_API_KEY}"
            geo_resp = requests.get(geo_url)
            geo_resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if geo_resp.status_code == 429:
                logger.error("Превышен лимит запросов к OpenWeatherMap API")
                raise ValueError("Превышен лимит запросов к OpenWeatherMap API")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе гео-данных: {e}")
            raise ValueError("Ошибка при получении координат города")

        geo_data = geo_resp.json()

        if not geo_data:
            raise ValueError("Город не найден")

        lat = geo_data[0]['lat']
        lon = geo_data[0]['lon']
        found_city_name = geo_data[0]['name']

        # Формируем список всех доступных daily параметров
        daily_params = ",".join([
            "temperature_2m_max", "temperature_2m_min",
            "apparent_temperature_max", "apparent_temperature_min",
            "precipitation_sum", "rain_sum", "showers_sum", "snowfall_sum",
            "precipitation_hours", "windspeed_10m_max", "windgusts_10m_max",
            "winddirection_10m_dominant", "shortwave_radiation_sum",
            "et0_fao_evapotranspiration", "weathercode",
            "sunrise", "sunset"
        ])

        meteo_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&daily={daily_params}"
            f"&timezone=auto"
        )

        # Запрос к Open-Meteo
        try:
            meteo_resp = requests.get(meteo_url)
            meteo_resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if meteo_resp.status_code == 429:
                logger.error("Превышен лимит запросов к Open-Meteo API")
                raise ValueError("Превышен лимит запросов к Open-Meteo API")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Open-Meteo: {e}")
            raise ValueError("Ошибка при получении данных погоды")

        meteo_data = meteo_resp.json()

        # Найдём индекс нужной даты
        daily_dates = meteo_data.get("daily", {}).get("time", [])
        try:
            index = daily_dates.index(target_date.isoformat())
        except ValueError:
            raise ValueError("Нет погодных данных на указанную дату")

        # Соберем все данные по индексу
        result = {
            "city": found_city_name,
            "date": target_date,
        }
                # Русские названия для отображения
        field_translations = {
            "temperature_2m_max": "Максимальная температура воздуха",
            "temperature_2m_min": "Минимальная температура воздуха",
            "apparent_temperature_max": "Максимальная ощущаемая температура",
            "apparent_temperature_min": "Минимальная ощущаемая температура",
            "precipitation_sum": "Суммарное количество осадков",
            "rain_sum": "Количество дождя",
            "showers_sum": "Количество ливней",
            "snowfall_sum": "Количество снега",
            "precipitation_hours": "Часы с осадками",
            "windspeed_10m_max": "Максимальная скорость ветра (10 м)",
            "windgusts_10m_max": "Максимальные порывы ветра",
            "winddirection_10m_dominant": "Преобладающее направление ветра",
            "shortwave_radiation_sum": "Коротковолновая солнечная радиация",
            "et0_fao_evapotranspiration": "Эвапотранспирация по ФАО",
            "weathercode": "Код погоды",
            "sunrise": "Восход",
            "sunset": "Закат",
            "time": "Дата"
        }


        for key, values in meteo_data.get("daily", {}).items():
            if isinstance(values, list) and len(values) > index:
                translated_key = field_translations.get(key, key)
                result[translated_key] = values[index]


        cache.set(cache_key, result, 60 * 60)
        return result


    @staticmethod
    def _get_current_weather(lat, lon):
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
        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast?"
            f"lat={lat}&lon={lon}"
            f"&appid={settings.OPENWEATHERMAP_API_KEY}"
            f"&units=metric&lang=ru"
        )
        response = requests.get(forecast_url)
        response.raise_for_status()
        forecast_data = response.json()

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
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    if len(lines) < 3:
        raise ValueError("Файл должен содержать 3 строки: страна, город и дата")

    date_formats = [
        '%d.%m.%Y',
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%d %m %Y',
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
