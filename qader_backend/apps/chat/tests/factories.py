# apps/chat/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

from apps.users.tests.factories import UserProfileFactory  # Re-use UserProfileFactory
from ..models import Conversation, Message

User = get_user_model()


class ConversationFactory(DjangoModelFactory):
    class Meta:
        model = Conversation

    # You'll typically set student and teacher explicitly in tests
    # based on specific roles and assigned_mentor relationships.
    # student = factory.SubFactory(UserProfileFactory, role='STUDENT')
    # teacher = factory.SubFactory(UserProfileFactory, role='TEACHER')

    # Example of how to ensure the teacher is the student's mentor if creating directly:
    # @factory.post_generation
    # def link_mentor(obj, create, extracted, **kwargs):
    #     if create and obj.student and obj.teacher:
    #         if obj.student.assigned_mentor != obj.teacher:
    #             obj.student.assigned_mentor = obj.teacher
    #             obj.student.save()


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = Message

    conversation = factory.SubFactory(ConversationFactory)
    sender = factory.SubFactory(
        User
    )  # Or use UserFactory from apps.users.tests.factories
    content = factory.Faker("sentence")
    is_read = False
