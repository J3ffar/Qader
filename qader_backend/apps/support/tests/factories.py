import factory
from factory.django import DjangoModelFactory
from django.utils import timezone

from apps.users.tests.factories import UserFactory  # Assuming you have a UserFactory
from ..models import SupportTicket, SupportTicketReply


class SupportTicketFactory(DjangoModelFactory):
    class Meta:
        model = SupportTicket

    user = factory.SubFactory(UserFactory)
    issue_type = factory.Faker(
        "random_element",
        elements=[choice[0] for choice in SupportTicket.IssueType.choices],
    )
    subject = factory.Faker("sentence", nb_words=6)
    description = factory.Faker("text", max_nb_chars=200)
    status = SupportTicket.Status.OPEN
    priority = SupportTicket.Priority.MEDIUM
    assigned_to = None
    attachment = None
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyAttribute(lambda o: o.created_at)
    closed_at = None

    class Params:
        assigned = factory.Trait(
            assigned_to=factory.SubFactory(UserFactory, is_staff=True)
        )
        closed = factory.Trait(
            status=SupportTicket.Status.CLOSED,
            closed_at=factory.LazyFunction(timezone.now),
        )


class SupportTicketReplyFactory(DjangoModelFactory):
    class Meta:
        model = SupportTicketReply

    ticket = factory.SubFactory(SupportTicketFactory)
    user = factory.SubFactory(UserFactory)
    message = factory.Faker("text", max_nb_chars=150)
    is_internal_note = False
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyAttribute(lambda o: o.created_at)

    class Params:
        internal = factory.Trait(
            is_internal_note=True, user=factory.SubFactory(UserFactory, is_staff=True)
        )
        by_admin = factory.Trait(user=factory.SubFactory(UserFactory, is_staff=True))
        by_user = factory.Trait(user=factory.LazyAttribute(lambda o: o.ticket.user))
