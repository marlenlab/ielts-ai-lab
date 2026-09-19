from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from apps.exams.models import Exam, ExamSection

from .answer import Answer
from .models import Question


User = get_user_model()


class QuestionSecurityTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='TestPassword123',
        )

        self.other_user = User.objects.create_user(
            username='student2',
            email='student2@example.com',
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

        self.active_section = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.LISTENING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        self.inactive_section = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.READING,
            status=ExamSection.Status.NOT_STARTED,
        )

        self.other_exam = Exam.objects.create(
            user=self.other_user,
            exam_type=Exam.ExamType.FULL_MOCK,
            status=Exam.Status.IN_PROGRESS,
        )

        self.other_section = ExamSection.objects.create(
            exam=self.other_exam,
            section_type=ExamSection.SectionType.LISTENING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        self.active_question = Question.objects.create(
            section=self.active_section,
            skill=Question.Skill.LISTENING,
            question_type=Question.QuestionType.MULTIPLE_CHOICE,
            text='What time does the train leave?',
            options=['8:00', '8:30', '9:00'],
            correct_answer='8:30',
            points=1,
            order=1,
        )

        self.inactive_question = Question.objects.create(
            section=self.inactive_section,
            skill=Question.Skill.READING,
            question_type=Question.QuestionType.TRUE_FALSE_NOT_GIVEN,
            text='The statement is correct.',
            correct_answer='TRUE',
            points=1,
            order=1,
        )

        self.other_question = Question.objects.create(
            section=self.other_section,
            skill=Question.Skill.LISTENING,
            question_type=Question.QuestionType.MULTIPLE_CHOICE,
            text='Another question.',
            options=['A', 'B', 'C'],
            correct_answer='A',
            points=1,
            order=1,
        )

    def test_student_sees_only_questions_from_own_active_section(self):
        response = self.client.get(
            '/api/v1/questions/',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        question_ids = [
            item['id']
            for item in response.data
        ]

        self.assertIn(
            self.active_question.id,
            question_ids,
        )

        self.assertNotIn(
            self.inactive_question.id,
            question_ids,
        )

        self.assertNotIn(
            self.other_question.id,
            question_ids,
        )

    def test_student_cannot_see_correct_answer(self):
        response = self.client.get(
            '/api/v1/questions/',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        question_data = response.data[0]

        self.assertNotIn(
            'correct_answer',
            question_data,
        )

    def test_student_can_create_question_only_in_own_section(self):
        response = self.client.post(
            '/api/v1/questions/',
            {
                'section': self.active_section.id,
                'skill': Question.Skill.LISTENING,
                'question_type': Question.QuestionType.MULTIPLE_CHOICE,
                'text': 'New question',
                'options': ['A', 'B', 'C'],
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

    def test_student_cannot_create_question_in_another_users_section(self):
        response = self.client.post(
            '/api/v1/questions/',
            {
                'section': self.other_section.id,
                'skill': Question.Skill.LISTENING,
                'question_type': Question.QuestionType.MULTIPLE_CHOICE,
                'text': 'Unauthorized question',
                'options': ['A', 'B', 'C'],
                'correct_answer': 'A',
                'points': 1,
                'order': 2,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )


class AnswerUpdateTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='answerstudent',
            email='answerstudent@example.com',
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

        self.section = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.LISTENING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        self.question = Question.objects.create(
            section=self.section,
            skill=Question.Skill.LISTENING,
            question_type=Question.QuestionType.MULTIPLE_CHOICE,
            text='What time does the train leave?',
            options=['8:00', '8:30', '9:00'],
            correct_answer='8:30',
            points=1,
            order=1,
        )

    def test_student_can_change_answer(self):
        first_response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': self.question.id,
                'answer': '9:00',
            },
            format='json',
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        self.assertFalse(
            first_response.data['is_correct'],
        )

        second_response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': self.question.id,
                'answer': '8:30',
            },
            format='json',
        )

        self.assertEqual(
            second_response.status_code,
            201,
        )

        self.assertTrue(
            second_response.data['is_correct'],
        )

        self.assertEqual(
            second_response.data['points_earned'],
            1,
        )

        self.assertEqual(
            Answer.objects.filter(
                exam=self.exam,
                question=self.question,
            ).count(),
            1,
        )

    def test_correct_answer_is_scored_correctly(self):
        response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': self.question.id,
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
            self.question.points,
        )

    def test_incorrect_answer_gets_zero_points(self):
        response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': self.question.id,
                'answer': '9:00',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertFalse(
            response.data['is_correct'],
        )

        self.assertEqual(
            response.data['points_earned'],
            0,
        )

    def test_cannot_answer_inactive_section(self):
        inactive_section = ExamSection.objects.create(
            exam=self.exam,
            section_type=ExamSection.SectionType.READING,
            status=ExamSection.Status.NOT_STARTED,
        )

        inactive_question = Question.objects.create(
            section=inactive_section,
            skill=Question.Skill.READING,
            question_type=Question.QuestionType.TRUE_FALSE_NOT_GIVEN,
            text='Inactive question',
            correct_answer='TRUE',
            points=1,
            order=1,
        )

        response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': inactive_question.id,
                'answer': 'TRUE',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_cannot_answer_question_from_another_exam(self):
        other_user = User.objects.create_user(
            username='otheranswerstudent',
            email='otheranswerstudent@example.com',
            password='TestPassword123',
        )

        other_exam = Exam.objects.create(
            user=other_user,
            exam_type=Exam.ExamType.FULL_MOCK,
            status=Exam.Status.IN_PROGRESS,
        )

        other_section = ExamSection.objects.create(
            exam=other_exam,
            section_type=ExamSection.SectionType.LISTENING,
            status=ExamSection.Status.IN_PROGRESS,
        )

        other_question = Question.objects.create(
            section=other_section,
            skill=Question.Skill.LISTENING,
            question_type=Question.QuestionType.MULTIPLE_CHOICE,
            text='Foreign question',
            options=['A', 'B', 'C'],
            correct_answer='A',
            points=1,
            order=1,
        )

        response = self.client.post(
            '/api/v1/questions/answers/',
            {
                'exam': self.exam.id,
                'question': other_question.id,
                'answer': 'A',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            403,
        )
