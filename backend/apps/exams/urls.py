from django.urls import path

from .views import (
    ExamListCreateView,
    ExamSectionListCreateView,
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
]
