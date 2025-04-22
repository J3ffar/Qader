import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import gettext_lazy as _

from apps.content import models
from .factories import (
    PageFactory,
    FAQCategoryFactory,
    FAQItemFactory,
    PartnerCategoryFactory,
    HomepageFeatureCardFactory,
    HomepageStatisticFactory,
)

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# === Test PageViewSet ===


def test_retrieve_published_page_by_slug(api_client):
    """Verify retrieving a published page by its slug."""
    page = PageFactory(is_published=True, slug="test-page-slug")
    url = reverse("api:v1:content:page-detail", kwargs={"slug": page.slug})
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data["slug"] == page.slug
    assert response.data["title"] == page.title
    assert "content" in response.data


def test_retrieve_unpublished_page_returns_404(api_client):
    """Verify attempting to retrieve an unpublished page results in 404."""
    page = PageFactory(is_published=False, slug="unpublished-page")
    url = reverse("api:v1:content:page-detail", kwargs={"slug": page.slug})
    response = api_client.get(url)

    assert response.status_code == 404


def test_retrieve_non_existent_page_returns_404(api_client):
    """Verify attempting to retrieve a non-existent slug results in 404."""
    url = reverse("api:v1:content:page-detail", kwargs={"slug": "non-existent-slug"})
    response = api_client.get(url)

    assert response.status_code == 404


# === Test HomepageView ===


def test_homepage_view_structure(api_client):
    """Verify the structure and data aggregation of the homepage endpoint."""
    # Create necessary Page objects with specific slugs
    intro_page = PageFactory(
        slug="homepage-intro", is_published=True, title="Intro Title"
    )
    praise_page = PageFactory(
        slug="homepage-praise", is_published=True, title="Praise Title"
    )
    why_partner_page = PageFactory(
        slug="why-partner", is_published=True, title="Why Partner"
    )
    # Create other homepage elements
    feature1 = HomepageFeatureCardFactory(is_active=True, order=1, title="Feature 1")
    feature2 = HomepageFeatureCardFactory(is_active=True, order=2, title="Feature 2")
    HomepageFeatureCardFactory(is_active=False)  # Inactive one
    stat1 = HomepageStatisticFactory(is_active=True, order=1, label="Stat 1")
    stat2 = HomepageStatisticFactory(is_active=True, order=2, label="Stat 2")
    HomepageStatisticFactory(is_active=False)  # Inactive one

    url = reverse("api:v1:content:homepage")
    response = api_client.get(url)

    assert response.status_code == 200
    data = response.data

    # Check main keys
    assert "intro" in data
    assert "praise" in data
    assert "intro_video_url" in data  # Even if null
    assert "features" in data
    assert "statistics" in data
    assert "why_partner_text" in data

    # Check data correctness (basic checks)
    assert data["intro"]["title"] == intro_page.title
    assert data["praise"]["title"] == praise_page.title
    assert data["why_partner_text"]["title"] == why_partner_page.title
    assert len(data["features"]) == 2  # Only active ones
    assert data["features"][0]["title"] == feature1.title
    assert data["features"][1]["title"] == feature2.title
    assert len(data["statistics"]) == 2  # Only active ones
    assert data["statistics"][0]["label"] == stat1.label
    assert data["statistics"][1]["label"] == stat2.label


def test_homepage_view_handles_missing_pages(api_client):
    """Verify homepage endpoint handles missing specific Page objects gracefully."""
    HomepageFeatureCardFactory.create_batch(2, is_active=True)
    HomepageStatisticFactory.create_batch(1, is_active=True)
    # No pages with slugs 'homepage-intro', 'homepage-praise', 'why-partner' created

    url = reverse("api:v1:content:homepage")
    response = api_client.get(url)

    assert response.status_code == 200
    data = response.data
    assert data["intro"] is None
    assert data["praise"] is None
    assert data["why_partner_text"] is None
    assert len(data["features"]) == 2
    assert len(data["statistics"]) == 1


# === Test FAQListView ===


def test_faq_list_structure_and_filtering(api_client):
    """Verify FAQ list structure, ordering, and filtering of inactive items."""
    cat1 = FAQCategoryFactory(order=1, name="Category One")
    cat2 = FAQCategoryFactory(order=0, name="Category Two")

    # Items for cat1
    item1_cat1 = FAQItemFactory(
        category=cat1, order=1, is_active=True, question="Q1 Cat1"
    )
    FAQItemFactory(category=cat1, order=0, is_active=False, question="Inactive Q Cat1")
    item3_cat1 = FAQItemFactory(
        category=cat1, order=2, is_active=True, question="Q3 Cat1"
    )

    # Items for cat2
    item1_cat2 = FAQItemFactory(
        category=cat2, order=0, is_active=True, question="Q1 Cat2"
    )

    url = reverse("api:v1:content:faq-list")
    response = api_client.get(url)

    assert response.status_code == 200
    data = response.data["results"]  # Assuming pagination is enabled in base settings

    assert len(data) == 2  # Two categories

    # Check order of categories
    assert data[0]["name"] == cat2.name  # Order 0
    assert data[1]["name"] == cat1.name  # Order 1

    # Check items within categories (only active, ordered)
    assert len(data[0]["items"]) == 1
    assert data[0]["items"][0]["question"] == item1_cat2.question

    assert len(data[1]["items"]) == 2  # Only active items
    assert data[1]["items"][0]["question"] == item1_cat1.question  # Order 1
    assert data[1]["items"][1]["question"] == item3_cat1.question  # Order 2


def test_faq_list_search(api_client):
    """Verify search functionality for FAQs."""
    cat1 = FAQCategoryFactory(name="General Questions")
    cat2 = FAQCategoryFactory(name="Technical Issues")
    item1 = FAQItemFactory(
        category=cat1, question="How to subscribe?", answer="Use serial code."
    )
    item2 = FAQItemFactory(
        category=cat2, question="Password reset?", answer="Click forgot password."
    )
    item3 = FAQItemFactory(
        category=cat1, question="What is Qader?", answer="A learning platform."
    )

    url = reverse("api:v1:content:faq-list")

    # Search matching question in cat1
    response = api_client.get(url, {"search": "subscribe"})
    assert response.status_code == 200
    data = response.data["results"]  # Assuming pagination
    assert len(data) == 1
    assert data[0]["name"] == cat1.name
    # *** CORRECTED ASSERTION ***
    # It should return the category, which contains *all* its active items
    assert len(data[0]["items"]) == 2
    # Optionally, verify the specific items are present if needed
    item_questions = {item["question"] for item in data[0]["items"]}
    assert item1.question in item_questions
    assert item3.question in item_questions

    # Search matching answer in cat2
    response = api_client.get(url, {"search": "forgot password"})
    assert response.status_code == 200
    data = response.data["results"]  # Assuming pagination
    assert len(data) == 1
    assert data[0]["name"] == cat2.name
    assert len(data[0]["items"]) == 1
    assert data[0]["items"][0]["question"] == item2.question

    # Search matching category name
    response = api_client.get(url, {"search": "General"})
    assert response.status_code == 200
    data = response.data["results"]  # Assuming pagination
    assert len(data) == 1
    assert data[0]["name"] == cat1.name
    assert len(data[0]["items"]) == 2  # Both items from General category

    # Search term not matching anything
    response = api_client.get(url, {"search": "xyz123"})
    assert response.status_code == 200
    data = response.data["results"]  # Assuming pagination
    assert len(data) == 0


# === Test PartnerCategoryListView ===


def test_partner_category_list(api_client):
    """Verify listing of active partner categories."""
    partner1 = PartnerCategoryFactory(is_active=True, order=1, name="Partner A")
    PartnerCategoryFactory(is_active=False, order=0)  # Inactive
    partner3 = PartnerCategoryFactory(is_active=True, order=0, name="Partner C")

    url = reverse("api:v1:content:partner-category-list")
    response = api_client.get(url)

    assert response.status_code == 200
    data = response.data["results"]  # Assuming pagination

    assert len(data) == 2
    assert data[0]["name"] == partner3.name  # Order 0
    assert data[1]["name"] == partner1.name  # Order 1


# === Test ContactMessageCreateView ===


def test_contact_us_submission_success(api_client):
    """Verify successful submission of the contact form."""
    url = reverse("api:v1:content:contact-us-create")
    payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "subject": "Test Inquiry Subject",
        "message": "This is the test message body.",
    }
    response = api_client.post(url, data=payload)

    assert response.status_code == 201
    # Check the custom success message
    assert response.data["detail"] == str(
        _(
            "Thank you for contacting us. We will get back to you as soon as possible, God willing."
        )
    )  # Use str() for lazy proxy
    assert models.ContactMessage.objects.count() == 1
    message = models.ContactMessage.objects.first()
    assert message.full_name == payload["full_name"]
    assert message.email == payload["email"]
    assert message.subject == payload["subject"]
    assert message.status == models.ContactMessage.STATUS_NEW


def test_contact_us_submission_invalid_email(api_client):
    """Verify validation error for invalid email."""
    url = reverse("api:v1:content:contact-us-create")
    payload = {
        "full_name": "Test User",
        "email": "invalid-email",
        "subject": "Test Inquiry Subject",
        "message": "This is the test message body.",
    }
    response = api_client.post(url, data=payload)

    assert response.status_code == 400
    assert "email" in response.data
    assert models.ContactMessage.objects.count() == 0


def test_contact_us_submission_missing_field(api_client):
    """Verify validation error for missing required field."""
    url = reverse("api:v1:content:contact-us-create")
    payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        # Subject is missing
        "message": "This is the test message body.",
    }
    response = api_client.post(url, data=payload)

    assert response.status_code == 400
    assert "subject" in response.data
    assert models.ContactMessage.objects.count() == 0


def test_contact_us_submission_with_attachment(api_client):
    """Verify successful submission with a file attachment."""
    url = reverse("api:v1:content:contact-us-create")
    # Create a dummy file
    dummy_file = SimpleUploadedFile(
        "test_attachment.txt", b"file_content", content_type="text/plain"
    )
    payload = {
        "full_name": "File User",
        "email": "file@example.com",
        "subject": "Submission With File",
        "message": "Please see attached file.",
        "attachment": dummy_file,
    }
    # Use format='multipart' for file uploads
    response = api_client.post(url, data=payload, format="multipart")

    assert response.status_code == 201
    assert models.ContactMessage.objects.count() == 1
    message = models.ContactMessage.objects.first()
    assert message.attachment is not None
    assert message.attachment.name.endswith("test_attachment.txt")
    # Clean up the uploaded file (Django's test runner usually handles this for FileField in tests)
    message.attachment.delete(save=False)  # Clean up file manually if needed
