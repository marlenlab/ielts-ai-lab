from rest_framework import serializers

from .models import (
    AdaptiveProfile,
    AdaptiveRecommendation,
)


class AdaptiveProfileSerializer(
    serializers.ModelSerializer,
):
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


class AdaptiveActivityAnswerSerializer(
    serializers.Serializer,
):
    item_id = serializers.IntegerField(
        min_value=1,
    )

    answer = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


class AdaptiveActivityAnswerResponseSerializer(
    serializers.Serializer,
):
    activity_id = serializers.IntegerField()
    item_id = serializers.IntegerField()
    correct = serializers.BooleanField()
    completed_count = serializers.IntegerField()
    target_count = serializers.IntegerField()
    correct_count = serializers.IntegerField()
    incorrect_count = serializers.IntegerField()
    points_earned = serializers.IntegerField()
    activity_completed = serializers.BooleanField()
    weakest_skill = serializers.CharField(
        allow_null=True,
    )
    strongest_skill = serializers.CharField(
        allow_null=True,
    )
    vocabulary_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )
    grammar_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
    )
