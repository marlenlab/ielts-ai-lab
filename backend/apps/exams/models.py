from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


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

    duration_minutes = models.PositiveIntegerField(
        default=165,
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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def is_expired(self):
        if self.status != self.Status.IN_PROGRESS:
            return False

        if not self.started_at:
            return False

        end_time = (
            self.started_at
            + timedelta(minutes=self.duration_minutes)
        )

        return timezone.now() >= end_time

    def expire_if_needed(self):
        if not self.is_expired():
            return False

        self.status = self.Status.SUBMITTED
        self.submitted_at = timezone.now()

        self.save(
            update_fields=[
                'status',
                'submitted_at',
                'updated_at',
            ],
        )

        return True

    def calculate_score(self):
        from apps.questions.answer import Answer

        answers = Answer.objects.filter(
            exam=self,
        )

        total_points = sum(
            answer.question.points
            for answer in answers
        )

        earned_points = sum(
            answer.points_earned
            for answer in answers
        )

        return {
            'total_points': total_points,
            'earned_points': earned_points,
            'answered_questions': answers.count(),
        }

    def __str__(self):
        return f'{self.user.username} - {self.exam_type}'


class ExamSection(models.Model):

    class SectionType(models.TextChoices):
        LISTENING = 'LISTENING', 'Listening'
        READING = 'READING', 'Reading'
        WRITING = 'WRITING', 'Writing'
        SPEAKING = 'SPEAKING', 'Speaking'

    class Status(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Not Started'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='sections',
    )

    section_type = models.CharField(
        max_length=20,
        choices=SectionType.choices,
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

    score = models.DecimalField(
        max_digits=4,
        decimal_places=1,
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
        ordering = ['id']

    def __str__(self):
        return f'{self.exam} - {self.section_type}'
