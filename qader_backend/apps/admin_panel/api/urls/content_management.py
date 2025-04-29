from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.admin_panel.api.views import content_management as views

router = DefaultRouter()
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

urlpatterns = [
    path("", include(router.urls)),
]
