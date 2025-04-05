# Create your views here.


from django.shortcuts import render
from .models import Country

def country_list(request):
    countries = Country.objects.all()
    return render(request, 'country_list.html', {'countries': countries})