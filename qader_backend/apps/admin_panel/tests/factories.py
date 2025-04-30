import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
from django.core.files.base import ContentFile
from faker import Faker

from apps.content import models
from apps.users.tests.factories import (
    UserFactory,
)
from apps.blog.models import (
    AdviceRequestStatusChoices,
    BlogAdviceRequest,
    BlogPost,
    PostStatusChoices,
)  # Assuming UserFactory is here or adjust path

fake = Faker()


class PageFactory(DjangoModelFactory):
    class Meta:
        model = models.Page
        django_get_or_create = ("slug",)  # Prevent duplicate slugs

    title = factory.Faker("sentence", nb_words=4)
    # Generate slug from title if not provided explicitly
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    content = factory.Faker("paragraphs", nb=3, ext_word_list=None)
    is_published = True
    icon_class = factory.Maybe(
        "is_published", yes_declaration=factory.Faker("word"), no_declaration=None
    )


class FAQCategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.FAQCategory
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"FAQ Category {n}")
    order = factory.Sequence(lambda n: n)


class FAQItemFactory(DjangoModelFactory):
    class Meta:
        model = models.FAQItem

    category = factory.SubFactory(FAQCategoryFactory)
    question = factory.Faker("sentence", nb_words=8, variable_nb_words=True)
    answer = factory.Faker("paragraph", nb_sentences=3)
    is_active = True
    order = factory.Sequence(lambda n: n)


class PartnerCategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.PartnerCategory
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Partnership Type {n}")
    description = factory.Faker("text", max_nb_chars=200)
    icon_svg_or_class = factory.Faker("word")
    google_form_link = factory.Faker("url")
    order = factory.Sequence(lambda n: n)
    is_active = True


class HomepageFeatureCardFactory(DjangoModelFactory):
    class Meta:
        model = models.HomepageFeatureCard

    title = factory.Faker("catch_phrase")
    text = factory.Faker("sentence", nb_words=10)
    svg_image = "<svg>...</svg>"  # Simple placeholder
    order = factory.Sequence(lambda n: n)
    is_active = True


class HomepageStatisticFactory(DjangoModelFactory):
    class Meta:
        model = models.HomepageStatistic

    label = factory.Faker("bs")
    value = factory.Faker("numerify", text="##,###+")
    order = factory.Sequence(lambda n: n)
    is_active = True


class ContactMessageFactory(DjangoModelFactory):
    class Meta:
        model = models.ContactMessage

    full_name = factory.Faker("name")
    email = factory.Faker("email")
    subject = factory.Faker("sentence", nb_words=5)
    message = factory.Faker("text")
    status = models.ContactMessage.STATUS_NEW
    # Example for creating a dummy file attachment
    # attachment = factory.LazyFunction(
    #     lambda: ContentFile(factory.Faker('binary', length=1024).generate(), name='test_attachment.pdf')
    # )


class BlogPostFactory(DjangoModelFactory):
    class Meta:
        model = BlogPost

    # Use UserFactory, ensuring the author is staff if specified, or allow null
    author = factory.SubFactory(UserFactory, is_staff=True)
    title = factory.LazyAttribute(lambda o: fake.sentence(nb_words=6))
    # Auto-generate slug from title, ensuring basic uniqueness for factory runs
    slug = factory.LazyAttribute(
        lambda o: slugify(o.title + fake.pystr(min_chars=3, max_chars=5))
    )
    content = factory.LazyAttribute(lambda o: "\n\n".join(fake.paragraphs(nb=3)))
    status = factory.Iterator(PostStatusChoices.values)
    # published_at is handled by model's save method based on status

    # Add tags after creation
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of tags were passed in, use them
            for tag in extracted:
                self.tags.add(tag)
        else:
            # Add some default tags
            num_tags = fake.random_int(min=1, max=4)
            for _ in range(num_tags):
                self.tags.add(fake.word())


class BlogAdviceRequestFactory(DjangoModelFactory):
    class Meta:
        model = BlogAdviceRequest

    user = factory.SubFactory(UserFactory)  # Any user can create one
    problem_type = factory.LazyAttribute(lambda o: fake.sentence(nb_words=4))
    description = factory.LazyAttribute(lambda o: fake.paragraph(nb_sentences=5))
    status = factory.Iterator(AdviceRequestStatusChoices.values)
    # response_via, related_* fields are typically set by admin later

    # Example: Factory to create a request linked to a ticket
    # class BlogAdviceRequestWithTicketFactory(BlogAdviceRequestFactory):
    #     status = AdviceRequestStatusChoices.ANSWERED_SUPPORT
    #     response_via = AdviceResponseViaChoices.SUPPORT
    #     related_support_ticket = factory.SubFactory(SupportTicketFactory) # Assumes SupportTicketFactory exists

    # Example: Factory to create a request linked to a post
    # class BlogAdviceRequestWithPostFactory(BlogAdviceRequestFactory):
    #     status = AdviceRequestStatusChoices.PUBLISHED_AS_POST
    #     response_via = AdviceResponseViaChoices.BLOG_POST
    #     related_blog_post = factory.SubFactory(BlogPostFactory, status=PostStatusChoices.PUBLISHED)
