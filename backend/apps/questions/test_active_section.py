from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from apps.exams.models import Exam, ExamSection

from .models import Question


User = get_user_model()


class ActiveSectionAnswerTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='active_section_test',
            email='active_section@example.com',
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
            status=ExamSection.Status.IN_PROGRESS,
        )

        self.reading = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.READING,
            status=ExamSection.Status.NOT_STARTED,
        )

        self.listening_question = Question.objects.create(
            section=self.listening,
            skill=Question.Skill.LISTENING,
            question_type=Question.QuestionType.MULTIPLE_CHOICE,
            text='What time does the train leave?',
            options=[
                '8:00',
                '8:30',
                '9:00',
            ],
            correct_answer='8:30',
            points=1,
            order=1,
        )

        self.reading_question = Question.objects.create(
            section=self.reading,
            skill=Question.Skill.READING,
            question_type=Question.QuestionType.TRUE_FALSE_NOT_GIVEN,
            text='The statement is true.',
            options=[
                'TRUE',
                'FALSE',
                'NOT GIVEN',
            ],
            correct_answer='TRUE',
            points=1,
            order=1,
        )

    def test_can_answer_question_from_active_section(self):
        response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': self.listening_question.id,
                'answer': '8:30',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertTrue(
            response.data['is_correct'],
        )

        self.assertEqual(
            response.data['points_earned'],
            1,
        )

    def test_cannot_answer_question_from_inactive_section(self):
        response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': self.reading_question.id,
                'answer': 'TRUE',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.data['detail'],
            'You can only answer questions from the active section.',
        )

    def test_question_list_does_not_expose_correct_answer(self):
        response = self.client.get(
            '/api/v1/questions/',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        question = response.data[0]

        self.assertEqual(
            question['id'],
            self.listening_question.id,
        )

        self.assertNotIn(
            'correct_answer',
            question,
        )

    def test_question_creation_can_still_use_correct_answer(self):
        response = self.client.post(
            '/api/v1/questions/',
            {
                'section': self.reading.id,
                'skill': Question.Skill.READING,
                'question_type': (
                    Question.QuestionType.MULTIPLE_CHOICE
                ),
                'text': 'Choose the correct answer.',
                'options': [
                    'A',
                    'B',
                    'C',
                ],
                'correct_answer': 'A',
                'points': 1,
                'order': 2,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data['correct_answer'],
            'A',
        )
