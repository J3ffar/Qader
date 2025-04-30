from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogPostViewSet, BlogAdviceRequestViewSet, BlogTagListView

app_name = "blog"

router = DefaultRouter()
router.register(r"posts", BlogPostViewSet, basename="blogpost")
# Advice requests only needs a create endpoint
# router.register(r'advice-requests', BlogAdviceRequestViewSet, basename='advice-request')

urlpatterns = [
    path("", include(router.urls)),
    # Explicit path for creating advice requests
    path(
        "advice-requests/",
        BlogAdviceRequestViewSet.as_view({"post": "create"}),
        name="advice-request-create",
    ),
    path(
        "tags/",
        BlogTagListView.as_view(),
        name="blog-tags-list",
    ),
]
