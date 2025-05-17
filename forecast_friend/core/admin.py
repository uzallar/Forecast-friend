from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'is_visible')
    list_filter = ('is_visible',)
    actions = ['make_visible', 'make_invisible']

    @admin.action(description="Сделать отзывы видимыми")
    def make_visible(self, request, queryset):
        queryset.update(is_visible=True)

    @admin.action(description="Скрыть отзывы")
    def make_invisible(self, request, queryset):
        queryset.update(is_visible=False)
