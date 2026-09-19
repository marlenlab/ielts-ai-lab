from rest_framework import serializers

from .models import Exam, ExamSection


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = (
            'id',
            'exam_type',
            'status',
            'started_at',
            'submitted_at',
            'completed_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'status',
            'started_at',
            'submitted_at',
            'completed_at',
            'created_at',
            'updated_at',
        )


class ExamSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamSection
        fields = (
            'id',
            'section_type',
            'status',
            'started_at',
            'submitted_at',
            'completed_at',
            'score',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'status',
            'started_at',
            'submitted_at',
            'completed_at',
            'score',
            'created_at',
            'updated_at',
        )
