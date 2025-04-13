from django.urls import path, include

app_name = "v1"

urlpatterns = [
    path("v1/", include("apps.api.v1.urls")),
]
