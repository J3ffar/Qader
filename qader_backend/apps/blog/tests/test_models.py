import os
import pytest
from django.utils import timezone
from django.utils.text import slugify

# --- For testing image field on model ---
from django.core.files.uploadedfile import SimpleUploadedFile

# --- End import ---

from .factories import BlogPostFactory, BlogAdviceRequestFactory, UserFactory
from ..models import AdviceRequestStatusChoices, BlogPost, PostStatusChoices

pytestmark = pytest.mark.django_db


class TestBlogPostModel:
    def test_str_method(self):
        post = BlogPostFactory.build(title="Test Post Title")
        assert str(post) == "Test Post Title"

    def test_slug_generation_on_save(self):
        post = BlogPostFactory(title="A New Post Title", slug="")
        post.save()
        post.refresh_from_db()
        assert post.slug == "a-new-post-title"

    def test_slug_uniqueness_on_save(self):
        title = "Unique Title"
        slug = slugify(title)
        BlogPostFactory(title=title, slug=slug)
        post2 = BlogPostFactory(title=title, slug="")
        post2.save()
        post2.refresh_from_db()
        assert post2.slug == f"{slug}-1"

    def test_published_at_set_on_publish(self):
        post = BlogPostFactory(status=PostStatusChoices.DRAFT, published_at=None)
        post.status = PostStatusChoices.PUBLISHED
        post.save()
        post.refresh_from_db()
        assert post.published_at is not None
        assert (timezone.now() - post.published_at).total_seconds() < 5

    def test_excerpt_method(self):
        html_content = "<h1>Header</h1><p>This is the <b>first</b> sentence of the main text.</p><p>Second sentence follows.</p>"
        post = BlogPostFactory.build(content=html_content)
        excerpt = post.excerpt  # Access the property

        # Expected output after processing:
        # 1. Block tags replaced by space: "Header <p>This is the <b>first</b> sentence of the main text. <p>Second sentence follows. "
        # 2. strip_tags: "Header This is the first sentence of the main text. Second sentence follows. "
        # 3. ' '.join(...split()): "Header This is the first sentence of the main text. Second sentence follows."
        # 4. truncatewords_html(..., 30) will then apply.
        # Let's count words: "Header", "This", "is", "the", "first", "sentence", "of", "the", "main", "text.", "Second", "sentence", "follows." (13 words)
        # So, the full text should be returned by truncatewords_html(30)

        expected_excerpt = "Header This is the first sentence of the main text. Second sentence follows."
        assert excerpt == expected_excerpt
        assert "<b>" not in excerpt  # Should still be true
        assert "<h1>" not in excerpt  # Should still be true

        # Test with more words to ensure truncation happens
        long_html_content = "<p>Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8 Word9 Word10 Word11 Word12 Word13 Word14 Word15 Word16 Word17 Word18 Word19 Word20 Word21 Word22 Word23 Word24 Word25 Word26 Word27 Word28 Word29 Word30 Word31 Word32.</p>"
        post_long = BlogPostFactory.build(content=long_html_content)
        long_excerpt = post_long.excerpt
        # Expected: "Word1 ... Word30..." (with the ellipsis if truncatewords_html adds it)
        # `truncatewords_html` adds "..." if truncated.
        words_in_long_excerpt = long_excerpt.replace("...", "").split()
        assert len(words_in_long_excerpt) <= 31

    def test_author_display_name_property(self):
        post_no_author = BlogPostFactory.build(author=None)
        assert post_no_author.author_display_name == "Qader Team"
        # ... other author_display_name tests ...

    def test_image_field_can_be_null(self):
        post = BlogPostFactory(image=None)  # Factory default is None
        post.save()
        post.refresh_from_db()
        assert post.image is None or not post.image  # Should be falsy

    def test_image_field_can_store_image(self):
        dummy_image = SimpleUploadedFile("test.png", b"file_content", "image/png")
        post = BlogPostFactory(image=dummy_image)
        post.save()  # This will save the file
        post.refresh_from_db()
        assert post.image is not None
        assert post.image.name.endswith("test.png")
        # Check if file exists physically
        assert os.path.exists(post.image.path)
        # Clean up the created file
        if os.path.exists(post.image.path):
            os.remove(post.image.path)
            # Also remove parent directories if they were created by upload_to and are now empty
            # This can get complex, so careful management of MEDIA_ROOT for tests is better.


# TestBlogAdviceRequestModel remains the same
class TestBlogAdviceRequestModel:
    def test_str_method(self):
        user = UserFactory.build(username="requester")
        request = BlogAdviceRequestFactory.build(
            user=user, status=AdviceRequestStatusChoices.SUBMITTED
        )
        assert str(request) == f"Advice request from requester (Submitted)"
