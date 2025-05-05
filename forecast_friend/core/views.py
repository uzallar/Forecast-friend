from django.shortcuts import render, redirect
from .forms import CountryForm, RegisterForm, ProfileForm
from .models import City, Country
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .forms import WeatherForm
from .services import WeatherService
from .forms import TicketForm

import os
import pdfplumber
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import TicketUploadForm
from .models import TravelTicket
from .models import Ticket
from .services import parse_ticket_data  # Или используйте функцию прямо здесь

from datetime import datetime

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
        # Определяем какую форму использовать
        if 'pdf_file' in request.FILES:
            form = TicketUploadForm(request.POST, request.FILES)
        else:
            form = TicketForm(request.POST)

        if form.is_valid():
            ticket = form.save(commit=False)  # Создаем ticket только после валидации
            
            # Обработка PDF
            if 'pdf_file' in request.FILES:
                try:
                    with pdfplumber.open(ticket.pdf_file) as pdf:
                        text = "\n".join(page.extract_text() for page in pdf.pages)
                        data = parse_ticket_data(text)
                        
                        # Обновляем данные из PDF
                        ticket.country = data.get('country', '')
                        ticket.city = data.get('city', '')
                        ticket.date = data.get('date', None)
                        
                        messages.success(request, '✅ Билет успешно обработан из PDF!')
                except Exception as e:
                    if hasattr(ticket, 'pdf_file') and ticket.pdf_file:
                        try:
                            os.remove(ticket.pdf_file.path)
                        except:
                            pass
                    messages.error(request, f'❌ Ошибка обработки PDF: {str(e)}')
                    return render(request, 'core/add_ticket.html', {
                        'pdf_form': TicketUploadForm(),
                        'text_form': TicketForm()
                    })
            else:
                ticket.country = form.cleaned_data.get('country', '')
                ticket.city = form.cleaned_data.get('city', '')
                ticket.date = form.cleaned_data.get('date','')
                messages.info(request, 'Данные взяты из текстовых полей')
            
            
            # Сохраняем билет в любом случае
            ticket.save()
            return redirect('ticket_detail', pk=ticket.pk)
        
        # Если форма не валидна
        messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        # При GET-запросе
        form = TicketUploadForm()

    # Всегда возвращаем форму (при GET или невалидном POST)
    return render(request, 'core/add_ticket.html', {
        'pdf_form': TicketUploadForm(),
        'text_form': TicketForm()
    })
    
   

def ticket_detail_view(request, pk):
    try:
        if 'pdf_file' in request.FILES:
            ticket = TravelTicket.objects.get(pk=pk)
        else:
            ticket=Ticket.objects.get(pk=pk)
        
        # Форматируем дату
        formatted_date = ticket.date.strftime('%d.%m.%Y') if ticket.date else 'Дата не указана' 
        
        # Проверяем источник данных
        data_source = 'PDF' if ticket.pdf_file else 'текстовые поля'
        
        return render(request, 'core/ticket_detail.html', {
            'ticket': ticket,
            'formatted_date': formatted_date,
            'data_source': data_source
        })
    except TravelTicket.DoesNotExist:
        messages.error(request, 'Билет не найден')
        return redirect('add_ticket')
