# qader_backend/apps/study/api/urls/level_assessment.py
from django.urls import path
from ..views import LevelAssessmentStartView, LevelAssessmentSubmitView


# Define urlpatterns for this specific feature
urlpatterns = [
    path(
        "start/",
        LevelAssessmentStartView.as_view(),
        name="level-assessment-start",
    ),
    path(
        "<int:attempt_id>/submit/",
        LevelAssessmentSubmitView.as_view(),
        name="level-assessment-submit",
    ),
]
