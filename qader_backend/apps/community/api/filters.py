import django_filters
from django.utils.translation import gettext_lazy as _
from taggit.models import Tag
from django.contrib.auth.models import User
from django.db.models import Q

from apps.community.models import CommunityPost
from apps.users.constants import GradeChoices


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


# NEW FILTERSET FOR PARTNER SEARCH
class UserPartnerFilter(django_filters.FilterSet):
    """
    FilterSet for searching for potential study partners (Users).

    Provides filters for:
    - `name`: Search by full name or username.
    - `grade`: Exact match on the user's grade/level.
    - `section`: Filter by a learning section slug the user has posted in.
    """

    name = django_filters.CharFilter(
        method="filter_by_name", label=_("User's Name or Username")
    )
    grade = django_filters.CharFilter(
        method="filter_by_grades",
        label=_("Grade(s) (comma-separated keys, e.g., high_1,high_2)"),
    )
    # Filter by learning section the user has posted in
    section = django_filters.CharFilter(
        field_name="community_posts__section_filter__slug",
        lookup_expr="iexact",
        label=_("Learning Section Slug"),
        distinct=True,  # Important to avoid duplicate users
    )

    class Meta:
        model = User
        fields = ["name", "grade", "section"]

    def filter_by_name(self, queryset, name, value):
        """
        Filters by full_name (in UserProfile) or username (in User).
        """
        if not value:
            return queryset

        return queryset.filter(
            Q(username__icontains=value) | Q(profile__full_name__icontains=value)
        ).distinct()

    def filter_by_grades(self, queryset, name, value):
        """
        Filters users by one or more grade keys provided as a comma-separated string.
        """
        if not value:
            return queryset

        # Split the string, strip whitespace, and filter out any empty strings
        grade_keys = [key.strip() for key in value.split(",") if key.strip()]
        print(grade_keys)
        if not grade_keys:
            return queryset

        # Optional but recommended: Validate that the provided keys are valid choices.
        # This prevents invalid data from being passed to the DB query.
        valid_keys = GradeChoices.values
        validated_grade_keys = [key for key in grade_keys if key in valid_keys]

        if not validated_grade_keys:
            return queryset

        # Filter the queryset where the user's profile grade is in the list of provided keys.
        # .distinct() is good practice here to ensure a user isn't returned multiple times if somehow possible.
        return queryset.filter(profile__grade__in=validated_grade_keys).distinct()
