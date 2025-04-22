import django_filters
from taggit.models import Tag
from apps.community.models import CommunityPost


class CommunityPostFilter(django_filters.FilterSet):
    post_type = django_filters.ChoiceFilter(choices=CommunityPost.PostType.choices)
    section_filter = django_filters.CharFilter(
        field_name="section_filter__slug", lookup_expr="iexact"
    )
    tags = django_filters.CharFilter(method="filter_by_tags")
    pinned = django_filters.BooleanFilter(field_name="is_pinned")

    class Meta:
        model = CommunityPost
        fields = ["post_type", "section_filter", "tags", "pinned"]

    def filter_by_tags(self, queryset, name, value):
        # Assuming tags are comma-separated slugs/names in the query param
        tag_names = [tag.strip() for tag in value.split(",") if tag.strip()]
        if not tag_names:
            return queryset
        # Use Taggit's filter mechanism
        return queryset.filter(tags__name__in=tag_names).distinct()
