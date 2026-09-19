from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

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

    def test_create_question(self):
        response = self.client.post(
            '/api/v1/questions/',
            {
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

        self.assertTrue(
            Question.objects.filter(
                skill='LISTENING',
            ).exists()
        )

    def test_list_questions(self):
        Question.objects.create(
            skill='READING',
            question_type='TRUE_FALSE_NOT_GIVEN',
            text='The statement is correct.',
            correct_answer='TRUE',
            order=1,
        )

        response = self.client.get(
            '/api/v1/questions/'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            '/api/v1/questions/'
        )

        self.assertEqual(response.status_code, 401)
