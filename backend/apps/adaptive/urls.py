from django.urls import path

from .views import (
    AdaptiveLearningSessionCreateView,
    AdaptiveProfileView,
    AdaptiveRecommendationCompleteView,
    AdaptiveRecommendationGenerateView,
    AdaptiveRecommendationListView,
)


urlpatterns = [
    path(
        'profile/',
        AdaptiveProfileView.as_view(),
        name='adaptive-profile',
    ),
    path(
        'recommendations/',
        AdaptiveRecommendationListView.as_view(),
        name='adaptive-recommendations',
    ),
    path(
        'recommendations/generate/',
        AdaptiveRecommendationGenerateView.as_view(),
        name='adaptive-recommendations-generate',
    ),
    path(
        'recommendations/<int:pk>/complete/',
        AdaptiveRecommendationCompleteView.as_view(),
        name='adaptive-recommendation-complete',
    ),
    path(
        'learning-session/',
        AdaptiveLearningSessionCreateView.as_view(),
        name='adaptive-learning-session',
    ),
]
