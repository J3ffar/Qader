import logging
from typing import Optional, Union

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, APIException

from apps.learning.models import Question
from apps.study.models import UserTestAttempt, UserQuestionAttempt
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


@transaction.atomic
def record_traditional_action_and_get_data(
    user: User,
    test_attempt: UserTestAttempt,
    question: Question,
    action_type: str,
) -> Optional[Union[str, bool]]:
    """
    Records a specific action (hint, eliminate, reveal) in UserQuestionAttempt
    for a traditional session and returns the relevant data (hint text, answer, explanation).
    """
    if (
        test_attempt.attempt_type != UserTestAttempt.AttemptType.TRADITIONAL
        or test_attempt.status != UserTestAttempt.Status.STARTED
        or test_attempt.user != user
    ):
        raise PermissionDenied(_("Action not valid for this session."))

    update_fields = {}
    return_data = None

    if action_type == "hint":
        update_fields, return_data = {"used_hint": True}, question.hint
    elif action_type == "eliminate":
        update_fields, return_data = {"used_elimination": True}, True
    elif action_type == "reveal_answer":
        update_fields, return_data = {"revealed_answer": True}, question.correct_answer
    elif action_type == "reveal_explanation":
        update_fields, return_data = {
            "revealed_explanation": True
        }, question.explanation
    else:
        logger.error(f"Unknown traditional action type '{action_type}' requested.")
        raise ValueError("Invalid action type specified.")

    try:
        _, created = UserQuestionAttempt.objects.update_or_create(
            user=user,
            test_attempt=test_attempt,
            question=question,
            defaults={
                **update_fields,
                "mode": UserQuestionAttempt.Mode.TRADITIONAL,
                "attempted_at": timezone.now(),
            },
        )
        logger.info(
            f"Recorded action ({', '.join(update_fields.keys())}) for Q:{question.id}, Trad. Attempt:{test_attempt.id}, User:{user.id} (Created: {created})"
        )
        return return_data
    except Exception as e:
        logger.exception(
            f"Error recording action ({', '.join(update_fields.keys())}) for Q:{question.id}, User:{user.id}: {e}"
        )
        raise APIException(
            _("Failed to record action."), status.HTTP_500_INTERNAL_SERVER_ERROR
        )
