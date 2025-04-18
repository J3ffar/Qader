# qader_backend/apps/study/api/urls/traditional.py
from django.urls import path
from ..views import (
    TraditionalLearningQuestionListView,
    TraditionalLearningAnswerView,
)


urlpatterns = [
    path(
        "questions/",
        TraditionalLearningQuestionListView.as_view(),
        name="traditional-questions-list",
    ),
    path(
        "answer/",
        TraditionalLearningAnswerView.as_view(),
        name="traditional-answer-submit",
    ),
]
