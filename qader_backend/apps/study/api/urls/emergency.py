from django.urls import path
from apps.study.api.views.emergency import (
    EmergencyModeStartView,
    EmergencyModeSessionUpdateView,
    EmergencyModeAnswerView,
)

urlpatterns = [
    path("start/", EmergencyModeStartView.as_view(), name="emergency-start"),
    path(
        "<int:session_id>/",
        EmergencyModeSessionUpdateView.as_view(),
        name="emergency-update",
    ),
    path("answer/", EmergencyModeAnswerView.as_view(), name="emergency-answer"),
]
