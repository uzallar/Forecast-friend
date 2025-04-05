from django.shortcuts import render, redirect
from .forms import CountryForm
from .models import Country

def country_list(request):
    countries = Country.objects.all()
    return render(request, 'core/country_list.html', {'countries': countries})

def add_country(request):
    if request.method == 'POST':
        form = CountryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('country_list')
    else:
        form = CountryForm()
    return render(request, 'core/add_country.html', {'form': form})