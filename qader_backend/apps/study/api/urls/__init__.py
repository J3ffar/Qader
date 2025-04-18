# qader_backend/apps/study/api/urls.py (MODIFIED Original File)
from django.urls import path, include

app_name = "study"

# Include URLs from the feature-specific files
urlpatterns = [
    path("level-assessment/", include("apps.study.api.urls.level_assessment")),
    path("traditional/", include("apps.study.api.urls.traditional")),
    path("tests/", include("apps.study.api.urls.tests")),
    path("statistics/", include("apps.study.api.urls.statistics")),
    # --- Add includes for other study features (Emergency, Conversation etc.) when created ---
    # e.g., path("emergency-mode/", include("apps.study.api.urls.emergency")),
]

# --- Ensure the top-level API router includes these study URLs ---
# In qader_backend/apps/api/v1/urls.py (or similar):
# from django.urls import path, include
#
# urlpatterns = [
#     path('study/', include('apps.study.api.urls', namespace='study')),
#     path('users/', include('apps.users.api.users_urls', namespace='users')),
#     # ... other app api includes
# ]
