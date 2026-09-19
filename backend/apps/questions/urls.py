from django.urls import path

from .answer_views import AnswerListCreateView
from .views import QuestionListCreateView


urlpatterns = [
    path(
        '',
        QuestionListCreateView.as_view(),
        name='question-list-create',
    ),
    path(
        'answers/',
        AnswerListCreateView.as_view(),
        name='answer-list-create',
    ),
]
