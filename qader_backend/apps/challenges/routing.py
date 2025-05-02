from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # Route for connecting to a specific challenge
    re_path(
        r"ws/challenges/(?P<challenge_pk>\d+)/$",
        consumers.ChallengeConsumer.as_asgi(),
        name="ws_challenge_detail",
    ),
    # Optional: Route for general challenge notifications (e.g., new invites)
    re_path(
        r"ws/challenges/notifications/$",
        consumers.ChallengeNotificationConsumer.as_asgi(),
        name="ws_challenge_notifications",
    ),
]
