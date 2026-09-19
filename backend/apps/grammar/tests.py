from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import GrammarExercise, GrammarProgress, GrammarTopic


User = get_user_model()


class GrammarAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='grammar_user',
            email='grammar@example.com',
            password='StrongPassword123!',
        )

        self.other_user = User.objects.create_user(
            username='other_grammar_user',
            email='other_grammar@example.com',
            password='StrongPassword123!',
        )

        self.client.force_authenticate(user=self.user)

        self.topic = GrammarTopic.objects.create(
            title='Present Perfect',
            description='Using the present perfect tense.',
            level=GrammarTopic.Level.B1,
            explanation='Use the present perfect for experiences and actions connected to the present.',
            examples=[
                'I have visited London.',
                'She has finished her homework.',
            ],
            common_mistakes=[
                'Using the past simple with unfinished time periods.',
            ],
        )

        self.second_topic = GrammarTopic.objects.create(
            title='Conditionals',
            description='Conditional sentences in English.',
            level=GrammarTopic.Level.B2,
            explanation='Conditionals describe possible, hypothetical, or unreal situations.',
            examples=[
                'If I study, I will pass.',
            ],
            common_mistakes=[
                'Using will directly after if in the first conditional.',
            ],
        )

        self.exercise = GrammarExercise.objects.create(
            topic=self.topic,
            exercise_type=GrammarExercise.ExerciseType.MULTIPLE_CHOICE,
            question='I ___ to London three times.',
            options=['have been', 'went', 'go'],
            correct_answer='have been',
            explanation='Use present perfect for life experience.',
            points=1,
            order=1,
        )

        self.second_exercise = GrammarExercise.objects.create(
            topic=self.topic,
            exercise_type=GrammarExercise.ExerciseType.FILL_GAP,
            question='She ___ already finished the task.',
            options=[],
            correct_answer='has',
            explanation='Use has with third-person singular.',
            points=1,
            order=2,
        )

    def test_list_topics(self):
        response = self.client.get('/api/v1/grammar/topics/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_topics_by_level(self):
        response = self.client.get(
            '/api/v1/grammar/topics/?level=B1'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]['title'],
            'Present Perfect',
        )

    def test_create_topic(self):
        payload = {
            'title': 'Passive Voice',
            'description': 'Passive constructions.',
            'level': 'B2',
            'explanation': 'The object becomes the focus of the sentence.',
            'examples': ['The book was written in 1990.'],
            'common_mistakes': [],
        }

        response = self.client.post(
            '/api/v1/grammar/topics/',
            payload,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            GrammarTopic.objects.count(),
            3,
        )

    def test_list_exercises(self):
        response = self.client.get(
            '/api/v1/grammar/exercises/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        self.assertNotIn(
            'correct_answer',
            response.data[0],
        )

    def test_filter_exercises_by_topic(self):
        response = self.client.get(
            f'/api/v1/grammar/exercises/?topic={self.topic.id}'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_exercise(self):
        payload = {
            'topic': self.second_topic.id,
            'exercise_type': 'ERROR_CORRECTION',
            'question': 'He go to school every day.',
            'options': [],
            'correct_answer': 'goes',
            'explanation': 'Use goes with he.',
            'points': 1,
            'order': 1,
        }

        response = self.client.post(
            '/api/v1/grammar/exercises/',
            payload,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            GrammarExercise.objects.count(),
            3,
        )

    def test_correct_answer_creates_progress(self):
        response = self.client.post(
            '/api/v1/grammar/answer/',
            {
                'exercise': self.exercise.id,
                'answer': 'have been',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['correct'])

        progress = GrammarProgress.objects.get(
            user=self.user,
            topic=self.topic,
        )

        self.assertEqual(progress.correct_answers, 1)
        self.assertEqual(progress.incorrect_answers, 0)
        self.assertTrue(progress.last_answer_correct)
        self.assertEqual(float(progress.mastery_score), 82.0)
        self.assertEqual(
            progress.status,
            GrammarProgress.Status.MASTERED,
        )

    def test_incorrect_answer_updates_progress(self):
        response = self.client.post(
            '/api/v1/grammar/answer/',
            {
                'exercise': self.exercise.id,
                'answer': 'went',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['correct'])

        progress = GrammarProgress.objects.get(
            user=self.user,
            topic=self.topic,
        )

        self.assertEqual(progress.correct_answers, 0)
        self.assertEqual(progress.incorrect_answers, 1)
        self.assertFalse(progress.last_answer_correct)
        self.assertEqual(float(progress.mastery_score), 0.0)
        self.assertEqual(
            progress.status,
            GrammarProgress.Status.NEW,
        )

    def test_mixed_answers_calculate_mastery(self):
        for answer in [
            'have been',
            'have been',
            'went',
            'went',
            'have been',
        ]:
            self.client.post(
                '/api/v1/grammar/answer/',
                {
                    'exercise': self.exercise.id,
                    'answer': answer,
                },
                format='json',
            )

        progress = GrammarProgress.objects.get(
            user=self.user,
            topic=self.topic,
        )

        self.assertEqual(progress.correct_answers, 3)
        self.assertEqual(progress.incorrect_answers, 2)

        self.assertEqual(
            float(progress.mastery_score),
            54.0,
        )

        self.assertEqual(
            progress.status,
            GrammarProgress.Status.LEARNING,
        )

    def test_repeated_correct_answers_can_master_topic(self):
        for _ in range(5):
            response = self.client.post(
                '/api/v1/grammar/answer/',
                {
                    'exercise': self.exercise.id,
                    'answer': 'have been',
                },
                format='json',
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
            )

        progress = GrammarProgress.objects.get(
            user=self.user,
            topic=self.topic,
        )

        self.assertEqual(progress.correct_answers, 5)
        self.assertEqual(progress.incorrect_answers, 0)
        self.assertEqual(float(progress.mastery_score), 90.0)
        self.assertEqual(
            progress.status,
            GrammarProgress.Status.MASTERED,
        )

    def test_progress_is_private(self):
        self.client.post(
            '/api/v1/grammar/answer/',
            {
                'exercise': self.exercise.id,
                'answer': 'have been',
            },
            format='json',
        )

        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.get(
            '/api/v1/grammar/progress/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_other_user_cannot_access_progress_detail(self):
        progress, _ = GrammarProgress.objects.get_or_create(
            user=self.user,
            topic=self.topic,
        )

        self.client.force_authenticate(
            user=self.other_user,
        )

        response = self.client.get(
            f'/api/v1/grammar/progress/{progress.id}/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_due_topics(self):
        progress = GrammarProgress.objects.create(
            user=self.user,
            topic=self.topic,
            correct_answers=2,
            incorrect_answers=1,
            last_answer_correct=True,
            mastery_score=Decimal('58.67'),
            status=GrammarProgress.Status.LEARNING,
            last_reviewed_at=timezone.now() - timedelta(days=4),
            next_review_at=timezone.now() - timedelta(minutes=1),
        )

        response = self.client.get(
            '/api/v1/grammar/due/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]['topic']['title'],
            'Present Perfect',
        )

    def test_unauthenticated_access_is_denied(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            '/api/v1/grammar/topics/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
