from decimal import Decimal
from typing import Dict, Optional, Tuple

from apps.adaptive.models import AdaptiveProfile
from apps.exams.models import Exam
from apps.learning.models import LearningSession
from apps.questions.answer import Answer

from .models import LearnerAnalytics


SkillScores = Dict[str, Optional[Decimal]]


SKILL_FIELDS = (
    'vocabulary_score',
    'grammar_score',
    'listening_score',
    'reading_score',
    'writing_score',
    'speaking_score',
)


def _calculate_accuracy(
    questions_answered: int,
    correct_answers: int,
) -> Decimal:
    if questions_answered == 0:
        return Decimal('0.00')

    accuracy = (
        Decimal(correct_answers)
        / Decimal(questions_answered)
        * Decimal('100')
    )

    return accuracy.quantize(Decimal('0.01'))


def _calculate_study_minutes(user) -> int:
    sessions = LearningSession.objects.filter(
        user=user,
        status=LearningSession.Status.COMPLETED,
        completed_at__isnull=False,
    )

    total_seconds = 0

    for session in sessions:
        if session.started_at and session.completed_at:
            duration = (
                session.completed_at - session.started_at
            ).total_seconds()

            if duration > 0:
                total_seconds += duration

    return int(total_seconds // 60)


def _get_skill_scores(user) -> SkillScores:
    try:
        profile = AdaptiveProfile.objects.get(
            user=user,
        )
    except AdaptiveProfile.DoesNotExist:
        return {
            field: Decimal('0.00')
            for field in SKILL_FIELDS
        }

    return {
        field: getattr(profile, field)
        for field in SKILL_FIELDS
    }


def _get_strongest_and_weakest_skill(
    skill_scores: SkillScores,
) -> Tuple[Optional[str], Optional[str]]:
    non_zero_scores: Dict[str, Decimal] = {
        field: score
        for field, score in skill_scores.items()
        if score is not None
    }

    if not non_zero_scores:
        return None, None

    strongest_skill = max(
        non_zero_scores,
        key=lambda field: non_zero_scores[field],
    )

    weakest_skill = min(
        non_zero_scores,
        key=lambda field: non_zero_scores[field],
    )

    return weakest_skill, strongest_skill


def update_analytics(user) -> LearnerAnalytics:
    """
    Recalculate and save all analytics for a user.
    """

    skill_scores = _get_skill_scores(user)

    weakest_skill, strongest_skill = (
        _get_strongest_and_weakest_skill(
            skill_scores
        )
    )

    exams_completed = Exam.objects.filter(
        user=user,
        status=Exam.Status.COMPLETED,
    ).count()

    answers_queryset = Answer.objects.filter(
        exam__user=user,
    )

    questions_answered = answers_queryset.count()

    correct_answers = answers_queryset.filter(
        points_earned__gt=0,
    ).count()

    accuracy = _calculate_accuracy(
        questions_answered=questions_answered,
        correct_answers=correct_answers,
    )

    study_minutes = _calculate_study_minutes(user)

    available_scores = [
        score
        for score in skill_scores.values()
        if score is not None
    ]

    if available_scores:
        overall_score = (
            sum(available_scores)
            / Decimal(len(available_scores))
        ).quantize(Decimal('0.01'))
    else:
        overall_score = Decimal('0.00')

    analytics, _ = LearnerAnalytics.objects.update_or_create(
        user=user,
        defaults={
            'overall_score': overall_score,
            'vocabulary_score': skill_scores[
                'vocabulary_score'
            ],
            'grammar_score': skill_scores[
                'grammar_score'
            ],
            'listening_score': skill_scores[
                'listening_score'
            ],
            'reading_score': skill_scores[
                'reading_score'
            ],
            'writing_score': skill_scores[
                'writing_score'
            ],
            'speaking_score': skill_scores[
                'speaking_score'
            ],
            'weakest_skill': weakest_skill,
            'strongest_skill': strongest_skill,
            'exams_completed': exams_completed,
            'questions_answered': questions_answered,
            'correct_answers': correct_answers,
            'accuracy': accuracy,
            'study_minutes': study_minutes,
        },
    )

    return analytics


def get_analytics(user) -> LearnerAnalytics:
    """
    Return fresh analytics for a user.
    """

    return update_analytics(user)
