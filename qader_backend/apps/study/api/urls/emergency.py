from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.study.api.views.emergency import (
    EmergencyModeStartView,
    EmergencyModeSessionUpdateView,
    EmergencyModeQuestionsView,
    EmergencyModeAnswerView,
    EmergencyModeCompleteView,
)

# URLs related to the management of an ongoing emergency session
session_patterns = [
    path("", EmergencyModeSessionUpdateView.as_view(), name="emergency-session-update"),
    path(
        "questions/",
        EmergencyModeQuestionsView.as_view(),
        name="emergency-session-questions",
    ),
    path("answer/", EmergencyModeAnswerView.as_view(), name="emergency-session-answer"),
    path(
        "complete/",
        EmergencyModeCompleteView.as_view(),
        name="emergency-session-complete",
    ),
]

urlpatterns = [
    # Factory endpoint to create a new session
    path("start/", EmergencyModeStartView.as_view(), name="emergency-start"),
    # Endpoints for a specific session resource
    path("sessions/<int:session_id>/", include(session_patterns)),
]
