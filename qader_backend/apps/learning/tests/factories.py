import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
from django.conf import settings

from ..models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
    UserStarredQuestion,
)

# Assuming UserFactory is accessible (e.g., defined globally or imported)
# If not, explicitly import: from apps.users.tests.factories import UserFactory


class LearningSectionFactory(DjangoModelFactory):
    class Meta:
        model = LearningSection
        django_get_or_create = ("slug",)  # Avoid duplicates based on slug

    name = factory.Sequence(lambda n: f"Learning Section {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    order = factory.Sequence(lambda n: n)


class LearningSubSectionFactory(DjangoModelFactory):
    class Meta:
        model = LearningSubSection
        django_get_or_create = ("slug",)

    section = factory.SubFactory(LearningSectionFactory)
    name = factory.Sequence(lambda n: f"Sub Section {n}")
    slug = factory.LazyAttribute(lambda o: slugify(f"{o.section.slug}-{o.name}"))
    order = factory.Sequence(lambda n: n)


class SkillFactory(DjangoModelFactory):
    class Meta:
        model = Skill
        django_get_or_create = ("slug",)

    subsection = factory.SubFactory(LearningSubSectionFactory)
    name = factory.Sequence(lambda n: f"Skill {n}")
    slug = factory.LazyAttribute(lambda o: slugify(f"{o.subsection.slug}-{o.name}"))


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question

    subsection = factory.SubFactory(LearningSubSectionFactory)
    skill = factory.SubFactory(
        SkillFactory, subsection=factory.SelfAttribute("..subsection")
    )  # Ensure skill belongs to same subsection
    question_text = factory.Sequence(lambda n: f"What is the answer to question {n}?")
    option_a = "Option A Value"
    option_b = "Option B Value"
    option_c = "Option C Value"
    option_d = "Option D Value"
    correct_answer = factory.Iterator(["A", "B", "C", "D"])
    explanation = factory.LazyAttribute(
        lambda o: f"The correct answer is {o.correct_answer} because..."
    )
    hint = "Think carefully."
    difficulty = factory.Iterator([1, 2, 3, 4, 5])
    is_active = True


class UserStarredQuestionFactory(DjangoModelFactory):
    class Meta:
        model = UserStarredQuestion
        # Prevent creating duplicate stars in tests easily
        django_get_or_create = ("user", "question")

    user = factory.SubFactory(
        settings.AUTH_USER_MODEL
    )  # Use the actual User model from settings
    question = factory.SubFactory(QuestionFactory)
