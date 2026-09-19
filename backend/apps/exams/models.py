from django.conf import settings
from django.db import models


class Exam(models.Model):
    class ExamType(models.TextChoices):
        FULL_MOCK = 'FULL_MOCK', 'Full Mock'
        DIAGNOSTIC = 'DIAGNOSTIC', 'Diagnostic'
        PRACTICE = 'PRACTICE', 'Practice'

    class Status(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Not Started'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        PAUSED = 'PAUSED', 'Paused'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='exams',
    )

    exam_type = models.CharField(
        max_length=20,
        choices=ExamType.choices,
        default=ExamType.FULL_MOCK,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.exam_type}'
