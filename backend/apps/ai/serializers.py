from rest_framework import serializers

from .models import AIAssessment


class AIAssessmentSerializer(
    serializers.ModelSerializer,
):
    class Meta:
        model = AIAssessment

        fields = [
            'id',
            'skill',
            'source_text',
            'source_file',
            'status',
            'overall_score',
            'task_achievement',
            'coherence_cohesion',
            'lexical_resource',
            'grammar_accuracy',
            'task_response',
            'feedback',
            'strengths',
            'weaknesses',
            'suggestions',
            'raw_response',
            'error_message',
            'processing_time_ms',
            'created_at',
            'updated_at',
            'completed_at',
        ]

        read_only_fields = [
            'id',
            'status',
            'overall_score',
            'task_achievement',
            'coherence_cohesion',
            'lexical_resource',
            'grammar_accuracy',
            'feedback',
            'strengths',
            'weaknesses',
            'suggestions',
            'raw_response',
            'error_message',
            'processing_time_ms',
            'created_at',
            'updated_at',
            'completed_at',
        ]

    def validate_skill(self, value):
        valid_skills = {
            choice[0]
            for choice in AIAssessment.Skill.choices
        }

        if value not in valid_skills:
            raise serializers.ValidationError(
                'Invalid AI assessment skill.'
            )

        return value

    def validate(self, attrs):
        source_text = attrs.get(
            'source_text',
            '',
        )

        source_file = attrs.get(
            'source_file'
        )

        task_response = attrs.get(
            'task_response',
            '',
        )

        if not any([
            source_text,
            source_file,
            task_response,
        ]):
            raise serializers.ValidationError(
                'At least one of source_text, '
                'source_file, or task_response '
                'is required.'
            )

        return attrs


class AIAssessmentCompleteSerializer(
    serializers.Serializer,
):
    overall_score = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
    )

    task_achievement = serializers.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        max_value=9,
        required=False,
        allow_null=True,
    )

    coherence_cohesion = serializers.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        max_value=9,
        required=False,
        allow_null=True,
    )

    lexical_resource = serializers.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        max_value=9,
        required=False,
        allow_null=True,
    )

    grammar_accuracy = serializers.DecimalField(
        max_digits=3,
        decimal_places=1,
        min_value=0,
        max_value=9,
        required=False,
        allow_null=True,
    )

    feedback = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    strengths = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    weaknesses = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    suggestions = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )

    raw_response = serializers.JSONField(
        required=False,
    )

    processing_time_ms = serializers.IntegerField(
        required=False,
        min_value=0,
    )


class AIAssessmentFailSerializer(
    serializers.Serializer,
):
    error_message = serializers.CharField(
        min_length=1,
    )
