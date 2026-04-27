from django.contrib import admin
from .models import PostAnalytics


@admin.register(PostAnalytics)
class PostAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('plan', 'likes', 'impressions', 'reach', 'updated_at')
    search_fields = ('plan__title',)
