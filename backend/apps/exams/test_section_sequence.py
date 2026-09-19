from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from .models import Exam, ExamSection


User = get_user_model()


class ExamSectionSequenceTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='sequence_test',
            email='sequence@example.com',
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
        )

        self.reading = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.READING,
        )

        self.writing = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.WRITING,
        )

        self.speaking = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.SPEAKING,
        )

    def test_listening_can_start_first(self):
        response = self.client.post(
            f'/api/v1/exams/sections/{self.listening.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['section_type'],
            ExamSection.SectionType.LISTENING,
        )

        self.assertEqual(
            response.data['status'],
            ExamSection.Status.IN_PROGRESS,
        )

    def test_reading_cannot_start_before_listening(self):
        response = self.client.post(
            f'/api/v1/exams/sections/{self.reading.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.data['detail'],
            'This section cannot be started yet.',
        )

    def test_reading_can_start_after_listening(self):
        self.listening.status = ExamSection.Status.SUBMITTED
        self.listening.save(
            update_fields=['status'],
        )

        response = self.client.post(
            f'/api/v1/exams/sections/{self.reading.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['section_type'],
            ExamSection.SectionType.READING,
        )

        self.assertEqual(
            response.data['status'],
            ExamSection.Status.IN_PROGRESS,
        )

    def test_writing_cannot_start_before_reading(self):
        self.listening.status = ExamSection.Status.SUBMITTED
        self.listening.save(
            update_fields=['status'],
        )

        response = self.client.post(
            f'/api/v1/exams/sections/{self.writing.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_writing_can_start_after_reading(self):
        self.listening.status = ExamSection.Status.SUBMITTED
        self.reading.status = ExamSection.Status.SUBMITTED

        self.listening.save(
            update_fields=['status'],
        )

        self.reading.save(
            update_fields=['status'],
        )

        response = self.client.post(
            f'/api/v1/exams/sections/{self.writing.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['section_type'],
            ExamSection.SectionType.WRITING,
        )

    def test_speaking_cannot_start_before_writing(self):
        self.listening.status = ExamSection.Status.SUBMITTED
        self.reading.status = ExamSection.Status.SUBMITTED

        self.listening.save(
            update_fields=['status'],
        )

        self.reading.save(
            update_fields=['status'],
        )

        response = self.client.post(
            f'/api/v1/exams/sections/{self.speaking.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_speaking_can_start_after_writing(self):
        self.listening.status = ExamSection.Status.SUBMITTED
        self.reading.status = ExamSection.Status.SUBMITTED
        self.writing.status = ExamSection.Status.SUBMITTED

        self.listening.save(
            update_fields=['status'],
        )

        self.reading.save(
            update_fields=['status'],
        )

        self.writing.save(
            update_fields=['status'],
        )

        response = self.client.post(
            f'/api/v1/exams/sections/{self.speaking.id}/start/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['section_type'],
            ExamSection.SectionType.SPEAKING,
        )
