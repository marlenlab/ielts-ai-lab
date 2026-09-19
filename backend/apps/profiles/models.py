from django.conf import settings
from django.db import models


class LearnerProfile(models.Model):
    class EnglishLevel(models.TextChoices):
        A1 = 'A1', 'A1'
        A2 = 'A2', 'A2'
        B1 = 'B1', 'B1'
        B2 = 'B2', 'B2'
        C1 = 'C1', 'C1'
        C2 = 'C2', 'C2'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learner_profile',
    )

    target_band = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
    )

    current_band = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
    )

    english_level = models.CharField(
        max_length=2,
        choices=EnglishLevel.choices,
        blank=True,
    )

    exam_date = models.DateField(
        null=True,
        blank=True,
    )

    daily_study_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    preferred_study_time = models.TimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} profile'
