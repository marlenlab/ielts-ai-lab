from django.db import models

from apps.exams.models import ExamSection


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'MULTIPLE_CHOICE', 'Multiple Choice'
        TRUE_FALSE_NOT_GIVEN = (
            'TRUE_FALSE_NOT_GIVEN',
            'True / False / Not Given',
        )
        YES_NO_NOT_GIVEN = (
            'YES_NO_NOT_GIVEN',
            'Yes / No / Not Given',
        )
        MATCHING = 'MATCHING', 'Matching'
        FILL_GAP = 'FILL_GAP', 'Fill in the Gap'

    class Skill(models.TextChoices):
        LISTENING = 'LISTENING', 'Listening'
        READING = 'READING', 'Reading'

    section = models.ForeignKey(
        ExamSection,
        on_delete=models.CASCADE,
        related_name='questions',
        null=True,
        blank=True,
    )

    skill = models.CharField(
        max_length=20,
        choices=Skill.choices,
    )

    question_type = models.CharField(
        max_length=30,
        choices=QuestionType.choices,
    )

    text = models.TextField()

    options = models.JSONField(
        default=list,
        blank=True,
    )

    correct_answer = models.TextField()

    points = models.PositiveIntegerField(
        default=1,
    )

    order = models.PositiveIntegerField(
        default=1,
    )

    explanation = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ['section', 'order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['section', 'order'],
                name='unique_question_order_per_section',
            ),
        ]

    def __str__(self):
        return (
            f'{self.skill} - '
            f'{self.question_type} - '
            f'{self.id}'
        )

from .answer import Answer
