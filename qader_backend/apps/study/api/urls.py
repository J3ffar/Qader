from django.urls import path
from .views import (
    LevelAssessmentStartView,
    LevelAssessmentSubmitView,
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
    # Add other study-related endpoints here later (traditional, tests, etc.)
]
