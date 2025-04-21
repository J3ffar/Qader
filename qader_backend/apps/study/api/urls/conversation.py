from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.study.api.views.conversation import ConversationViewSet

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("", include(router.urls)),
]
