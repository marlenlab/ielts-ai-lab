from django.urls import path

from .views import (
    ExamListCreateView,
    ExamSectionListCreateView,
    ExamStartView,
    ExamSubmitView,
)


urlpatterns = [
    path(
        '',
        ExamListCreateView.as_view(),
        name='exam-list-create',
    ),
    path(
        '<int:exam_id>/sections/',
        ExamSectionListCreateView.as_view(),
        name='exam-section-list-create',
    ),
    path(
        '<int:pk>/start/',
        ExamStartView.as_view(),
        name='exam-start',
    ),
    path(
        '<int:pk>/submit/',
        ExamSubmitView.as_view(),
        name='exam-submit',
    ),
]
