from django.urls import path

from .views import (
    AIAssessmentCompleteView,
    AIAssessmentDetailView,
    AIAssessmentFailView,
    AIAssessmentListCreateView,
    AIAssessmentStartView,
)

urlpatterns = [
    path(
        'assessments/',
        AIAssessmentListCreateView.as_view(),
        name='ai-assessments',
    ),
    path(
        'assessments/<int:pk>/',
        AIAssessmentDetailView.as_view(),
        name='ai-assessment-detail',
    ),
    path(
        'assessments/<int:pk>/start/',
        AIAssessmentStartView.as_view(),
        name='ai-assessment-start',
    ),
    path(
        'assessments/<int:pk>/complete/',
        AIAssessmentCompleteView.as_view(),
        name='ai-assessment-complete',
    ),
    path(
        'assessments/<int:pk>/fail/',
        AIAssessmentFailView.as_view(),
        name='ai-assessment-fail',
    ),
]
