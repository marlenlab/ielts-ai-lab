from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.grammar.models import GrammarProgress, GrammarTopic
from apps.learning.models import (
    LearningActivity,
    LearningSession,
)
from apps.vocabulary.models import VocabularyProgress, VocabularyWord

from .models import AdaptiveProfile, AdaptiveRecommendation
from .services import (
    calculate_skill_scores,
    complete_recommendation,
    generate_recommendations,
    update_adaptive_profile,
)

User = get_user_model()


class AdaptiveServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='adaptive_user',
            email='adaptive@example.com',
            password='testpass123',
        )

        self.vocabulary_word = VocabularyWord.objects.create(
            word='substantial',
            definition='Large or important in size or amount.',
            example_sentence=(
                'The project requires substantial effort.'
            ),
            translation='значительный',
            difficulty='B2',
            topic='Academic',
            part_of_speech='adjective',
        )

        self.grammar_topic = GrammarTopic.objects.create(
            title='Present Perfect',
            description='Using the present perfect tense.',
            level='B2',
            explanation=(
                'The present perfect connects past actions '
                'to the present.'
            ),
            examples=[
                'I have finished my homework.',
            ],
            common_mistakes=[
                'Using past simple instead of present perfect.',
            ],
        )

    def test_calculate_skill_scores(self):
        VocabularyProgress.objects.create(
            user=self.user,
            word=self.vocabulary_word,
            mastery_score=Decimal('60.00'),
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=self.grammar_topic,
            mastery_score=Decimal('80.00'),
        )

        scores = calculate_skill_scores(self.user)

        self.assertEqual(
            scores[AdaptiveProfile.Skill.VOCABULARY],
            Decimal('60.00'),
        )

        self.assertEqual(
            scores[AdaptiveProfile.Skill.GRAMMAR],
            Decimal('80.00'),
        )

        self.assertIsNone(
            scores[AdaptiveProfile.Skill.LISTENING],
        )

        self.assertIsNone(
            scores[AdaptiveProfile.Skill.READING],
        )

        self.assertIsNone(
            scores[AdaptiveProfile.Skill.WRITING],
        )

        self.assertIsNone(
            scores[AdaptiveProfile.Skill.SPEAKING],
        )

    def test_update_adaptive_profile(self):
        VocabularyProgress.objects.create(
            user=self.user,
            word=self.vocabulary_word,
            mastery_score=Decimal('30.00'),
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=self.grammar_topic,
            mastery_score=Decimal('80.00'),
        )

        profile = update_adaptive_profile(
            self.user,
        )

        self.assertEqual(
            profile.vocabulary_score,
            Decimal('30.00'),
        )

        self.assertEqual(
            profile.grammar_score,
            Decimal('80.00'),
        )

        self.assertEqual(
            profile.weakest_skill,
            AdaptiveProfile.Skill.VOCABULARY,
        )

        self.assertEqual(
            profile.strongest_skill,
            AdaptiveProfile.Skill.GRAMMAR,
        )

        self.assertEqual(
            profile.listening_score,
            Decimal('0.00'),
        )

        self.assertEqual(
            profile.reading_score,
            Decimal('0.00'),
        )

        self.assertEqual(
            profile.writing_score,
            Decimal('0.00'),
        )

        self.assertEqual(
            profile.speaking_score,
            Decimal('0.00'),
        )

    def test_update_adaptive_profile_with_no_progress(self):
        profile = update_adaptive_profile(
            self.user,
        )

        self.assertIsNone(
            profile.weakest_skill,
        )

        self.assertIsNone(
            profile.strongest_skill,
        )

        self.assertEqual(
            profile.vocabulary_score,
            Decimal('0.00'),
        )

        self.assertEqual(
            profile.grammar_score,
            Decimal('0.00'),
        )

    def test_generate_recommendations(self):
        VocabularyProgress.objects.create(
            user=self.user,
            word=self.vocabulary_word,
            mastery_score=Decimal('30.00'),
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=self.grammar_topic,
            mastery_score=Decimal('80.00'),
        )

        recommendations = generate_recommendations(
            self.user,
        )

        self.assertEqual(
            len(recommendations),
            2,
        )

        self.assertEqual(
            recommendations[0].skill,
            AdaptiveProfile.Skill.VOCABULARY,
        )

        self.assertEqual(
            recommendations[0].score,
            Decimal('30.00'),
        )

        self.assertEqual(
            recommendations[0].priority,
            AdaptiveRecommendation.Priority.HIGH,
        )

        self.assertEqual(
            recommendations[1].skill,
            AdaptiveProfile.Skill.GRAMMAR,
        )

        self.assertEqual(
            recommendations[1].score,
            Decimal('80.00'),
        )

        self.assertEqual(
            recommendations[1].priority,
            AdaptiveRecommendation.Priority.LOW,
        )

    def test_generate_recommendations_without_progress(self):
        recommendations = generate_recommendations(
            self.user,
        )

        self.assertEqual(
            len(recommendations),
            0,
        )

        self.assertFalse(
            AdaptiveRecommendation.objects.filter(
                user=self.user,
            ).exists(),
        )

    def test_complete_recommendation(self):
        recommendation = (
            AdaptiveRecommendation.objects.create(
                user=self.user,
                skill=AdaptiveProfile.Skill.VOCABULARY,
                title='Improve vocabulary',
                reason='Vocabulary score is low.',
                priority=(
                    AdaptiveRecommendation.Priority.HIGH
                ),
                score=Decimal('30.00'),
            )
        )

        completed = complete_recommendation(
            recommendation,
        )

        self.assertTrue(
            completed.is_completed,
        )

        self.assertIsNotNone(
            completed.completed_at,
        )

    def test_complete_already_completed_recommendation(self):
        recommendation = (
            AdaptiveRecommendation.objects.create(
                user=self.user,
                skill=AdaptiveProfile.Skill.VOCABULARY,
                title='Improve vocabulary',
                reason='Vocabulary score is low.',
                priority=(
                    AdaptiveRecommendation.Priority.HIGH
                ),
                score=Decimal('30.00'),
                is_completed=True,
            )
        )

        original_completed_at = (
            recommendation.completed_at
        )

        completed = complete_recommendation(
            recommendation,
        )

        self.assertTrue(
            completed.is_completed,
        )

        self.assertEqual(
            completed.completed_at,
            original_completed_at,
        )


class AdaptiveAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='api_user',
            email='api@example.com',
            password='testpass123',
        )

        self.other_user = User.objects.create_user(
            username='other_user',
            email='other@example.com',
            password='testpass123',
        )

        self.vocabulary_word = VocabularyWord.objects.create(
            word='significant',
            definition='Important or noticeable.',
            example_sentence=(
                'This is a significant improvement.'
            ),
            translation='значительный',
            difficulty='B2',
            topic='Academic',
            part_of_speech='adjective',
        )

        self.grammar_topic = GrammarTopic.objects.create(
            title='Conditionals',
            description='Conditional sentences.',
            level='B2',
            explanation=(
                'Conditionals describe possible or '
                'imaginary situations.'
            ),
            examples=[
                'If I study, I will improve.',
            ],
            common_mistakes=[
                'Incorrect verb forms.',
            ],
        )

        self.client.force_authenticate(
            user=self.user,
        )

    def test_profile_endpoint_requires_authentication(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.get(
            '/api/v1/adaptive/profile/',
        )

        self.assertEqual(
            response.status_code,
            401,
        )

    def test_profile_endpoint_returns_user_profile(self):
        VocabularyProgress.objects.create(
            user=self.user,
            word=self.vocabulary_word,
            mastery_score=Decimal('45.00'),
        )

        response = self.client.get(
            '/api/v1/adaptive/profile/',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['vocabulary_score'],
            '45.00',
        )

        self.assertEqual(
            response.data['weakest_skill'],
            AdaptiveProfile.Skill.VOCABULARY,
        )

        self.assertEqual(
            AdaptiveProfile.objects.filter(
                user=self.user,
            ).count(),
            1,
        )

    def test_generate_recommendations_endpoint(self):
        VocabularyProgress.objects.create(
            user=self.user,
            word=self.vocabulary_word,
            mastery_score=Decimal('30.00'),
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=self.grammar_topic,
            mastery_score=Decimal('80.00'),
        )

        response = self.client.post(
            '/api/v1/adaptive/recommendations/generate/',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data['count'],
            2,
        )

        self.assertEqual(
            response.data['recommendations'][0]['skill'],
            AdaptiveProfile.Skill.VOCABULARY,
        )

        self.assertEqual(
            response.data['recommendations'][0]['priority'],
            AdaptiveRecommendation.Priority.HIGH,
        )

    def test_recommendations_list_is_user_specific(self):
        AdaptiveRecommendation.objects.create(
            user=self.user,
            skill=AdaptiveProfile.Skill.VOCABULARY,
            title='Improve vocabulary',
            reason='Low vocabulary score.',
            priority=AdaptiveRecommendation.Priority.HIGH,
            score=Decimal('30.00'),
        )

        AdaptiveRecommendation.objects.create(
            user=self.other_user,
            skill=AdaptiveProfile.Skill.GRAMMAR,
            title='Improve grammar',
            reason='Low grammar score.',
            priority=AdaptiveRecommendation.Priority.HIGH,
            score=Decimal('20.00'),
        )

        response = self.client.get(
            '/api/v1/adaptive/recommendations/',
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
            response.data[0]['skill'],
            AdaptiveProfile.Skill.VOCABULARY,
        )

    def test_complete_recommendation_endpoint(self):
        recommendation = (
            AdaptiveRecommendation.objects.create(
                user=self.user,
                skill=AdaptiveProfile.Skill.VOCABULARY,
                title='Improve vocabulary',
                reason='Low vocabulary score.',
                priority=AdaptiveRecommendation.Priority.HIGH,
                score=Decimal('30.00'),
            )
        )

        response = self.client.post(
            f'/api/v1/adaptive/recommendations/'
            f'{recommendation.id}/complete/',
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(
            response.data['is_completed'],
        )

        recommendation.refresh_from_db()

        self.assertTrue(
            recommendation.is_completed,
        )

        self.assertIsNotNone(
            recommendation.completed_at,
        )

    def test_cannot_complete_other_users_recommendation(self):
        recommendation = (
            AdaptiveRecommendation.objects.create(
                user=self.other_user,
                skill=AdaptiveProfile.Skill.GRAMMAR,
                title='Improve grammar',
                reason='Low grammar score.',
                priority=AdaptiveRecommendation.Priority.HIGH,
                score=Decimal('20.00'),
            )
        )

        response = self.client.post(
            f'/api/v1/adaptive/recommendations/'
            f'{recommendation.id}/complete/',
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class AdaptiveLearningSessionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='learning_user',
            email='learning@example.com',
            password='testpass123',
        )

        self.vocabulary_word = VocabularyWord.objects.create(
            word='persistent',
            definition='Continuing firmly despite difficulty.',
            example_sentence=(
                'Persistent practice leads to improvement.'
            ),
            translation='настойчивый',
            difficulty='B2',
            topic='Academic',
            part_of_speech='adjective',
        )

        self.grammar_topic = GrammarTopic.objects.create(
            title='Passive Voice',
            description='Using passive voice.',
            level='B2',
            explanation=(
                'The passive voice focuses on the action '
                'or the receiver of the action.'
            ),
            examples=[
                'The book was written in 2020.',
            ],
            common_mistakes=[
                'Incorrect past participle.',
            ],
        )

        self.client.force_authenticate(
            user=self.user,
        )

    def test_create_adaptive_learning_session(self):
        VocabularyProgress.objects.create(
            user=self.user,
            word=self.vocabulary_word,
            mastery_score=Decimal('30.00'),
        )

        GrammarProgress.objects.create(
            user=self.user,
            topic=self.grammar_topic,
            mastery_score=Decimal('60.00'),
        )

        response = self.client.post(
            '/api/v1/adaptive/learning-session/',
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data['session_type'],
            'MIXED',
        )

        self.assertEqual(
            response.data['target_minutes'],
            30,
        )

        self.assertEqual(
            len(response.data['activities']),
            2,
        )

        self.assertEqual(
            response.data['activities'][0][
                'activity_type'
            ],
            'VOCABULARY',
        )

        self.assertEqual(
            response.data['activities'][0][
                'target_count'
            ],
            15,
        )

        self.assertEqual(
            response.data['activities'][1][
                'activity_type'
            ],
            'GRAMMAR',
        )

        self.assertEqual(
            response.data['activities'][1][
                'target_count'
            ],
            10,
        )

        self.assertEqual(
            LearningSession.objects.filter(
                user=self.user,
            ).count(),
            1,
        )

        self.assertEqual(
            LearningActivity.objects.filter(
                session__user=self.user,
            ).count(),
            2,
        )

    def test_create_adaptive_learning_session_without_data(
        self,
    ):
        response = self.client.post(
            '/api/v1/adaptive/learning-session/',
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            LearningSession.objects.filter(
                user=self.user,
            ).count(),
            0,
        )
