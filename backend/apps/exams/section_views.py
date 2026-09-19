from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Exam, ExamSection


class ExamSectionStartView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExamSection.objects.filter(
            exam__user=self.request.user,
            status=ExamSection.Status.NOT_STARTED,
        )

    def post(self, request, *args, **kwargs):
        section = self.get_object()

        if section.exam.status != Exam.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The exam must be in progress.'
            )

        section.status = ExamSection.Status.IN_PROGRESS
        section.started_at = timezone.now()

        section.save(
            update_fields=[
                'status',
                'started_at',
                'updated_at',
            ],
        )

        return Response({
            'id': section.id,
            'exam_id': section.exam_id,
            'section_type': section.section_type,
            'status': section.status,
            'started_at': section.started_at,
        })


class ExamSectionSubmitView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExamSection.objects.filter(
            exam__user=self.request.user,
            status=ExamSection.Status.IN_PROGRESS,
        )

    def post(self, request, *args, **kwargs):
        section = self.get_object()

        if section.exam.status != Exam.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The exam must be in progress.'
            )

        section.status = ExamSection.Status.SUBMITTED
        section.submitted_at = timezone.now()

        section.save(
            update_fields=[
                'status',
                'submitted_at',
                'updated_at',
            ],
        )

        return Response({
            'id': section.id,
            'exam_id': section.exam_id,
            'section_type': section.section_type,
            'status': section.status,
            'submitted_at': section.submitted_at,
        })
