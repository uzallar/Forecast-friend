from django.core.management.base import BaseCommand
from core.models import Country, City

class Command(BaseCommand):
    help = 'Заполняет базу данных городами'
    
    def handle(self, *args, **options):
        # Пример добавления городов
        russia, _ = Country.objects.get_or_create(name='Россия')
        usa, _ = Country.objects.get_or_create(name='США')
        
        cities = [
            {'name': 'Москва', 'country': russia, 'latitude': 55.7558, 'longitude': 37.6176},
            {'name': 'Санкт-Петербург', 'country': russia, 'latitude': 59.9343, 'longitude': 30.3351},
            {'name': 'Нью-Йорк', 'country': usa, 'latitude': 40.7128, 'longitude': -74.0060},
            {'name': 'Лондон', 'country': Country.objects.get_or_create(name='Великобритания')[0], 
             'latitude': 51.5074, 'longitude': -0.1278}
        ]
        
        for city_data in cities:
            City.objects.get_or_create(**city_data)
        
        self.stdout.write(self.style.SUCCESS('Города успешно добавлены!'))