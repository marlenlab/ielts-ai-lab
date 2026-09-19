from datetime import timedelta

from django.utils import timezone

from .models import VocabularyProgress


def calculate_mastery_score(progress):
    total_answers = (
        progress.correct_answers
        + progress.incorrect_answers
    )

    if total_answers == 0:
        return 0.0

    accuracy = (
        progress.correct_answers
        / total_answers
    )

    consistency_bonus = min(
        progress.correct_answers * 2,
        20,
    )

    score = (
        accuracy * 80
        + consistency_bonus
    )

    return round(
        min(score, 100),
        2,
    )


def calculate_status(mastery_score):
    if mastery_score >= 80:
        return VocabularyProgress.Status.MASTERED

    if mastery_score >= 40:
        return VocabularyProgress.Status.LEARNING

    return VocabularyProgress.Status.NEW


def calculate_next_review(progress):
    score = float(progress.mastery_score)

    if score >= 80:
        days = 14
    elif score >= 60:
        days = 7
    elif score >= 40:
        days = 3
    elif score >= 20:
        days = 1
    else:
        days = 0

    return timezone.now() + timedelta(
        days=days,
    )


def register_answer(
    user,
    word,
    correct,
):
    progress, _ = VocabularyProgress.objects.get_or_create(
        user=user,
        word=word,
    )

    if correct:
        progress.correct_answers += 1
    else:
        progress.incorrect_answers += 1

    progress.last_answer_correct = correct
    progress.last_reviewed_at = timezone.now()

    progress.mastery_score = calculate_mastery_score(
        progress,
    )

    progress.status = calculate_status(
        float(progress.mastery_score),
    )

    progress.next_review_at = calculate_next_review(
        progress,
    )

    progress.save()

    return progress
