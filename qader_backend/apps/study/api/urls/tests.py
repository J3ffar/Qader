# qader_backend/apps/study/api/urls/tests.py
from django.urls import path
from ..views.tests import (
    UserTestAttemptListView,
    StartTestAttemptView,
    UserTestAttemptDetailView,
    SubmitTestAttemptView,
    ReviewTestAttemptView,
    RetakeSimilarTestAttemptView,
)


urlpatterns = [
    path("", UserTestAttemptListView.as_view(), name="test-attempt-list"),
    path("start/", StartTestAttemptView.as_view(), name="test-attempt-start"),
    path(
        "<int:attempt_id>/",
        UserTestAttemptDetailView.as_view(),
        name="test-attempt-detail",
    ),
    path(
        "<int:attempt_id>/submit/",
        SubmitTestAttemptView.as_view(),
        name="test-attempt-submit",
    ),
    path(
        "<int:attempt_id>/review/",
        ReviewTestAttemptView.as_view(),
        name="test-attempt-review",
    ),
    path(
        "<int:attempt_id>/retake-similar/",
        RetakeSimilarTestAttemptView.as_view(),
        name="test-attempt-retake-similar",
    ),
]
