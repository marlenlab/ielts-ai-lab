from django.conf import settings
from django.db import models


class VocabularyWord(models.Model):

    class Difficulty(models.TextChoices):
        A1 = 'A1', 'A1'
        A2 = 'A2', 'A2'
        B1 = 'B1', 'B1'
        B2 = 'B2', 'B2'
        C1 = 'C1', 'C1'
        C2 = 'C2', 'C2'

    word = models.CharField(
        max_length=100,
    )

    definition = models.TextField()

    example_sentence = models.TextField(
        blank=True,
    )

    translation = models.CharField(
        max_length=255,
        blank=True,
    )

    difficulty = models.CharField(
        max_length=2,
        choices=Difficulty.choices,
    )

    topic = models.CharField(
        max_length=100,
        blank=True,
    )

    part_of_speech = models.CharField(
        max_length=50,
        blank=True,
    )

    pronunciation = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ['difficulty', 'word']
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'difficulty'],
                name='unique_vocabulary_word_difficulty',
            ),
        ]

    def __str__(self):
        return self.word


class VocabularyProgress(models.Model):

    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        LEARNING = 'LEARNING', 'Learning'
        MASTERED = 'MASTERED', 'Mastered'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vocabulary_progress',
    )

    word = models.ForeignKey(
        VocabularyWord,
        on_delete=models.CASCADE,
        related_name='progress',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    correct_answers = models.PositiveIntegerField(
        default=0,
    )

    incorrect_answers = models.PositiveIntegerField(
        default=0,
    )

    last_answer_correct = models.BooleanField(
        null=True,
        blank=True,
    )

    mastery_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    last_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    next_review_at = models.DateTimeField(
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
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'word'],
                name='unique_vocabulary_progress_per_user',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.word.word}'
