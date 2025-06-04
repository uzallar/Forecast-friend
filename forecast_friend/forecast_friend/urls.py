from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from core.views import *


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),
    path('stats/', visits_statistics, name='visits_stats'),

    
    path('countries/', country_list, name='country_list'),
    path('countries/edit/<int:country_id>/', edit_country, name='edit_country'),
    path('countries/delete/<int:country_id>/', delete_country, name='delete_country'),
    path('countries/add/', add_country, name='add_country'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('weather/', weather_view, name='weather'),
    path('add_ticket/', add_ticket_view, name='add_ticket'),
    path('ticket/<int:pk>/', ticket_detail_view, name='ticket_detail'),
    path('admin/', add_admin, name='add_admin'),
    path('reviews/', review_page, name='review_page'),
    path('reviews/delete/<int:review_id>/', delete_review, name='delete_review'),
    path('', RedirectView.as_view(url='weather/', permanent=True)),
]