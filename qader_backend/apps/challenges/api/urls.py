from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChallengeTypeListView, ChallengeViewSet

app_name = "challenges"

router = DefaultRouter()
router.register(r"challenges", ChallengeViewSet, basename="challenge")

urlpatterns = [
    path("", include(router.urls)),
    # Add non-router views if needed (e.g., ChallengeTypeListView)
    path("types/", ChallengeTypeListView.as_view(), name="challenge-types-list"),
]
