from django.shortcuts import render, redirect
from .forms import CountryForm, RegisterForm, ProfileForm
from .models import City, Country
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .forms import WeatherForm
from .services import WeatherService

def country_list(request):
    countries = Country.objects.all()
    return render(request, 'core/country_list.html', {'countries': countries})

def add_country(request):
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав доступа к этой странице.')
        return redirect('profile')
    if request.method == 'POST':
        form = CountryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('country_list')
    else:
        form = CountryForm()
    return render(request, 'core/add_country.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Регистрация прошла успешно! Теперь войдите в аккаунт.')
            return redirect('login')  # предполагаем, что у тебя есть URL с именем 'login'
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def profile_view(request):
    return render(request, 'profile.html', {'user': request.user})

def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('profile')  # после сохранения редиректим на страницу профиля
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'edit_profile.html', {'form': form})


def weather_view(request):
    weather_data = None
    error = None
    available_cities = City.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
    
    if request.method == 'POST':
        form = WeatherForm(request.POST)
        if form.is_valid():
            city = form.cleaned_data['city']
            try:
                city_obj = City.objects.get(name__iexact=city)
                weather_data = WeatherService.get_weather(city_obj.name)
            except City.DoesNotExist:
                error = f"Город '{city}' не найден. Доступные города: {', '.join([c.name for c in available_cities])}"
            except ValueError as e:
                error = str(e)
    else:
        form = WeatherForm()
    
    return render(request, 'core/weather.html', {
        'form': form,
        'weather': weather_data,
        'error': error,
        'available_cities': available_cities
    })