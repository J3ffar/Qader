# apps/study/api/urls/attempts.py
from django.urls import path
from apps.study.api.views import (
    LevelAssessmentStartView,
    StartTestAttemptView,
    UserTestAttemptListView,
    UserTestAttemptDetailView,
    TestAttemptAnswerView,
    CompleteTestAttemptView,
    CancelTestAttemptView,
    RevealAnswerView,
    RetakeSimilarTestAttemptView,
    ReviewTestAttemptView,
    StartTraditionalAttemptView,
    EndTraditionalAttemptView,
)

urlpatterns = [
    # --- Starting Attempts ---
    path(
        "start/level-assessment/",
        LevelAssessmentStartView.as_view(),
        name="attempt-start-level-assessment",
    ),
    path(
        "start/practice-simulation/",
        StartTestAttemptView.as_view(),
        name="attempt-start-practice-simulation",
    ),
    path(
        "start/traditional/",
        StartTraditionalAttemptView.as_view(),
        name="attempt-start-traditional",
    ),  # <-- ADD
    # --- Managing & Viewing Attempts ---
    path("", UserTestAttemptListView.as_view(), name="attempt-list"),
    path(
        "<int:attempt_id>/", UserTestAttemptDetailView.as_view(), name="attempt-detail"
    ),
    path(
        "<int:attempt_id>/answer/",
        TestAttemptAnswerView.as_view(),
        name="attempt-answer",
    ),
    path(
        "<int:attempt_id>/complete/",
        CompleteTestAttemptView.as_view(),
        name="attempt-complete",
    ),  # (Rejects traditional)
    path(
        "<int:attempt_id>/cancel/",
        CancelTestAttemptView.as_view(),
        name="attempt-cancel",
    ),  # (Works for traditional)
    path(
        "<int:attempt_id>/end-traditional/",
        EndTraditionalAttemptView.as_view(),
        name="attempt-end-traditional",
    ),
    # --- Review & Retake ---
    path(
        "<int:attempt_id>/review/",
        ReviewTestAttemptView.as_view(),
        name="attempt-review",
    ),
    path(
        "<int:attempt_id>/retake-similar/",
        RetakeSimilarTestAttemptView.as_view(),
        name="attempt-retake-similar",
    ),
    # --- In-Progress Helpers (Traditional Only) ---
    path(
        "<int:attempt_id>/question/<int:question_id>/reveal/",
        RevealAnswerView.as_view(),
        name="attempt-reveal-answer",
    ),  # <-- ADD
]
