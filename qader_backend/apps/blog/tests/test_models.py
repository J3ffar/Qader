import pytest
from django.utils import timezone
from django.utils.text import slugify
from .factories import BlogPostFactory, BlogAdviceRequestFactory, UserFactory
from ..models import AdviceRequestStatusChoices, BlogPost, PostStatusChoices

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


class TestBlogPostModel:
    def test_str_method(self):
        """Test the __str__ method returns the title."""
        post = BlogPostFactory.build(
            title="Test Post Title"
        )  # Use build for simple cases
        assert str(post) == "Test Post Title"

    def test_slug_generation_on_save(self):
        """Test that slug is auto-generated from title if not provided."""
        post = BlogPostFactory(title="A New Post Title", slug="")  # Create in DB
        post.save()  # Trigger save logic again if needed (factory should handle first save)
        post.refresh_from_db()
        assert post.slug == "a-new-post-title"

    def test_slug_uniqueness_on_save(self):
        """Test that slug generation handles conflicts."""
        title = "Unique Title"
        slug = slugify(title)
        BlogPostFactory(title=title, slug=slug)  # First post
        post2 = BlogPostFactory(title=title, slug="")  # Second post with same title
        post2.save()
        post2.refresh_from_db()
        assert post2.slug == f"{slug}-1"  # Expect suffix

        post3 = BlogPostFactory(title=title, slug="")  # Third post
        post3.save()
        post3.refresh_from_db()
        assert post3.slug == f"{slug}-2"

    def test_published_at_set_on_publish(self):
        """Test published_at is set when status changes to PUBLISHED."""
        post = BlogPostFactory(status=PostStatusChoices.DRAFT, published_at=None)
        assert post.published_at is None

        post.status = PostStatusChoices.PUBLISHED
        post.save()
        post.refresh_from_db()
        assert post.published_at is not None
        # Check it's close to now (allow some tolerance)
        assert (timezone.now() - post.published_at).total_seconds() < 5

    def test_published_at_not_set_for_draft(self):
        """Test published_at remains None for draft posts."""
        post = BlogPostFactory(status=PostStatusChoices.DRAFT, published_at=None)
        post.title = "Updated Draft Title"  # Make a change
        post.save()
        post.refresh_from_db()
        assert post.published_at is None

    def test_get_excerpt_method(self):
        """Test the get_excerpt method generates truncated plain text."""
        content = "<p>This is the <b>first</b> sentence.</p><p>Second sentence follows. Third one too.</p>"
        post = BlogPostFactory.build(content=content)

        # Ensure the call uses parentheses () and passes the argument
        excerpt = post.get_excerpt(words=5)  # Correct method call
        assert excerpt == "This is the first sentence."
        assert "<b>" not in excerpt

        # Test default word count
        post_long = BlogPostFactory.build(content="Word " * 50)
        default_excerpt = post_long.get_excerpt()  # Correct method call with default
        assert len(default_excerpt.split()) <= 31

    def test_author_display_name_property(self):
        """Test author_display_name preference order."""
        # 1. No Author
        post_no_author = BlogPostFactory.build(author=None)
        assert post_no_author.author_display_name == "Qader Team"

        # 2. Author with username only (no profile or preferred name)
        user_basic = UserFactory.build(username="basic_user")  # Build only
        post_basic_author = BlogPostFactory.build(author=user_basic)
        assert post_basic_author.author_display_name == "basic_user"

        # 3. Author with profile but no preferred name
        user_profile = UserFactory(username="profile_user")  # Create user
        # Ensure profile exists (factory should handle this, but be explicit)
        user_profile.profile.preferred_name = None
        user_profile.profile.save()
        post_profile_author = BlogPostFactory.build(author=user_profile)
        assert post_profile_author.author_display_name == "profile_user"

        # 4. Author with preferred name
        user_preferred = UserFactory(username="preferred_user")  # Create user
        user_preferred.profile.preferred_name = "Pref Name"
        user_preferred.profile.save()
        post_preferred_author = BlogPostFactory.build(author=user_preferred)
        assert post_preferred_author.author_display_name == "Pref Name"


class TestBlogAdviceRequestModel:
    def test_str_method(self):
        """Test the __str__ method."""
        user = UserFactory.build(username="requester")  # Build user
        request = BlogAdviceRequestFactory.build(
            user=user, status=AdviceRequestStatusChoices.SUBMITTED
        )
        assert str(request) == f"Advice request from requester (Submitted)"

        request.status = AdviceRequestStatusChoices.UNDER_REVIEW
        assert str(request) == f"Advice request from requester (Under Review)"

    # No complex model logic to test here for now
