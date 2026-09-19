from rest_framework import serializers

from .models import VocabularyProgress, VocabularyWord


class VocabularyWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyWord
        fields = (
            'id',
            'word',
            'definition',
            'example_sentence',
            'translation',
            'difficulty',
            'topic',
            'part_of_speech',
            'pronunciation',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )


class VocabularyProgressSerializer(serializers.ModelSerializer):
    word = VocabularyWordSerializer(
        read_only=True,
    )

    class Meta:
        model = VocabularyProgress
        fields = (
            'id',
            'word',
            'status',
            'correct_answers',
            'incorrect_answers',
            'last_answer_correct',
            'mastery_score',
            'last_reviewed_at',
            'next_review_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'word',
            'status',
            'correct_answers',
            'incorrect_answers',
            'last_answer_correct',
            'mastery_score',
            'last_reviewed_at',
            'next_review_at',
            'created_at',
            'updated_at',
        )


class VocabularyAnswerSerializer(serializers.Serializer):
    word = serializers.PrimaryKeyRelatedField(
        queryset=VocabularyWord.objects.all(),
    )

    correct = serializers.BooleanField()
