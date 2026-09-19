from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .answer import Answer
from .answer_serializers import AnswerSerializer


class AnswerListCreateView(generics.ListCreateAPIView):
    serializer_class = AnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Answer.objects.filter(
            exam__user=self.request.user,
        ).order_by('question__order', 'id')

    def perform_create(self, serializer):
        exam = serializer.validated_data['exam']
        question = serializer.validated_data['question']

        if exam.user != self.request.user:
            raise PermissionDenied(
                'You do not have permission to answer this exam.'
            )

        if question.section.exam_id != exam.id:
            raise PermissionDenied(
                'Question does not belong to this exam.'
            )

        correct = (
            serializer.validated_data['answer'].strip().lower()
            == question.correct_answer.strip().lower()
        )

        points_earned = question.points if correct else 0

        serializer.save(
            is_correct=correct,
            points_earned=points_earned,
        )
