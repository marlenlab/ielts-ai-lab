from rest_framework import serializers

from .models import LearnerAnalytics


class LearnerAnalyticsSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()

    class Meta:
        model = LearnerAnalytics
        fields = (
            'id',
            'overall_score',
            'skills',
            'weakest_skill',
            'strongest_skill',
            'exams_completed',
            'questions_answered',
            'correct_answers',
            'accuracy',
            'study_minutes',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_skills(self, obj):
        return {
            'vocabulary': obj.vocabulary_score,
            'grammar': obj.grammar_score,
            'listening': obj.listening_score,
            'reading': obj.reading_score,
            'writing': obj.writing_score,
            'speaking': obj.speaking_score,
        }
