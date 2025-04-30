from django.shortcuts import render, redirect
from .forms import CountryForm, RegisterForm, ProfileForm
from .models import City, Country
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .forms import WeatherForm
from .services import WeatherService

import pdfplumber
from .forms import TicketUploadForm
from .models import TravelTicket

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
    
    if request.method == 'POST':
        form = WeatherForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['city']
            try:
                weather_data = WeatherService.get_weather(city_name)
            except ValueError as e:
                error = str(e)
    else:
        form = WeatherForm()
    
    return render(request, 'core/weather.html', {
        'form': form,
        'weather': weather_data,
        'error': error
    })




def add_ticket_view(request):
    if request.method == 'POST':
        form = TicketUploadForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            
            try:
                # Парсим PDF
                with pdfplumber.open(ticket.pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"
                    
                    # Простая логика парсинга (может потребоваться доработка)
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    ticket.country = lines[0] if len(lines) > 0 else "Не указано"
                    ticket.city = lines[1] if len(lines) > 1 else "Не указано"
                    
                    # Парсим дату (пример для формата ДД.ММ.ГГГГ)
                    from datetime import datetime
                    try:
                        ticket.date = datetime.strptime(lines[2], '%d.%m.%Y').date()
                    except:
                        ticket.date = datetime.now().date()
                    
                    ticket.save()
                    messages.success(request, 'Билет успешно загружен и обработан!')
                    return redirect('ticket_detail', pk=ticket.pk)
                    
            except Exception as e:
                messages.error(request, f'Ошибка при обработке PDF: {str(e)}')
    else:
        form = TicketUploadForm()
    
    return render(request, 'core/add_ticket.html', {'form': form})

def ticket_detail_view(request, pk):
    ticket = TravelTicket.objects.get(pk=pk)
    return render(request, 'core/ticket_detail.html', {'ticket': ticket})