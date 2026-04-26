from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile


class PlannerViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester',
            password='strong-password-123',
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_dashboard_renders_for_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_upload_rejects_non_excel_file(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile('plan.txt', b'not an excel file')

        response = self.client.post(reverse('upload_plan'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please upload an Excel file')

    def test_profile_saves_encrypted_token(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('profile'), {'token': 'secret-token'})

        self.assertRedirects(response, reverse('profile'))
        profile = UserProfile.objects.get(user=self.user)
        self.assertNotEqual(profile.instagram_token, 'secret-token')
        self.assertEqual(profile.get_token(), 'secret-token')

# Create your tests here.
