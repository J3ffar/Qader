import django_filters
from .models import Challenge, ChallengeStatus


class ChallengeFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=ChallengeStatus.choices)
    challenge_type = django_filters.CharFilter(lookup_expr="iexact")
    # Filter by opponent username (might need custom method)
    opponent_username = django_filters.CharFilter(
        field_name="opponent__username", lookup_expr="iexact"
    )
    is_pending_invite_for_user = django_filters.BooleanFilter(
        method="filter_pending_invite_for_user"
    )

    class Meta:
        model = Challenge
        fields = ["status", "challenge_type", "opponent_username"]

    def filter_pending_invite_for_user(self, queryset, name, value):
        """Filter for challenges pending the logged-in user's acceptance."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(opponent=user, status=ChallengeStatus.PENDING_INVITE)
        return queryset
