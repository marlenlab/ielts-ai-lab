from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.adaptive.models import AdaptiveProfile
from apps.learning.models import LearningSession

from .models import LearnerAnalytics
from .services import (
    SkillScores,
    _calculate_accuracy,
    _calculate_study_minutes,
    _get_strongest_and_weakest_skill,
    update_analytics,
)


User = get_user_model()


class AnalyticsServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='analytics_user',
            email='analytics@example.com',
            password='StrongPassword123!',
        )

    def test_calculate_accuracy(self):
        accuracy = _calculate_accuracy(
            questions_answered=10,
            correct_answers=8,
        )

        self.assertEqual(
            accuracy,
            Decimal('80.00'),
        )

    def test_calculate_accuracy_without_answers(self):
        accuracy = _calculate_accuracy(
            questions_answered=0,
            correct_answers=0,
        )

        self.assertEqual(
            accuracy,
            Decimal('0.00'),
        )

    def test_strongest_and_weakest_skill(self):
        skill_scores: SkillScores = {
            'vocabulary_score': Decimal('70.00'),
            'grammar_score': Decimal('45.00'),
            'listening_score': Decimal('80.00'),
            'reading_score': Decimal('60.00'),
            'writing_score': Decimal('35.00'),
            'speaking_score': Decimal('55.00'),
        }

        weakest, strongest = (
            _get_strongest_and_weakest_skill(
                skill_scores
            )
        )

        self.assertEqual(
            weakest,
            'writing_score',
        )

        self.assertEqual(
            strongest,
            'listening_score',
        )

    def test_update_analytics_creates_analytics(self):
        AdaptiveProfile.objects.create(
            user=self.user,
            vocabulary_score=Decimal('70.00'),
            grammar_score=Decimal('50.00'),
            listening_score=Decimal('80.00'),
            reading_score=Decimal('60.00'),
            writing_score=Decimal('40.00'),
            speaking_score=Decimal('30.00'),
        )

        analytics = update_analytics(
            self.user
        )

        self.assertIsInstance(
            analytics,
            LearnerAnalytics,
        )

        self.assertEqual(
            analytics.vocabulary_score,
            Decimal('70.00'),
        )

        self.assertEqual(
            analytics.grammar_score,
            Decimal('50.00'),
        )

        self.assertEqual(
            analytics.overall_score,
            Decimal('55.00'),
        )

        self.assertEqual(
            analytics.weakest_skill,
            'speaking_score',
        )

        self.assertEqual(
            analytics.strongest_skill,
            'listening_score',
        )

    def test_update_analytics_without_adaptive_profile(self):
        analytics = update_analytics(
            self.user
        )

        self.assertEqual(
            analytics.overall_score,
            Decimal('0.00'),
        )

        self.assertEqual(
            analytics.vocabulary_score,
            Decimal('0.00'),
        )

        self.assertEqual(
            analytics.grammar_score,
            Decimal('0.00'),
        )

        self.assertEqual(
            analytics.weakest_skill,
            'vocabulary_score',
        )

        self.assertEqual(
            analytics.strongest_skill,
            'vocabulary_score',
        )

    def test_study_minutes_from_completed_sessions(self):
        session = LearningSession.objects.create(
            user=self.user,
            session_type=LearningSession.SessionType.MIXED,
            status=LearningSession.Status.COMPLETED,
            target_minutes=30,
        )

        completed_at = timezone.now()
        started_at = completed_at - timedelta(
            minutes=45
        )

        LearningSession.objects.filter(
            pk=session.pk
        ).update(
            started_at=started_at,
            completed_at=completed_at,
        )

        study_minutes = _calculate_study_minutes(
            self.user
        )

        self.assertEqual(
            study_minutes,
            45,
        )

        session.refresh_from_db()

        self.assertEqual(
            session.status,
            LearningSession.Status.COMPLETED,
        )


class AnalyticsAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='analytics_api_user',
            email='analytics_api@example.com',
            password='StrongPassword123!',
        )

        self.client.force_authenticate(
            user=self.user
        )

    def test_dashboard_requires_authentication(self):
        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            '/api/v1/analytics/dashboard/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_dashboard_returns_analytics(self):
        AdaptiveProfile.objects.create(
            user=self.user,
            vocabulary_score=Decimal('75.00'),
            grammar_score=Decimal('55.00'),
            listening_score=Decimal('85.00'),
            reading_score=Decimal('65.00'),
            writing_score=Decimal('45.00'),
            speaking_score=Decimal('35.00'),
        )

        response = self.client.get(
            '/api/v1/analytics/dashboard/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['overall_score'],
            '60.00',
        )

        self.assertEqual(
            response.data['skills']['vocabulary'],
            Decimal('75.00'),
        )

        self.assertEqual(
            response.data['skills']['listening'],
            Decimal('85.00'),
        )

        self.assertEqual(
            response.data['weakest_skill'],
            'speaking_score',
        )

        self.assertEqual(
            response.data['strongest_skill'],
            'listening_score',
        )

    def test_dashboard_creates_analytics_record(self):
        self.assertFalse(
            LearnerAnalytics.objects.filter(
                user=self.user
            ).exists()
        )

        response = self.client.get(
            '/api/v1/analytics/dashboard/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            LearnerAnalytics.objects.filter(
                user=self.user
            ).exists()
        )

    def test_dashboard_contains_progress_metrics(self):
        response = self.client.get(
            '/api/v1/analytics/dashboard/'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            'exams_completed',
            response.data,
        )

        self.assertIn(
            'questions_answered',
            response.data,
        )

        self.assertIn(
            'correct_answers',
            response.data,
        )

        self.assertIn(
            'accuracy',
            response.data,
        )

        self.assertIn(
            'study_minutes',
            response.data,
        )
