from rest_framework import serializers

from .models import AdaptiveProfile, AdaptiveRecommendation


class AdaptiveProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptiveProfile
        fields = (
            'id',
            'weakest_skill',
            'strongest_skill',
            'vocabulary_score',
            'grammar_score',
            'listening_score',
            'reading_score',
            'writing_score',
            'speaking_score',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class AdaptiveRecommendationSerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = AdaptiveRecommendation
        fields = (
            'id',
            'skill',
            'title',
            'reason',
            'priority',
            'score',
            'is_completed',
            'created_at',
            'completed_at',
        )
        read_only_fields = fields


class AdaptiveLearningActivitySerializer(
    serializers.Serializer,
):
    id = serializers.IntegerField()
    activity_type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    target_count = serializers.IntegerField()
    order = serializers.IntegerField()
    content = serializers.JSONField()


class AdaptiveLearningSessionSerializer(
    serializers.Serializer,
):
    session_id = serializers.IntegerField()
    session_type = serializers.CharField()
    status = serializers.CharField()
    target_minutes = serializers.IntegerField()
    activities = AdaptiveLearningActivitySerializer(
        many=True,
    )
