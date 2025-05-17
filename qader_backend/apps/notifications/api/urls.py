from django.urls import path
from . import views

app_name = "notifications"  # For namespacing if needed

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="list_notifications"),
    path(
        "mark-read/",
        views.NotificationMarkAsReadView.as_view(),
        name="mark_notifications_read",
    ),
    path(
        "mark-all-read/",
        views.NotificationMarkAllAsReadView.as_view(),
        name="mark_all_notifications_read",
    ),
    path(
        "<int:pk>/delete/",
        views.NotificationDeleteView.as_view(),
        name="delete_notification",
    ),
    path(
        "unread-count/",
        views.UnreadNotificationCountView.as_view(),
        name="unread_notification_count",
    ),
]
