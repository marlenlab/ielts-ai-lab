from rest_framework import serializers

from .models import LearningActivity, LearningSession


class LearningActivitySerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = LearningActivity
        fields = (
            'id',
            'activity_type',
            'title',
            'description',
            'target_count',
            'completed_count',
            'correct_count',
            'incorrect_count',
            'points_earned',
            'order',
            'is_completed',
            'completed_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'completed_count',
            'correct_count',
            'incorrect_count',
            'points_earned',
            'is_completed',
            'completed_at',
            'created_at',
            'updated_at',
        )

    def get_is_completed(self, obj):
        return obj.is_completed()


class LearningSessionSerializer(serializers.ModelSerializer):
    activities = LearningActivitySerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = LearningSession
        fields = (
            'id',
            'session_type',
            'status',
            'target_minutes',
            'started_at',
            'completed_at',
            'activities',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'status',
            'started_at',
            'completed_at',
            'activities',
            'created_at',
            'updated_at',
        )
