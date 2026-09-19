from django.urls import path

from .views import (
    SpeakingSubmissionDetailView,
    SpeakingSubmissionListCreateView,
    SpeakingSubmissionSubmitView,
    SpeakingTaskDetailView,
    SpeakingTaskListCreateView,
)


urlpatterns = [
    path(
        'tasks/',
        SpeakingTaskListCreateView.as_view(),
        name='speaking-task-list-create',
    ),
    path(
        'tasks/<int:pk>/',
        SpeakingTaskDetailView.as_view(),
        name='speaking-task-detail',
    ),
    path(
        'submissions/',
        SpeakingSubmissionListCreateView.as_view(),
        name='speaking-submission-list-create',
    ),
    path(
        'submissions/<int:pk>/',
        SpeakingSubmissionDetailView.as_view(),
        name='speaking-submission-detail',
    ),
    path(
        'submissions/<int:pk>/submit/',
        SpeakingSubmissionSubmitView.as_view(),
        name='speaking-submission-submit',
    ),
]
