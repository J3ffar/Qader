from django.urls import path
from .views import (
    LevelAssessmentStartView,
    LevelAssessmentSubmitView,
    TraditionalLearningAnswerView,
    TraditionalLearningQuestionListView,
    # Import other views as they are created
)

app_name = "study"

urlpatterns = [
    # --- Level Assessment ---
    path(
        "level-assessment/start/",
        LevelAssessmentStartView.as_view(),
        name="level-assessment-start",
    ),
    path(
        "level-assessment/<int:attempt_id>/submit/",
        LevelAssessmentSubmitView.as_view(),
        name="level-assessment-submit",
    ),
    # --- Traditional Learning ---
    path(
        "traditional/questions/",
        TraditionalLearningQuestionListView.as_view(),
        name="traditional-questions-list",
    ),
    path(
        "traditional/answer/",
        TraditionalLearningAnswerView.as_view(),
        name="traditional-answer-submit",
    ),
    # Add other study-related endpoints here later (tests, etc.)
]
