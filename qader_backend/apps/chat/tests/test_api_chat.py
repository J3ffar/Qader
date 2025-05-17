import pytest
from django.urls import reverse
from rest_framework import status

from apps.chat.models import Conversation, Message
from apps.users.models import RoleChoices, UserProfile
from apps.users.tests.factories import UserFactory
from apps.users.constants import GenderChoices  # For checking roles

pytestmark = pytest.mark.django_db


class TestStudentConversationAPI:
    def test_student_get_my_conversation_no_mentor(self, student_client, student_user):
        # Ensure student has no mentor initially
        student_user.profile.assigned_mentor = None
        student_user.profile.save()

        url = reverse("api:v1:chat:student-my-conversation")
        response = student_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_student_get_my_conversation_with_mentor(
        self, student_mentor_client, student_with_mentor, teacher_user
    ):
        url = reverse("api:v1:chat:student-my-conversation")
        response = student_mentor_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert (
            response.data["student_profile"]["user_id"]
            == student_with_mentor.profile.pk
        )
        assert response.data["teacher_profile"]["user_id"] == teacher_user.profile.pk
        assert Conversation.objects.count() == 1

    def test_non_student_cannot_access_my_conversation(self, teacher_client):
        url = reverse("api:v1:chat:student-my-conversation")
        response = teacher_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_list_messages_in_my_conversation(
        self,
        student_mentor_client,
        conversation_between_student_and_mentor,
        student_with_mentor,
        teacher_user,
    ):
        Message.objects.create(
            conversation=conversation_between_student_and_mentor,
            sender=teacher_user,
            content="Hi Student",
        )
        Message.objects.create(
            conversation=conversation_between_student_and_mentor,
            sender=student_with_mentor,
            content="Hi Mentor",
        )

        url = reverse("api:v1:chat:student-my-conversation-messages")
        response = student_mentor_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert (
            len(response.data["results"]) == 2
        )  # Assuming pagination, check results key
        assert response.data["results"][0]["content"] == "Hi Student"

        # Check if teacher's message is now read
        teacher_message = Message.objects.get(sender=teacher_user)
        assert teacher_message.is_read is True

    def test_student_send_message_in_my_conversation(
        self, student_mentor_client, student_with_mentor, teacher_user
    ):
        # Ensure conversation exists or is created
        convo, _ = Conversation.get_or_create_conversation(
            student_with_mentor.profile, teacher_user.profile
        )

        url = reverse("api:v1:chat:student-my-conversation-messages")
        data = {"content": "Hello from student!"}
        response = student_mentor_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        print(response.data)
        assert response.data["content"] == data["content"]
        assert response.data["sender"] == student_with_mentor.pk
        assert (
            Message.objects.filter(
                conversation=convo, sender=student_with_mentor
            ).count()
            == 1
        )


class TestTeacherConversationAPI:
    def test_teacher_list_their_conversations(
        self,
        teacher_client,
        teacher_user,
        student_with_mentor,
        student_user,  # student_user fixture is not used here
    ):
        # student_with_mentor is already assigned to teacher_user
        convo1, _ = Conversation.get_or_create_conversation(
            student_with_mentor.profile, teacher_user.profile
        )

        # Create another student and assign them to the same teacher
        # FIX: Use UserFactory to create the user, then access its profile
        other_student_user = UserFactory(
            username="otherstudent",
            email="other@q.test",
            profile_data={  # Pass profile data to the factory
                "full_name": "Other Student",
                "role": RoleChoices.STUDENT,
                "assigned_mentor_profile": teacher_user.profile,  # Custom param for factory hook
                "gender": GenderChoices.MALE,
                "grade": "11",
                "has_taken_qiyas_before": False,
            },
        )
        other_student_profile = other_student_user.profile
        # Ensure the factory or a post_generation hook in UserFactory sets assigned_mentor
        # If not, set it manually after profile is available:
        if other_student_profile.assigned_mentor != teacher_user.profile:
            other_student_profile.assigned_mentor = teacher_user.profile
            other_student_profile.save()

        convo2, _ = Conversation.get_or_create_conversation(
            other_student_profile, teacher_user.profile
        )

        url = reverse("api:v1:chat:teacher-conversations-list")
        response = teacher_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # Assuming pagination
        conversation_ids_in_response = {c["id"] for c in response.data["results"]}
        assert convo1.id in conversation_ids_in_response
        assert convo2.id in conversation_ids_in_response

    def test_non_teacher_cannot_list_teacher_conversations(self, student_client):
        url = reverse("api:v1:chat:teacher-conversations-list")
        response = student_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_teacher_list_messages_in_specific_conversation(
        self,
        teacher_client,
        conversation_between_student_and_mentor,
        student_with_mentor,
        teacher_user,
    ):
        Message.objects.create(
            conversation=conversation_between_student_and_mentor,
            sender=student_with_mentor,
            content="Question from student",
        )
        Message.objects.create(
            conversation=conversation_between_student_and_mentor,
            sender=teacher_user,
            content="Answer from teacher",
        )

        url = reverse(
            "api:v1:chat:teacher-conversation-messages",
            kwargs={"conversation_pk": conversation_between_student_and_mentor.id},
        )
        response = teacher_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2
        assert response.data["results"][0]["content"] == "Question from student"

        # Check if student's message is now read
        student_message = Message.objects.get(sender=student_with_mentor)
        assert student_message.is_read is True

    def test_teacher_send_message_in_specific_conversation(
        self, teacher_client, conversation_between_student_and_mentor, teacher_user
    ):
        url = reverse(
            "api:v1:chat:teacher-conversation-messages",
            kwargs={"conversation_pk": conversation_between_student_and_mentor.id},
        )
        data = {"content": "Follow up from teacher."}
        response = teacher_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["content"] == data["content"]
        print(response.data)
        assert response.data["sender"] == teacher_user.pk
        assert (
            Message.objects.filter(
                conversation=conversation_between_student_and_mentor,
                sender=teacher_user,
            ).count()
            == 1
        )

    def test_teacher_cannot_access_unrelated_conversation_messages(
        self,
        teacher_client,
        student_user,  # Not directly used for the setup of 'other_teacher'
        teacher_user,  # teacher_user is the one authed for client
    ):
        # Create a different teacher and a conversation they are part of
        other_teacher_user = UserFactory(
            username="otherteacher",
            email="otherteacher@q.test",
            profile_data={
                "role": RoleChoices.TEACHER,
                "full_name": "Other Teacher",
                "gender": GenderChoices.FEMALE,  # Add missing fields for completion
                "grade": "N/A",
                "has_taken_qiyas_before": False,
            },
        )
        other_teacher_profile = other_teacher_user.profile
        student_for_other_user = UserFactory(
            username="studentforother",
            email="sfo@q.test",
            profile_data={
                "role": RoleChoices.STUDENT,
                "full_name": "Student for Other",
                "assigned_mentor_profile": other_teacher_profile,
                "gender": GenderChoices.FEMALE,
                "grade": "10",
                "has_taken_qiyas_before": True,
            },
        )
        student_profile_for_other_teacher = student_for_other_user.profile
        # As above, ensure factory handles assigned_mentor or set manually
        if student_profile_for_other_teacher.assigned_mentor != other_teacher_profile:
            student_profile_for_other_teacher.assigned_mentor = other_teacher_profile
            student_profile_for_other_teacher.save()

        unrelated_convo, _ = Conversation.get_or_create_conversation(
            student_profile_for_other_teacher, other_teacher_profile
        )

        url = reverse(
            "api:v1:chat:teacher-conversation-messages",
            kwargs={"conversation_pk": unrelated_convo.id},
        )
        response = teacher_client.get(url)  # teacher_client is authed as 'teacher_user'
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        )  # Or 403 depending on get_object_or_404 behavior


class TestMarkMessagesAsReadAPI:
    def test_participant_can_mark_messages_read(
        self,
        student_mentor_client,
        conversation_between_student_and_mentor,
        teacher_user,
    ):
        # Teacher sends a message, student will mark it as read
        msg = Message.objects.create(
            conversation=conversation_between_student_and_mentor,
            sender=teacher_user,
            content="Test read",
            is_read=False,
        )
        assert msg.is_read is False

        url = reverse(
            "api:v1:chat:conversation-mark-read",
            kwargs={"conversation_pk": conversation_between_student_and_mentor.id},
        )
        # student_mentor_client is authenticated as the student
        response = student_mentor_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        msg.refresh_from_db()
        assert msg.is_read is True

    def test_non_participant_cannot_mark_messages_read(
        self,
        api_client,
        conversation_between_student_and_mentor,  # No specific client needed here
    ):
        # Create a completely unrelated user for this test
        unrelated_user = UserFactory(username="unrelated_guy")
        api_client.force_authenticate(
            user=unrelated_user
        )  # Authenticate as this new user

        url = reverse(
            "api:v1:chat:conversation-mark-read",  # Corrected namespace
            kwargs={"conversation_pk": conversation_between_student_and_mentor.id},
        )
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        api_client.force_authenticate(user=None)
