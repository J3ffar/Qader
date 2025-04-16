from django.urls import path
from . import views

app_name = "study"

urlpatterns = [
    path(
        "level-assessment/start/",
        views.StartLevelAssessmentView.as_view(),
        name="level-assessment-start",
    ),
    path(
        "level-assessment/<int:attempt_id>/submit/",
        views.SubmitLevelAssessmentView.as_view(),
        name="level-assessment-submit",
    ),
    # Add other study-related endpoints here later (traditional, tests, etc.)
]
