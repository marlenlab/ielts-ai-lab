from django.urls import path

from .views import AnalyticsDashboardView


urlpatterns = [
    path(
        'dashboard/',
        AnalyticsDashboardView.as_view(),
        name='analytics-dashboard',
    ),
]
