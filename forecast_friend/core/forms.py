from django import forms
from .models import Country, Review
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
                'class': 'form-control',
                'required': True
            })
        }


from django import forms
from .models import Ticket
from datetime import datetime

class TicketForm(forms.ModelForm):
    # Обязательное поле с явной валидацией формата
    date = forms.CharField(
        label='Дата (ДД.ММ.ГГГГ)',
        required=True,  # Поле обязательно
        widget=forms.TextInput(attrs={
            'placeholder': 'ДД.ММ.ГГГГ',
            'pattern': r'\d{2}\.\d{2}\.\d{4}',
            'title': 'Введите дату в формате ДД.ММ.ГГГГ'
        })
    )

    class Meta:
        model = Ticket
        fields = ['country', 'city', 'date', 'pdf_file', 'ticket_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pdf_file'].required = False
        self.fields['country'].required = False
        self.fields['city'].required = False

    def clean_date(self):
        date_str = self.cleaned_data.get('date')
        if not date_str:
            raise forms.ValidationError("Это поле обязательно")

        try:
            # Удаляем возможные пробелы и преобразуем
            date_str = date_str.strip()
            return datetime.strptime(date_str, '%d.%m.%Y').date()
        except ValueError:
            raise forms.ValidationError("Неверный формат. Требуется ДД.ММ.ГГГГ")

    def clean(self):
        cleaned_data = super().clean()
        pdf_file = cleaned_data.get('pdf_file')
        country = cleaned_data.get('country')
        city = cleaned_data.get('city')

        # Проверяем либо PDF, либо все текстовые поля
        if not pdf_file and not (country and city):
            raise forms.ValidationError(
                "Заполните страну и город или загрузите PDF файл"
            )
        return cleaned_data

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Оставьте ваш отзыв...'}),
        }

