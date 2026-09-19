from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from apps.exams.models import Exam, ExamSection

from .models import Question


User = get_user_model()


class QuestionAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='questiontest',
            email='questiontest@example.com',
            password='TestPassword123',
        )

        self.client.force_authenticate(user=self.user)

        self.exam = Exam.objects.create(
            user=self.user,
            exam_type='FULL_MOCK',
        )

        self.section = ExamSection.objects.create(
            exam=self.exam,
            section_type='LISTENING',
        )

    def test_create_question(self):
        response = self.client.post(
            '/api/v1/questions/',
            {
                'section': self.section.id,
                'skill': 'LISTENING',
                'question_type': 'MULTIPLE_CHOICE',
                'text': 'What time does the train leave?',
                'options': [
                    '8:00',
                    '8:30',
                    '9:00',
                ],
                'correct_answer': '8:30',
                'points': 1,
                'order': 1,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data['skill'],
            'LISTENING',
        )
        self.assertEqual(
            response.data['section'],
            self.section.id,
        )

        self.assertTrue(
            Question.objects.filter(
                section=self.section,
            ).exists()
        )

    def test_list_questions(self):
        Question.objects.create(
            section=self.section,
            skill='LISTENING',
            question_type='MULTIPLE_CHOICE',
            text='The statement is correct.',
            correct_answer='TRUE',
            order=1,
        )

        response = self.client.get(
            '/api/v1/questions/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_cannot_create_question_for_another_users_section(self):
        other_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='TestPassword123',
        )

        other_exam = Exam.objects.create(
            user=other_user,
            exam_type='FULL_MOCK',
        )

        other_section = ExamSection.objects.create(
            exam=other_exam,
            section_type='READING',
        )

        response = self.client.post(
            '/api/v1/questions/',
            {
                'section': other_section.id,
                'skill': 'READING',
                'question_type': 'TRUE_FALSE_NOT_GIVEN',
                'text': 'The statement is correct.',
                'correct_answer': 'TRUE',
                'order': 1,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            '/api/v1/questions/'
        )

        self.assertEqual(response.status_code, 401)
