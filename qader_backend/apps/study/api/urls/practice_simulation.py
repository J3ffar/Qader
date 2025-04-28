from django.urls import path
from apps.study.api.views import practice_simulation as views

urlpatterns = [
    path(
        "",  # Path relative to /api/v1/study/start/practice-simulation/
        views.PracticeSimulationStartView.as_view(),
        name="start-practice-simulation",
    ),
]
