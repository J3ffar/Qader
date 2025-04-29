import django_filters
from django.db.models import Q
from apps.users.models import UserProfile


class AdminUserProfileFilter(django_filters.FilterSet):
    """
    FilterSet for AdminUserViewSet to allow filtering by model properties.
    """

    # Define a MethodFilter for the 'level_determined' property
    # The method name must be filter_<field_name>
    level_determined = django_filters.Filter(
        method="filter_level_determined", label="Level Determined"
    )

    class Meta:
        model = UserProfile
        # List the model fields you want to filter on here
        # DO NOT include 'level_determined' in Meta.fields or Meta.filterset_fields
        # The MethodFilter handles filtering for the property
        fields = [
            "user__is_active",
            "role",
            "user__date_joined",
            "subscription_expires_at",
            "has_taken_qiyas_before",
            "gender",
            # Add any other actual model fields you want to filter on here
        ]

    def filter_level_determined(self, queryset, name, value):
        """
        Custom filter method for the 'level_determined' property.
        Filters users based on whether both verbal and quantitative levels are set.
        Value is expected to be a boolean (True/False), often passed as string from URL.
        """
        # Convert the value from query param (string) to boolean
        # Handles 'true', 'false', '1', '0', case-insensitively
        value_bool = str(value).lower() in ["true", "1"]

        if value_bool:
            # level_determined is True if both levels are NOT NULL
            return queryset.filter(
                current_level_verbal__isnull=False,
                current_level_quantitative__isnull=False,
            )
        else:
            # level_determined is False if either level IS NULL
            # Use Q objects for an OR condition
            return queryset.filter(
                Q(current_level_verbal__isnull=True)
                | Q(current_level_quantitative__isnull=True)
            )


# You can add other FilterSets for different admin models here if needed
