from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.exams.models import ExamSection

from .models import WritingSubmission, WritingTask
from .serializers import (
    WritingSubmissionSerializer,
    WritingTaskSerializer,
)


class WritingTaskListCreateView(generics.ListCreateAPIView):
    serializer_class = WritingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WritingTask.objects.all().order_by(
            'task_type',
            'id',
        )


class WritingTaskDetailView(generics.RetrieveAPIView):
    serializer_class = WritingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WritingTask.objects.all()


class WritingSubmissionListCreateView(generics.ListCreateAPIView):
    serializer_class = WritingSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WritingSubmission.objects.filter(
            user=self.request.user,
        ).select_related(
            'section',
            'task',
        ).order_by(
            'task__task_type',
            'id',
        )

    def perform_create(self, serializer):
        section = serializer.validated_data['section']
        task = serializer.validated_data['task']

        self.validate_submission_context(
            section=section,
            task=task,
        )

        submission, _ = WritingSubmission.objects.update_or_create(
            user=self.request.user,
            section=section,
            task=task,
            defaults={
                'content': serializer.validated_data.get('content', ''),
                'status': WritingSubmission.Status.DRAFT,
            },
        )

        submission.update_word_count()
        submission.save(
            update_fields=[
                'word_count',
                'updated_at',
            ],
        )

        serializer.instance = submission

    def validate_submission_context(self, section, task):
        if section.section_type != ExamSection.SectionType.WRITING:
            raise PermissionDenied(
                'Writing submissions are only allowed for the Writing section.'
            )

        if section.exam.user != self.request.user:
            raise PermissionDenied(
                'You do not have permission to use this exam section.'
            )

        if section.status != ExamSection.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The Writing section must be in progress.'
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

        if task.task_type not in (
            WritingTask.TaskType.TASK_1,
            WritingTask.TaskType.TASK_2,
        ):
            raise ValidationError(
                'Invalid Writing task type.'
            )


class WritingSubmissionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = WritingSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WritingSubmission.objects.filter(
            user=self.request.user,
        ).select_related(
            'section',
            'task',
        )

    def perform_update(self, serializer):
        submission = self.get_object()

        if submission.status != WritingSubmission.Status.DRAFT:
            raise PermissionDenied(
                'Only draft submissions can be edited.'
            )

        section = submission.section
        exam = section.exam

        if section.status != ExamSection.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The Writing section must be in progress.'
            )

        if exam.status != exam.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The exam must be in progress.'
            )

        if exam.expire_if_needed():
            raise PermissionDenied(
                'The exam time has expired.'
            )

        content = serializer.validated_data.get(
            'content',
            submission.content,
        )

        submission.content = content
        submission.update_word_count()

        serializer.instance = submission

        submission.save(
            update_fields=[
                'content',
                'word_count',
                'updated_at',
            ],
        )


class WritingSubmissionSubmitView(generics.GenericAPIView):
    serializer_class = WritingSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WritingSubmission.objects.filter(
            user=self.request.user,
        ).select_related(
            'section',
            'task',
        )

    def post(self, request, *args, **kwargs):
        submission = self.get_object()

        if submission.status != WritingSubmission.Status.DRAFT:
            raise PermissionDenied(
                'Only draft submissions can be submitted.'
            )

        section = submission.section
        exam = section.exam

        if section.status != ExamSection.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The Writing section must be in progress.'
            )

        if exam.status != exam.Status.IN_PROGRESS:
            raise PermissionDenied(
                'The exam must be in progress.'
            )

        if exam.expire_if_needed():
            raise PermissionDenied(
                'The exam time has expired.'
            )

        submission.update_word_count()

        if submission.word_count < submission.task.minimum_words:
            raise ValidationError({
                'content': (
                    f'Your essay must contain at least '
                    f'{submission.task.minimum_words} words. '
                    f'Current word count: {submission.word_count}.'
                )
            })

        submission.status = WritingSubmission.Status.SUBMITTED
        submission.submitted_at = timezone.now()

        submission.save(
            update_fields=[
                'word_count',
                'status',
                'submitted_at',
                'updated_at',
            ],
        )

        return Response(
            self.get_serializer(submission).data
        )
