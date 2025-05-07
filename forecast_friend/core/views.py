from django.shortcuts import render, redirect
from .forms import CountryForm, RegisterForm, ProfileForm, ReviewForm
from .models import City, Country, Review
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
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

from django.shortcuts import render
from .models import Country

def country_list(request):
    search_query = request.GET.get('search', '').title().strip()
    
    if search_query:
        countries = Country.objects.filter(name__icontains=search_query)
    else:
        countries = Country.objects.all()
    
    countries = countries.prefetch_related('visits')
    
    return render(request, 'core/country_list.html', {
        'countries': countries,
        'search_query': search_query
    })



def edit_country(request, country_id):
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав доступа к этой странице.')
        return redirect('profile')
    country = get_object_or_404(Country, id=country_id)
    if request.method == 'POST':
        form = CountryForm(request.POST, instance=country)
        if form.is_valid():
            form.save()
            return redirect('country_list')
    else:
        form = CountryForm(instance=country)
    
    return render(request, 'core/edit_country.html', {
        'form': form,
        'country': country
    })


def delete_country(request, country_id):
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав доступа к этой странице.')
        return redirect('profile')
    country = get_object_or_404(Country, id=country_id)
    if request.method == 'POST':
        country.delete()
        return redirect('country_list')
    return render(request, 'core/confirm_delete.html', {'country': country})


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
    initial_data = {}
    auto_fetch = False
    ticket_id = None
    
    # Получаем параметры из GET-запроса
    if 'city' in request.GET:
        initial_data['city'] = request.GET['city']
        auto_fetch = True
    
    if 'date' in request.GET:
        initial_data['date'] = request.GET['date']
    
    if 'ticket_id' in request.GET:
        ticket_id = request.GET['ticket_id']
    
    if request.method == 'POST':
        form = WeatherForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['city']
            date = form.cleaned_data.get('date')
            try:
                weather_data = WeatherService.get_weather(city_name, date=date)
                weather_data['city'] = city_name
                # Всегда добавляем дату, даже если она не указана в форме
                weather_data['date'] = date if date else timezone.now().date()
            except ValueError as e:
                error = str(e)
    else:
        form = WeatherForm(initial=initial_data)
        
        if auto_fetch and initial_data['city']:
            try:
                date = initial_data.get('date')
                weather_data = WeatherService.get_weather(initial_data['city'], date=date)
                weather_data['city'] = initial_data['city']
                # Всегда добавляем дату
                weather_data['date'] = date if date else timezone.now().date()
            except ValueError as e:
                error = str(e)
    
    return render(request, 'core/weather.html', {
        'form': form,
        'weather': weather_data,
        'error': error,
        'auto_fetched': auto_fetch,
        'ticket_id': ticket_id
    })


def add_ticket_view(request):
    if request.method == 'POST':
        # Определяем какую форму использовать
        if 'pdf_file' in request.FILES:
            form = TicketUploadForm(request.POST, request.FILES)
            is_pdf = True
        else:
            form = TicketForm(request.POST)
            is_pdf = False

        if form.is_valid():
            try:
                if is_pdf:
                    # Создаем объект билета, но пока не сохраняем
                    ticket = form.save(commit=False)
                    
                    # Обработка PDF
                    with pdfplumber.open(ticket.pdf_file) as pdf:
                        text = "\n".join(page.extract_text() for page in pdf.pages)
                        data = parse_ticket_data(text)
                        
                        # Заполняем поля из распарсенных данных
                        ticket.country = data.get('country', '')
                        ticket.city = data.get('city', '')
                        ticket.date = data.get('date', None)
                        
                        # Сохраняем билет в базу
                        ticket.save()
                        
                        messages.success(request, '✅ Билет успешно обработан из PDF!')
                        return redirect('ticket_detail', pk=ticket.pk)
                else:
                    # Обработка обычной формы
                    ticket = form.save()
                    messages.success(request, '✅ Билет успешно сохранён!')
                    return redirect('ticket_detail', pk=ticket.pk)
                    
            except Exception as e:
                # Удаляем временный файл, если он был создан
                if is_pdf and 'ticket' in locals() and hasattr(ticket, 'pdf_file'):
                    try:
                        os.remove(ticket.pdf_file.path)
                    except:
                        pass
                
                messages.error(request, f'❌ Ошибка: {str(e)}')
                return render(request, 'core/add_ticket.html', {
                    'pdf_form': TicketUploadForm(),
                    'text_form': TicketForm()
                })
    
    # GET запрос или невалидная форма
    return render(request, 'core/add_ticket.html', {
        'pdf_form': TicketUploadForm(),
        'text_form': TicketForm()
    })

from django.shortcuts import get_object_or_404

def ticket_detail_view(request, pk):
    # Пробуем найти билет в обеих моделях
    ticket = get_object_or_404(Ticket, pk=pk) if Ticket.objects.filter(pk=pk).exists() else get_object_or_404(TravelTicket, pk=pk)
    
    # Форматируем дату
    formatted_date = ticket.date.strftime('%d.%m.%Y') if ticket.date else 'Дата не указана'
    
    # Проверяем источник данных
    data_source = 'PDF' if hasattr(ticket, 'pdf_file') and ticket.pdf_file else 'текстовые поля'
    
    return render(request, 'core/ticket_detail.html', {
        'ticket': ticket,
        'formatted_date': formatted_date,
        'data_source': data_source
    })
    
def review_page(request):
    reviews = Review.objects.filter(is_visible=True).order_by('-created_at')
    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.save()
        return redirect('review_page')

    return render(request, 'reviews.html', {'form': form, 'reviews': reviews})

def delete_review(request, review_id):
    review = Review.objects.get(id=review_id)
    review.delete()
    return redirect('review_page')

def travel_recommendations(request):
    # Здесь будет логика для рекомендаций по поездке
    return render(request, 'core/travel_recommendations.html')

def add_admin(request):
    # Здесь будет логика для рекомендаций по поездке
    return render(request, 'core/add_admin.html')