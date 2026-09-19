from django.urls import path

from .views import (
    GrammarAnswerView,
    GrammarDueTopicsView,
    GrammarExerciseDetailView,
    GrammarExerciseListCreateView,
    GrammarProgressDetailView,
    GrammarProgressListView,
    GrammarTopicDetailView,
    GrammarTopicListCreateView,
)


urlpatterns = [
    path(
        'topics/',
        GrammarTopicListCreateView.as_view(),
        name='grammar-topic-list-create',
    ),
    path(
        'topics/<int:pk>/',
        GrammarTopicDetailView.as_view(),
        name='grammar-topic-detail',
    ),
    path(
        'exercises/',
        GrammarExerciseListCreateView.as_view(),
        name='grammar-exercise-list-create',
    ),
    path(
        'exercises/<int:pk>/',
        GrammarExerciseDetailView.as_view(),
        name='grammar-exercise-detail',
    ),
    path(
        'progress/',
        GrammarProgressListView.as_view(),
        name='grammar-progress-list',
    ),
    path(
        'progress/<int:pk>/',
        GrammarProgressDetailView.as_view(),
        name='grammar-progress-detail',
    ),
    path(
        'answer/',
        GrammarAnswerView.as_view(),
        name='grammar-answer',
    ),
    path(
        'due/',
        GrammarDueTopicsView.as_view(),
        name='grammar-due-topics',
    ),
]
