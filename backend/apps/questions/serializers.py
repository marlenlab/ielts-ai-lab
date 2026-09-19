from rest_framework import serializers

from apps.exams.models import ExamSection

from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    section = serializers.PrimaryKeyRelatedField(
        queryset=ExamSection.objects.all(),
    )

    class Meta:
        model = Question
        fields = (
            'id',
            'section',
            'skill',
            'question_type',
            'text',
            'options',
            'correct_answer',
            'points',
            'order',
            'explanation',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )
