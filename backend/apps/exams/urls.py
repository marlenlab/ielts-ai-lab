from django.urls import path

from .views import ExamListCreateView


urlpatterns = [
    path('', ExamListCreateView.as_view(), name='exam-list-create'),
]
