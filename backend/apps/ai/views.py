from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import AIAssessment
from .serializers import (
    AIAssessmentCompleteSerializer,
    AIAssessmentFailSerializer,
    AIAssessmentSerializer,
)
from .services import (
    complete_assessment,
    create_assessment,
    fail_assessment,
    start_assessment,
)


class AIAssessmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AIAssessmentSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return AIAssessment.objects.filter(
            user=self.request.user,
        )

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            status=AIAssessment.Status.PENDING,
        )


class AIAssessmentDetailView(
    generics.RetrieveAPIView,
):
    serializer_class = AIAssessmentSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return AIAssessment.objects.filter(
            user=self.request.user,
        )


class AIAssessmentStartView(
    generics.GenericAPIView,
):
    serializer_class = AIAssessmentSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return AIAssessment.objects.filter(
            user=self.request.user,
        )

    def post(self, request, pk):
        try:
            assessment = self.get_queryset().get(
                pk=pk,
            )
        except AIAssessment.DoesNotExist:
            return Response(
                {
                    'detail': 'Assessment not found.',
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if assessment.status not in {
            AIAssessment.Status.PENDING,
            AIAssessment.Status.FAILED,
        }:
            return Response(
                {
                    'detail': (
                        'Only pending or failed assessments '
                        'can be started.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        assessment = start_assessment(
            assessment,
        )

        return Response(
            AIAssessmentSerializer(
                assessment,
            ).data,
            status=status.HTTP_200_OK,
        )


class AIAssessmentCompleteView(
    generics.GenericAPIView,
):
    serializer_class = AIAssessmentCompleteSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return AIAssessment.objects.filter(
            user=self.request.user,
        )

    def post(self, request, pk):
        try:
            assessment = self.get_queryset().get(
                pk=pk,
            )
        except AIAssessment.DoesNotExist:
            return Response(
                {
                    'detail': 'Assessment not found.',
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if assessment.status != AIAssessment.Status.PROCESSING:
            return Response(
                {
                    'detail': (
                        'Only processing assessments '
                        'can be completed.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AIAssessmentCompleteSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        data = serializer.validated_data

        overall_score = data.get(
            'overall_score',
        )

        if overall_score is None:
            return Response(
                {
                    'overall_score': (
                        'This field is required.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        assessment = complete_assessment(
            assessment=assessment,
            overall_score=overall_score,
            task_achievement=data.get(
                'task_achievement',
            ),
            coherence_cohesion=data.get(
                'coherence_cohesion',
            ),
            lexical_resource=data.get(
                'lexical_resource',
            ),
            grammar_accuracy=data.get(
                'grammar_accuracy',
            ),
            feedback=data.get(
                'feedback',
                '',
            ),
            strengths=data.get(
                'strengths',
                [],
            ),
            weaknesses=data.get(
                'weaknesses',
                [],
            ),
            suggestions=data.get(
                'suggestions',
                [],
            ),
            raw_response=data.get(
                'raw_response',
                {},
            ),
            processing_time_ms=data.get(
                'processing_time_ms',
            ),
        )

        return Response(
            AIAssessmentSerializer(
                assessment,
            ).data,
            status=status.HTTP_200_OK,
        )


class AIAssessmentFailView(
    generics.GenericAPIView,
):
    serializer_class = AIAssessmentFailSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return AIAssessment.objects.filter(
            user=self.request.user,
        )

    def post(self, request, pk):
        try:
            assessment = self.get_queryset().get(
                pk=pk,
            )
        except AIAssessment.DoesNotExist:
            return Response(
                {
                    'detail': 'Assessment not found.',
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if assessment.status != AIAssessment.Status.PROCESSING:
            return Response(
                {
                    'detail': (
                        'Only processing assessments '
                        'can be failed.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AIAssessmentFailSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        assessment = fail_assessment(
            assessment=assessment,
            error_message=serializer.validated_data[
                'error_message'
            ],
        )

        return Response(
            AIAssessmentSerializer(
                assessment,
            ).data,
            status=status.HTTP_200_OK,
        )
