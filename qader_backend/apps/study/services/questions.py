import random
import logging
from typing import Optional, List

from django.db.models import QuerySet, Q, Case, When, IntegerField
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.learning.models import Question
from apps.study.models import UserSkillProficiency
from django.contrib.auth import get_user_model

from .constants import DEFAULT_PROFICIENCY_THRESHOLD

User = get_user_model()
logger = logging.getLogger(__name__)


def get_filtered_questions(
    user: User,
    limit: int = 10,
    subsections: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    starred: bool = False,
    not_mastered: bool = False,
    exclude_ids: Optional[List[int]] = None,
    proficiency_threshold: float = DEFAULT_PROFICIENCY_THRESHOLD,
    min_required: int = 1,
) -> QuerySet[Question]:
    """
    Retrieves a randomly ordered QuerySet of active Questions based on various filters.

    Args:
        user: The User for whom to filter (required for 'starred' and 'not_mastered').
        limit: The maximum number of questions to return.
        subsections: Optional list of subsection slugs to filter by.
        skills: Optional list of skill slugs to filter by.
        starred: If True, only return questions starred by the user.
        not_mastered: If True, prioritize questions from skills the user is below
                      the proficiency_threshold in, or skills they haven't attempted yet.
        exclude_ids: Optional list of Question IDs to exclude from the results.
        proficiency_threshold: The score threshold used for the 'not_mastered' filter.
        min_required: If > 0, checks if at least this many questions match the criteria.

    Returns:
        A QuerySet of Question objects, randomly ordered up to the specified limit.
        Returns an empty QuerySet if no matching questions are found or limit is <= 0.
    """
    if limit <= 0:
        return Question.objects.none()

    queryset = Question.objects.with_user_annotations(user=user).filter(is_active=True)

    filters = Q()
    exclude_ids_set = (
        set(int(id) for id in exclude_ids if isinstance(id, int))
        if exclude_ids
        else set()
    )

    if subsections:
        filters &= Q(subsection__slug__in=subsections)
    if skills:
        filters &= Q(skill__slug__in=skills)

    if starred:
        if not user or not user.is_authenticated:
            logger.warning(
                "get_filtered_questions: 'starred=True' filter requested for anonymous user. Returning no questions."
            )
            return Question.objects.none()
        filters &= Q(user_has_starred=True)

    if not_mastered:
        if not user or not user.is_authenticated:
            logger.warning(
                "get_filtered_questions: 'not_mastered' filter requested for anonymous user. Ignoring filter."
            )
        else:
            try:
                low_prof_skill_ids = set(
                    UserSkillProficiency.objects.filter(
                        user=user, proficiency_score__lt=proficiency_threshold
                    ).values_list("skill_id", flat=True)
                )
                attempted_skill_ids = set(
                    UserSkillProficiency.objects.filter(user=user).values_list(
                        "skill_id", flat=True
                    )
                )
                not_mastered_filter = Q(skill_id__in=low_prof_skill_ids) | (
                    Q(skill__isnull=False) & ~Q(skill_id__in=attempted_skill_ids)
                )
                filters &= not_mastered_filter
            except Exception as e:
                logger.error(
                    f"get_filtered_questions: Error applying 'not_mastered' filter for user {user.id}: {e}",
                    exc_info=True,
                )
                logger.warning(
                    f"Could not apply 'not_mastered' filter for user {user.id} due to error. Proceeding without it."
                )

    if filters:
        queryset = queryset.filter(filters)

    if exclude_ids_set:
        queryset = queryset.exclude(id__in=exclude_ids_set)

    if min_required > 0:
        pool_count = queryset.count()
        if pool_count < min_required:
            raise serializers.ValidationError(
                _(
                    "Not enough questions found matching your criteria (found {count}, need at least {min}). Please broaden your filters."
                ).format(count=pool_count, min=min_required)
            )

    all_matching_ids = list(queryset.values_list("id", flat=True))
    count = len(all_matching_ids)
    if count == 0:
        return Question.objects.none()

    num_to_fetch = min(limit, count)
    try:
        random_ids = random.sample(all_matching_ids, num_to_fetch)
    except ValueError as e:
        logger.error(
            f"Error during random sampling in get_filtered_questions: {e}. IDs: {all_matching_ids}, Num: {num_to_fetch}",
            exc_info=True,
        )
        return Question.objects.none()

    preserved_order = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(random_ids)],
        output_field=IntegerField(),
    )

    final_queryset = (
        Question.objects.with_user_annotations(user=user)
        .filter(id__in=random_ids)
        .select_related("subsection", "subsection__section", "skill")
        .order_by(preserved_order)
    )

    logger.info(
        f"get_filtered_questions: Returning {len(random_ids)} annotated questions for user {user.id if user and user.is_authenticated else 'Anonymous'}."
    )
    return final_queryset
