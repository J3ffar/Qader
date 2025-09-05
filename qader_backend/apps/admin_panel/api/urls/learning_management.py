from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ..views import learning_management as views

router = DefaultRouter()

router.register(
    r"test-types",
    views.AdminTestTypeViewSet,
    basename="admin-test-type",
)
router.register(
    r"media-files",
    views.AdminMediaFileViewSet,
    basename="admin-media-file",
) # NEW
router.register(
    r"articles",
    views.AdminArticleViewSet,
    basename="admin-article",
) # NEW
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

urlpatterns = [
    path("", include(router.urls)),
]
