from decimal import Decimal

from django.conf import settings
from django.db import models


class LearnerAnalytics(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics',
    )

    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    vocabulary_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    grammar_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    listening_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    reading_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    writing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    speaking_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    weakest_skill = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    strongest_skill = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    exams_completed = models.PositiveIntegerField(
        default=0,
    )

    questions_answered = models.PositiveIntegerField(
        default=0,
    )

    correct_answers = models.PositiveIntegerField(
        default=0,
    )

    accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    study_minutes = models.PositiveIntegerField(
        default=0,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user.username} analytics'
