from datetime import timedelta

from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import Exam


class ExamTimerView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Exam.objects.filter(
            user=self.request.user,
        )

    def retrieve(self, request, *args, **kwargs):
        exam = self.get_object()

        if exam.expire_if_needed():
            return Response({
                'exam_id': exam.id,
                'status': exam.status,
                'remaining_seconds': 0,
                'expired': True,
            })

        if exam.status != Exam.Status.IN_PROGRESS:
            return Response({
                'exam_id': exam.id,
                'status': exam.status,
                'remaining_seconds': 0,
                'expired': exam.status == Exam.Status.SUBMITTED,
            })

        if not exam.started_at:
            return Response({
                'exam_id': exam.id,
                'status': exam.status,
                'remaining_seconds': 0,
                'expired': True,
            })

        now = timezone.now()

        end_time = (
            exam.started_at
            + timedelta(minutes=exam.duration_minutes)
        )

        remaining_seconds = max(
            0,
            int((end_time - now).total_seconds()),
        )

        return Response({
            'exam_id': exam.id,
            'status': exam.status,
            'duration_minutes': exam.duration_minutes,
            'remaining_seconds': remaining_seconds,
            'expired': remaining_seconds == 0,
            'started_at': exam.started_at,
            'end_time': end_time,
        })
