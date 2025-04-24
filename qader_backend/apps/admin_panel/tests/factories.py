import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
from django.core.files.base import ContentFile

from apps.content import models
from apps.users.tests.factories import (
    UserFactory,
)  # Assuming UserFactory is here or adjust path


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
