from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from accounts.models import UserProfile
from analytics.models import PostAnalytics
from analytics.tasks import fetch_analytics
from planner.models import WeeklyPlan


class FetchAnalyticsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='analytics-user',
            password='strong-password-123',
        )
        self.profile = UserProfile.objects.create(user=self.user)
        self.profile.set_token('instagram-token')
        self.profile.save()
        self.plan = WeeklyPlan.objects.create(
            user=self.user,
            title='Posted AI post',
            description='Generated caption',
            content='Generated image prompt',
            scheduled_time=timezone.now(),
            posted_at=timezone.now(),
            status=WeeklyPlan.STATUS_POSTED,
            instagram_media_id='17890000000000000',
        )

    @patch('analytics.tasks.requests.get')
    def test_fetch_analytics_updates_post_metrics(self, mock_get):
        media_response = Mock()
        media_response.json.return_value = {'like_count': 12}
        media_response.raise_for_status.return_value = None
        insights_response = Mock()
        insights_response.json.return_value = {
            'data': [
                {'name': 'impressions', 'values': [{'value': 150}]},
                {'name': 'reach', 'values': [{'value': 90}]},
            ]
        }
        insights_response.raise_for_status.return_value = None
        mock_get.side_effect = [media_response, insights_response]

        updated_count = fetch_analytics(self.plan.id)

        self.assertEqual(updated_count, 1)
        analytics = PostAnalytics.objects.get(plan=self.plan)
        self.assertEqual(analytics.likes, 12)
        self.assertEqual(analytics.impressions, 150)
        self.assertEqual(analytics.reach, 90)

    def test_fetch_analytics_skips_plans_without_media_id(self):
        self.plan.instagram_media_id = ''
        self.plan.save(update_fields=['instagram_media_id'])

        updated_count = fetch_analytics(self.plan.id)

        self.assertEqual(updated_count, 0)
        self.assertFalse(PostAnalytics.objects.exists())
