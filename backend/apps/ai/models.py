from django.conf import settings
from django.db import models


class AIAssessment(models.Model):
    class Skill(models.TextChoices):
        WRITING = 'WRITING', 'Writing'
        SPEAKING = 'SPEAKING', 'Speaking'
        GRAMMAR = 'GRAMMAR', 'Grammar'
        VOCABULARY = 'VOCABULARY', 'Vocabulary'
        READING = 'READING', 'Reading'
        LISTENING = 'LISTENING', 'Listening'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_assessments',
    )

    skill = models.CharField(
        max_length=20,
        choices=Skill.choices,
    )

    source_text = models.TextField(
        blank=True,
    )

    source_file = models.FileField(
        upload_to='ai/assessments/',
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Overall IELTS band score.
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # IELTS Writing criteria.
    task_achievement = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )

    coherence_cohesion = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )

    lexical_resource = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )

    grammar_accuracy = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
    )

    task_response = models.TextField(
        blank=True,
    )

    feedback = models.TextField(
        blank=True,
    )

    strengths = models.JSONField(
        default=list,
        blank=True,
    )

    weaknesses = models.JSONField(
        default=list,
        blank=True,
    )

    suggestions = models.JSONField(
        default=list,
        blank=True,
    )

    raw_response = models.JSONField(
        default=dict,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
    )

    processing_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.skill} - '
            f'{self.status}'
        )
