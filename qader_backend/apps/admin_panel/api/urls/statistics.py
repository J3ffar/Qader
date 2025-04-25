# qader_backend/apps/admin_panel/api/urls/statistics.py
from django.urls import path
from apps.admin_panel.api.views import statistics as views

urlpatterns = [
    path(
        "overview/",
        views.AdminStatisticsOverviewAPIView.as_view(),
        name="admin-statistics-overview",
    ),
    path(
        "export/",
        views.AdminStatisticsExportAPIView.as_view(),
        name="admin-statistics-export",
    ),
    # Optional: Endpoint to check export task status if using Celery
    # path('export-tasks/<str:task_id>/status/', views.ExportTaskStatusAPIView.as_view(), name='admin-export-task-status'),
]
