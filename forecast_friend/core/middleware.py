from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse

class LoginRequiredMiddleware:
    """
    Перенаправляет всех незалогиненных пользователей на страницу логина
    кроме исключений.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        login_url = reverse('login')
        # страницы, на которые можно без авторизации
        allowed_urls = [login_url, reverse('register'), reverse('review_page'), reverse('country_list')]  

        if not request.user.is_authenticated and request.path not in allowed_urls:
            return redirect(login_url)

        response = self.get_response(request)
        return response