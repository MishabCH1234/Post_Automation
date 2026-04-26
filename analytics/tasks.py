from celery import shared_task
from planner.models import WeeklyPlan

@shared_task
def fetch_analytics():
    plans = WeeklyPlan.objects.filter(status='posted')

    for plan in plans:
        # Call Instagram Insights API
        pass
