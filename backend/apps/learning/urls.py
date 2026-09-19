from django.urls import path

from .views import (
    LearningActivityCompleteView,
    LearningActivityDetailView,
    LearningActivityListCreateView,
    LearningSessionCancelView,
    LearningSessionDetailView,
    LearningSessionListCreateView,
    LearningSessionProgressView,
)


urlpatterns = [
    path(
        'sessions/',
        LearningSessionListCreateView.as_view(),
        name='learning-session-list-create',
    ),
    path(
        'sessions/<int:pk>/',
        LearningSessionDetailView.as_view(),
        name='learning-session-detail',
    ),
    path(
        'sessions/<int:pk>/progress/',
        LearningSessionProgressView.as_view(),
        name='learning-session-progress',
    ),
    path(
        'sessions/<int:pk>/cancel/',
        LearningSessionCancelView.as_view(),
        name='learning-session-cancel',
    ),
    path(
        'sessions/<int:session_id>/activities/',
        LearningActivityListCreateView.as_view(),
        name='learning-activity-list-create',
    ),
    path(
        'activities/<int:pk>/',
        LearningActivityDetailView.as_view(),
        name='learning-activity-detail',
    ),
    path(
        'activities/<int:pk>/complete/',
        LearningActivityCompleteView.as_view(),
        name='learning-activity-complete',
    ),
]
