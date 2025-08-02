from django.urls import path
from apps.study.api.views import attempts as attempt_views  # Alias for clarity

urlpatterns = [
    path("", attempt_views.UserTestAttemptListView.as_view(), name="attempt-list"),
    path(
        "<int:attempt_id>/",
        attempt_views.UserTestAttemptDetailView.as_view(),
        name="attempt-detail",
    ),
    path(
        "<int:attempt_id>/resume/",
        attempt_views.UserTestAttemptResumeView.as_view(),
        name="attempt-resume",
    ),
    path(
        "<int:attempt_id>/answer/",
        attempt_views.UserTestAttemptAnswerView.as_view(),
        name="attempt-answer",
    ),
    path(
        "<int:attempt_id>/complete/",
        attempt_views.UserTestAttemptCompleteView.as_view(),
        name="attempt-complete",
    ),
    path(
        "<int:attempt_id>/cancel/",
        attempt_views.UserTestAttemptCancelView.as_view(),
        name="attempt-cancel",
    ),
    path(
        "<int:attempt_id>/review/",
        attempt_views.UserTestAttemptReviewView.as_view(),
        name="attempt-review",
    ),
    path(
        "<int:attempt_id>/retake/",
        attempt_views.UserTestAttemptRetakeView.as_view(),
        name="attempt-retake",
    ),
]
