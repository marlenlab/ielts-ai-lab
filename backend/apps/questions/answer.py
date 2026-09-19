from django.db import models


class Answer(models.Model):
    exam = models.ForeignKey(
        'exams.Exam',
        on_delete=models.CASCADE,
        related_name='answers',
    )

    question = models.ForeignKey(
        'questions.Question',
        on_delete=models.CASCADE,
        related_name='answers',
    )

    answer = models.TextField(
        blank=True,
    )

    is_correct = models.BooleanField(
        null=True,
        blank=True,
    )

    points_earned = models.PositiveIntegerField(
        default=0,
    )

    answered_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['exam', 'question'],
                name='unique_answer_per_exam_question',
            ),
        ]

    def __str__(self):
        return f'{self.exam} - Question {self.question_id}'
