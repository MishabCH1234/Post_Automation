from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import UserProfile
from planner.models import WeeklyPlan
from scheduler.tasks import process_plan, schedule_post


class SchedulerTaskTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='scheduler-user',
            password='strong-password-123',
        )
        self.plan = WeeklyPlan.objects.create(
            user=self.user,
            title='Promo',
            description='Caption',
            content='Prompt',
            scheduled_time=timezone.now(),
        )

    @patch('scheduler.tasks.schedule_post.apply_async')
    @patch('scheduler.tasks.generate_image_bytes', return_value=b'image-bytes')
    def test_process_plan_saves_generated_image_and_schedules_post(self, mock_generate, mock_apply_async):
        process_plan.run(self.plan.id)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, WeeklyPlan.STATUS_SCHEDULED)
        self.assertTrue(self.plan.image.name.startswith(f'posts/{self.plan.id}'))
        self.assertTrue(self.plan.image.name.endswith('.png'))
        mock_generate.assert_called_once_with('Promo - Prompt')
        mock_apply_async.assert_called_once()

    @override_settings(SITE_URL='https://example.com')
    @patch('scheduler.tasks.requests.post')
    def test_schedule_post_records_instagram_media_id(self, mock_post):
        profile = UserProfile.objects.create(user=self.user)
        profile.set_token('instagram-token')
        profile.save()
        self.plan.image.save('test.png', ContentFile(b'image-bytes'))
        self.plan.save()

        create_response = Mock()
        create_response.json.return_value = {'id': 'creation-id'}
        create_response.raise_for_status.return_value = None
        publish_response = Mock()
        publish_response.json.return_value = {'id': 'media-id'}
        publish_response.raise_for_status.return_value = None
        mock_post.side_effect = [create_response, publish_response]

        schedule_post.run(self.plan.id)

        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, WeeklyPlan.STATUS_POSTED)
        self.assertEqual(self.plan.instagram_media_id, 'media-id')
        self.assertIsNotNone(self.plan.posted_at)

# Create your tests here.
