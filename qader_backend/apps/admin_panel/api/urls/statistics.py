# qader_backend/apps/admin_panel/api/urls/statistics.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.admin_panel.api.views import statistics as views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"export-jobs", views.ExportJobViewSet, basename="export-job")

urlpatterns = [
    path(
        "overview/",
        views.AdminStatisticsOverviewAPIView.as_view(),
        name="admin-statistics-overview",
    ),
    # The router handles the URLs for the export jobs now
    # - POST /export-jobs/ -> create
    # - GET /export-jobs/ -> list
    # - GET /export-jobs/{pk}/ -> retrieve
    path("", include(router.urls)),
]
