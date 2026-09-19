from django.urls import path

from .views import (
    VocabularyAnswerView,
    VocabularyDueWordsView,
    VocabularyProgressDetailView,
    VocabularyProgressListView,
    VocabularyWordDetailView,
    VocabularyWordListCreateView,
)


urlpatterns = [
    path(
        'words/',
        VocabularyWordListCreateView.as_view(),
        name='vocabulary-word-list-create',
    ),
    path(
        'words/<int:pk>/',
        VocabularyWordDetailView.as_view(),
        name='vocabulary-word-detail',
    ),
    path(
        'progress/',
        VocabularyProgressListView.as_view(),
        name='vocabulary-progress-list',
    ),
    path(
        'progress/<int:pk>/',
        VocabularyProgressDetailView.as_view(),
        name='vocabulary-progress-detail',
    ),
    path(
        'answer/',
        VocabularyAnswerView.as_view(),
        name='vocabulary-answer',
    ),
    path(
        'due/',
        VocabularyDueWordsView.as_view(),
        name='vocabulary-due',
    ),
]
