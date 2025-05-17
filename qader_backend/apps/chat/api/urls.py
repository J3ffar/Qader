from django.urls import path
from .views import (
    StudentConversationView,
    MessageListCreateView,
    TeacherConversationListView,
    MarkMessagesAsReadView,
)

app_name = "chat_api"  # Use a distinct app_name for API urls

urlpatterns = [
    # Student Endpoints
    path(
        "my-conversation/",
        StudentConversationView.as_view(),
        name="student-my-conversation",
    ),
    path(  # Student listing their messages or sending a message
        "my-conversation/messages/",
        MessageListCreateView.as_view(),
        name="student-my-conversation-messages",
    ),
    # Teacher/Trainer Endpoints
    path(
        "teacher/conversations/",
        TeacherConversationListView.as_view(),
        name="teacher-conversations-list",
    ),
    path(  # Teacher listing messages for a specific student or sending a message
        "teacher/conversations/<int:conversation_pk>/messages/",
        MessageListCreateView.as_view(),
        name="teacher-conversation-messages",
    ),
    # Optional: Explicit mark as read
    path(
        "conversations/<int:conversation_pk>/mark-read/",
        MarkMessagesAsReadView.as_view(),
        name="conversation-mark-read",
    ),
]
