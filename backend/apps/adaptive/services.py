from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.grammar.models import GrammarProgress, GrammarTopic
from apps.learning.models import LearningActivity, LearningSession
from apps.vocabulary.models import VocabularyProgress, VocabularyWord

from .models import AdaptiveProfile, AdaptiveRecommendation


def get_vocabulary_score(user):
    progress_queryset = VocabularyProgress.objects.filter(
        user=user,
    )

    if not progress_queryset.exists():
        return None

    total = sum(
        progress.mastery_score
        for progress in progress_queryset
    )

    count = progress_queryset.count()

    if count == 0:
        return None

    return (total / count).quantize(Decimal('0.01'))


def get_grammar_score(user):
    progress_queryset = GrammarProgress.objects.filter(
        user=user,
    )

    if not progress_queryset.exists():
        return None

    total = sum(
        progress.mastery_score
        for progress in progress_queryset
    )

    count = progress_queryset.count()

    if count == 0:
        return None

    return (total / count).quantize(Decimal('0.01'))


def calculate_skill_scores(user):
    return {
        AdaptiveProfile.Skill.VOCABULARY: get_vocabulary_score(user),
        AdaptiveProfile.Skill.GRAMMAR: get_grammar_score(user),
        AdaptiveProfile.Skill.LISTENING: None,
        AdaptiveProfile.Skill.READING: None,
        AdaptiveProfile.Skill.WRITING: None,
        AdaptiveProfile.Skill.SPEAKING: None,
    }


def get_assessed_scores(skill_scores):
    return {
        skill: score
        for skill, score in skill_scores.items()
        if score is not None
    }


def update_adaptive_profile(user):
    skill_scores = calculate_skill_scores(user)
    assessed_scores = get_assessed_scores(skill_scores)

    profile, _ = AdaptiveProfile.objects.get_or_create(
        user=user,
    )

    profile.vocabulary_score = (
        skill_scores[AdaptiveProfile.Skill.VOCABULARY]
        or Decimal('0.00')
    )

    profile.grammar_score = (
        skill_scores[AdaptiveProfile.Skill.GRAMMAR]
        or Decimal('0.00')
    )

    profile.listening_score = Decimal('0.00')
    profile.reading_score = Decimal('0.00')
    profile.writing_score = Decimal('0.00')
    profile.speaking_score = Decimal('0.00')

    if assessed_scores:
        weakest_skill = min(
            assessed_scores.items(),
            key=lambda item: item[1],
        )[0]

        strongest_skill = max(
            assessed_scores.items(),
            key=lambda item: item[1],
        )[0]

        profile.weakest_skill = weakest_skill
        profile.strongest_skill = strongest_skill
    else:
        profile.weakest_skill = None
        profile.strongest_skill = None

    profile.save()

    return profile


def get_recommendation_priority(score):
    if score < Decimal('40.00'):
        return AdaptiveRecommendation.Priority.HIGH

    if score < Decimal('70.00'):
        return AdaptiveRecommendation.Priority.MEDIUM

    return AdaptiveRecommendation.Priority.LOW


def build_recommendation(user, skill, score):
    priority = get_recommendation_priority(score)

    titles = {
        AdaptiveProfile.Skill.VOCABULARY:
            'Improve your vocabulary',
        AdaptiveProfile.Skill.GRAMMAR:
            'Improve your grammar',
        AdaptiveProfile.Skill.LISTENING:
            'Improve your listening',
        AdaptiveProfile.Skill.READING:
            'Improve your reading',
        AdaptiveProfile.Skill.WRITING:
            'Improve your writing',
        AdaptiveProfile.Skill.SPEAKING:
            'Improve your speaking',
    }

    reasons = {
        AdaptiveProfile.Skill.VOCABULARY:
            'Your vocabulary mastery score indicates that '
            'additional vocabulary practice is needed.',
        AdaptiveProfile.Skill.GRAMMAR:
            'Your grammar mastery score indicates that '
            'additional grammar practice is needed.',
        AdaptiveProfile.Skill.LISTENING:
            'Listening performance needs additional practice.',
        AdaptiveProfile.Skill.READING:
            'Reading performance needs additional practice.',
        AdaptiveProfile.Skill.WRITING:
            'Writing performance needs additional practice.',
        AdaptiveProfile.Skill.SPEAKING:
            'Speaking performance needs additional practice.',
    }

    return AdaptiveRecommendation.objects.create(
        user=user,
        skill=skill,
        title=titles[skill],
        reason=reasons[skill],
        priority=priority,
        score=score,
    )


def generate_recommendations(user):
    update_adaptive_profile(user)

    AdaptiveRecommendation.objects.filter(
        user=user,
        is_completed=False,
    ).delete()

    skill_scores = calculate_skill_scores(user)

    recommendations = []

    for skill, score in skill_scores.items():
        if score is None:
            continue

        recommendations.append(
            build_recommendation(
                user=user,
                skill=skill,
                score=score,
            )
        )

    return recommendations


def complete_recommendation(recommendation):
    if recommendation.is_completed:
        return recommendation

    recommendation.is_completed = True
    recommendation.completed_at = timezone.now()

    recommendation.save(
        update_fields=[
            'is_completed',
            'completed_at',
        ],
    )

    return recommendation


def get_activity_target_count(priority):
    if priority == AdaptiveRecommendation.Priority.HIGH:
        return 15

    if priority == AdaptiveRecommendation.Priority.MEDIUM:
        return 10

    return 5


def get_vocabulary_content(user, target_count):
    progress_queryset = (
        VocabularyProgress.objects
        .filter(user=user)
        .select_related('word')
        .order_by(
            'mastery_score',
            'next_review_at',
            'id',
        )[:target_count]
    )

    items = []

    for progress in progress_queryset:
        word = progress.word

        items.append({
            'id': word.id,
            'word': word.word,
            'definition': word.definition,
            'example_sentence': word.example_sentence,
            'translation': word.translation,
            'difficulty': word.difficulty,
            'topic': word.topic,
            'part_of_speech': word.part_of_speech,
            'pronunciation': word.pronunciation,
            'mastery_score': float(progress.mastery_score),
        })

    if not items:
        words = (
            VocabularyWord.objects
            .order_by('id')[:target_count]
        )

        for word in words:
            items.append({
                'id': word.id,
                'word': word.word,
                'definition': word.definition,
                'example_sentence': word.example_sentence,
                'translation': word.translation,
                'difficulty': word.difficulty,
                'topic': word.topic,
                'part_of_speech': word.part_of_speech,
                'pronunciation': word.pronunciation,
                'mastery_score': 0.0,
            })

    return items


def get_grammar_content(user, target_count):
    progress_queryset = (
        GrammarProgress.objects
        .filter(user=user)
        .select_related('topic')
        .order_by(
            'mastery_score',
            'next_review_at',
            'id',
        )
    )

    items = []

    for progress in progress_queryset:
        topic = progress.topic

        exercises = (
            topic.exercises
            .order_by('order', 'id')[:target_count]
        )

        for exercise in exercises:
            items.append({
                'id': exercise.id,
                'topic_id': topic.id,
                'topic_title': topic.title,
                'topic_level': topic.level,
                'exercise_type': exercise.exercise_type,
                'question': exercise.question,
                'options': exercise.options,
                'points': exercise.points,
                'explanation': exercise.explanation,
                'mastery_score': float(progress.mastery_score),
            })

            if len(items) >= target_count:
                return items

    if not items:
        topics = (
            GrammarTopic.objects
            .prefetch_related('exercises')
            .order_by('level', 'id')
        )

        for topic in topics:
            for exercise in topic.exercises.all():
                items.append({
                    'id': exercise.id,
                    'topic_id': topic.id,
                    'topic_title': topic.title,
                    'topic_level': topic.level,
                    'exercise_type': exercise.exercise_type,
                    'question': exercise.question,
                    'options': exercise.options,
                    'points': exercise.points,
                    'explanation': exercise.explanation,
                    'mastery_score': 0.0,
                })

                if len(items) >= target_count:
                    return items

    return items


def get_adaptive_content(user, skill, target_count):
    if skill == AdaptiveProfile.Skill.VOCABULARY:
        return get_vocabulary_content(
            user=user,
            target_count=target_count,
        )

    if skill == AdaptiveProfile.Skill.GRAMMAR:
        return get_grammar_content(
            user=user,
            target_count=target_count,
        )

    return []


def create_activity_for_recommendation(
    session,
    recommendation,
    order,
):
    target_count = get_activity_target_count(
        recommendation.priority,
    )

    activity_type_map = {
        AdaptiveProfile.Skill.VOCABULARY:
            LearningActivity.ActivityType.VOCABULARY,
        AdaptiveProfile.Skill.GRAMMAR:
            LearningActivity.ActivityType.GRAMMAR,
        AdaptiveProfile.Skill.LISTENING:
            LearningActivity.ActivityType.LISTENING,
        AdaptiveProfile.Skill.READING:
            LearningActivity.ActivityType.READING,
        AdaptiveProfile.Skill.WRITING:
            LearningActivity.ActivityType.WRITING,
        AdaptiveProfile.Skill.SPEAKING:
            LearningActivity.ActivityType.SPEAKING,
    }

    activity_type = activity_type_map[
        recommendation.skill
    ]

    content = get_adaptive_content(
        user=session.user,
        skill=recommendation.skill,
        target_count=target_count,
    )

    description = (
        f'Adaptive {recommendation.skill.lower()} practice '
        f'generated from your current learning profile.'
    )

    return LearningActivity.objects.create(
        session=session,
        activity_type=activity_type,
        title=recommendation.title,
        description=description,
        target_count=target_count,
        order=order,
        content={
            'skill': recommendation.skill,
            'recommendation_id': recommendation.id,
            'items': content,
        },
    )


@transaction.atomic
def create_adaptive_learning_session(user):
    recommendations = list(
        AdaptiveRecommendation.objects
        .filter(
            user=user,
            is_completed=False,
        )
        .order_by(
            '-score',
            'created_at',
        )[:3]
    )

    if not recommendations:
        recommendations = generate_recommendations(user)

    recommendations = recommendations[:3]

    if not recommendations:
        return None

    session = LearningSession.objects.create(
        user=user,
        session_type=LearningSession.SessionType.MIXED,
        status=LearningSession.Status.ACTIVE,
        target_minutes=30,
    )

    for index, recommendation in enumerate(
        recommendations,
        start=1,
    ):
        create_activity_for_recommendation(
            session=session,
            recommendation=recommendation,
            order=index,
        )

    return session
