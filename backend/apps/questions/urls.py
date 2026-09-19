from django.urls import path

from .views import QuestionListCreateView


urlpatterns = [
    path(
        '',
        QuestionListCreateView.as_view(),
        name='question-list-create',
    ),
]
