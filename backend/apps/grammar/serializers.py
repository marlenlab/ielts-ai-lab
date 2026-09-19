from rest_framework import serializers

from .models import GrammarExercise, GrammarProgress, GrammarTopic


class GrammarTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarTopic
        fields = (
            'id',
            'title',
            'description',
            'level',
            'explanation',
            'examples',
            'common_mistakes',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )


class GrammarExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarExercise
        fields = (
            'id',
            'topic',
            'exercise_type',
            'question',
            'options',
            'correct_answer',
            'explanation',
            'points',
            'order',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )


class StudentGrammarExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrammarExercise
        fields = (
            'id',
            'topic',
            'exercise_type',
            'question',
            'options',
            'points',
            'order',
            'explanation',
        )
        read_only_fields = (
            'id',
            'topic',
            'exercise_type',
            'question',
            'options',
            'points',
            'order',
            'explanation',
        )


class GrammarProgressSerializer(serializers.ModelSerializer):
    topic = GrammarTopicSerializer(read_only=True)

    class Meta:
        model = GrammarProgress
        fields = (
            'id',
            'topic',
            'correct_answers',
            'incorrect_answers',
            'last_answer_correct',
            'mastery_score',
            'status',
            'last_reviewed_at',
            'next_review_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'topic',
            'correct_answers',
            'incorrect_answers',
            'last_answer_correct',
            'mastery_score',
            'status',
            'last_reviewed_at',
            'next_review_at',
            'created_at',
            'updated_at',
        )


class GrammarAnswerSerializer(serializers.Serializer):
    exercise = serializers.PrimaryKeyRelatedField(
        queryset=GrammarExercise.objects.select_related('topic').all()
    )
    answer = serializers.CharField()
