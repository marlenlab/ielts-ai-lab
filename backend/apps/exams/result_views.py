from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import Exam


class ExamResultView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Exam.objects.filter(
            user=self.request.user,
        )

    def retrieve(self, request, *args, **kwargs):
        exam = self.get_object()

        result = exam.calculate_score()

        return Response({
            'exam_id': exam.id,
            'exam_type': exam.exam_type,
            'status': exam.status,
            'result': result,
        })
