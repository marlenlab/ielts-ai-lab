from rest_framework import serializers

from .models import WritingSubmission, WritingTask


class WritingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingTask
        fields = (
            'id',
            'task_type',
            'title',
            'instructions',
            'minimum_words',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )


class WritingSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WritingSubmission
        fields = (
            'id',
            'section',
            'task',
            'content',
            'word_count',
            'status',
            'submitted_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'word_count',
            'status',
            'submitted_at',
            'created_at',
            'updated_at',
        )
