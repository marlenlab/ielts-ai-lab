from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from apps.exams.models import Exam, ExamSection
from apps.questions.answer import Answer
from apps.questions.models import Question

User = get_user_model()


class AnswerAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='answertest',
            email='answertest@example.com',
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

        self.question = Question.objects.create(
            section=self.section,
            skill='LISTENING',
            question_type='MULTIPLE_CHOICE',
            text='What time does the train leave?',
            options=['8:00', '8:30', '9:00'],
            correct_answer='8:30',
            points=1,
            order=1,
        )

    def test_create_correct_answer(self):
        response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': self.question.id,
                'answer': '8:30',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['is_correct'])
        self.assertEqual(response.data['points_earned'], 1)

    def test_create_incorrect_answer(self):
        response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': self.question.id,
                'answer': '9:00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data['is_correct'])
        self.assertEqual(response.data['points_earned'], 0)

    def test_cannot_answer_question_from_another_exam(self):
        other_exam = Exam.objects.create(
            user=self.user,
            exam_type='FULL_MOCK',
        )

        other_section = ExamSection.objects.create(
            exam=other_exam,
            section_type='READING',
        )

        other_question = Question.objects.create(
            section=other_section,
            skill='READING',
            question_type='TRUE_FALSE_NOT_GIVEN',
            text='The statement is correct.',
            correct_answer='TRUE',
            points=1,
            order=1,
        )

        response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': other_question.id,
                'answer': 'TRUE',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            '/api/v1/questions/answers/'
        )

        self.assertEqual(response.status_code, 401)
