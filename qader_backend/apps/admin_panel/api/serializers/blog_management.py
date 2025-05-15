from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from django.conf import settings
from django.contrib.auth import get_user_model
import markdown  # For Markdown to HTML conversion
import bleach  # For HTML sanitization

from apps.blog.models import BlogPost, BlogAdviceRequest
from apps.support.models import SupportTicket

User = get_user_model()

# --- Bleach Configuration ---
# Define allowed HTML tags. Customize this list based on your needs.
# This is a reasonably safe default set for rich text.
ALLOWED_TAGS = [
    "p",
    "strong",
    "em",
    "u",
    "s",
    "strike",
    "del",
    "ins",
    "a",
    "img",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "dd",
    "dt",
    "blockquote",
    "q",
    "cite",
    "pre",
    "code",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "caption",
    "hr",
    "br",
    "sub",
    "sup",
    # Consider 'span' if you need it for specific styling classes
]

# Define allowed attributes for tags. '*' means for all tags.
# Customize this carefully.
ALLOWED_ATTRIBUTES = {
    "*": ["class", "id", "style"],  # Be cautious with 'style'
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height", "style"],
    "q": ["cite"],
    "blockquote": ["cite"],
    "td": ["colspan", "rowspan", "align", "valign"],
    "th": ["colspan", "rowspan", "align", "valign", "scope"],
    "table": ["summary", "width", "border", "cellspacing", "cellpadding"],
}

# Define allowed protocols for links (e.g., in 'href' attributes)
ALLOWED_PROTOCOLS = ["http", "https", "mailto", "ftp"]
# --- End Bleach Configuration ---


class AdminBlogPostSerializer(TaggitSerializer, serializers.ModelSerializer):
    """
    Admin Serializer for full CRUD operations on Blog Posts.
    Content is accepted as Markdown and stored as sanitized HTML.
    """

    tags = TagListSerializerField(
        required=False, help_text="A comma-separated list of tags."
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=True),
        required=False,
        allow_null=True,
        help_text="Select the staff member authoring this post. Defaults to current user if staff.",
    )
    author_username = serializers.CharField(
        source="author.username", read_only=True, required=False
    )
    author_display_name = serializers.CharField(read_only=True)
    image = serializers.ImageField(
        required=False, allow_null=True, use_url=True
    )  # Ensure image field is present

    # The 'content' field will receive Markdown input from the admin.
    # We will override to_internal_value or create/update to process it.

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "author",
            "author_username",
            "author_display_name",
            "title",
            "slug",
            "content",  # Admin inputs Markdown here
            "image",
            "status",
            "published_at",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author_username",
            "author_display_name",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "slug": {
                "required": False,
                "allow_blank": True,
                "help_text": "URL-friendly identifier (auto-generated if left blank).",
            },
            "content": {
                "help_text": "Main content of the post. Write using Markdown. HTML tags like <script> will be removed."
            },
            "published_at": {
                "allow_null": True,
                "required": False,
                "help_text": "Set publish date/time. If unset and status is 'Published', it's set to now.",
            },
        }

    def _process_content(self, markdown_text: str) -> str:
        """Converts Markdown to sanitized HTML."""
        if not markdown_text:
            return ""

        # 1. Convert Markdown to HTML
        #    Common extensions for richer Markdown:
        #    - 'extra': Includes tables, fenced code blocks, footnotes, etc.
        #    - 'nl2br': Converts newlines to <br> tags.
        #    - 'codehilite': For syntax highlighting in code blocks (requires Pygments).
        #    - 'toc': For generating a table of contents.
        #    - 'sane_lists': For more predictable list behavior.
        html_content = markdown.markdown(
            markdown_text,
            extensions=["extra", "nl2br", "codehilite", "toc", "sane_lists"],
        )

        # 2. Sanitize the HTML
        #    `strip=True` removes disallowed tags entirely.
        #    `strip_comments=True` removes HTML comments.
        cleaned_html = bleach.clean(
            html_content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
            strip_comments=True,
        )
        return cleaned_html

    def validate_content(self, value: str) -> str:
        """
        Although we process in create/update, validating here can be a good
        place to ensure the input is reasonable before full processing,
        or to return early if content is empty.
        For now, we'll just pass it through, as main processing is in create/update.
        """
        return value  # Raw Markdown passes through validation for now

    def create(self, validated_data: dict) -> BlogPost:
        markdown_content = validated_data.pop("content", "")
        validated_data["content"] = self._process_content(markdown_content)

        # Default author to current user if they are staff and no author is provided
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_staff:
            if "author" not in validated_data or validated_data["author"] is None:
                validated_data["author"] = request.user

        return super().create(validated_data)

    def update(self, instance: BlogPost, validated_data: dict) -> BlogPost:
        if "content" in validated_data:
            markdown_content = validated_data.pop("content")
            validated_data["content"] = self._process_content(markdown_content)
        return super().update(instance, validated_data)


class AdminBlogAdviceRequestSerializer(serializers.ModelSerializer):
    """
    Admin Serializer for viewing and managing Blog Advice Requests.
    Allows updating status and linking related tickets/posts.
    """

    user_info = serializers.SerializerMethodField(read_only=True)
    related_support_ticket = serializers.PrimaryKeyRelatedField(
        queryset=SupportTicket.objects.all(),
        required=False,
        allow_null=True,
        help_text="Link to the support ticket used to answer this request.",
    )
    related_blog_post = serializers.PrimaryKeyRelatedField(
        queryset=BlogPost.objects.all(),
        required=False,
        allow_null=True,
        help_text="Link to the blog post published based on this request.",
    )

    class Meta:
        model = BlogAdviceRequest
        fields = [
            "id",
            "user",
            "user_info",
            "problem_type",
            "description",
            "status",
            "response_via",
            "related_support_ticket",
            "related_blog_post",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "user_info",
            "problem_type",
            "description",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "status": {"help_text": "Update the status of this advice request."},
            "response_via": {"help_text": "How was this advice request addressed?"},
        }

    def get_user_info(self, obj: BlogAdviceRequest) -> dict:
        if obj.user:
            profile = getattr(obj.user, "profile", None)
            return {
                "id": obj.user.id,
                "username": obj.user.username,
                "email": getattr(obj.user, "email", None),
                "preferred_name": (
                    getattr(profile, "preferred_name", None) if profile else None
                ),
            }
        return {}
