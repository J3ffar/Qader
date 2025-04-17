from django.urls import path
from .views import (
    LevelAssessmentStartView,
    LevelAssessmentSubmitView,
    TraditionalLearningAnswerView,
    TraditionalLearningQuestionListView,
    UserTestAttemptListView,
    StartTestAttemptView,
    UserTestAttemptDetailView,
    SubmitTestAttemptView,
    ReviewTestAttemptView,
    RetakeSimilarTestAttemptView,
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
    # --- General Tests ---
    path("tests/", UserTestAttemptListView.as_view(), name="test-attempt-list"),
    path("tests/start/", StartTestAttemptView.as_view(), name="test-attempt-start"),
    path(
        "tests/<int:attempt_id>/",
        UserTestAttemptDetailView.as_view(),
        name="test-attempt-detail",
    ),
    path(
        "tests/<int:attempt_id>/submit/",
        SubmitTestAttemptView.as_view(),
        name="test-attempt-submit",
    ),
    path(
        "tests/<int:attempt_id>/review/",
        ReviewTestAttemptView.as_view(),
        name="test-attempt-review",
    ),
    path(
        "tests/<int:attempt_id>/retake-similar/",
        RetakeSimilarTestAttemptView.as_view(),
        name="test-attempt-retake-similar",
    ),
    # Add other study-related endpoints here later (tests, etc.)
]
