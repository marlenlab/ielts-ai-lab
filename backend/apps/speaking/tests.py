from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from apps.exams.models import Exam, ExamSection

from .models import SpeakingSubmission, SpeakingTask


User = get_user_model()


class SpeakingAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='speakingtest',
            email='speakingtest@example.com',
            password='TestPassword123',
        )

        self.other_user = User.objects.create_user(
            username='otherspeaking',
            email='otherspeaking@example.com',
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

        self.speaking_section = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.SPEAKING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        self.task_1 = SpeakingTask.objects.create(
            part=SpeakingTask.Part.PART_1,
            title='Introduction and Interview',
            instructions='Answer questions about yourself and familiar topics.',
            preparation_seconds=0,
            response_seconds=30,
        )

        self.task_2 = SpeakingTask.objects.create(
            part=SpeakingTask.Part.PART_2,
            title='Long Turn',
            instructions='Speak about the given topic for up to two minutes.',
            preparation_seconds=60,
            response_seconds=120,
        )

    def test_list_speaking_tasks(self):
        response = self.client.get(
            '/api/v1/speaking/tasks/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

    def test_create_speaking_task(self):
        response = self.client.post(
            '/api/v1/speaking/tasks/',
            {
                'part': SpeakingTask.Part.PART_3,
                'title': 'Discussion',
                'instructions': 'Discuss the topic in detail.',
                'preparation_seconds': 0,
                'response_seconds': 60,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data['part'],
            SpeakingTask.Part.PART_3,
        )

    def test_create_speaking_draft(self):
        response = self.client.post(
            '/api/v1/speaking/submissions/',
            {
                'section': self.speaking_section.id,
                'task': self.task_1.id,
                'audio_url': 'https://example.com/audio/answer.mp3',
                'transcript': 'I am from Kyrgyzstan.',
                'duration_seconds': 25,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data['status'],
            SpeakingSubmission.Status.DRAFT,
        )

        self.assertEqual(
            response.data['audio_url'],
            'https://example.com/audio/answer.mp3',
        )

        self.assertEqual(
            response.data['transcript'],
            'I am from Kyrgyzstan.',
        )

        self.assertEqual(
            response.data['duration_seconds'],
            25,
        )

    def test_repeated_create_updates_existing_draft(self):
        first_response = self.client.post(
            '/api/v1/speaking/submissions/',
            {
                'section': self.speaking_section.id,
                'task': self.task_1.id,
                'audio_url': 'https://example.com/audio/first.mp3',
                'transcript': 'First answer.',
                'duration_seconds': 20,
            },
            format='json',
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        second_response = self.client.post(
            '/api/v1/speaking/submissions/',
            {
                'section': self.speaking_section.id,
                'task': self.task_1.id,
                'audio_url': 'https://example.com/audio/second.mp3',
                'transcript': 'Second answer.',
                'duration_seconds': 30,
            },
            format='json',
        )

        self.assertEqual(
            second_response.status_code,
            201,
        )

        self.assertEqual(
            SpeakingSubmission.objects.filter(
                user=self.user,
                section=self.speaking_section,
                task=self.task_1,
            ).count(),
            1,
        )

        submission = SpeakingSubmission.objects.get(
            user=self.user,
            section=self.speaking_section,
            task=self.task_1,
        )

        self.assertEqual(
            submission.audio_url,
            'https://example.com/audio/second.mp3',
        )

        self.assertEqual(
            submission.transcript,
            'Second answer.',
        )

    def test_update_speaking_draft(self):
        submission = SpeakingSubmission.objects.create(
            user=self.user,
            section=self.speaking_section,
            task=self.task_1,
            audio_url='https://example.com/audio/old.mp3',
            transcript='Old transcript.',
            duration_seconds=20,
        )

        response = self.client.patch(
            f'/api/v1/speaking/submissions/{submission.id}/',
            {
                'audio_url': 'https://example.com/audio/new.mp3',
                'transcript': 'New transcript.',
                'duration_seconds': 28,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        submission.refresh_from_db()

        self.assertEqual(
            submission.audio_url,
            'https://example.com/audio/new.mp3',
        )

        self.assertEqual(
            submission.transcript,
            'New transcript.',
        )

        self.assertEqual(
            submission.duration_seconds,
            28,
        )

    def test_submit_speaking_with_audio_url(self):
        submission = SpeakingSubmission.objects.create(
            user=self.user,
            section=self.speaking_section,
            task=self.task_1,
            audio_url='https://example.com/audio/answer.mp3',
            transcript='My speaking answer.',
            duration_seconds=30,
        )

        response = self.client.post(
            f'/api/v1/speaking/submissions/{submission.id}/submit/',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        submission.refresh_from_db()

        self.assertEqual(
            submission.status,
            SpeakingSubmission.Status.SUBMITTED,
        )

        self.assertIsNotNone(
            submission.submitted_at,
        )

    def test_cannot_submit_without_audio(self):
        submission = SpeakingSubmission.objects.create(
            user=self.user,
            section=self.speaking_section,
            task=self.task_1,
            transcript='I answered the question.',
        )

        response = self.client.post(
            f'/api/v1/speaking/submissions/{submission.id}/submit/',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        submission.refresh_from_db()

        self.assertEqual(
            submission.status,
            SpeakingSubmission.Status.DRAFT,
        )

    def test_cannot_edit_submitted_speaking(self):
        submission = SpeakingSubmission.objects.create(
            user=self.user,
            section=self.speaking_section,
            task=self.task_1,
            audio_url='https://example.com/audio/answer.mp3',
            transcript='Submitted answer.',
            duration_seconds=30,
            status=SpeakingSubmission.Status.SUBMITTED,
        )

        response = self.client.patch(
            f'/api/v1/speaking/submissions/{submission.id}/',
            {
                'transcript': 'Changed answer.',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_cannot_create_speaking_for_non_speaking_section(self):
        reading_section = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.READING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        response = self.client.post(
            '/api/v1/speaking/submissions/',
            {
                'section': reading_section.id,
                'task': self.task_1.id,
                'audio_url': 'https://example.com/audio/answer.mp3',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_cannot_create_speaking_for_another_users_section(self):
        other_exam = Exam.objects.create(
            user=self.other_user,
            exam_type=Exam.ExamType.FULL_MOCK,
            status=Exam.Status.IN_PROGRESS,
        )

        other_section = ExamSection.objects.create(
            exam=other_exam,
            section_type=ExamSection.SectionType.SPEAKING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        response = self.client.post(
            '/api/v1/speaking/submissions/',
            {
                'section': other_section.id,
                'task': self.task_1.id,
                'audio_url': 'https://example.com/audio/private.mp3',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_student_sees_only_own_submissions(self):
        own_submission = SpeakingSubmission.objects.create(
            user=self.user,
            section=self.speaking_section,
            task=self.task_1,
            audio_url='https://example.com/audio/own.mp3',
        )

        other_exam = Exam.objects.create(
            user=self.other_user,
            exam_type=Exam.ExamType.FULL_MOCK,
            status=Exam.Status.IN_PROGRESS,
        )

        other_section = ExamSection.objects.create(
            exam=other_exam,
            section_type=ExamSection.SectionType.SPEAKING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        SpeakingSubmission.objects.create(
            user=self.other_user,
            section=other_section,
            task=self.task_1,
            audio_url='https://example.com/audio/other.mp3',
        )

        response = self.client.get(
            '/api/v1/speaking/submissions/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]['id'],
            own_submission.id,
        )

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            '/api/v1/speaking/tasks/'
        )

        self.assertEqual(
            response.status_code,
            401,
        )
