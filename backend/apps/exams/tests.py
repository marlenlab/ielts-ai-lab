from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Exam


User = get_user_model()


class ExamAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='examtest',
            email='examtest@example.com',
            password='TestPassword123',
        )

        self.client.force_authenticate(user=self.user)

    def test_create_exam(self):
        response = self.client.post(
            '/api/v1/exams/',
            {
                'exam_type': 'FULL_MOCK',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['exam_type'], 'FULL_MOCK')
        self.assertEqual(response.data['status'], 'NOT_STARTED')

        self.assertTrue(
            Exam.objects.filter(user=self.user).exists()
        )

    def test_list_only_my_exams(self):
        Exam.objects.create(
            user=self.user,
            exam_type='FULL_MOCK',
        )

        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='TestPassword123',
        )

        Exam.objects.create(
            user=other_user,
            exam_type='FULL_MOCK',
        )

        response = self.client.get('/api/v1/exams/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
