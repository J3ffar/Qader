from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..views.serial_code_management import SerialCodeAdminViewSet

router = DefaultRouter()
router.register(r"", SerialCodeAdminViewSet, basename="admin-serial-code")
# The `generate_codes` action will be automatically mapped to /generate-batch/ by the router

urlpatterns = [
    path("", include(router.urls)),
]
