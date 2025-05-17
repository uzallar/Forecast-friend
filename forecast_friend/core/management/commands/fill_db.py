from django.core.management.base import BaseCommand
from core.models import Country, CountryVisit
import random

class Command(BaseCommand):
    help = 'Fill initial visit data for countries'
    
    def handle(self, *args, **options):
        countries = Country.objects.all()
        
        for country in countries:
            # Создаем данные для каждого месяца
            for month in range(1, 13):
                # Генерируем случайные данные с учетом сезонности
                if month in [6, 7, 8]:  # лето - высокий сезон
                    visits = random.randint(800, 1200)
                elif month in [12, 1, 2]:  # зима - зависит от страны
                    visits = random.randint(400, 800)
                else:  # межсезонье
                    visits = random.randint(200, 500)
                
                CountryVisit.objects.create(
                    country=country,
                    month=month,
                    visit_count=visits
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully filled visit data'))