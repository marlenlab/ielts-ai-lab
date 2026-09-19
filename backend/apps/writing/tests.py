from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from apps.exams.models import Exam, ExamSection

from .models import WritingSubmission, WritingTask


User = get_user_model()


class WritingAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='writingtest',
            email='writingtest@example.com',
            password='TestPassword123',
        )

        self.other_user = User.objects.create_user(
            username='otherwriting',
            email='otherwriting@example.com',
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

        self.writing_section = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.WRITING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        self.task_1 = WritingTask.objects.create(
            task_type=WritingTask.TaskType.TASK_1,
            title='IELTS Writing Task 1',
            instructions='Describe the information shown in the chart.',
            minimum_words=150,
        )

        self.task_2 = WritingTask.objects.create(
            task_type=WritingTask.TaskType.TASK_2,
            title='IELTS Writing Task 2',
            instructions='Discuss both views and give your opinion.',
            minimum_words=250,
        )

    def test_list_writing_tasks(self):
        response = self.client.get(
            '/api/v1/writing/tasks/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

    def test_create_writing_task(self):
        response = self.client.post(
            '/api/v1/writing/tasks/',
            {
                'task_type': WritingTask.TaskType.TASK_1,
                'title': 'New Task',
                'instructions': 'Describe the graph.',
                'minimum_words': 150,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data['task_type'],
            WritingTask.TaskType.TASK_1,
        )

    def test_create_writing_draft(self):
        content = (
            'This is my first writing response '
            'with several words for testing.'
        )

        response = self.client.post(
            '/api/v1/writing/submissions/',
            {
                'section': self.writing_section.id,
                'task': self.task_1.id,
                'content': content,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data['status'],
            WritingSubmission.Status.DRAFT,
        )

        self.assertEqual(
            response.data['word_count'],
            len(content.split()),
        )

        self.assertTrue(
            WritingSubmission.objects.filter(
                user=self.user,
                section=self.writing_section,
                task=self.task_1,
            ).exists()
        )

    def test_update_writing_draft(self):
        submission = WritingSubmission.objects.create(
            user=self.user,
            section=self.writing_section,
            task=self.task_1,
            content='Initial draft.',
        )

        submission.update_word_count()
        submission.save()

        new_content = (
            'This is the updated writing draft '
            'with more words for the IELTS task.'
        )

        response = self.client.patch(
            f'/api/v1/writing/submissions/{submission.id}/',
            {
                'content': new_content,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        submission.refresh_from_db()

        self.assertEqual(
            submission.content,
            new_content,
        )

        self.assertEqual(
            submission.word_count,
            len(new_content.split()),
        )

    def test_repeated_create_updates_existing_draft(self):
        first_content = 'First version of the essay.'

        first_response = self.client.post(
            '/api/v1/writing/submissions/',
            {
                'section': self.writing_section.id,
                'task': self.task_1.id,
                'content': first_content,
            },
            format='json',
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        second_content = (
            'Second version of the essay with additional content.'
        )

        second_response = self.client.post(
            '/api/v1/writing/submissions/',
            {
                'section': self.writing_section.id,
                'task': self.task_1.id,
                'content': second_content,
            },
            format='json',
        )

        self.assertEqual(
            second_response.status_code,
            201,
        )

        self.assertEqual(
            WritingSubmission.objects.filter(
                user=self.user,
                section=self.writing_section,
                task=self.task_1,
            ).count(),
            1,
        )

        submission = WritingSubmission.objects.get(
            user=self.user,
            section=self.writing_section,
            task=self.task_1,
        )

        self.assertEqual(
            submission.content,
            second_content,
        )

    def test_submit_writing_with_enough_words(self):
        content = ' '.join(
            ['word'] * 150
        )

        submission = WritingSubmission.objects.create(
            user=self.user,
            section=self.writing_section,
            task=self.task_1,
            content=content,
        )

        response = self.client.post(
            f'/api/v1/writing/submissions/{submission.id}/submit/',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        submission.refresh_from_db()

        self.assertEqual(
            submission.status,
            WritingSubmission.Status.SUBMITTED,
        )

        self.assertEqual(
            submission.word_count,
            150,
        )

        self.assertIsNotNone(
            submission.submitted_at,
        )

    def test_cannot_submit_writing_below_minimum_words(self):
        content = ' '.join(
            ['word'] * 100
        )

        submission = WritingSubmission.objects.create(
            user=self.user,
            section=self.writing_section,
            task=self.task_1,
            content=content,
        )

        response = self.client.post(
            f'/api/v1/writing/submissions/{submission.id}/submit/',
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        submission.refresh_from_db()

        self.assertEqual(
            submission.status,
            WritingSubmission.Status.DRAFT,
        )

    def test_cannot_edit_submitted_writing(self):
        submission = WritingSubmission.objects.create(
            user=self.user,
            section=self.writing_section,
            task=self.task_1,
            content=' '.join(['word'] * 150),
            word_count=150,
            status=WritingSubmission.Status.SUBMITTED,
        )

        response = self.client.patch(
            f'/api/v1/writing/submissions/{submission.id}/',
            {
                'content': 'Changed content.',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_cannot_create_writing_for_non_writing_section(self):
        reading_section = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.READING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        response = self.client.post(
            '/api/v1/writing/submissions/',
            {
                'section': reading_section.id,
                'task': self.task_1.id,
                'content': 'Some essay content.',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_cannot_create_writing_for_another_users_section(self):
        other_exam = Exam.objects.create(
            user=self.other_user,
            exam_type=Exam.ExamType.FULL_MOCK,
            status=Exam.Status.IN_PROGRESS,
        )

        other_section = ExamSection.objects.create(
            exam=other_exam,
            section_type=ExamSection.SectionType.WRITING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        response = self.client.post(
            '/api/v1/writing/submissions/',
            {
                'section': other_section.id,
                'task': self.task_1.id,
                'content': 'Private essay content.',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_student_sees_only_own_submissions(self):
        own_submission = WritingSubmission.objects.create(
            user=self.user,
            section=self.writing_section,
            task=self.task_1,
            content='My essay.',
        )

        other_exam = Exam.objects.create(
            user=self.other_user,
            exam_type=Exam.ExamType.FULL_MOCK,
            status=Exam.Status.IN_PROGRESS,
        )

        other_section = ExamSection.objects.create(
            exam=other_exam,
            section_type=ExamSection.SectionType.WRITING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        WritingSubmission.objects.create(
            user=self.other_user,
            section=other_section,
            task=self.task_1,
            content='Another user essay.',
        )

        response = self.client.get(
            '/api/v1/writing/submissions/'
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
            '/api/v1/writing/tasks/'
        )

        self.assertEqual(
            response.status_code,
            401,
        )
