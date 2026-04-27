from django.contrib import admin
from .models import WeeklyPlan


@admin.register(WeeklyPlan)
class WeeklyPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'scheduled_time', 'posted_at', 'instagram_media_id')
    list_filter = ('status', 'scheduled_time', 'posted_at')
    search_fields = ('title', 'description', 'content', 'instagram_media_id')
