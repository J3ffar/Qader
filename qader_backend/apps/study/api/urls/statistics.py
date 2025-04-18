# qader_backend/apps/study/api/urls/statistics.py
from django.urls import path
from ..views.statistics import UserStatisticsView


urlpatterns = [
    path("", UserStatisticsView.as_view(), name="user-statistics"),
]
