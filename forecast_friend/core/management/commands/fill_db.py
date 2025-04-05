from django.core.management.base import BaseCommand
from core.models import Country, City

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми странами и городами'

    def handle(self, *args, **kwargs):
        Country.objects.all().delete()
        
        countries = [
            {"name": "Франция", "cities": ["Париж", "Лион"]},
            {"name": "Италия", "cities": ["Рим", "Милан"]},
        ]
        
        for data in countries:
            country = Country.objects.create(name=data["name"])
            for city_name in data["cities"]:
                City.objects.create(country=country, name=city_name)
        
        self.stdout.write("База данных заполнена!")