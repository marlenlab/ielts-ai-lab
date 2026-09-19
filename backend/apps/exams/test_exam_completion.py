from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from .models import Exam, ExamSection


User = get_user_model()


class ExamCompletionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='completion_test',
            email='completion@example.com',
            password='TestPassword123',
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.exam = Exam.objects.create(
            user=self.user,
            exam_type=Exam.ExamType.FULL_MOCK,
            status=Exam.Status.IN_PROGRESS,
        )

        self.listening = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.LISTENING,
            status=ExamSection.Status.SUBMITTED,
        )

        self.reading = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.READING,
            status=ExamSection.Status.SUBMITTED,
        )

        self.writing = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.WRITING,
            status=ExamSection.Status.SUBMITTED,
        )

        self.speaking = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.SPEAKING,
            status=ExamSection.Status.IN_PROGRESS,
        )

    def test_exam_is_completed_after_speaking_submission(self):
        response = self.client.post(
            f'/api/v1/exams/sections/{self.speaking.id}/submit/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['status'],
            ExamSection.Status.SUBMITTED,
        )

        self.assertEqual(
            response.data['exam_status'],
            Exam.Status.COMPLETED,
        )

        self.exam.refresh_from_db()

        self.assertEqual(
            self.exam.status,
            Exam.Status.COMPLETED,
        )

        self.assertIsNotNone(
            self.exam.completed_at,
        )

    def test_exam_cannot_be_submitted_before_all_sections(self):
        self.speaking.status = ExamSection.Status.NOT_STARTED
        self.speaking.save(
            update_fields=['status'],
        )

        response = self.client.post(
            f'/api/v1/exams/{self.exam.id}/submit/'
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.data['detail'],
            'All exam sections must be completed '
            'before submitting the exam.',
        )

    def test_cannot_create_duplicate_section(self):
        response = self.client.post(
            f'/api/v1/exams/{self.exam.id}/sections/',
            {
                'section_type': ExamSection.SectionType.LISTENING,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.data['detail'],
            'This section already exists for the exam.',
        )

    def test_cannot_start_second_section_while_first_is_active(self):
        self.reading.status = ExamSection.Status.NOT_STARTED
        self.reading.save(
            update_fields=['status'],
        )

        self.speaking.status = ExamSection.Status.NOT_STARTED
        self.speaking.save(
            update_fields=['status'],
        )

        self.listening.status = ExamSection.Status.IN_PROGRESS
        self.listening.save(
            update_fields=['status'],
        )

        response = self.client.post(
            f'/api/v1/exams/sections/{self.reading.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.data['detail'],
            'Another section is already in progress.',
        )
