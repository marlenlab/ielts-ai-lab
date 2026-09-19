from django.conf import settings
from django.db import models

from apps.exams.models import ExamSection


class WritingTask(models.Model):

    class TaskType(models.TextChoices):
        TASK_1 = 'TASK_1', 'Task 1'
        TASK_2 = 'TASK_2', 'Task 2'

    task_type = models.CharField(
        max_length=10,
        choices=TaskType.choices,
    )

    title = models.CharField(
        max_length=255,
    )

    instructions = models.TextField()

    minimum_words = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ['task_type', 'id']

    def __str__(self):
        return f'{self.task_type} - {self.title}'


class WritingSubmission(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='writing_submissions',
    )

    section = models.ForeignKey(
        ExamSection,
        on_delete=models.CASCADE,
        related_name='writing_submissions',
    )

    task = models.ForeignKey(
        WritingTask,
        on_delete=models.CASCADE,
        related_name='submissions',
    )

    content = models.TextField(
        blank=True,
    )

    word_count = models.PositiveIntegerField(
        default=0,
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
                name='unique_writing_submission_per_task',
            ),
        ]
        ordering = ['task__task_type', 'id']

    def calculate_word_count(self):
        if not self.content.strip():
            return 0

        return len(self.content.split())

    def update_word_count(self):
        self.word_count = self.calculate_word_count()

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.task.task_type} - '
            f'{self.status}'
        )
