import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings

from apps.users.tests.factories import UserFactory  # Use existing UserFactory
from ..models import (
    BlogPost,
    BlogAdviceRequest,
    PostStatusChoices,
    AdviceRequestStatusChoices,
)


class BlogPostFactory(DjangoModelFactory):
    """Factory for the BlogPost model."""

    class Meta:
        model = BlogPost

    author = factory.SubFactory(UserFactory, is_staff=True)
    title = factory.Faker("sentence", nb_words=6)
    slug = factory.LazyAttribute(lambda o: slugify(o.title)[:255])
    content = factory.Faker("paragraphs", nb=3, ext_word_list=None)
    status = PostStatusChoices.DRAFT
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    published_at = None

    # --- Correct Trait Definition ---
    class Params:
        # Trait for published posts
        published = factory.Trait(
            status=PostStatusChoices.PUBLISHED,
            published_at=factory.LazyAttribute(
                lambda o: o.created_at if o.created_at else timezone.now()
            ),
        )
        # Trait for archived posts
        archived = factory.Trait(status=PostStatusChoices.ARCHIVED, published_at=None)
        # REMOVED tags_list = factory.LazyAttribute(lambda _: [])

    @factory.post_generation
    def tags(
        self, create, extracted, **kwargs
    ):  # Changed hook name to 'tags' for clarity
        """Handle adding tags after generation. Use by passing tags=['tag1', 'tag2']"""
        if not create:
            return

        if extracted:  # 'extracted' will contain the list passed as tags=[...]
            for tag in extracted:
                # Access the actual tag manager via self.tags
                self.tags.add(tag)


# --- BlogAdviceRequestFactory remains the same ---
class BlogAdviceRequestFactory(DjangoModelFactory):
    """Factory for the BlogAdviceRequest model."""

    class Meta:
        model = BlogAdviceRequest

    user = factory.SubFactory(UserFactory)
    problem_type = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("paragraph", nb_sentences=3)
    status = AdviceRequestStatusChoices.SUBMITTED
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    response_via = None
    related_support_ticket = None
    related_blog_post = None
