from django.urls import path, include

app_name = "admin_panel"

urlpatterns = [
    path("", include("apps.admin_panel.api.urls.user_management")),
    path("content/", include("apps.admin_panel.api.urls.content_management")),
    path("learning/", include("apps.admin_panel.api.urls.learning_management")),
    # You can add other top-level admin routes here if needed in the future
    # path("dashboard-summary/", SomeDashboardView.as_view(), name="admin-dashboard-summary"),
]
