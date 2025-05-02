from django.shortcuts import render, redirect
from .forms import CountryForm, RegisterForm, ProfileForm, ReviewForm
from .models import City, Country, Review
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .forms import WeatherForm
from .services import WeatherService
import os
import pdfplumber
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import TicketUploadForm
from .models import TravelTicket
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
        form = TicketUploadForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            
            try:
                with pdfplumber.open(ticket.pdf_file) as pdf:
                    text = "\n".join(page.extract_text() for page in pdf.pages)
                    data = parse_ticket_data(text)
                    
                    ticket.country = data['country']
                    ticket.city = data['city']
                    ticket.date = data['date']
                    ticket.save()
                    
                    messages.success(request, '✅ Билет успешно обработан!')
                    return redirect('ticket_detail', pk=ticket.pk)
                    
            except Exception as e:
                # Удаляем файл если возникла ошибка
                if hasattr(ticket, 'pdf_file') and ticket.pdf_file:
                    try:
                        os.remove(ticket.pdf_file.path)
                    except:
                        pass
                messages.error(request, f'❌ Ошибка: {str(e)}')
    else:
        form = TicketUploadForm()
    
    return render(request, 'core/add_ticket.html', {'form': form})

def ticket_detail_view(request, pk):
    try:
        ticket = TravelTicket.objects.get(pk=pk)
        return render(request, 'core/ticket_detail.html', {
            'ticket': ticket,
            'formatted_date': ticket.date.strftime('%d.%m.%Y')
        })
    except TravelTicket.DoesNotExist:
        messages.error(request, 'Билет не найден')
        return redirect('add_ticket')
    
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