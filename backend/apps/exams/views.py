from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import Exam, ExamSection
from .serializers import ExamSerializer, ExamSectionSerializer


class ExamListCreateView(generics.ListCreateAPIView):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Exam.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExamSectionListCreateView(generics.ListCreateAPIView):
    serializer_class = ExamSectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExamSection.objects.filter(
            exam__user=self.request.user
        ).order_by('id')

    def perform_create(self, serializer):
        exam_id = self.kwargs['exam_id']

        exam = get_object_or_404(
            Exam,
            id=exam_id,
            user=self.request.user,
        )

        serializer.save(exam=exam)


class ExamStartView(generics.GenericAPIView):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Exam.objects.filter(
            user=self.request.user,
            status=Exam.Status.NOT_STARTED,
        )

    def post(self, request, *args, **kwargs):
        exam = self.get_object()

        from django.utils import timezone

        exam.status = Exam.Status.IN_PROGRESS
        exam.started_at = timezone.now()
        exam.save(
            update_fields=[
                'status',
                'started_at',
                'updated_at',
            ]
        )

        serializer = self.get_serializer(exam)

        return Response(serializer.data)

class ExamSubmitView(generics.GenericAPIView):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Exam.objects.filter(
            user=self.request.user,
            status=Exam.Status.IN_PROGRESS,
        )

    def post(self, request, *args, **kwargs):
        exam = self.get_object()

        from django.utils import timezone

        if exam.is_expired():
            exam.status = Exam.Status.SUBMITTED
            exam.submitted_at = timezone.now()
            exam.save(
                update_fields=[
                    'status',
                    'submitted_at',
                    'updated_at',
                ],
            )

            serializer = self.get_serializer(exam)

            return Response(
                serializer.data,
                status=200,
            )

        exam.status = Exam.Status.SUBMITTED
        exam.submitted_at = timezone.now()

        exam.save(
            update_fields=[
                'status',
                'submitted_at',
                'updated_at',
            ],
        )

        serializer = self.get_serializer(exam)

        return Response(serializer.data)
