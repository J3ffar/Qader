import factory
import random  # Import random for the tags hook
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, post_generation
from django.utils.text import slugify

from apps.community.models import CommunityPost, CommunityReply

# Use forward reference string to avoid potential circular import issues
# from apps.learning.models import LearningSection
from apps.users.tests.factories import UserFactory

# --- Learning Section Factory (Robust Fallback/Example) ---
try:
    from apps.learning.tests.factories import LearningSectionFactory
except ImportError:
    print(
        "Warning: LearningSectionFactory not found in apps.learning.tests.factories. Using fallback."
    )

    class LearningSectionFactory(DjangoModelFactory):
        class Meta:
            model = "learning.LearningSection"  # Use string reference
            django_get_or_create = ("slug",)

        name = Faker("catch_phrase")
        slug = factory.LazyAttribute(lambda o: slugify(o.name))
        description = Faker("text", max_nb_chars=150)
        order = factory.Sequence(lambda n: n)


# --- End Learning Section Factory ---


class CommunityPostFactory(DjangoModelFactory):
    class Meta:
        model = CommunityPost
        skip_postgeneration_save = True

    author = SubFactory(UserFactory)
    post_type = factory.Iterator(CommunityPost.PostType.values)

    # Simplified title logic: More likely present for certain types
    @factory.lazy_attribute
    def title(self):
        if self.post_type in [
            CommunityPost.PostType.DISCUSSION,
            CommunityPost.PostType.TIP,
            CommunityPost.PostType.COMPETITION,
        ]:
            return Faker("sentence", nb_words=5).evaluate(
                None, None, extra={"locale": None}
            )
        # For other types (achievement, partner_search), 50% chance of having a title
        elif random.choice([True, False]):
            return Faker("sentence", nb_words=5).evaluate(
                None, None, extra={"locale": None}
            )
        else:
            return None  # Use None if title is absent, matching null=True

    content = Faker("text", max_nb_chars=600)
    section_filter = factory.Maybe(
        Faker("boolean", chance_of_getting_true=50),
        yes_declaration=SubFactory(LearningSectionFactory),
        no_declaration=None,
    )
    is_pinned = False
    is_closed = False

    @post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # Handle passed-in tags
            tags_to_add = []
            if isinstance(extracted, (list, tuple)):
                tags_to_add.extend(tag for tag in extracted if isinstance(tag, str))
            elif isinstance(extracted, str):
                tags_to_add.append(extracted)
            self.tags.add(*tags_to_add)
        else:
            # Use random.sample for default tags without needing Faker.generate
            possible_tags = [
                "python",
                "django",
                "testing",
                "question",
                "help",
                "general",
                "quant",
                "verbal",
            ]
            num_tags = random.randint(1, 3)
            default_tags = random.sample(
                possible_tags, min(num_tags, len(possible_tags))
            )
            self.tags.add(*default_tags)


class CommunityReplyFactory(DjangoModelFactory):
    class Meta:
        model = CommunityReply

    post = SubFactory(CommunityPostFactory)
    author = SubFactory(UserFactory)
    content = Faker("paragraph", nb_sentences=3)
    parent_reply = None
