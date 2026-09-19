from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status

from .models import AdaptiveRecommendation
from .serializers import (
    AdaptiveActivityAnswerResponseSerializer,
    AdaptiveActivityAnswerSerializer,
    AdaptiveLearningSessionSerializer,
    AdaptiveProfileSerializer,
    AdaptiveRecommendationSerializer,
)
from .services import (
    complete_recommendation,
    create_adaptive_learning_session,
    generate_recommendations,
    submit_adaptive_activity_answer,
    update_adaptive_profile,
)


class AdaptiveProfileView(
    generics.RetrieveAPIView,
):
    serializer_class = AdaptiveProfileSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_object(self):
        return update_adaptive_profile(
            self.request.user,
        )


class AdaptiveRecommendationListView(
    generics.ListAPIView,
):
    serializer_class = AdaptiveRecommendationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return (
            AdaptiveRecommendation.objects
            .filter(
                user=self.request.user,
            )
            .order_by(
                'is_completed',
                'score',
                '-created_at',
            )
        )


class AdaptiveRecommendationGenerateView(
    generics.GenericAPIView,
):
    serializer_class = AdaptiveRecommendationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        recommendations = generate_recommendations(
            request.user,
        )

        serializer = self.get_serializer(
            recommendations,
            many=True,
        )

        return Response(
            {
                'count': len(recommendations),
                'recommendations': serializer.data,
            },
        )


class AdaptiveRecommendationCompleteView(
    generics.GenericAPIView,
):
    serializer_class = AdaptiveRecommendationSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return AdaptiveRecommendation.objects.filter(
            user=self.request.user,
        )

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        recommendation = self.get_object()

        recommendation = complete_recommendation(
            recommendation,
        )

        serializer = self.get_serializer(
            recommendation,
        )

        return Response(
            serializer.data,
        )


class AdaptiveLearningSessionCreateView(
    generics.GenericAPIView,
):
    serializer_class = AdaptiveLearningSessionSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(
        self,
        request,
        *args,
        **kwargs,
    ):
        session = create_adaptive_learning_session(
            request.user,
        )

        if session is None:
            return Response(
                {
                    'detail': (
                        'Not enough learning data '
                        'to create an adaptive session.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
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
                    'activity_type': (
                        activity.activity_type
                    ),
                    'title': activity.title,
                    'description': activity.description,
                    'target_count': (
                        activity.target_count
                    ),
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
            status=status.HTTP_201_CREATED,
        )


class AdaptiveActivityAnswerView(
    generics.GenericAPIView,
):
    serializer_class = (
        AdaptiveActivityAnswerSerializer
    )
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(
        self,
        request,
        pk,
        *args,
        **kwargs,
    ):
        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        item_id = serializer.validated_data[
            'item_id'
        ]

        answer = serializer.validated_data[
            'answer'
        ]

        try:
            result = submit_adaptive_activity_answer(
                user=request.user,
                activity_id=pk,
                item_id=item_id,
                answer=answer,
            )

        except ValueError as exc:
            return Response(
                {
                    'detail': str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        activity = result['activity']
        profile = result['profile']

        response_data = {
            'activity_id': activity.id,
            'item_id': item_id,
            'correct': result['correct'],
            'completed_count': (
                activity.completed_count
            ),
            'target_count': (
                activity.target_count
            ),
            'correct_count': (
                activity.correct_count
            ),
            'incorrect_count': (
                activity.incorrect_count
            ),
            'points_earned': (
                activity.points_earned
            ),
            'activity_completed': (
                activity.is_completed()
            ),
            'weakest_skill': (
                profile.weakest_skill
            ),
            'strongest_skill': (
                profile.strongest_skill
            ),
            'vocabulary_score': (
                profile.vocabulary_score
            ),
            'grammar_score': (
                profile.grammar_score
            ),
        }

        response_serializer = (
            AdaptiveActivityAnswerResponseSerializer(
                data=response_data,
            )
        )

        response_serializer.is_valid(
            raise_exception=True,
        )

        return Response(
            response_serializer.validated_data,
            status=status.HTTP_200_OK,
        )
