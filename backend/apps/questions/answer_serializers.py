from rest_framework import serializers

from .answer import Answer


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = (
            'id',
            'exam',
            'question',
            'answer',
            'is_correct',
            'points_earned',
            'answered_at',
        )
        read_only_fields = (
            'id',
            'is_correct',
            'points_earned',
            'answered_at',
        )
