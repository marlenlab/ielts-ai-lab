from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from .models import Exam, ExamSection


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

    def test_create_exam_section(self):
        exam = Exam.objects.create(
            user=self.user,
            exam_type='FULL_MOCK',
        )

        response = self.client.post(
            f'/api/v1/exams/{exam.id}/sections/',
            {
                'section_type': 'LISTENING',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['section_type'], 'LISTENING')
        self.assertEqual(response.data['status'], 'NOT_STARTED')

        self.assertTrue(
            ExamSection.objects.filter(
                exam=exam,
                section_type='LISTENING',
            ).exists()
        )

    def test_cannot_create_section_for_another_users_exam(self):
        other_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='TestPassword123',
        )

        exam = Exam.objects.create(
            user=other_user,
            exam_type='FULL_MOCK',
        )

        response = self.client.post(
            f'/api/v1/exams/{exam.id}/sections/',
            {
                'section_type': 'READING',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 404)

    def test_start_exam(self):
        exam = Exam.objects.create(
            user=self.user,
            exam_type='FULL_MOCK',
        )

        response = self.client.post(
            f'/api/v1/exams/{exam.id}/start/',
            {},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['status'],
            'IN_PROGRESS',
        )

        exam.refresh_from_db()

        self.assertEqual(
            exam.status,
            Exam.Status.IN_PROGRESS,
        )
        self.assertIsNotNone(exam.started_at)

    def test_submit_exam(self):
        exam = Exam.objects.create(
            user=self.user,
            exam_type='FULL_MOCK',
            status=Exam.Status.IN_PROGRESS,
        )

        response = self.client.post(
            f'/api/v1/exams/{exam.id}/submit/',
            {},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['status'],
            'SUBMITTED',
        )

        exam.refresh_from_db()

        self.assertEqual(
            exam.status,
            Exam.Status.SUBMITTED,
        )
        self.assertIsNotNone(exam.submitted_at)
