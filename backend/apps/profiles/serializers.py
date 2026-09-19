from rest_framework import serializers

from .models import LearnerProfile


class LearnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearnerProfile
        fields = (
            'target_band',
            'current_band',
            'english_level',
            'exam_date',
            'daily_study_minutes',
            'preferred_study_time',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'created_at',
            'updated_at',
        )
