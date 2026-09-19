from django.urls import path

from .views import (
    WritingSubmissionDetailView,
    WritingSubmissionListCreateView,
    WritingSubmissionSubmitView,
    WritingTaskDetailView,
    WritingTaskListCreateView,
)


urlpatterns = [
    path(
        'tasks/',
        WritingTaskListCreateView.as_view(),
        name='writing-task-list-create',
    ),
    path(
        'tasks/<int:pk>/',
        WritingTaskDetailView.as_view(),
        name='writing-task-detail',
    ),
    path(
        'submissions/',
        WritingSubmissionListCreateView.as_view(),
        name='writing-submission-list-create',
    ),
    path(
        'submissions/<int:pk>/',
        WritingSubmissionDetailView.as_view(),
        name='writing-submission-detail',
    ),
    path(
        'submissions/<int:pk>/submit/',
        WritingSubmissionSubmitView.as_view(),
        name='writing-submission-submit',
    ),
]
