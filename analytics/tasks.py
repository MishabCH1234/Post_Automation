from celery import shared_task
import requests

from analytics.models import PostAnalytics
from planner.models import WeeklyPlan


def _metric_value(insights, metric_name):
    for item in insights.get('data', []):
        if item.get('name') == metric_name and item.get('values'):
            return item['values'][0].get('value', 0)
    return 0


@shared_task
def fetch_analytics(plan_id=None):
    plans = WeeklyPlan.objects.filter(
        status=WeeklyPlan.STATUS_POSTED,
    ).exclude(instagram_media_id='')
    if plan_id:
        plans = plans.filter(id=plan_id)

    updated_count = 0
    for plan in plans:
        try:
            token = plan.user.userprofile.get_token()
        except Exception:
            continue

        if not token:
            continue

        media_url = f"https://graph.facebook.com/v18.0/{plan.instagram_media_id}"
        try:
            media_response = requests.get(
                media_url,
                params={
                    'fields': 'like_count',
                    'access_token': token,
                },
                timeout=30,
            )
            media_response.raise_for_status()
            media_data = media_response.json()

            insights_response = requests.get(
                f"{media_url}/insights",
                params={
                    'metric': 'impressions,reach',
                    'access_token': token,
                },
                timeout=30,
            )
            insights_response.raise_for_status()
            insights_data = insights_response.json()
        except requests.RequestException:
            continue

        PostAnalytics.objects.update_or_create(
            plan=plan,
            defaults={
                'likes': media_data.get('like_count', 0),
                'impressions': _metric_value(insights_data, 'impressions'),
                'reach': _metric_value(insights_data, 'reach'),
            },
        )
        updated_count += 1

    return updated_count
