from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from .models import VocabularyProgress, VocabularyWord


User = get_user_model()


class VocabularyAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='vocabularytest',
            email='vocabularytest@example.com',
            password='TestPassword123',
        )

        self.other_user = User.objects.create_user(
            username='othervocabulary',
            email='othervocabulary@example.com',
            password='TestPassword123',
        )

        self.client.force_authenticate(
            user=self.user,
        )

        self.word = VocabularyWord.objects.create(
            word='sustainable',
            definition='Able to continue without causing serious damage.',
            example_sentence=(
                'We need to develop sustainable solutions.'
            ),
            translation='устойчивый',
            difficulty=VocabularyWord.Difficulty.B2,
            topic='Environment',
            part_of_speech='adjective',
            pronunciation='/səˈsteɪnəbl/',
        )

        self.second_word = VocabularyWord.objects.create(
            word='innovation',
            definition='A new idea, method, or technology.',
            example_sentence=(
                'Innovation can improve many industries.'
            ),
            translation='инновация',
            difficulty=VocabularyWord.Difficulty.C1,
            topic='Technology',
            part_of_speech='noun',
            pronunciation='/ˌɪnəˈveɪʃən/',
        )

    def test_list_vocabulary_words(self):
        response = self.client.get(
            '/api/v1/vocabulary/words/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            2,
        )

    def test_filter_vocabulary_by_difficulty(self):
        response = self.client.get(
            '/api/v1/vocabulary/words/?difficulty=B2'
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
            response.data[0]['word'],
            'sustainable',
        )

    def test_filter_vocabulary_by_topic(self):
        response = self.client.get(
            '/api/v1/vocabulary/words/?topic=technology'
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
            response.data[0]['word'],
            'innovation',
        )

    def test_create_vocabulary_word(self):
        response = self.client.post(
            '/api/v1/vocabulary/words/',
            {
                'word': 'resilient',
                'definition': 'Able to recover quickly from difficulties.',
                'example_sentence': (
                    'Successful people are often resilient.'
                ),
                'translation': 'устойчивый',
                'difficulty': 'C1',
                'topic': 'Personal Development',
                'part_of_speech': 'adjective',
                'pronunciation': '/rɪˈzɪliənt/',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data['word'],
            'resilient',
        )

    def test_answer_creates_progress(self):
        response = self.client.post(
            '/api/v1/vocabulary/answer/',
            {
                'word': self.word.id,
                'correct': True,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        progress = VocabularyProgress.objects.get(
            user=self.user,
            word=self.word,
        )

        self.assertEqual(
            progress.correct_answers,
            1,
        )

        self.assertEqual(
            progress.incorrect_answers,
            0,
        )

        self.assertTrue(
            progress.last_answer_correct,
        )

        self.assertGreater(
            float(progress.mastery_score),
            0,
        )

        self.assertIsNotNone(
            progress.next_review_at,
        )

    def test_incorrect_answer_updates_progress(self):
        response = self.client.post(
            '/api/v1/vocabulary/answer/',
            {
                'word': self.word.id,
                'correct': False,
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        progress = VocabularyProgress.objects.get(
            user=self.user,
            word=self.word,
        )

        self.assertEqual(
            progress.correct_answers,
            0,
        )

        self.assertEqual(
            progress.incorrect_answers,
            1,
        )

        self.assertFalse(
            progress.last_answer_correct,
        )

        self.assertEqual(
            float(progress.mastery_score),
            0,
        )

        self.assertEqual(
            progress.status,
            VocabularyProgress.Status.NEW,
        )

    def test_repeated_correct_answers_increase_mastery(self):
        for _ in range(5):
            response = self.client.post(
                '/api/v1/vocabulary/answer/',
                {
                    'word': self.word.id,
                    'correct': True,
                },
                format='json',
            )

            self.assertEqual(
                response.status_code,
                200,
            )

        progress = VocabularyProgress.objects.get(
            user=self.user,
            word=self.word,
        )

        self.assertEqual(
            progress.correct_answers,
            5,
        )

        self.assertEqual(
            progress.incorrect_answers,
            0,
        )

        self.assertEqual(
            float(progress.mastery_score),
            90.0,
        )

        self.assertEqual(
            progress.status,
            VocabularyProgress.Status.MASTERED,
        )

    def test_mixed_answers_calculate_mastery(self):
        answers = [
            True,
            True,
            False,
            True,
            False,
        ]

        for correct in answers:
            response = self.client.post(
                '/api/v1/vocabulary/answer/',
                {
                    'word': self.word.id,
                    'correct': correct,
                },
                format='json',
            )

            self.assertEqual(
                response.status_code,
                200,
            )

        progress = VocabularyProgress.objects.get(
            user=self.user,
            word=self.word,
        )

        self.assertEqual(
            progress.correct_answers,
            3,
        )

        self.assertEqual(
            progress.incorrect_answers,
            2,
        )

        self.assertEqual(
            float(progress.mastery_score),
            54.0,
        )

        self.assertEqual(
            progress.status,
            VocabularyProgress.Status.LEARNING,
        )

    def test_progress_is_private_to_user(self):
        VocabularyProgress.objects.create(
            user=self.other_user,
            word=self.word,
            correct_answers=10,
            mastery_score=100,
            status=VocabularyProgress.Status.MASTERED,
        )

        response = self.client.get(
            '/api/v1/vocabulary/progress/'
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            0,
        )

    def test_user_cannot_access_another_users_progress_detail(self):
        other_progress = VocabularyProgress.objects.create(
            user=self.other_user,
            word=self.word,
            correct_answers=5,
            mastery_score=90,
            status=VocabularyProgress.Status.MASTERED,
        )

        response = self.client.get(
            f'/api/v1/vocabulary/progress/{other_progress.id}/'
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_due_words_returns_review_items(self):
        progress = VocabularyProgress.objects.create(
            user=self.user,
            word=self.word,
            correct_answers=1,
            mastery_score=10,
            status=VocabularyProgress.Status.NEW,
            next_review_at=timezone.now() - timedelta(
                minutes=5,
            ),
        )

        response = self.client.get(
            '/api/v1/vocabulary/due/'
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
            progress.id,
        )

    def test_unauthenticated_access_denied(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            '/api/v1/vocabulary/progress/'
        )

        self.assertEqual(
            response.status_code,
            401,
        )
