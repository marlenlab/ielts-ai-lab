from django.utils import timezone

from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import VocabularyProgress, VocabularyWord
from .serializers import (
    VocabularyAnswerSerializer,
    VocabularyProgressSerializer,
    VocabularyWordSerializer,
)
from .services import register_answer


class VocabularyWordListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = VocabularyWordSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        queryset = VocabularyWord.objects.all()

        difficulty = self.request.query_params.get(
            'difficulty'
        )

        topic = self.request.query_params.get(
            'topic'
        )

        if difficulty:
            queryset = queryset.filter(
                difficulty=difficulty,
            )

        if topic:
            queryset = queryset.filter(
                topic__iexact=topic,
            )

        return queryset.order_by(
            'difficulty',
            'word',
        )


class VocabularyWordDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = VocabularyWordSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    queryset = VocabularyWord.objects.all()


class VocabularyProgressListView(
    generics.ListAPIView
):
    serializer_class = VocabularyProgressSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return VocabularyProgress.objects.filter(
            user=self.request.user,
        ).select_related(
            'word',
        ).order_by(
            '-updated_at',
        )


class VocabularyProgressDetailView(
    generics.RetrieveAPIView
):
    serializer_class = VocabularyProgressSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        return VocabularyProgress.objects.filter(
            user=self.request.user,
        ).select_related(
            'word',
        )


class VocabularyAnswerView(
    generics.GenericAPIView
):
    serializer_class = VocabularyAnswerSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        word = serializer.validated_data['word']
        correct = serializer.validated_data['correct']

        progress = register_answer(
            user=request.user,
            word=word,
            correct=correct,
        )

        return Response(
            VocabularyProgressSerializer(
                progress,
            ).data
        )


class VocabularyDueWordsView(
    generics.ListAPIView
):
    serializer_class = VocabularyProgressSerializer
    permission_classes = [
        permissions.IsAuthenticated,
    ]

    def get_queryset(self):
        now = timezone.now()

        return VocabularyProgress.objects.filter(
            user=self.request.user,
            next_review_at__lte=now,
        ).select_related(
            'word',
        ).order_by(
            'next_review_at',
        )
