from django.conf import settings
from django.db import models

from apps.exams.models import ExamSection


class SpeakingTask(models.Model):

    class Part(models.TextChoices):
        PART_1 = 'PART_1', 'Part 1'
        PART_2 = 'PART_2', 'Part 2'
        PART_3 = 'PART_3', 'Part 3'

    part = models.CharField(
        max_length=10,
        choices=Part.choices,
    )

    title = models.CharField(
        max_length=255,
    )

    instructions = models.TextField()

    preparation_seconds = models.PositiveIntegerField(
        default=0,
    )

    response_seconds = models.PositiveIntegerField(
        default=60,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ['part', 'id']

    def __str__(self):
        return f'{self.part} - {self.title}'


class SpeakingSubmission(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='speaking_submissions',
    )

    section = models.ForeignKey(
        ExamSection,
        on_delete=models.CASCADE,
        related_name='speaking_submissions',
    )

    task = models.ForeignKey(
        SpeakingTask,
        on_delete=models.CASCADE,
        related_name='submissions',
    )

    audio_file = models.FileField(
        upload_to='speaking/audio/',
        null=True,
        blank=True,
    )

    audio_url = models.URLField(
        blank=True,
    )

    transcript = models.TextField(
        blank=True,
    )

    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'section', 'task'],
                name='unique_speaking_submission_per_task',
            ),
        ]
        ordering = ['task__part', 'id']

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.task.part} - '
            f'{self.status}'
        )
