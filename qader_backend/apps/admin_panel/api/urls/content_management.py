from django.urls import path, include
from rest_framework_nested import routers

from apps.admin_panel.api.views import content_management as views

# Main router for top-level resources
router = routers.DefaultRouter()

router.register(r"pages", views.PageAdminViewSet, basename="admin-pages")
router.register(
    r"faq-categories", views.FAQCategoryAdminViewSet, basename="admin-faq-categories"
)
router.register(r"faq-items", views.FAQItemAdminViewSet, basename="admin-faq-items")
router.register(
    r"partner-categories",
    views.PartnerCategoryAdminViewSet,
    basename="admin-partner-categories",
)
router.register(
    r"homepage-features",
    views.HomepageFeatureCardAdminViewSet,
    basename="admin-homepage-features",
)
router.register(
    r"homepage-stats",
    views.HomepageStatisticAdminViewSet,
    basename="admin-homepage-stats",
)
router.register(
    r"contact-messages",
    views.ContactMessageAdminViewSet,
    basename="admin-contact-messages",
)
# New endpoint for the general (un-attached) media library
router.register(
    r"media-library", views.ContentImageAdminViewSet, basename="admin-media-library"
)


# Nested router for images specifically related to a page
# Creates URLs like: /api/admin/content/pages/{page_slug}/images/
pages_router = routers.NestedSimpleRouter(router, r"pages", lookup="page")
pages_router.register(
    r"images", views.PageContentImageAdminViewSet, basename="page-images"
)

urlpatterns = [
    path("", include(router.urls)),
    path("", include(pages_router.urls)),
]
