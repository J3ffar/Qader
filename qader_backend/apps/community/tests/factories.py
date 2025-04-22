# apps/community/tests/factories.py

import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, post_generation

from apps.community.models import CommunityPost, CommunityReply, LearningSection
from apps.users.tests.factories import UserFactory

# Assuming a LearningSectionFactory exists or create a basic one here if needed
try:
    # Attempt to import from learning app's factories first
    from apps.learning.tests.factories import LearningSectionFactory
except ImportError:
    # Define a basic fallback LearningSectionFactory if not found
    class LearningSectionFactory(DjangoModelFactory):
        class Meta:
            model = LearningSection
            django_get_or_create = ("slug",)  # Avoid creating duplicates

        name = Faker("bs")
        slug = Faker("slug")
        order = factory.Sequence(lambda n: n)


class CommunityPostFactory(DjangoModelFactory):
    class Meta:
        model = CommunityPost

    author = SubFactory(UserFactory)
    post_type = factory.Iterator(CommunityPost.PostType.choices, getter=lambda c: c[0])
    title = factory.Maybe(
        # Provide title only for certain types or randomly
        LazyAttribute(
            lambda o: o.post_type
            in [CommunityPost.PostType.DISCUSSION, CommunityPost.PostType.TIP]
        ),
        Faker("sentence", nb_words=6),
        "",  # Empty string if no title
    )
    content = Faker("text", max_nb_chars=500)
    section_filter = factory.Maybe(
        # 50% chance of having a section filter if learning app is integrated
        Faker("boolean", chance_of_getting_true=50),
        SubFactory(LearningSectionFactory),
        None,
    )
    is_pinned = False
    is_closed = False

    # Handle tags using post_generation hook
    @post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of tags were passed in, use them
            for tag in extracted:
                self.tags.add(tag)
        else:
            # Add some default tags maybe?
            # self.tags.add('test', 'community')
            pass


class CommunityReplyFactory(DjangoModelFactory):
    class Meta:
        model = CommunityReply

    post = SubFactory(CommunityPostFactory)
    author = SubFactory(UserFactory)
    content = Faker("text", max_nb_chars=200)
    parent_reply = None  # Default to top-level reply
