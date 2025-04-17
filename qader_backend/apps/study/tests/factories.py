# qader_backend/apps/study/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from django.conf import settings
from factory.faker import Faker
from apps.learning.tests.factories import SkillFactory
import random

# Import UserFactory if not globally available in tests
from apps.users.tests.factories import UserFactory
from apps.study.models import UserSkillProficiency


class UserSkillProficiencyFactory(DjangoModelFactory):
    class Meta:
        model = UserSkillProficiency
        django_get_or_create = ("user", "skill")  # Avoid duplicates

    user = factory.SubFactory(UserFactory)
    skill = factory.SubFactory(SkillFactory)
    proficiency_score = factory.Faker(
        "pyfloat", left_digits=1, right_digits=2, min_value=0.0, max_value=1.0
    )
    attempts_count = factory.Faker("random_int", min=1, max=50)
    # --- FIX: Correct usage of Faker within LazyAttribute ---
    correct_count = factory.LazyAttribute(
        # Use evaluate to get the value from the Faker instance
        lambda o: factory.Faker("random_int", min=0, max=o.attempts_count).evaluate(
            None, None, extra={"locale": None}
        )
        # Alternatively, using Python's random is often simpler:
        # lambda o: random.randint(0, o.attempts_count if o.attempts_count > 0 else 0) # Ensure max >= min
    )
