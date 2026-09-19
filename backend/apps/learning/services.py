from django.utils import timezone

from .models import LearningActivity, LearningSession


def calculate_session_progress(session):
    activities = session.activities.all()

    total_target = sum(
        activity.target_count
        for activity in activities
    )

    total_completed = sum(
        activity.completed_count
        for activity in activities
    )

    total_correct = sum(
        activity.correct_count
        for activity in activities
    )

    total_incorrect = sum(
        activity.incorrect_count
        for activity in activities
    )

    total_points = sum(
        activity.points_earned
        for activity in activities
    )

    if total_target == 0:
        completion_percentage = 0.0
    else:
        completion_percentage = round(
            min(
                total_completed / total_target * 100,
                100,
            ),
            2,
        )

    total_answers = total_correct + total_incorrect

    if total_answers == 0:
        accuracy_percentage = 0.0
    else:
        accuracy_percentage = round(
            total_correct / total_answers * 100,
            2,
        )

    return {
        'total_activities': activities.count(),
        'total_target': total_target,
        'total_completed': total_completed,
        'completion_percentage': completion_percentage,
        'correct_answers': total_correct,
        'incorrect_answers': total_incorrect,
        'accuracy_percentage': accuracy_percentage,
        'points_earned': total_points,
    }


def complete_activity(
    activity,
    completed_count=1,
    correct_count=0,
    incorrect_count=0,
    points_earned=0,
):
    if activity.session.status != LearningSession.Status.ACTIVE:
        return activity

    activity.completed_count += completed_count
    activity.correct_count += correct_count
    activity.incorrect_count += incorrect_count
    activity.points_earned += points_earned

    if activity.is_completed():
        activity.completed_count = min(
            activity.completed_count,
            activity.target_count,
        )
        activity.completed_at = timezone.now()

    activity.save()

    return activity


def complete_session(session):
    if session.status != LearningSession.Status.ACTIVE:
        return False

    activities = session.activities.all()

    if not activities.exists():
        return False

    if not all(
        activity.is_completed()
        for activity in activities
    ):
        return False

    session.status = LearningSession.Status.COMPLETED
    session.completed_at = timezone.now()
    session.save(
        update_fields=[
            'status',
            'completed_at',
            'updated_at',
        ],
    )

    return True


def cancel_session(session):
    if session.status != LearningSession.Status.ACTIVE:
        return False

    session.status = LearningSession.Status.CANCELLED
    session.save(
        update_fields=[
            'status',
            'updated_at',
        ],
    )

    return True
