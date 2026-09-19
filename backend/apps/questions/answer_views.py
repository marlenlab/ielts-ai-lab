from django.db import IntegrityError

from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from .answer import Answer
from .answer_serializers import AnswerSerializer


class AnswerListCreateView(generics.ListCreateAPIView):
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Answer.objects.filter(
            exam__user=self.request.user,
        ).order_by(
            'question__order',
            'id',
        )

    def perform_create(self, serializer):
        exam = serializer.validated_data['exam']
        question = serializer.validated_data['question']

        if exam.user != self.request.user:
            raise PermissionDenied(
                'You do not have permission to answer this exam.'
            )

        if exam.status != exam.Status.IN_PROGRESS:
            raise PermissionDenied(
                'You can only answer an exam that is in progress.'
            )

        if exam.expire_if_needed():
            raise PermissionDenied(
                'The exam time has expired.'
            )

        section = question.section

        if section is None:
            raise PermissionDenied(
                'Question is not assigned to an exam section.'
            )

        if section.exam_id != exam.id:
            raise PermissionDenied(
                'Question does not belong to this exam.'
            )

        if section.status != section.Status.IN_PROGRESS:
            raise PermissionDenied(
                'You can only answer questions from the active section.'
            )

        active_sections = exam.sections.filter(
            status=section.Status.IN_PROGRESS,
        )

        if active_sections.count() != 1:
            raise PermissionDenied(
                'There must be exactly one active exam section.'
            )

        if active_sections.first().id != section.id:
            raise PermissionDenied(
                'You can only answer questions from the active section.'
            )

        submitted_answer = (
            serializer.validated_data['answer']
            .strip()
            .lower()
        )

        correct_answer = (
            question.correct_answer
            .strip()
            .lower()
        )

        correct = submitted_answer == correct_answer

        points_earned = (
            question.points
            if correct
            else 0
        )

        try:
            answer, created = Answer.objects.update_or_create(
                exam=exam,
                question=question,
                defaults={
                    'answer': serializer.validated_data['answer'],
                    'is_correct': correct,
                    'points_earned': points_earned,
                },
            )
        except IntegrityError:
            raise ValidationError(
                'Unable to save this answer.'
            )

        serializer.instance = answer
