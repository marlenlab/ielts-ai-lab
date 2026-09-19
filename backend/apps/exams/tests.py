from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from apps.questions.answer import Answer
from apps.questions.models import Question

from .models import Exam, ExamSection

User = get_user_model()


class ExamAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='examtest',
            email='examtest@example.com',
            password='TestPassword123',
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.exam = Exam.objects.create(
            user=self.user,
            exam_type='FULL_MOCK',
        )

    def test_create_exam(self):
        response = self.client.post(
            '/api/v1/exams/',
            {
                'exam_type': 'FULL_MOCK',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data['exam_type'],
            'FULL_MOCK',
        )

        self.assertEqual(
            response.data['status'],
            'NOT_STARTED',
        )

        self.assertEqual(
            response.data['duration_minutes'],
            165,
        )

    def test_list_exams(self):
        response = self.client.get(
            '/api/v1/exams/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_create_exam_section(self):
        response = self.client.post(
            f'/api/v1/exams/{self.exam.id}/sections/',
            {
                'section_type': 'LISTENING',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data['section_type'],
            'LISTENING',
        )

        self.assertEqual(
            response.data['status'],
            'NOT_STARTED',
        )

    def test_list_exam_sections(self):
        ExamSection.objects.create(
            exam=self.exam,
            section_type='LISTENING',
        )

        response = self.client.get(
            f'/api/v1/exams/{self.exam.id}/sections/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_start_exam(self):
        response = self.client.post(
            f'/api/v1/exams/{self.exam.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['status'],
            'IN_PROGRESS',
        )

    def test_submit_exam(self):
        ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.LISTENING,
            status=ExamSection.Status.SUBMITTED,
        )

        ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.READING,
            status=ExamSection.Status.SUBMITTED,
        )

        ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.WRITING,
            status=ExamSection.Status.SUBMITTED,
        )

        ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.SPEAKING,
            status=ExamSection.Status.SUBMITTED,
        )

        self.exam.status = Exam.Status.IN_PROGRESS
        self.exam.save(
            update_fields=['status'],
        )

        response = self.client.post(
            f'/api/v1/exams/{self.exam.id}/submit/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['status'],
            Exam.Status.SUBMITTED,
        )

    def test_exam_result(self):
        section = ExamSection.objects.create(
            exam=self.exam,
            section_type='LISTENING',
        )

        question_1 = Question.objects.create(
            section=section,
            skill='LISTENING',
            question_type='MULTIPLE_CHOICE',
            text='Question 1',
            correct_answer='A',
            points=1,
            order=1,
        )

        question_2 = Question.objects.create(
            section=section,
            skill='LISTENING',
            question_type='MULTIPLE_CHOICE',
            text='Question 2',
            correct_answer='B',
            points=2,
            order=2,
        )

        Answer.objects.create(
            exam=self.exam,
            question=question_1,
            answer='A',
            is_correct=True,
            points_earned=1,
        )

        Answer.objects.create(
            exam=self.exam,
            question=question_2,
            answer='A',
            is_correct=False,
            points_earned=0,
        )

        response = self.client.get(
            f'/api/v1/exams/{self.exam.id}/result/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['result']['total_points'],
            3,
        )

        self.assertEqual(
            response.data['result']['earned_points'],
            1,
        )

        self.assertEqual(
            response.data['result']['answered_questions'],
            2,
        )

    def test_timer_for_in_progress_exam(self):
        self.exam.status = Exam.Status.IN_PROGRESS
        self.exam.started_at = timezone.now()

        self.exam.save(
            update_fields=[
                'status',
                'started_at',
            ],
        )

        response = self.client.get(
            f'/api/v1/exams/{self.exam.id}/timer/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['status'],
            'IN_PROGRESS',
        )

        self.assertGreater(
            response.data['remaining_seconds'],
            0,
        )

        self.assertFalse(
            response.data['expired'],
        )

    def test_expired_exam_is_automatically_submitted(self):
        self.exam.status = Exam.Status.IN_PROGRESS
        self.exam.started_at = (
            timezone.now()
            - timedelta(
                minutes=self.exam.duration_minutes + 1,
            )
        )

        self.exam.save(
            update_fields=[
                'status',
                'started_at',
            ],
        )

        response = self.client.get(
            f'/api/v1/exams/{self.exam.id}/timer/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['status'],
            'SUBMITTED',
        )

        self.assertEqual(
            response.data['remaining_seconds'],
            0,
        )

        self.assertTrue(
            response.data['expired'],
        )

        self.exam.refresh_from_db()

        self.assertEqual(
            self.exam.status,
            Exam.Status.SUBMITTED,
        )

        self.assertIsNotNone(
            self.exam.submitted_at,
        )

    def test_submitted_exam_timer_is_expired(self):
        self.exam.status = Exam.Status.SUBMITTED
        self.exam.submitted_at = timezone.now()

        self.exam.save(
            update_fields=[
                'status',
                'submitted_at',
            ],
        )

        response = self.client.get(
            f'/api/v1/exams/{self.exam.id}/timer/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['status'],
            'SUBMITTED',
        )

        self.assertEqual(
            response.data['remaining_seconds'],
            0,
        )

        self.assertTrue(
            response.data['expired'],
        )

    def test_start_exam_section(self):
        section = ExamSection.objects.create(
            exam=self.exam,
            section_type='LISTENING',
        )

        self.exam.status = Exam.Status.IN_PROGRESS
        self.exam.started_at = timezone.now()

        self.exam.save(
            update_fields=[
                'status',
                'started_at',
            ],
        )

        response = self.client.post(
            f'/api/v1/exams/sections/{section.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['status'],
            'IN_PROGRESS',
        )

        section.refresh_from_db()

        self.assertEqual(
            section.status,
            ExamSection.Status.IN_PROGRESS,
        )

        self.assertIsNotNone(
            section.started_at,
        )

    def test_submit_exam_section(self):
        section = ExamSection.objects.create(
            exam=self.exam,
            section_type='READING',
            status=ExamSection.Status.IN_PROGRESS,
            started_at=timezone.now(),
        )

        self.exam.status = Exam.Status.IN_PROGRESS
        self.exam.started_at = timezone.now()

        self.exam.save(
            update_fields=[
                'status',
                'started_at',
            ],
        )

        response = self.client.post(
            f'/api/v1/exams/sections/{section.id}/submit/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['status'],
            'SUBMITTED',
        )

        section.refresh_from_db()

        self.assertEqual(
            section.status,
            ExamSection.Status.SUBMITTED,
        )

        self.assertIsNotNone(
            section.submitted_at,
        )
