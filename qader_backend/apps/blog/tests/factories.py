import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings

# --- Import SimpleUploadedFile for image factory ---
from django.core.files.uploadedfile import SimpleUploadedFile

# --- End import ---

from apps.users.tests.factories import UserFactory
from ..models import (
    BlogPost,
    BlogAdviceRequest,
    PostStatusChoices,
    AdviceRequestStatusChoices,
)


class BlogPostFactory(DjangoModelFactory):
    class Meta:
        model = BlogPost

    author = factory.SubFactory(UserFactory, is_staff=True)
    title = factory.Faker("sentence", nb_words=6)
    slug = factory.LazyAttribute(lambda o: slugify(o.title)[:255])
    content = factory.Faker(
        "paragraphs", nb=3, ext_word_list=None
    )  # Stored as HTML after admin processing
    status = PostStatusChoices.DRAFT
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    published_at = None

    # --- Add image field ---
    # By default, no image. Can be set in tests: BlogPostFactory(image=...)
    image = None
    # Example of how to provide a dummy image if always needed:
    # image = factory.django.ImageField(filename='test_image.png', color='blue')
    # Or for more control:
    # @factory.lazy_attribute
    # def image(self):
    #     return SimpleUploadedFile(
    #         name='test_image.jpg',
    #         content=b'',  # Empty content for dummy file
    #         content_type='image/jpeg'
    #     )
    # --- End image field ---

    class Params:
        published = factory.Trait(
            status=PostStatusChoices.PUBLISHED,
            published_at=factory.LazyAttribute(
                lambda o: o.created_at if o.created_at else timezone.now()
            ),
        )
        archived = factory.Trait(status=PostStatusChoices.ARCHIVED, published_at=None)

        # Trait to simulate Markdown input for admin tests
        # This won't be saved directly to the model, but used as input for admin serializer tests
        with_markdown_content = factory.Trait(
            raw_markdown_content="# Test Header\n*   List item\n\nSome `code`."
        )

        # Trait for posts with an image
        with_image = factory.Trait(
            image=factory.django.ImageField(
                filename="post_image.png", color="green", width=100, height=100
            )
        )

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)


class BlogAdviceRequestFactory(DjangoModelFactory):
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
