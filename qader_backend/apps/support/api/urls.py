from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserSupportTicketViewSet, AdminSupportTicketViewSet

# Using separate routers for clarity, could combine if preferred
user_router = DefaultRouter()
user_router.register(r"tickets", UserSupportTicketViewSet, basename="user-ticket")

admin_router = DefaultRouter()
admin_router.register(r"tickets", AdminSupportTicketViewSet, basename="admin-ticket")

app_name = "support"

urlpatterns = [
    # User-facing endpoints (/api/v1/support/tickets/...)
    path("", include(user_router.urls)),
    # Admin-facing endpoints (/api/v1/support/admin/tickets/...)
    path("admin/", include(admin_router.urls)),
    # Manual nested routes (alternative to drf-nested-routers)
    # POST/GET /api/v1/support/tickets/{ticket_pk}/replies/
    path(
        "tickets/<int:pk>/replies/",
        UserSupportTicketViewSet.as_view({"get": "replies", "post": "replies"}),
        name="user-ticket-replies",
    ),
    # POST/GET /api/v1/support/admin/tickets/{ticket_pk}/replies/
    path(
        "admin/tickets/<int:pk>/replies/",
        AdminSupportTicketViewSet.as_view({"get": "replies", "post": "replies"}),
        name="admin-ticket-replies",
    ),
]
