from django.urls import path
from apps.study.api.views import level_assessment as views

urlpatterns = [
    path(
        "",  # Path relative to /api/v1/study/start/level-assessment/
        views.LevelAssessmentStartView.as_view(),
        name="start-level-assessment",
    ),
]
