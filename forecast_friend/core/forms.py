from django import forms
from .models import Country
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserChangeForm
from .models import TravelTicket

class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'description']

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class ProfileForm(UserChangeForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')



class WeatherForm(forms.Form):
    city = forms.CharField(
        label='Город',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название города'
        })
    )
    date = forms.DateField(
        label='Дата',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'min': timezone.now().date().isoformat()
        }),
        required=False,
        initial=timezone.now().date
    )




class TicketUploadForm(forms.ModelForm):
    class Meta:
        model = TravelTicket
        fields = ['pdf_file']
        widgets = {
            'pdf_file': forms.FileInput(attrs={
                'accept': '.pdf',
                'class': 'form-control'
            })
        }