from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "gamification"

router = DefaultRouter()
router.register(r"reward-store", views.RewardStoreItemViewSet, basename="reward-store")
router.register(r"point-log", views.PointLogViewSet, basename="point-log")

urlpatterns = [
    path("", include(router.urls)),
    path("summary/", views.GamificationSummaryView.as_view(), name="summary"),
    path("badges/", views.BadgeListView.as_view(), name="badge-list"),
    path(
        "my-badges/",
        views.UserEarnedBadgesListView.as_view(),
        name="user-earned-badge-list",
    ),
    path(
        "my-items/",
        views.UserPurchasedItemsListView.as_view(),
        name="user-purchased-item-list",
    ),
    path(
        "reward-store/purchase/<int:item_id>/",
        views.RewardPurchaseView.as_view(),
        name="reward-purchase",
    ),
    path("study-days/", views.StudyDayLogListView.as_view(), name="study-day-list"),
    path(
        "points-summary/",
        views.DailyPointSummaryView.as_view(),
        name="points-summary",
    ),
]
