import django_filters
from django.utils.translation import gettext_lazy as _
from taggit.models import Tag

from apps.community.models import CommunityPost


# Adheres to SRP: This class is solely responsible for defining filtering logic for CommunityPost.
class CommunityPostFilter(django_filters.FilterSet):
    """
    FilterSet for querying Community Posts based on various criteria.

    Provides filters for:
    - `post_type`: Exact match on the post type.
    - `section_filter`: Exact match on the related LearningSection slug.
    - `tags`: Filters posts containing ANY of the provided tag names/slugs (comma-separated).
    - `pinned`: Filters posts based on their pinned status.
    """

    # Use ChoiceFilter for explicit choices based on the model
    post_type = django_filters.ChoiceFilter(
        choices=CommunityPost.PostType.choices, label=_("Post Type")
    )
    # Filter by the slug of the related LearningSection model
    section_filter = django_filters.CharFilter(
        field_name="section_filter__slug",
        lookup_expr="iexact",  # Case-insensitive match for slugs
        label=_("Section Slug"),
    )
    # Custom method for handling comma-separated tag inputs
    tags = django_filters.CharFilter(
        method="filter_by_tags", label=_("Tags (comma-separated names/slugs)")
    )
    pinned = django_filters.BooleanFilter(field_name="is_pinned", label=_("Is Pinned?"))

    class Meta:
        model = CommunityPost
        # Define the fields exposed for filtering
        fields = ["post_type", "section_filter", "tags", "pinned"]

    def filter_by_tags(self, queryset, name, value):
        """
        Filters the queryset to include posts tagged with any of the tags
        provided in the comma-separated 'value' string.
        """
        # Split, strip whitespace, and remove empty strings
        tag_names = [tag.strip() for tag in value.split(",") if tag.strip()]
        if not tag_names:
            # If no valid tags provided, return the original queryset
            return queryset
        # Use Taggit's built-in __in lookup for efficiency
        # distinct() is important when filtering across M2M relationships
        return queryset.filter(tags__name__in=tag_names).distinct()
