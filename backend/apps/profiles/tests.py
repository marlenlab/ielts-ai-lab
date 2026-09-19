from datetime import date, time

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import LearnerProfile


User = get_user_model()


class LearnerProfileAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='profiletest',
            email='profiletest@example.com',
            password='TestPassword123',
        )

        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get('/api/v1/profile/me/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['target_band'], None)

        self.assertTrue(
            LearnerProfile.objects.filter(user=self.user).exists()
        )

    def test_update_profile(self):
        response = self.client.patch(
            '/api/v1/profile/me/',
            {
                'target_band': '7.5',
                'current_band': '6.0',
                'english_level': 'B2',
                'exam_date': date(2026, 12, 15),
                'daily_study_minutes': 120,
                'preferred_study_time': time(18, 30),
            },
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['target_band'], '7.5')
        self.assertEqual(response.data['english_level'], 'B2')
        self.assertEqual(response.data['daily_study_minutes'], 120)
