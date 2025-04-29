from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.support.api.views import AdminSupportTicketViewSet

router = DefaultRouter()
router.register(r"tickets", AdminSupportTicketViewSet, basename="admin-ticket")

urlpatterns = [
    # Include the router URLs (e.g., /api/v1/admin/support/tickets/)
    *router.urls,
    path(
        "tickets/<int:pk>/replies/",
        AdminSupportTicketViewSet.as_view({"get": "replies", "post": "replies"}),
        name="admin-ticket-replies",
    ),
]
