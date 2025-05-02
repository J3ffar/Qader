from django.urls import path, include

app_name = "admin_panel"

urlpatterns = [
    path("", include("apps.admin_panel.api.urls.user_management")),
    path("content/", include("apps.admin_panel.api.urls.content_management")),
    path("learning/", include("apps.admin_panel.api.urls.learning_management")),
    path("support/", include("apps.admin_panel.api.urls.support_management")),
    path("serial-codes/", include("apps.admin_panel.api.urls.serial_code_management")),
    path("gamification/", include("apps.admin_panel.api.urls.gamification_management")),
    path("blog/", include("apps.admin_panel.api.urls.blog_management")),
    path(
        "community/",
        include("apps.admin_panel.api.urls.community_management"),
    ),
    path("statistics/", include("apps.admin_panel.api.urls.statistics")),
]
