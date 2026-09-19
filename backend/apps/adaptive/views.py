from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import AdaptiveRecommendation
from .serializers import (
    AdaptiveLearningSessionSerializer,
    AdaptiveProfileSerializer,
    AdaptiveRecommendationSerializer,
)
from .services import (
    complete_recommendation,
    create_adaptive_learning_session,
    generate_recommendations,
    update_adaptive_profile,
)


class AdaptiveProfileView(generics.RetrieveAPIView):
    serializer_class = AdaptiveProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return update_adaptive_profile(
            self.request.user,
        )


class AdaptiveRecommendationListView(
    generics.ListAPIView,
):
    serializer_class = AdaptiveRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AdaptiveRecommendation.objects.filter(
            user=self.request.user,
        ).order_by(
            'is_completed',
            'score',
            '-created_at',
        )


class AdaptiveRecommendationGenerateView(
    generics.GenericAPIView,
):
    serializer_class = AdaptiveRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        recommendations = generate_recommendations(
            request.user,
        )

        serializer = self.get_serializer(
            recommendations,
            many=True,
        )

        return Response({
            'count': len(recommendations),
            'recommendations': serializer.data,
        })


class AdaptiveRecommendationCompleteView(
    generics.GenericAPIView,
):
    serializer_class = AdaptiveRecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AdaptiveRecommendation.objects.filter(
            user=self.request.user,
        )

    def post(self, request, *args, **kwargs):
        recommendation = self.get_object()

        recommendation = complete_recommendation(
            recommendation,
        )

        serializer = self.get_serializer(
            recommendation,
        )

        return Response(serializer.data)


class AdaptiveLearningSessionCreateView(
    generics.GenericAPIView,
):
    serializer_class = AdaptiveLearningSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        session = create_adaptive_learning_session(
            request.user,
        )

        if session is None:
            return Response(
                {
                    'detail': (
                        'Not enough learning data to '
                        'create an adaptive session.'
                    ),
                },
                status=400,
            )

        activities = session.activities.all()

        response_data = {
            'session_id': session.id,
            'session_type': session.session_type,
            'status': session.status,
            'target_minutes': session.target_minutes,
            'activities': [
                {
                    'id': activity.id,
                    'activity_type': activity.activity_type,
                    'title': activity.title,
                    'description': activity.description,
                    'target_count': activity.target_count,
                    'order': activity.order,
                    'content': activity.content,
                }
                for activity in activities
            ],
        }

        serializer = self.get_serializer(
            data=response_data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        return Response(
            serializer.validated_data,
            status=201,
        )
