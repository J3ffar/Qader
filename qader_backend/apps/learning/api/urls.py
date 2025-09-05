from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "learning"

router = DefaultRouter()
router.register(r"test-types", views.TestTypeViewSet, basename="test-type")  # NEW
router.register(r"sections", views.LearningSectionViewSet, basename="section")
router.register(r"subsections", views.LearningSubSectionViewSet, basename="subsection")
router.register(r"skills", views.SkillViewSet, basename="skill")
router.register(r"questions", views.QuestionViewSet, basename="question")

urlpatterns = [
    path("", include(router.urls)),
]
