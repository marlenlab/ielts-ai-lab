from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import GrammarExercise, GrammarProgress, GrammarTopic
from .serializers import (
    GrammarAnswerSerializer,
    GrammarExerciseSerializer,
    GrammarProgressSerializer,
    GrammarTopicSerializer,
    StudentGrammarExerciseSerializer,
)
from .services import register_answer


class GrammarTopicListCreateView(generics.ListCreateAPIView):
    serializer_class = GrammarTopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = GrammarTopic.objects.all()

        level = self.request.query_params.get('level')

        if level:
            queryset = queryset.filter(level=level)

        return queryset.order_by('level', 'title')


class GrammarTopicDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GrammarTopicSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = GrammarTopic.objects.all()


class GrammarExerciseListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = GrammarExercise.objects.select_related(
            'topic',
        ).order_by(
            'topic__level',
            'topic__title',
            'order',
            'id',
        )

        topic_id = self.request.query_params.get('topic')

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StudentGrammarExerciseSerializer

        return GrammarExerciseSerializer


class GrammarExerciseDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    queryset = GrammarExercise.objects.select_related('topic')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StudentGrammarExerciseSerializer

        return GrammarExerciseSerializer


class GrammarProgressListView(generics.ListAPIView):
    serializer_class = GrammarProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GrammarProgress.objects.filter(
            user=self.request.user,
        ).select_related(
            'topic',
        ).order_by('-updated_at')


class GrammarProgressDetailView(generics.RetrieveAPIView):
    serializer_class = GrammarProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GrammarProgress.objects.filter(
            user=self.request.user,
        ).select_related(
            'topic',
        )


class GrammarAnswerView(generics.GenericAPIView):
    serializer_class = GrammarAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exercise = serializer.validated_data['exercise']
        answer = serializer.validated_data['answer']

        progress, correct = register_answer(
            user=request.user,
            exercise=exercise,
            answer=answer,
        )

        return Response({
            'correct': correct,
            'correct_answer': exercise.correct_answer,
            'explanation': exercise.explanation,
            'progress': GrammarProgressSerializer(progress).data,
        })


class GrammarDueTopicsView(generics.ListAPIView):
    serializer_class = GrammarProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        now = timezone.now()

        return GrammarProgress.objects.filter(
            user=self.request.user,
            next_review_at__lte=now,
        ).select_related(
            'topic',
        ).order_by('next_review_at')
