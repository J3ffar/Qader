# qader_backend/apps/users/services.py (or create a dedicated apps/limits/services.py)

import logging
from typing import Optional
from django.conf import settings
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from apps.study.models import UserTestAttempt, ConversationMessage, ConversationSession
from apps.api.exceptions import UsageLimitExceeded

# If using constants for limit keys: from .constants import LIMIT_MAX_TEST_ATTEMPTS_PER_TYPE, ...
# Otherwise use the string keys directly.

logger = logging.getLogger(__name__)


class UsageLimiter:
    """
    Provides methods to check if a user action is allowed based on their account limits.
    """

    def __init__(self, user):
        if not user or not user.is_authenticated or not hasattr(user, "profile"):
            # Raise error or handle appropriately if user/profile is invalid
            # For simplicity, we might rely on view permissions to ensure valid user
            raise ValueError(
                "UsageLimiter requires a valid, authenticated user with a profile."
            )

        self.user = user
        self.profile = user.profile
        # Use the helper function from settings
        self.limits = settings.get_limits_for_user(self.user)
        logger.debug(
            f"UsageLimiter initialized for user {user.id} ({self.profile.account_type}). Limits: {self.limits}"
        )

    def _get_limit(self, limit_key: str) -> Optional[int]:
        """Helper to safely get a specific limit value."""
        return self.limits.get(limit_key)  # Defaults to None if key missing

    def check_can_start_test_attempt(self, attempt_type: UserTestAttempt.AttemptType):
        """
        Checks if the user can start a new test attempt of the specified type.

        Raises:
            UsageLimitExceeded: If the limit for this attempt type is reached.
        """
        limit_key = "MAX_TEST_ATTEMPTS_PER_TYPE"  # Or use LIMIT_MAX_TEST_ATTEMPTS_PER_TYPE constant
        limit = self._get_limit(limit_key)

        if limit is not None:  # None means unlimited
            # Count existing attempts of the *specific type* for this user
            current_count = UserTestAttempt.objects.filter(
                user=self.user, attempt_type=attempt_type
            ).count()

            if current_count >= limit:
                logger.warning(
                    f"User {self.user.id} ({self.profile.account_type}) blocked from starting "
                    f"test attempt type '{attempt_type}'. Limit: {limit}, Count: {current_count}."
                )
                raise UsageLimitExceeded(
                    limit_type=f"Test Attempts ({attempt_type.label})",  # Use .label for display
                    limit_value=limit,
                )
        # If limit is None or count < limit, the check passes silently
        logger.debug(
            f"User {self.user.id} permitted to start test attempt type '{attempt_type}'."
        )

    def get_max_questions_per_attempt(self) -> Optional[int]:
        """
        Returns the maximum number of questions allowed per test attempt for the user.
        Returns None if unlimited.
        """
        limit_key = "MAX_QUESTIONS_PER_TEST_ATTEMPT"  # Or use LIMIT_MAX_QUESTIONS_PER_ATTEMPT constant
        return self._get_limit(limit_key)

    def check_can_send_conversation_message(self):
        """
        Checks if the user can send another message in the Learning via Conversation feature.
        This checks the TOTAL number of USER messages across all their sessions.

        Raises:
            UsageLimitExceeded: If the message limit is reached.
        """
        limit_key = "MAX_CONVERSATION_USER_MESSAGES"  # Or use LIMIT_MAX_CONVERSATION_MESSAGES constant
        limit = self._get_limit(limit_key)

        if limit is not None:
            # Count total USER messages across all sessions for this user
            # Note: This assumes the limit is global for the user, not per-session.
            current_count = ConversationMessage.objects.filter(
                session__user=self.user,  # Filter by user via the session FK
                sender_type=ConversationMessage.SenderType.USER,
            ).count()

            if current_count >= limit:
                logger.warning(
                    f"User {self.user.id} ({self.profile.account_type}) blocked from sending "
                    f"conversation message. Limit: {limit}, Count: {current_count}."
                )
                raise UsageLimitExceeded(
                    limit_type="AI Conversation Messages", limit_value=limit
                )
        logger.debug(f"User {self.user.id} permitted to send conversation message.")

    # --- Add more check methods here as needed ---
    # def check_can_star_question(self):
    #     limit = self._get_limit('MAX_STARRED_QUESTIONS')
    #     if limit is not None:
    #         count = UserStarredQuestion.objects.filter(user=self.user).count()
    #         if count >= limit:
    #             raise UsageLimitExceeded(...)
