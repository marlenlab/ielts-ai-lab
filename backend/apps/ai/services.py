from decimal import Decimal
from typing import Optional

from django.utils import timezone

from .models import AIAssessment


def create_assessment(
    user,
    skill,
    source_text='',
    source_file=None,
    task_response='',
):
    return AIAssessment.objects.create(
        user=user,
        skill=skill,
        source_text=source_text,
        source_file=source_file,
        task_response=task_response,
        status=AIAssessment.Status.PENDING,
    )


def start_assessment(assessment):
    assessment.status = AIAssessment.Status.PROCESSING
    assessment.error_message = ''

    assessment.save(
        update_fields=[
            'status',
            'error_message',
            'updated_at',
        ]
    )

    return assessment


def complete_assessment(
    assessment,
    overall_score: Decimal,
    feedback='',
    strengths: Optional[list] = None,
    weaknesses: Optional[list] = None,
    suggestions: Optional[list] = None,
    raw_response: Optional[dict] = None,
    processing_time_ms: Optional[int] = None,
    task_achievement: Optional[Decimal] = None,
    coherence_cohesion: Optional[Decimal] = None,
    lexical_resource: Optional[Decimal] = None,
    grammar_accuracy: Optional[Decimal] = None,
):
    assessment.status = AIAssessment.Status.COMPLETED
    assessment.overall_score = overall_score

    assessment.task_achievement = task_achievement
    assessment.coherence_cohesion = coherence_cohesion
    assessment.lexical_resource = lexical_resource
    assessment.grammar_accuracy = grammar_accuracy

    assessment.feedback = feedback
    assessment.strengths = strengths or []
    assessment.weaknesses = weaknesses or []
    assessment.suggestions = suggestions or []
    assessment.raw_response = raw_response or {}
    assessment.processing_time_ms = processing_time_ms

    assessment.completed_at = timezone.now()
    assessment.error_message = ''

    assessment.save()

    return assessment


def fail_assessment(
    assessment,
    error_message,
):
    assessment.status = AIAssessment.Status.FAILED
    assessment.error_message = error_message
    assessment.completed_at = None

    assessment.save(
        update_fields=[
            'status',
            'error_message',
            'completed_at',
            'updated_at',
        ]
    )

    return assessment
