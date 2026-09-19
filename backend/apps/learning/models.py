from django.conf import settings
from django.db import models


class LearningSession(models.Model):
    class SessionType(models.TextChoices):
        VOCABULARY = 'VOCABULARY', 'Vocabulary'
        GRAMMAR = 'GRAMMAR', 'Grammar'
        LISTENING = 'LISTENING', 'Listening'
        READING = 'READING', 'Reading'
        WRITING = 'WRITING', 'Writing'
        SPEAKING = 'SPEAKING', 'Speaking'
        MIXED = 'MIXED', 'Mixed'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_sessions',
    )
    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    target_minutes = models.PositiveIntegerField(default=30)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.session_type}'


class LearningActivity(models.Model):
    class ActivityType(models.TextChoices):
        VOCABULARY = 'VOCABULARY', 'Vocabulary'
        GRAMMAR = 'GRAMMAR', 'Grammar'
        LISTENING = 'LISTENING', 'Listening'
        READING = 'READING', 'Reading'
        WRITING = 'WRITING', 'Writing'
        SPEAKING = 'SPEAKING', 'Speaking'

    session = models.ForeignKey(
        LearningSession,
        on_delete=models.CASCADE,
        related_name='activities',
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ActivityType.choices,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    target_count = models.PositiveIntegerField(default=1)
    completed_count = models.PositiveIntegerField(default=0)

    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    points_earned = models.PositiveIntegerField(default=0)

    order = models.PositiveIntegerField()

    # Concrete adaptive content selected for this activity.
    # Example:
    # {
    #     "items": [
    #         {
    #             "id": 12,
    #             "word": "allocate",
    #             "definition": "...",
    #             "example_sentence": "..."
    #         }
    #     ]
    # }
    content = models.JSONField(
        default=dict,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'order'],
                name='unique_learning_activity_order_per_session',
            ),
        ]

    def is_completed(self):
        return self.completed_count >= self.target_count

    def __str__(self):
        return f'{self.session} - {self.title}'
