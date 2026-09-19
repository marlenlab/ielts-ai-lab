from rest_framework import generics, permissions

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
