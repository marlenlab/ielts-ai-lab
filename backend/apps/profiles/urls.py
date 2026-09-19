from django.urls import path

from .views import LearnerProfileView


urlpatterns = [
    path('me/', LearnerProfileView.as_view(), name='profile-me'),
]
