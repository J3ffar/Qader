from django.urls import path
from apps.study.api.views.statistics import UserStatisticsView


urlpatterns = [
    path("", UserStatisticsView.as_view(), name="user-statistics"),
]
