from decimal import Decimal

from django.conf import settings
from django.db import models


class AdaptiveProfile(models.Model):
    class Skill(models.TextChoices):
        VOCABULARY = 'VOCABULARY', 'Vocabulary'
        GRAMMAR = 'GRAMMAR', 'Grammar'
        LISTENING = 'LISTENING', 'Listening'
        READING = 'READING', 'Reading'
        WRITING = 'WRITING', 'Writing'
        SPEAKING = 'SPEAKING', 'Speaking'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='adaptive_profile',
    )

    weakest_skill = models.CharField(
        max_length=20,
        choices=Skill.choices,
        null=True,
        blank=True,
    )

    strongest_skill = models.CharField(
        max_length=20,
        choices=Skill.choices,
        null=True,
        blank=True,
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

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user.username} adaptive profile'


class AdaptiveRecommendation(models.Model):
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='adaptive_recommendations',
    )

    skill = models.CharField(
        max_length=20,
        choices=AdaptiveProfile.Skill.choices,
    )

    title = models.CharField(max_length=255)

    reason = models.TextField()

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    is_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-priority', '-score', '-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.skill} - {self.title}'
