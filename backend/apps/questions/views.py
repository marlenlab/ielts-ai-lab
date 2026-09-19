from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Question
from .serializers import QuestionSerializer


class QuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Question.objects.all().order_by(
            'skill',
            'order',
            'id',
        )

    def perform_create(self, serializer):
        section = serializer.validated_data['section']

        if section.exam.user != self.request.user:
            raise PermissionDenied(
                'You do not have permission to use this exam section.'
            )

        serializer.save()
