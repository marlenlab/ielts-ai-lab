from decimal import Decimal
from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .evaluators import (
    AIEvaluationError,
    EvaluationResult,
    WritingEvaluator,
    evaluate_assessment,
)
from .models import AIAssessment
from .providers import AIProviderError
from .services import create_assessment


User = get_user_model()


class MockAIProvider:
    def __init__(
        self,
        response: dict[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error

    def evaluate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        if self.error is not None:
            raise self.error

        if self.response is None:
            raise RuntimeError(
                'Mock AI provider response is not configured.'
            )

        return self.response


def valid_ai_response() -> dict[str, Any]:
    return {
        'overall_score': 7.0,
        'feedback': (
            'The response addresses the task clearly '
            'and presents relevant ideas.'
        ),
        'strengths': [
            'Clear position.',
            'Logical organisation.',
        ],
        'weaknesses': [
            'Some ideas need more development.',
        ],
        'suggestions': [
            'Use more specific examples.',
        ],
        'criteria': {
            'task_achievement': 7.0,
            'coherence_cohesion': 7.0,
            'lexical_resource': 6.5,
            'grammar_accuracy': 6.5,
        },
    }


class AIAssessmentAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123',
        )

        self.client.force_authenticate(
            user=self.user,
        )

    def create_assessment(self):
        return AIAssessment.objects.create(
            user=self.user,
            skill=AIAssessment.Skill.WRITING,
            source_text='Write an essay about education.',
            task_response=(
                'Universities should provide students '
                'with useful knowledge.'
            ),
        )

    def test_create_assessment(self):
        response = self.client.post(
            reverse('ai-assessments'),
            {
                'skill': 'WRITING',
                'source_text': (
                    'Write an essay about education.'
                ),
                'task_response': (
                    'Universities should provide '
                    'students with useful knowledge.'
                ),
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data['skill'],
            'WRITING',
        )

        self.assertEqual(
            response.data['status'],
            'PENDING',
        )

    def test_create_assessment_requires_content(self):
        response = self.client.post(
            reverse('ai-assessments'),
            {
                'skill': 'WRITING',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_create_assessment_requires_authentication(self):
        self.client.force_authenticate(
            user=None,
        )

        response = self.client.post(
            reverse('ai-assessments'),
            {
                'skill': 'WRITING',
                'source_text': 'Task',
                'task_response': 'Response',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_list_assessments(self):
        self.create_assessment()

        response = self.client.get(
            reverse('ai-assessments'),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

    def test_detail_assessment(self):
        assessment = self.create_assessment()

        response = self.client.get(
            reverse(
                'ai-assessment-detail',
                kwargs={'pk': assessment.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data['id'],
            assessment.pk,
        )

    def test_detail_assessment_not_found(self):
        response = self.client.get(
            reverse(
                'ai-assessment-detail',
                kwargs={'pk': 99999},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_cannot_access_other_user_assessment(self):
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpassword123',
        )

        assessment = AIAssessment.objects.create(
            user=other_user,
            skill=AIAssessment.Skill.WRITING,
            source_text='Task',
            task_response='Response',
        )

        response = self.client.get(
            reverse(
                'ai-assessment-detail',
                kwargs={'pk': assessment.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_start_assessment(self):
        assessment = self.create_assessment()

        response = self.client.post(
            reverse(
                'ai-assessment-start',
                kwargs={'pk': assessment.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        assessment.refresh_from_db()

        self.assertEqual(
            assessment.status,
            AIAssessment.Status.PROCESSING,
        )

    def test_complete_assessment(self):
        assessment = self.create_assessment()

        start_response = self.client.post(
            reverse(
                'ai-assessment-start',
                kwargs={'pk': assessment.pk},
            ),
        )

        self.assertEqual(
            start_response.status_code,
            status.HTTP_200_OK,
        )

        assessment.refresh_from_db()

        self.assertEqual(
            assessment.status,
            AIAssessment.Status.PROCESSING,
        )

        response = self.client.post(
            reverse(
                'ai-assessment-complete',
                kwargs={'pk': assessment.pk},
            ),
            {
                'overall_score': '7.50',
                'task_achievement': '7.0',
                'coherence_cohesion': '7.0',
                'lexical_resource': '6.5',
                'grammar_accuracy': '6.5',
                'feedback': 'Good response.',
                'strengths': [
                    'Clear position.',
                ],
                'weaknesses': [
                    'Some ideas need development.',
                ],
                'suggestions': [
                    'Add specific examples.',
                ],
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        assessment.refresh_from_db()

        self.assertEqual(
            assessment.status,
            AIAssessment.Status.COMPLETED,
        )

        self.assertEqual(
            assessment.overall_score,
            Decimal('7.50'),
        )

        self.assertEqual(
            assessment.task_achievement,
            Decimal('7.0'),
        )

        self.assertEqual(
            assessment.coherence_cohesion,
            Decimal('7.0'),
        )

        self.assertEqual(
            assessment.lexical_resource,
            Decimal('6.5'),
        )

        self.assertEqual(
            assessment.grammar_accuracy,
            Decimal('6.5'),
        )

    def test_complete_assessment_rejects_invalid_criterion_score(self):
        assessment = self.create_assessment()

        response = self.client.post(
            reverse(
                'ai-assessment-complete',
                kwargs={'pk': assessment.pk},
            ),
            {
                'overall_score': '7.50',
                'task_achievement': '10.0',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_fail_assessment(self):
        assessment = self.create_assessment()

        start_response = self.client.post(
            reverse(
                'ai-assessment-start',
                kwargs={'pk': assessment.pk},
            ),
        )

        self.assertEqual(
            start_response.status_code,
            status.HTTP_200_OK,
        )

        assessment.refresh_from_db()

        self.assertEqual(
            assessment.status,
            AIAssessment.Status.PROCESSING,
        )

        response = self.client.post(
            reverse(
                'ai-assessment-fail',
                kwargs={'pk': assessment.pk},
            ),
            {
                'error_message': 'Provider unavailable.',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        assessment.refresh_from_db()

        self.assertEqual(
            assessment.status,
            AIAssessment.Status.FAILED,
        )

        self.assertEqual(
            assessment.error_message,
            'Provider unavailable.',
        )

    def test_start_other_user_assessment_returns_not_found(self):
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpassword123',
        )

        assessment = AIAssessment.objects.create(
            user=other_user,
            skill=AIAssessment.Skill.WRITING,
            source_text='Task',
            task_response='Response',
        )

        response = self.client.post(
            reverse(
                'ai-assessment-start',
                kwargs={'pk': assessment.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_complete_other_user_assessment_returns_not_found(self):
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpassword123',
        )

        assessment = AIAssessment.objects.create(
            user=other_user,
            skill=AIAssessment.Skill.WRITING,
            source_text='Task',
            task_response='Response',
        )

        response = self.client.post(
            reverse(
                'ai-assessment-complete',
                kwargs={'pk': assessment.pk},
            ),
            {
                'overall_score': '7.0',
                'task_achievement': '7.0',
                'coherence_cohesion': '7.0',
                'lexical_resource': '7.0',
                'grammar_accuracy': '7.0',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_fail_other_user_assessment_returns_not_found(self):
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpassword123',
        )

        assessment = AIAssessment.objects.create(
            user=other_user,
            skill=AIAssessment.Skill.WRITING,
            source_text='Task',
            task_response='Response',
        )

        response = self.client.post(
            reverse(
                'ai-assessment-fail',
                kwargs={'pk': assessment.pk},
            ),
            {
                'error_message': 'Provider unavailable.',
            },
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class WritingEvaluatorTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='evaluator',
            email='evaluator@example.com',
            password='testpassword123',
        )

        self.assessment = create_assessment(
            user=self.user,
            skill=AIAssessment.Skill.WRITING,
            source_text=(
                'Discuss whether universities should '
                'focus on employment.'
            ),
            task_response=(
                'Universities should prepare students '
                'for employment, but they should also '
                'provide a broader education.'
            ),
        )

    def test_build_prompt_contains_task_and_response(self):
        evaluator = WritingEvaluator(
            provider=MockAIProvider(
                response=valid_ai_response(),
            ),
        )

        prompt = evaluator.build_prompt(
            self.assessment,
        )

        self.assertIn(
            self.assessment.source_text,
            prompt,
        )

        self.assertIn(
            self.assessment.task_response,
            prompt,
        )

    def test_evaluation_returns_criterion_scores(self):
        evaluator = WritingEvaluator(
            provider=MockAIProvider(
                response=valid_ai_response(),
            ),
        )

        result = evaluator.evaluate(
            self.assessment,
        )

        self.assertEqual(
            result.overall_score,
            Decimal('7.0'),
        )

        self.assertEqual(
            result.task_achievement,
            Decimal('7.0'),
        )

        self.assertEqual(
            result.coherence_cohesion,
            Decimal('7.0'),
        )

        self.assertEqual(
            result.lexical_resource,
            Decimal('6.5'),
        )

        self.assertEqual(
            result.grammar_accuracy,
            Decimal('6.5'),
        )

    def test_evaluation_rejects_invalid_overall_score(self):
        response = valid_ai_response()

        response['overall_score'] = 10.0

        evaluator = WritingEvaluator(
            provider=MockAIProvider(
                response=response,
            ),
        )

        with self.assertRaises(
            AIEvaluationError,
        ):
            evaluator.evaluate(
                self.assessment,
            )

    def test_evaluation_rejects_invalid_criterion_score(self):
        response = valid_ai_response()

        response['criteria']['grammar_accuracy'] = 10.0

        evaluator = WritingEvaluator(
            provider=MockAIProvider(
                response=response,
            ),
        )

        with self.assertRaises(
            AIEvaluationError,
        ):
            evaluator.evaluate(
                self.assessment,
            )

    def test_evaluation_rejects_missing_criterion(self):
        response = valid_ai_response()

        del response['criteria']['lexical_resource']

        evaluator = WritingEvaluator(
            provider=MockAIProvider(
                response=response,
            ),
        )

        with self.assertRaises(
            AIEvaluationError,
        ):
            evaluator.evaluate(
                self.assessment,
            )

    def test_evaluation_completes_assessment(self):
        provider_response = valid_ai_response()

        provider_response['overall_score'] = 7.5
        provider_response['criteria'] = {
            'task_achievement': 7.5,
            'coherence_cohesion': 7.0,
            'lexical_resource': 7.0,
            'grammar_accuracy': 6.5,
        }

        provider = MockAIProvider(
            response=provider_response,
        )

        with patch(
            'apps.ai.evaluators.WritingEvaluator.evaluate',
            return_value=EvaluationResult(
                overall_score=Decimal('7.5'),
                task_achievement=Decimal('7.5'),
                coherence_cohesion=Decimal('7.0'),
                lexical_resource=Decimal('7.0'),
                grammar_accuracy=Decimal('6.5'),
                feedback='Strong response.',
                strengths=['Clear position.'],
                weaknesses=['Some grammar issues.'],
                suggestions=['Use more complex structures.'],
                raw_response=provider_response,
                processing_time_ms=500,
            ),
        ):
            assessment = evaluate_assessment(
                self.assessment,
                provider=provider,
            )

        self.assertEqual(
            assessment.status,
            AIAssessment.Status.COMPLETED,
        )

        self.assertEqual(
            assessment.overall_score,
            Decimal('7.5'),
        )

        self.assertEqual(
            assessment.task_achievement,
            Decimal('7.5'),
        )

        self.assertEqual(
            assessment.coherence_cohesion,
            Decimal('7.0'),
        )

        self.assertEqual(
            assessment.lexical_resource,
            Decimal('7.0'),
        )

        self.assertEqual(
            assessment.grammar_accuracy,
            Decimal('6.5'),
        )

        self.assertEqual(
            assessment.processing_time_ms,
            500,
        )

    def test_evaluation_provider_error_marks_assessment_failed(self):
        provider = MockAIProvider(
            error=AIProviderError(
                'Provider unavailable.',
            ),
        )

        assessment = evaluate_assessment(
            self.assessment,
            provider=provider,
        )

        self.assertEqual(
            assessment.status,
            AIAssessment.Status.FAILED,
        )

        self.assertEqual(
            assessment.error_message,
            'Provider unavailable.',
        )

    def test_evaluation_unsupported_skill_fails(self):
        self.assessment.skill = (
            AIAssessment.Skill.GRAMMAR
        )
        self.assessment.save()

        assessment = evaluate_assessment(
            self.assessment,
            provider=MockAIProvider(
                response=valid_ai_response(),
            ),
        )

        self.assertEqual(
            assessment.status,
            AIAssessment.Status.FAILED,
        )

        self.assertIn(
            'No evaluator implemented',
            assessment.error_message,
        )

    def test_evaluation_result_contains_all_writing_criteria(self):
        result = EvaluationResult(
            overall_score=Decimal('7.0'),
            task_achievement=Decimal('7.0'),
            coherence_cohesion=Decimal('6.5'),
            lexical_resource=Decimal('7.0'),
            grammar_accuracy=Decimal('6.5'),
            feedback='Good response.',
            strengths=['Clear ideas.'],
            weaknesses=['Limited development.'],
            suggestions=['Add examples.'],
            raw_response=valid_ai_response(),
            processing_time_ms=100,
        )

        self.assertEqual(
            result.task_achievement,
            Decimal('7.0'),
        )

        self.assertEqual(
            result.coherence_cohesion,
            Decimal('6.5'),
        )

        self.assertEqual(
            result.lexical_resource,
            Decimal('7.0'),
        )

        self.assertEqual(
            result.grammar_accuracy,
            Decimal('6.5'),
        )
