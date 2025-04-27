from django.urls import path, include

app_name = "study"

# Include URLs from the feature-specific files
urlpatterns = [
    path("level-assessment/", include("apps.study.api.urls.level_assessment")),
    path("traditional/", include("apps.study.api.urls.traditional")),
    path("tests/", include("apps.study.api.urls.tests")),
    path("statistics/", include("apps.study.api.urls.statistics")),
    path("emergency-mode/", include("apps.study.api.urls.emergency")),
    path("", include("apps.study.api.urls.conversation")),
]
