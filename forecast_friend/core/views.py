from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from .models import *
from .forms import *

from django.utils import timezone

import json
from datetime import timedelta
from django.contrib import messages
from .services import *
import os
import pdfplumber

from core.ml_models import (
    calculate_uv_index,
    predict_footwear,
    predict_bottom,
    predict_top,
    predict_accessories
)


def visits_statistics(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=6)

    visits_by_weekday = (
        Visit.objects.filter(visit_date__range=[start_date, end_date])
            .values('visit_date__week_day')
            .annotate(count=Count('id'))
            .order_by('visit_date__week_day')
    )

    weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    visits_data = {day: 0 for day in weekdays}

    for item in visits_by_weekday:
        day_index = item['visit_date__week_day'] - 2
        visits_data[weekdays[day_index]] = item['count']

    context = {
        'labels': json.dumps(weekdays, ensure_ascii=False),
        'data': json.dumps(list(visits_data.values())),
        'total_visits': sum(visits_data.values()),
        'average_visits': round(sum(visits_data.values()) / 7),
        'peak_day': max(visits_data, key=visits_data.get),
        'peak_visits': visits_data[max(visits_data, key=visits_data.get)],
    }

    return render(request, 'core/statistics.html', context)


def country_list(request):
    search_query = request.GET.get('search', '').strip()

    if search_query:
        countries = Country.objects.filter(name__icontains=search_query)
    else:
        countries = Country.objects.all()

    chart_data = []
    for country in countries:
        chart_data.append({
            'id': country.id,
            'name': country.name,
            'tourists': [
                country.tourists_winter or 0,
                country.tourists_spring or 0,
                country.tourists_summer or 0,
                country.tourists_autumn or 0,
            ]
        })

    context = {
        'countries': countries,
        'chart_data': chart_data,
        'search_query': search_query,
    }
    return render(request, 'core/country_list.html', context)


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
            country = form.save()
            messages.success(request, 'Страна успешно добавлена.')
            return redirect('country_list')
    else:
        form = CountryForm()

    return render(request, 'core/add_country.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('login')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки ниже.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def profile_view(request):
    return render(request, 'profile/profile.html', {'user': request.user})


def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'profile/edit_profile.html', {'form': form})


def weather_view(request):
    weather_data = None
    error = None
    initial_data = {}
    auto_fetch = False
    ticket_id = None

    topwear = bottomwear = footwear = accessories = None

    if 'city' in request.GET:
        initial_data['city'] = request.GET['city']
        auto_fetch = True

    if 'date' in request.GET:
        initial_data['date'] = request.GET['date']

    if 'ticket_id' in request.GET:
        ticket_id = request.GET['ticket_id']

    def get_recommendations(weather):
        temp = weather.get('temperature_2m_min', -20)
        feels_like = weather.get('feels_like', temp)
        wind = weather.get('apparent_temperature_max', 50)
        precip = weather.get('precipitation_sum', 0)
        humidity = weather.get('humidity', 50)
        condition = weather.get('weathercode', 'Sunny')

        ET0 = weather.get('et0_fao_evapotranspiration', 1)
        K = 1.0
        T_max = weather.get('temperature_2m_max', temp)
        WS_max = weather.get('wind_speed_max', wind)

        uv_index = calculate_uv_index(ET0, K, T_max, WS_max)

        return (
            predict_top(temp, feels_like, wind, precip, humidity, condition),
            predict_bottom(temp, feels_like, wind, precip, humidity, condition),
            predict_footwear(temp, feels_like, wind, precip, humidity, condition),
            predict_accessories(temp, feels_like, wind, precip, humidity, condition, uv_index)
        )

    if request.method == 'POST':
        form = WeatherForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['city']
            date = form.cleaned_data.get('date')
            try:
                weather_data = WeatherService.get_weather(city_name, date=date)
                weather_data['city'] = city_name
                weather_data['date'] = date or timezone.now().date()

                if weather_data:
                    topwear, bottomwear, footwear, accessories = get_recommendations(weather_data)
                else:
                    topwear = bottomwear = footwear = accessories = "Нет данных"
            except ValueError as e:
                error = str(e)
    else:
        form = WeatherForm(initial=initial_data)

        if auto_fetch and initial_data.get('city'):
            try:
                date = initial_data.get('date')
                weather_data = WeatherService.get_weather(initial_data['city'], date=date)
                weather_data['city'] = initial_data['city']
                weather_data['date'] = date or timezone.now().date()

                if weather_data:
                    topwear, bottomwear, footwear, accessories = get_recommendations(weather_data)
                else:
                    topwear = bottomwear = footwear = accessories = "Нет данных"
            except ValueError as e:
                error = str(e)

    return render(request, 'core/weather.html', {
        'form': form,
        'weather': weather_data,
        'error': error,
        'auto_fetched': auto_fetch,
        'ticket_id': ticket_id,
        'topwear': topwear,
        'bottomwear': bottomwear,
        'footwear': footwear,
        'accessories': accessories,
    })


def add_ticket_view(request):
    if request.method == 'POST':
        if 'pdf_file' in request.FILES:
            form = TicketUploadForm(request.POST, request.FILES)
            is_pdf = True
        else:
            form = TicketForm(request.POST)
            is_pdf = False

        if form.is_valid():
            try:
                if is_pdf:
                    ticket = form.save(commit=False)
                    with pdfplumber.open(ticket.pdf_file) as pdf:
                        text = "\n".join(page.extract_text() for page in pdf.pages)
                        data = parse_ticket_data(text)

                        ticket.country = data.get('country', '')
                        ticket.city = data.get('city', '')
                        ticket.date = data.get('date', None)

                        ticket.save()

                        messages.success(request, '✅ Билет успешно обработан из PDF!')
                        return redirect('ticket_detail', pk=ticket.pk)
                else:
                    ticket = form.save()
                    messages.success(request, '✅ Билет успешно сохранён!')
                    return redirect('ticket_detail', pk=ticket.pk)

            except Exception as e:
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

    return render(request, 'core/add_ticket.html', {
        'pdf_form': TicketUploadForm(),
        'text_form': TicketForm()
    })


def ticket_detail_view(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk) if Ticket.objects.filter(pk=pk).exists() else get_object_or_404(
        TravelTicket, pk=pk)

    formatted_date = ticket.date.strftime('%d.%m.%Y') if ticket.date else 'Дата не указана'

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

    return render(request, 'reviews/reviews.html', {'form': form, 'reviews': reviews})


def delete_review(request, review_id):
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав доступа к этой странице.')
        return redirect('profile')
    review = Review.objects.get(id=review_id)
    review.delete()
    return redirect('review_page')


def add_admin(request):
    return render(request, 'core/add_admin.html')
