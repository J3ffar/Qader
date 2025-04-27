from django.urls import path
from apps.study.api.views.emergency import (
    EmergencyModeQuestionsView,
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
    path(
        "<int:session_id>/questions/",
        EmergencyModeQuestionsView.as_view(),
        name="emergency-questions",
    ),
    path("answer/", EmergencyModeAnswerView.as_view(), name="emergency-answer"),
]
