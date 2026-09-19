from decimal import Decimal

from django.conf import settings
from django.db import models


class GrammarTopic(models.Model):
    class Level(models.TextChoices):
        A1 = 'A1', 'A1'
        A2 = 'A2', 'A2'
        B1 = 'B1', 'B1'
        B2 = 'B2', 'B2'
        C1 = 'C1', 'C1'
        C2 = 'C2', 'C2'

    title = models.CharField(max_length=255)
    description = models.TextField()
    level = models.CharField(max_length=2, choices=Level.choices)
    explanation = models.TextField()
    examples = models.JSONField(default=list, blank=True)
    common_mistakes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['level', 'title']

    def __str__(self):
        return f'{self.level} - {self.title}'


class GrammarExercise(models.Model):
    class ExerciseType(models.TextChoices):
        MULTIPLE_CHOICE = 'MULTIPLE_CHOICE', 'Multiple Choice'
        FILL_GAP = 'FILL_GAP', 'Fill in the Gap'
        ERROR_CORRECTION = 'ERROR_CORRECTION', 'Error Correction'

    topic = models.ForeignKey(
        GrammarTopic,
        on_delete=models.CASCADE,
        related_name='exercises',
    )
    exercise_type = models.CharField(
        max_length=30,
        choices=ExerciseType.choices,
    )
    question = models.TextField()
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['topic', 'order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['topic', 'order'],
                name='unique_grammar_exercise_order_per_topic',
            ),
        ]

    def __str__(self):
        return f'{self.topic.title} - Exercise {self.id}'


class GrammarProgress(models.Model):
    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        LEARNING = 'LEARNING', 'Learning'
        MASTERED = 'MASTERED', 'Mastered'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grammar_progress',
    )
    topic = models.ForeignKey(
        GrammarTopic,
        on_delete=models.CASCADE,
        related_name='progress',
    )
    correct_answers = models.PositiveIntegerField(default=0)
    incorrect_answers = models.PositiveIntegerField(default=0)
    last_answer_correct = models.BooleanField(null=True, blank=True)
    mastery_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    next_review_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'topic'],
                name='unique_grammar_progress_per_user_topic',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.topic.title}'
