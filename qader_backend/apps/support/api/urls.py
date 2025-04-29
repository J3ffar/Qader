from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserSupportTicketViewSet,
)

user_router = DefaultRouter()
user_router.register(r"tickets", UserSupportTicketViewSet, basename="user-ticket")


app_name = "support"

urlpatterns = [
    # User-facing endpoints (/api/v1/support/tickets/...)
    path("", include(user_router.urls)),
    path(
        "tickets/<int:pk>/replies/",
        UserSupportTicketViewSet.as_view({"get": "replies", "post": "replies"}),
        name="user-ticket-replies",
    ),
]
