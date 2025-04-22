import factory
from factory.django import DjangoModelFactory
from django.utils.text import slugify
from faker import Faker

from apps.content import models

fake = Faker()


class PageFactory(DjangoModelFactory):
    class Meta:
        model = models.Page

    title = factory.Faker("sentence", nb_words=4)
    # Ensure slug is unique and derived from title
    slug = factory.LazyAttribute(
        lambda o: slugify(o.title + fake.uuid4()[:6])
    )  # Add uuid for uniqueness
    content = factory.Faker("paragraphs", nb=3, ext_word_list=None)
    is_published = True
    icon_class = factory.Maybe(
        "is_published",  # Only add icons sometimes if published
        yes_declaration=factory.Faker("word"),
        no_declaration=None,
    )


class FAQCategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.FAQCategory

    name = factory.Sequence(
        lambda n: f"FAQ Category {n} - {fake.uuid4()[:4]}"
    )  # Ensure uniqueness
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

    name = factory.Sequence(lambda n: f"Partner Type {n} - {fake.uuid4()[:4]}")
    description = factory.Faker("paragraph")
    icon_svg_or_class = factory.Faker("word")
    google_form_link = factory.Faker("url")
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
    # attachment = None # Handled separately if testing uploads


class HomepageFeatureCardFactory(DjangoModelFactory):
    class Meta:
        model = models.HomepageFeatureCard

    title = factory.Faker("catch_phrase")
    text = factory.Faker("sentence")
    svg_image = factory.Maybe(
        "is_active",
        yes_declaration=factory.LazyFunction(lambda: f"<svg>...</svg>"),
        no_declaration=None,
    )
    order = factory.Sequence(lambda n: n)
    is_active = True


class HomepageStatisticFactory(DjangoModelFactory):
    class Meta:
        model = models.HomepageStatistic

    label = factory.Faker("bs")
    value = factory.Faker("numerify", text="###,###+")
    order = factory.Sequence(lambda n: n)
    is_active = True
