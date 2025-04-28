from django.urls import path, include

app_name = "study"

# Include URLs from the feature-specific files
urlpatterns = [
    path("attempts/", include("apps.study.api.urls.attempts")),
    path("traditional/", include("apps.study.api.urls.traditional")),
    path("statistics/", include("apps.study.api.urls.statistics")),
    path("emergency-mode/", include("apps.study.api.urls.emergency")),
    path("", include("apps.study.api.urls.conversation")),
]
