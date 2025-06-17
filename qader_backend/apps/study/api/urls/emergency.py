from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Creating a router for sessions to handle standard viewset actions cleanly
# For this specific case, we'll define paths manually for clarity.

from apps.study.api.views.emergency import (
    EmergencyModeStartView,
    EmergencyModeSessionUpdateView,
    EmergencyModeQuestionsView,
    EmergencyModeAnswerView,
)

# URLs related to the management of emergency sessions
session_patterns = [
    path("", EmergencyModeSessionUpdateView.as_view(), name="emergency-session-update"),
    path(
        "questions/",
        EmergencyModeQuestionsView.as_view(),
        name="emergency-session-questions",
    ),
    path("answer/", EmergencyModeAnswerView.as_view(), name="emergency-session-answer"),
]

urlpatterns = [
    # Factory endpoint to create a new session
    path("start/", EmergencyModeStartView.as_view(), name="emergency-start"),
    # Endpoints for a specific session resource
    path("sessions/<int:session_id>/", include(session_patterns)),
]
