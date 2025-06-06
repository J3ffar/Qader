from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import learning_management as views

# Create a router instance specific to learning management
router = DefaultRouter()
router.register(
    r"sections",
    views.AdminLearningSectionViewSet,
    basename="admin-learning-section",
)
router.register(
    r"subsections",
    views.AdminLearningSubSectionViewSet,
    basename="admin-learning-subsection",
)
router.register(r"skills", views.AdminSkillViewSet, basename="admin-learning-skill")
router.register(
    r"questions",
    views.AdminQuestionViewSet,
    basename="admin-learning-question",
)

# Define urlpatterns for this module
urlpatterns = [
    # Include URLs generated by the router
    # (e.g., /learning/sections/, /learning/sections/{pk}/, etc.)
    path("", include(router.urls)),
]
