from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import LearningActivity, LearningSession
from .serializers import (
    LearningActivitySerializer,
    LearningSessionSerializer,
)
from .services import (
    calculate_session_progress,
    cancel_session,
    complete_activity,
    complete_session,
)


class LearningSessionListCreateView(generics.ListCreateAPIView):
    serializer_class = LearningSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LearningSession.objects.filter(
            user=self.request.user,
        ).prefetch_related(
            'activities',
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
        )


class LearningSessionDetailView(generics.RetrieveAPIView):
    serializer_class = LearningSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LearningSession.objects.filter(
            user=self.request.user,
        ).prefetch_related(
            'activities',
        )


class LearningSessionProgressView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LearningSession.objects.filter(
            user=self.request.user,
        )

    def retrieve(self, request, *args, **kwargs):
        session = self.get_object()

        return Response({
            'session_id': session.id,
            'session_type': session.session_type,
            'status': session.status,
            'progress': calculate_session_progress(session),
        })


class LearningActivityListCreateView(generics.ListCreateAPIView):
    serializer_class = LearningActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LearningActivity.objects.filter(
            session__user=self.request.user,
        ).select_related(
            'session',
        ).order_by(
            'session_id',
            'order',
            'id',
        )

    def perform_create(self, serializer):
        session_id = self.kwargs['session_id']

        session = get_object_or_404(
            LearningSession,
            id=session_id,
            user=self.request.user,
        )

        if session.status != LearningSession.Status.ACTIVE:
            raise PermissionDenied(
                'Activities can only be added to an active session.',
            )

        if session.activities.filter(
            order=serializer.validated_data['order'],
        ).exists():
            raise PermissionDenied(
                'An activity with this order already exists.',
            )

        serializer.save(
            session=session,
        )


class LearningActivityDetailView(generics.RetrieveAPIView):
    serializer_class = LearningActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LearningActivity.objects.filter(
            session__user=self.request.user,
        ).select_related(
            'session',
        )


class LearningActivityCompleteView(generics.GenericAPIView):
    serializer_class = LearningActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LearningActivity.objects.filter(
            session__user=self.request.user,
        ).select_related(
            'session',
        )

    def post(self, request, *args, **kwargs):
        activity = self.get_object()

        completed_count = request.data.get(
            'completed_count',
            1,
        )
        correct_count = request.data.get(
            'correct_count',
            0,
        )
        incorrect_count = request.data.get(
            'incorrect_count',
            0,
        )
        points_earned = request.data.get(
            'points_earned',
            0,
        )

        try:
            completed_count = int(completed_count)
            correct_count = int(correct_count)
            incorrect_count = int(incorrect_count)
            points_earned = int(points_earned)
        except (TypeError, ValueError):
            raise PermissionDenied(
                'Activity progress values must be integers.',
            )

        if min(
            completed_count,
            correct_count,
            incorrect_count,
            points_earned,
        ) < 0:
            raise PermissionDenied(
                'Activity progress values cannot be negative.',
            )

        activity = complete_activity(
            activity=activity,
            completed_count=completed_count,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            points_earned=points_earned,
        )

        session_completed = complete_session(
            activity.session,
        )

        return Response({
            'activity': LearningActivitySerializer(
                activity,
            ).data,
            'session_completed': session_completed,
            'session_status': activity.session.status,
        })


class LearningSessionCancelView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LearningSession.objects.filter(
            user=self.request.user,
        )

    def post(self, request, *args, **kwargs):
        session = self.get_object()

        cancelled = cancel_session(session)

        if not cancelled:
            raise PermissionDenied(
                'Only active sessions can be cancelled.',
            )

        return Response(
            LearningSessionSerializer(session).data,
        )
