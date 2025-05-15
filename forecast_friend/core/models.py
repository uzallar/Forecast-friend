# Create your models here.
from django.db import models
from django.contrib.auth.models import User

import os
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64

class Country(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.name



    def generate_visits_chart(self):
        cache_key = f"country_chart_{self.id}"
        cached_chart = cache.get(cache_key)
        
        if cached_chart:
            return cached_chart
            
        # Генерация графика (код из предыдущего примера)
        chart = self._generate_chart()
        
        # Кэшируем на 1 час
        cache.set(cache_key, chart, 3600)
        return chart
    
    def _generate_chart(self):
        # Перенесите сюда код генерации графика
        # из предыдущего метода generate_visits_chart
        pass
        
    def generate_visits_chart(self):
        visits = list(self.visits.all().order_by('month'))
        if not visits:
            return None
            
        months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 
                 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        visit_counts = [v.visit_count for v in visits]
        
        plt.figure(figsize=(10, 4))
        sns.set_theme(style="whitegrid")
        ax = sns.barplot(x=months, y=visit_counts, palette="Blues_d")
        
        ax.set_title(f'Посещаемость {self.name} по месяцам')
        ax.set_xlabel('Месяц')
        ax.set_ylabel('Количество посещений')
        
        # Сохраняем в base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{image_base64}"

class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name}, {self.country.name}"

class WeatherData(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    date = models.DateField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    
    def __str__(self):
        return f"{self.city.name} - {self.date}"

class ClothingRecommendation(models.Model):
    weather = models.ForeignKey(WeatherData, on_delete=models.CASCADE)
    recommendation = models.CharField(max_length=200)
    
    def __str__(self):
        return self.recommendation

class TravelTicket(models.Model):
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    date = models.DateField()
    pdf_file = models.FileField(upload_to='tickets/pdfs/', blank=True, null=True)    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city}, {self.country} - {self.date.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'


class Ticket(models.Model):
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    date = models.DateField()
    pdf_file = models.FileField(upload_to='tickets/pdfs/', blank=True, null=True)
    ticket_image = models.ImageField(upload_to='tickets/images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

def __str__(self):
        return f"{self.country} - {self.city} ({self.date.strftime('%d.%m.%Y')})"
class Meta:
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField("Текст отзыва")
    created_at = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True)  # 👈 для скрытия/показа

    def __str__(self):
        return f"Отзыв от {self.user.username}"

class CountryVisit(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='visits')
    month = models.PositiveSmallIntegerField()  # 1-12
    visit_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('country', 'month')
        ordering = ['month']
    
    def __str__(self):
        return f"{self.country.name} - {self.month}: {self.visit_count} visits"