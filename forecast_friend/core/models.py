# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Country(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.name

    def get_visits_chart_data(self):
        visits = list(self.visits.all().order_by('month'))
        if not visits:
            visits = [CountryVisit(visit_count=0) for _ in range(12)]
        
        max_visits = max(v.visit_count for v in visits) if any(v.visit_count for v in visits) else 1
        
        return {
            'months': ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 
                      'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
            'visits': visits,
            'max_visits': max_visits
        }

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