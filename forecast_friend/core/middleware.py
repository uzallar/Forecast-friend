from django.shortcuts import redirect
from django.urls import reverse

from .models import Visit


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_url = reverse('login')
        allowed_urls = [login_url, reverse('register'), reverse('review_page'), reverse('country_list')]

        if not request.user.is_authenticated and request.path not in allowed_urls:
            return redirect(login_url)

        response = self.get_response(request)
        return response


class VisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/admin/') and not request.path.startswith('/static/'):
            Visit.objects.create(
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                path=request.path
            )

        response = self.get_response(request)
        return response
