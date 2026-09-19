from decimal import Decimal
from typing import Dict, Optional

from django.db import transaction
from django.utils import timezone

from apps.grammar.models import (
    GrammarExercise,
    GrammarProgress,
)
from apps.grammar.services import (
    register_answer as register_grammar_answer,
)
from apps.learning.models import (
    LearningActivity,
    LearningSession,
)
from apps.vocabulary.models import (
    VocabularyProgress,
    VocabularyWord,
)
from apps.vocabulary.services import (
    register_answer as register_vocabulary_answer,
)

from .models import (
    AdaptiveProfile,
    AdaptiveRecommendation,
)


SkillScores = Dict[
    str,
    Optional[Decimal],
]


SKILL_FIELDS = {
    AdaptiveProfile.Skill.VOCABULARY: 'vocabulary_score',
    AdaptiveProfile.Skill.GRAMMAR: 'grammar_score',
    AdaptiveProfile.Skill.LISTENING: 'listening_score',
    AdaptiveProfile.Skill.READING: 'reading_score',
    AdaptiveProfile.Skill.WRITING: 'writing_score',
    AdaptiveProfile.Skill.SPEAKING: 'speaking_score',
}


def calculate_skill_scores(
    user,
) -> SkillScores:
    scores: SkillScores = {
        AdaptiveProfile.Skill.VOCABULARY: None,
        AdaptiveProfile.Skill.GRAMMAR: None,
        AdaptiveProfile.Skill.LISTENING: None,
        AdaptiveProfile.Skill.READING: None,
        AdaptiveProfile.Skill.WRITING: None,
        AdaptiveProfile.Skill.SPEAKING: None,
    }

    vocabulary_progress = (
        VocabularyProgress.objects.filter(
            user=user,
        )
    )

    if vocabulary_progress.exists():
        vocabulary_count = (
            vocabulary_progress.count()
        )

        vocabulary_average = (
            sum(
                (
                    progress.mastery_score
                    for progress in vocabulary_progress
                ),
                Decimal('0.00'),
            )
            / vocabulary_count
        )

        scores[
            AdaptiveProfile.Skill.VOCABULARY
        ] = vocabulary_average.quantize(
            Decimal('0.01')
        )

    grammar_progress = (
        GrammarProgress.objects.filter(
            user=user,
        )
    )

    if grammar_progress.exists():
        grammar_count = (
            grammar_progress.count()
        )

        grammar_average = (
            sum(
                (
                    progress.mastery_score
                    for progress in grammar_progress
                ),
                Decimal('0.00'),
            )
            / grammar_count
        )

        scores[
            AdaptiveProfile.Skill.GRAMMAR
        ] = grammar_average.quantize(
            Decimal('0.01')
        )

    return scores


def update_adaptive_profile(
    user,
):
    scores = calculate_skill_scores(user)

    profile, _ = (
        AdaptiveProfile.objects.get_or_create(
            user=user,
        )
    )

    for skill, field_name in SKILL_FIELDS.items():
        score = scores.get(skill)

        if score is not None:
            setattr(
                profile,
                field_name,
                score,
            )

    available_scores: Dict[str, Decimal] = {
        skill: score
        for skill, score in scores.items()
        if score is not None
    }

    if available_scores:
        weakest_skill = min(
            available_scores,
            key=lambda skill: available_scores[skill],
        )

        strongest_skill = max(
            available_scores,
            key=lambda skill: available_scores[skill],
        )

        profile.weakest_skill = (
            weakest_skill
        )
        profile.strongest_skill = (
            strongest_skill
        )
    else:
        profile.weakest_skill = None
        profile.strongest_skill = None

    profile.save()

    return profile


def get_recommendation_priority(
    score,
):
    score = Decimal(str(score))

    if score < 40:
        return AdaptiveRecommendation.Priority.HIGH

    if score < 70:
        return AdaptiveRecommendation.Priority.MEDIUM

    return AdaptiveRecommendation.Priority.LOW


def generate_recommendations(
    user,
):
    update_adaptive_profile(user)

    scores = calculate_skill_scores(user)

    (
        AdaptiveRecommendation.objects
        .filter(
            user=user,
            is_completed=False,
        )
        .delete()
    )

    recommendations = []

    skill_data = [
        (
            AdaptiveProfile.Skill.VOCABULARY,
            scores.get(
                AdaptiveProfile.Skill.VOCABULARY,
            ),
            'Improve vocabulary',
            'Vocabulary mastery is below the target level.',
        ),
        (
            AdaptiveProfile.Skill.GRAMMAR,
            scores.get(
                AdaptiveProfile.Skill.GRAMMAR,
            ),
            'Improve grammar',
            'Grammar mastery is below the target level.',
        ),
        (
            AdaptiveProfile.Skill.LISTENING,
            scores.get(
                AdaptiveProfile.Skill.LISTENING,
            ),
            'Improve listening',
            'Listening performance needs more practice.',
        ),
        (
            AdaptiveProfile.Skill.READING,
            scores.get(
                AdaptiveProfile.Skill.READING,
            ),
            'Improve reading',
            'Reading performance needs more practice.',
        ),
        (
            AdaptiveProfile.Skill.WRITING,
            scores.get(
                AdaptiveProfile.Skill.WRITING,
            ),
            'Improve writing',
            'Writing performance needs more practice.',
        ),
        (
            AdaptiveProfile.Skill.SPEAKING,
            scores.get(
                AdaptiveProfile.Skill.SPEAKING,
            ),
            'Improve speaking',
            'Speaking performance needs more practice.',
        ),
    ]

    for (
        skill,
        score,
        title,
        reason,
    ) in skill_data:
        if score is None:
            continue

        recommendation = (
            AdaptiveRecommendation.objects.create(
                user=user,
                skill=skill,
                title=title,
                reason=reason,
                priority=(
                    get_recommendation_priority(
                        score,
                    )
                ),
                score=score,
            )
        )

        recommendations.append(
            recommendation,
        )

    return recommendations


def complete_recommendation(
    recommendation,
):
    if recommendation.is_completed:
        return recommendation

    recommendation.is_completed = True
    recommendation.completed_at = (
        timezone.now()
    )

    recommendation.save(
        update_fields=[
            'is_completed',
            'completed_at',
        ],
    )

    return recommendation


def get_vocabulary_content(
    user,
    target_count=10,
):
    progress_queryset = (
        VocabularyProgress.objects
        .filter(
            user=user,
        )
        .select_related('word')
        .order_by(
            'mastery_score',
            'last_reviewed_at',
            'id',
        )
    )

    content = []

    for progress in progress_queryset[
        :target_count
    ]:
        word = progress.word

        content.append(
            {
                'id': word.id,
                'word': word.word,
                'definition': word.definition,
                'example_sentence': (
                    word.example_sentence
                ),
                'translation': word.translation,
                'difficulty': word.difficulty,
                'topic': word.topic,
                'part_of_speech': (
                    word.part_of_speech
                ),
                'pronunciation': (
                    word.pronunciation
                ),
                'mastery_score': float(
                    progress.mastery_score
                ),
            }
        )

    return content


def get_grammar_content(
    user,
    target_count=10,
):
    progress_queryset = (
        GrammarProgress.objects
        .filter(
            user=user,
        )
        .select_related('topic')
        .order_by(
            'mastery_score',
            'last_reviewed_at',
            'id',
        )
    )

    content = []

    for progress in progress_queryset:
        exercises = (
            GrammarExercise.objects
            .filter(
                topic=progress.topic,
            )
            .order_by(
                'order',
                'id',
            )
        )

        for exercise in exercises:
            if len(content) >= target_count:
                break

            content.append(
                {
                    'id': exercise.id,
                    'topic_id': (
                        progress.topic.id
                    ),
                    'topic_title': (
                        progress.topic.title
                    ),
                    'exercise_type': (
                        exercise.exercise_type
                    ),
                    'question': exercise.question,
                    'options': exercise.options,
                    'correct_answer': (
                        exercise.correct_answer
                    ),
                    'explanation': (
                        exercise.explanation
                    ),
                    'points': exercise.points,
                    'mastery_score': float(
                        progress.mastery_score
                    ),
                }
            )

        if len(content) >= target_count:
            break

    return content


def get_adaptive_content(
    user,
    skill,
    target_count=10,
):
    if skill == (
        AdaptiveProfile.Skill.VOCABULARY
    ):
        return get_vocabulary_content(
            user=user,
            target_count=target_count,
        )

    if skill == (
        AdaptiveProfile.Skill.GRAMMAR
    ):
        return get_grammar_content(
            user=user,
            target_count=target_count,
        )

    return []


def create_adaptive_learning_session(
    user,
):
    recommendations = (
        generate_recommendations(user)
    )

    if not recommendations:
        return None

    session = LearningSession.objects.create(
        user=user,
        session_type=(
            LearningSession.SessionType.MIXED
        ),
        target_minutes=30,
    )

    order = 1

    for recommendation in recommendations:
        if recommendation.skill not in (
            AdaptiveProfile.Skill.VOCABULARY,
            AdaptiveProfile.Skill.GRAMMAR,
        ):
            continue

        if recommendation.skill == (
            AdaptiveProfile.Skill.VOCABULARY
        ):
            target_count = 15
            activity_type = (
                LearningActivity
                .ActivityType
                .VOCABULARY
            )
        else:
            target_count = 10
            activity_type = (
                LearningActivity
                .ActivityType
                .GRAMMAR
            )

        content = get_adaptive_content(
            user=user,
            skill=recommendation.skill,
            target_count=target_count,
        )

        LearningActivity.objects.create(
            session=session,
            activity_type=activity_type,
            title=recommendation.title,
            description=recommendation.reason,
            target_count=target_count,
            order=order,
            content={
                'skill': recommendation.skill,
                'recommendation_id': (
                    recommendation.id
                ),
                'items': content,
            },
        )

        order += 1

    if not session.activities.exists():
        session.delete()
        return None

    return session


def get_activity_by_user(
    user,
    activity_id,
):
    return (
        LearningActivity.objects
        .select_related('session')
        .filter(
            id=activity_id,
            session__user=user,
        )
        .first()
    )


def validate_activity_item(
    activity,
    item_id,
):
    content = activity.content or {}
    items = content.get(
        'items',
        [],
    )

    for item in items:
        if item.get('id') == item_id:
            return item

    return None


@transaction.atomic
def submit_adaptive_activity_answer(
    user,
    activity_id,
    item_id,
    answer,
):
    activity = get_activity_by_user(
        user=user,
        activity_id=activity_id,
    )

    if activity is None:
        raise ValueError(
            'Adaptive activity was not found.'
        )

    if activity.session.status != (
        LearningSession.Status.ACTIVE
    ):
        raise ValueError(
            'Learning session is not active.'
        )

    item = validate_activity_item(
        activity=activity,
        item_id=item_id,
    )

    if item is None:
        raise ValueError(
            'The selected item does not belong '
            'to this activity.'
        )

    answer = answer.strip()

    if not answer:
        raise ValueError(
            'Answer cannot be empty.'
        )

    skill = activity.content.get(
        'skill',
    )

    if skill == (
        AdaptiveProfile.Skill.VOCABULARY
    ):
        try:
            word = VocabularyWord.objects.get(
                pk=item_id,
            )
        except VocabularyWord.DoesNotExist:
            raise ValueError(
                'Vocabulary word was not found.'
            )

        submitted_answer = (
            answer.lower()
        )

        accepted_answers = {
            word.word.strip().lower(),
        }

        if word.translation:
            accepted_answers.add(
                word.translation
                .strip()
                .lower()
            )

        correct = (
            submitted_answer
            in accepted_answers
        )

        register_vocabulary_answer(
            user=user,
            word=word,
            correct=correct,
        )

        points = 1 if correct else 0

    elif skill == (
        AdaptiveProfile.Skill.GRAMMAR
    ):
        try:
            exercise = GrammarExercise.objects.get(
                pk=item_id,
            )
        except GrammarExercise.DoesNotExist:
            raise ValueError(
                'Grammar exercise was not found.'
            )

        (
            grammar_progress,
            correct,
        ) = register_grammar_answer(
            user=user,
            exercise=exercise,
            answer=answer,
        )

        points = (
            exercise.points
            if correct
            else 0
        )

    else:
        raise ValueError(
            'This adaptive skill does not support '
            'answer submission yet.'
        )

    activity.completed_count += 1

    if correct:
        activity.correct_count += 1
        activity.points_earned += points
    else:
        activity.incorrect_count += 1

    if activity.is_completed():
        activity.completed_at = (
            timezone.now()
        )

    activity.save(
        update_fields=[
            'completed_count',
            'correct_count',
            'incorrect_count',
            'points_earned',
            'completed_at',
            'updated_at',
        ],
    )

    profile = update_adaptive_profile(
        user,
    )

    return {
        'activity': activity,
        'item': item,
        'correct': correct,
        'profile': profile,
    }
