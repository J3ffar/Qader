import factory
from factory.django import DjangoModelFactory
from django.utils import timezone

from ..models import Challenge, ChallengeAttempt, ChallengeType, ChallengeStatus

# Assuming UserFactory exists in apps.users.tests.factories
from apps.users.tests.factories import UserFactory

# Assuming QuestionFactory exists or create a simple one if needed
from apps.learning.tests.factories import QuestionFactory


class ChallengeFactory(DjangoModelFactory):
    class Meta:
        model = Challenge

    challenger = factory.SubFactory(UserFactory)
    opponent = factory.SubFactory(UserFactory)  # Default to having an opponent
    challenge_type = factory.LazyFunction(lambda: ChallengeType.QUICK_QUANT_10)
    status = factory.LazyFunction(lambda: ChallengeStatus.PENDING_INVITE)
    challenge_config = factory.LazyAttribute(
        lambda o: (
            {
                "num_questions": 10,
                "time_limit_seconds": 300,
                "allow_hints": False,
                "sections": ["quantitative"],
                "name": "Test Quick Quant",
            }
            if o.challenge_type == ChallengeType.QUICK_QUANT_10
            else {"num_questions": 5}
        )
    )
    # Generate some dummy question IDs - ensure these questions exist in tests
    question_ids = factory.LazyFunction(
        lambda: [QuestionFactory().id for _ in range(5)]
    )
    created_at = factory.LazyFunction(timezone.now)

    # Helper trait for random matchmaking pending state
    class Params:
        random_pending = factory.Trait(
            opponent=None, status=ChallengeStatus.PENDING_MATCHMAKING
        )
        ongoing = factory.Trait(
            status=ChallengeStatus.ONGOING,
            accepted_at=factory.LazyFunction(timezone.now),
            started_at=factory.LazyFunction(timezone.now),
        )
        completed_tie = factory.Trait(
            status=ChallengeStatus.COMPLETED,
            accepted_at=factory.LazyFunction(timezone.now),
            started_at=factory.LazyFunction(timezone.now),
            completed_at=factory.LazyFunction(timezone.now),
            winner=None,
        )
        completed_challenger_win = factory.Trait(
            status=ChallengeStatus.COMPLETED,
            accepted_at=factory.LazyFunction(timezone.now),
            started_at=factory.LazyFunction(timezone.now),
            completed_at=factory.LazyFunction(timezone.now),
            winner=factory.SelfAttribute("..challenger"),
        )


class ChallengeAttemptFactory(DjangoModelFactory):
    class Meta:
        model = ChallengeAttempt

    challenge = factory.SubFactory(ChallengeFactory)
    user = factory.SelfAttribute("..challenge.challenger")  # Default to challenger
    score = factory.Faker("pyint", min_value=0, max_value=5)
    is_ready = False
    created_at = factory.LazyFunction(timezone.now)

    class Params:
        as_opponent = factory.Trait(
            user=factory.SelfAttribute("....challenge.opponent")
        )
        ready_to_start = factory.Trait(
            is_ready=True, start_time=factory.LazyFunction(timezone.now)
        )
        finished = factory.Trait(
            is_ready=True,  # Must be ready to finish
            start_time=factory.LazyFunction(timezone.now),
            end_time=factory.LazyFunction(timezone.now),
        )
