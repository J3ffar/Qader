from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.blog_management import AdminBlogPostViewSet, AdminBlogAdviceRequestViewSet

router = DefaultRouter()
router.register(r"posts", AdminBlogPostViewSet, basename="admin-blogpost")
router.register(
    r"advice-requests", AdminBlogAdviceRequestViewSet, basename="admin-advice-request"
)

urlpatterns = [
    path("", include(router.urls)),
]
