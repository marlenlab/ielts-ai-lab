from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Question
from .serializers import (
    QuestionSerializer,
    StudentQuestionSerializer,
)


class QuestionListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Question.objects.filter(
            section__exam__user=self.request.user,
        ).order_by(
            'section__id',
            'order',
            'id',
        )

        if self.request.method == 'GET':
            active_section_ids = queryset.filter(
                section__status='IN_PROGRESS',
            ).values_list(
                'section_id',
                flat=True,
            )

            return queryset.filter(
                section_id__in=active_section_ids,
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StudentQuestionSerializer

        return QuestionSerializer

    def perform_create(self, serializer):
        section = serializer.validated_data['section']

        if section.exam.user != self.request.user:
            raise PermissionDenied(
                'You do not have permission to use this exam section.'
            )

        serializer.save()
