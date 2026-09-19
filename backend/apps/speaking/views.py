from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.exams.models import ExamSection

from .models import SpeakingSubmission, SpeakingTask
from .serializers import (
    SpeakingSubmissionSerializer,
    SpeakingTaskSerializer,
)


class SpeakingTaskListCreateView(generics.ListCreateAPIView):
    serializer_class = SpeakingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SpeakingTask.objects.all().order_by(
            'part',
            'id',
        )


class SpeakingTaskDetailView(generics.RetrieveAPIView):
    serializer_class = SpeakingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    queryset = SpeakingTask.objects.all()


class SpeakingSubmissionListCreateView(generics.ListCreateAPIView):
    serializer_class = SpeakingSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SpeakingSubmission.objects.filter(
            user=self.request.user,
        ).select_related(
            'section',
            'task',
        ).order_by(
            'task__part',
            'id',
        )

    def perform_create(self, serializer):
        section = serializer.validated_data['section']
        task = serializer.validated_data['task']

        self.validate_submission_context(
            section=section,
            task=task,
        )

        submission, _ = SpeakingSubmission.objects.update_or_create(
            user=self.request.user,
            section=section,
            task=task,
            defaults={
                'audio_file': serializer.validated_data.get(
                    'audio_file'
                ),
                'audio_url': serializer.validated_data.get(
                    'audio_url',
                    '',
                ),
                'transcript': serializer.validated_data.get(
                    'transcript',
                    '',
                ),
                'duration_seconds': serializer.validated_data.get(
                    'duration_seconds'
                ),
                'status': SpeakingSubmission.Status.DRAFT,
            },
        )

        serializer.instance = submission

    def validate_submission_context(self, section, task):
        if section.section_type != ExamSection.SectionType.SPEAKING:
            raise PermissionDenied(
                'Speaking submissions are only allowed for the Speaking section.'
            )

        if section.exam.user != self.request.user:
            raise PermissionDenied(
                'You do not have permission to use this exam section.'
            )

        if section.status != ExamSection.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The Speaking section must be in progress.'
            )

        exam = section.exam

        if exam.status != exam.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The exam must be in progress.'
            )

        if exam.expire_if_needed():
            raise PermissionDenied(
                'The exam time has expired.'
            )


class SpeakingSubmissionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = SpeakingSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SpeakingSubmission.objects.filter(
            user=self.request.user,
        ).select_related(
            'section',
            'task',
        )

    def perform_update(self, serializer):
        submission = self.get_object()

        if submission.status != SpeakingSubmission.Status.DRAFT:
            raise PermissionDenied(
                'Only draft submissions can be edited.'
            )

        section = submission.section
        exam = section.exam

        if section.status != ExamSection.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The Speaking section must be in progress.'
            )

        if exam.status != exam.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The exam must be in progress.'
            )

        if exam.expire_if_needed():
            raise PermissionDenied(
                'The exam time has expired.'
            )

        serializer.save()


class SpeakingSubmissionSubmitView(generics.GenericAPIView):
    serializer_class = SpeakingSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SpeakingSubmission.objects.filter(
            user=self.request.user,
        ).select_related(
            'section',
            'task',
        )

    def post(self, request, *args, **kwargs):
        submission = self.get_object()

        if submission.status != SpeakingSubmission.Status.DRAFT:
            raise PermissionDenied(
                'Only draft submissions can be submitted.'
            )

        section = submission.section
        exam = section.exam

        if section.status != ExamSection.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The Speaking section must be in progress.'
            )

        if exam.status != exam.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The exam must be in progress.'
            )

        if exam.expire_if_needed():
            raise PermissionDenied(
                'The exam time has expired.'
            )

        if not submission.audio_file and not submission.audio_url:
            raise PermissionDenied(
                'An audio recording is required before submission.'
            )

        submission.status = SpeakingSubmission.Status.SUBMITTED
        submission.submitted_at = timezone.now()

        submission.save(
            update_fields=[
                'status',
                'submitted_at',
                'updated_at',
            ],
        )

        return Response(
            self.get_serializer(submission).data
        )
