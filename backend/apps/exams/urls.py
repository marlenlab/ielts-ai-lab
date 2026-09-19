from django.urls import path

from .result_views import ExamResultView
from .section_views import (
    ExamSectionStartView,
    ExamSectionSubmitView,
)
from .timer_views import ExamTimerView
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
    path(
        '<int:pk>/timer/',
        ExamTimerView.as_view(),
        name='exam-timer',
    ),
    path(
        '<int:pk>/result/',
        ExamResultView.as_view(),
        name='exam-result',
    ),
    path(
        'sections/<int:pk>/start/',
        ExamSectionStartView.as_view(),
        name='exam-section-start',
    ),
    path(
        'sections/<int:pk>/submit/',
        ExamSectionSubmitView.as_view(),
        name='exam-section-submit',
    ),
]
