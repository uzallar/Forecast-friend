# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Country(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.name

class City(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

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