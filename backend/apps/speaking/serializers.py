from rest_framework import serializers

from .models import SpeakingSubmission, SpeakingTask


class SpeakingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingTask
        fields = (
            'id',
            'part',
            'title',
            'instructions',
            'preparation_seconds',
            'response_seconds',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )


class SpeakingSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingSubmission
        fields = (
            'id',
            'section',
            'task',
            'audio_file',
            'audio_url',
            'transcript',
            'duration_seconds',
            'status',
            'submitted_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'status',
            'submitted_at',
            'created_at',
            'updated_at',
        )
