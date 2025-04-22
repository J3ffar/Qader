from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "content"

# Using a router for PageViewSet as it's a standard ReadOnlyModelViewSet
router = DefaultRouter()
router.register(r"pages", views.PageViewSet, basename="page")  # Basename is important

urlpatterns = [
    path("", include(router.urls)),  # Includes '/pages/' and '/pages/{slug}/'
    path("homepage/", views.HomepageView.as_view(), name="homepage"),
    path("faq/", views.FAQListView.as_view(), name="faq-list"),
    path(
        "partners/",
        views.PartnerCategoryListView.as_view(),
        name="partner-category-list",
    ),
    path(
        "contact-us/",
        views.ContactMessageCreateView.as_view(),
        name="contact-us-create",
    ),
]
