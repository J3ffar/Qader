from django.urls import path
from apps.study.api.views import (
    # Attempt Lifecycle
    LevelAssessmentStartView,  # Specific start for level assessment
    StartTestAttemptView,  # Specific start for practice/simulation
    UserTestAttemptListView,
    UserTestAttemptDetailView,
    TestAttemptAnswerView,  # NEW: Unified answer endpoint
    CompleteTestAttemptView,  # NEW: Unified complete endpoint
    CancelTestAttemptView,  # NEW: Unified cancel endpoint
    # Review & Retake
    ReviewTestAttemptView,
    RetakeSimilarTestAttemptView,
)

# Define urlpatterns for test attempts (Level Assessment, Practice, Simulation)
urlpatterns = [
    # --- Starting Attempts ---
    path(
        "start/level-assessment/",  # More specific path
        LevelAssessmentStartView.as_view(),
        name="attempt-start-level-assessment",
    ),
    path(
        "start/practice-simulation/",  # More specific path
        StartTestAttemptView.as_view(),
        name="attempt-start-practice-simulation",
    ),
    # --- Managing Attempts ---
    path(
        "",  # List all attempts (filterable)
        UserTestAttemptListView.as_view(),
        name="attempt-list",
    ),
    path(
        "<int:attempt_id>/",  # Get details of any attempt
        UserTestAttemptDetailView.as_view(),
        name="attempt-detail",
    ),
    path(
        "<int:attempt_id>/answer/",  # Submit single answer
        TestAttemptAnswerView.as_view(),
        name="attempt-answer",
    ),
    path(
        "<int:attempt_id>/complete/",  # Finalize and score
        CompleteTestAttemptView.as_view(),
        name="attempt-complete",
    ),
    path(
        "<int:attempt_id>/cancel/",  # Abandon attempt
        CancelTestAttemptView.as_view(),
        name="attempt-cancel",
    ),
    # --- Review & Retake ---
    path(
        "<int:attempt_id>/review/",  # Review completed attempt
        ReviewTestAttemptView.as_view(),
        name="attempt-review",
    ),
    path(
        "<int:attempt_id>/retake-similar/",  # Start new based on old config
        RetakeSimilarTestAttemptView.as_view(),
        name="attempt-retake-similar",
    ),
]
