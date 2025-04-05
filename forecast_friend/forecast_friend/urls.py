"""
URL configuration for forecast_friend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
# from django.urls import path
# from core.views import country_list
# from django.contrib.auth import views as auth_views


# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('countries/', country_list, name='country_list'),
#     path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
#     path('logout/', auth_views.LogoutView.as_view(), name='logout'),
#     path('countries/', country_list, name='country_list'),
#     path('countries/add/', add_country, name='add_country'),
# ]

from django.contrib import admin
from django.urls import path
from core.views import country_list, add_country  # Явный импорт обеих функций

urlpatterns = [
    path('admin/', admin.site.urls),
    path('countries/', country_list, name='country_list'),
    path('countries/add/', add_country, name='add_country'),
]
