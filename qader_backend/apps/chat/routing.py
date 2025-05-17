from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Path for student's conversation (implicitly knows the conversation via session/auth)
    re_path(r"ws/chat/my-conversation/$", consumers.ChatConsumer.as_asgi()),
    # Path for teacher accessing a specific conversation
    # The conversation_id will be extracted from the URL
    re_path(
        r"ws/chat/conversations/(?P<conversation_id>\d+)/$",
        consumers.ChatConsumer.as_asgi(),
    ),
]
