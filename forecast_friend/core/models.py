import base64
from io import BytesIO

import matplotlib.pyplot as plt
import seaborn as sns
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.utils import timezone


class Country(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    tourists_winter = models.PositiveIntegerField(default=0, verbose_name="Туристы (зима)")
    tourists_spring = models.PositiveIntegerField(default=0, verbose_name="Туристы (весна)")
    tourists_summer = models.PositiveIntegerField(default=0, verbose_name="Туристы (лето)")
    tourists_autumn = models.PositiveIntegerField(default=0, verbose_name="Туристы (осень)")

    def __str__(self):
        return self.name

    def generate_visits_chart(self):
        cache_key = f"country_chart_{self.id}"
        cached_chart = cache.get(cache_key)
        if cached_chart:
            return cached_chart

        visits = self.seasonal_visits.all()
        if not visits.exists():
            return None

        seasons = ['Зима', 'Весна', 'Лето', 'Осень']
        season_map = {'winter': 'Зима', 'spring': 'Весна', 'summer': 'Лето', 'autumn': 'Осень'}
        visit_counts = {season: 0 for season in seasons}

        for visit in visits:
            visit_counts[season_map[visit.season]] = visit.visit_count

        plt.figure(figsize=(8, 4))
        sns.set_theme(style="whitegrid")
        ax = sns.barplot(x=seasons, y=[visit_counts[s] for s in seasons], palette="coolwarm")

        ax.set_title(f'Посещаемость {self.name} по сезонам')
        ax.set_xlabel('Сезон')
        ax.set_ylabel('Количество посещений')

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()

        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        cache.set(cache_key, f"data:image/png;base64,{image_base64}", 3600)

        return f"data:image/png;base64,{image_base64}"


class Visit(models.Model):
    ip_address = models.CharField(max_length=50)
    user_agent = models.TextField(blank=True, null=True)
    visit_date = models.DateField(default=timezone.now)
    visit_time = models.TimeField(default=timezone.now)
    path = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['visit_date']),
        ]

    def __str__(self):
        return f"Visit from {self.ip_address} at {self.visit_date}"


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
    is_visible = models.BooleanField(default=True)

    def __str__(self):
        return f"Отзыв от {self.user.username}"


SEASON_CHOICES = [
    ('winter', 'Winter'),
    ('spring', 'Spring'),
    ('summer', 'Summer'),
    ('autumn', 'Autumn'),
]


class CountryVisit(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='visits')
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, default='summer')
    visit_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('country', 'season')
        ordering = ['season']

    def __str__(self):
        return f"{self.country.name} - {self.season}: {self.visit_count} visits"


class SeasonalVisit(models.Model):
    SEASONS = [
        ('winter', 'Зима'),
        ('spring', 'Весна'),
        ('summer', 'Лето'),
        ('autumn', 'Осень'),
    ]

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='seasonal_visits')
    season = models.CharField(max_length=10, choices=SEASONS)
    visit_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('country', 'season')

    def __str__(self):
        return f"{self.country.name} — {self.get_season_display()}: {self.visit_count}"
