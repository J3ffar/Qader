# apps/study/api/serializers.py
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from ..models import UserTestAttempt, UserQuestionAttempt, Test
from apps.learning.models import LearningSection, Question
from apps.learning.api.serializers import (
    QuestionListSerializer,
)  # Reuse for questions list
from apps.users.models import UserProfile

# from apps.users.api.serializers import UserProfileMinimalSerializer # Use for basic user info

import random
import logging

logger = logging.getLogger(__name__)

# --- Level Assessment Serializers ---


class LevelAssessmentStartSerializer(serializers.Serializer):
    """Serializer for starting a level assessment."""

    sections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug",
            queryset=LearningSection.objects.all(),  # Validate slugs exist
        ),
        min_length=1,
        help_text=_(
            "List of section slugs (e.g., ['verbal', 'quantitative']) to include."
        ),
    )
    num_questions = serializers.IntegerField(
        min_value=5,  # Sensible minimum
        max_value=100,  # Sensible maximum
        default=30,
        help_text=_("Number of questions for the assessment."),
    )

    def _get_user_from_context(self):
        """Helper to safely get the authenticated user from context."""
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        # Log error and raise a specific exception if user is not found/authenticated
        logger.error(
            "Authenticated user could not be retrieved from serializer context."
        )
        raise PermissionDenied(
            "User not found or not authenticated in serializer context."
        )

    def validate(self, data):
        user = self._get_user_from_context()  # Use the helper

        # Check profile existence defensively
        try:
            profile = user.profile  # Access the profile
            if profile.level_determined:
                # Use non_field_errors for general validation errors
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "Level assessment already completed. Feature to retake is not yet implemented or requires specific flag."
                            )
                        ]
                    }
                )
        except UserProfile.DoesNotExist:
            # This indicates a setup issue (user exists but profile doesn't)
            logger.error(
                f"UserProfile missing for authenticated user ID: {user.id}. Check signals/factory."
            )
            # Raise validation error
            raise serializers.ValidationError(
                {"non_field_errors": [_("User profile could not be found.")]}
            )
        except AttributeError as e:
            # Catch if user object doesn't even have .profile
            logger.error(f"AttributeError accessing profile for user ID {user.id}: {e}")
            raise serializers.ValidationError(
                {"non_field_errors": [_("Error accessing user profile.")]}
            )

        # Check for ongoing assessments
        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
            # Make the check for assessment_type safer
            test_configuration__assessment_type="level",
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "You already have an ongoing level assessment. Please complete or abandon it first."
                        )
                    ]
                }
            )

        return data

    def create(self, validated_data):
        user = self._get_user_from_context()  # Use the helper
        sections = validated_data["sections"]
        num_questions = validated_data["num_questions"]

        # --- Question Selection Logic ---
        question_pool = Question.objects.filter(
            subsection__section__in=sections, is_active=True
        ).values_list("id", flat=True)

        if not question_pool:
            # Ensure this matches the expected error structure
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("No active questions found for the selected sections.")
                    ]
                }
            )

        actual_num_questions = min(num_questions, len(question_pool))
        if actual_num_questions < num_questions:
            logger.warning(
                f"Requested {num_questions} questions for level assessment for user {user.id}, "
                f"but only {actual_num_questions} were available in sections: {[s.slug for s in sections]}."
            )

        # Convert QuerySet to list for random.sample only if needed
        question_ids = random.sample(list(question_pool), actual_num_questions)

        # --- Create the Test Attempt ---
        config_snapshot = {
            "assessment_type": "level",
            "sections": [s.slug for s in sections],
            "requested_num_questions": num_questions,
            "actual_num_questions": actual_num_questions,
        }

        test_attempt = UserTestAttempt.objects.create(
            user=user,
            test_configuration=config_snapshot,
            question_ids=question_ids,
            status=UserTestAttempt.Status.STARTED,
        )

        # Retrieve the actual Question objects to return
        # Ensure questions are returned in a consistent order if required by frontend
        # Fetching by filter(id__in=...) doesn't guarantee order. Fetch and sort if needed.
        questions = Question.objects.filter(pk__in=question_ids)
        questions_dict = {q.id: q for q in questions}
        ordered_questions = [
            questions_dict[qid] for qid in question_ids if qid in questions_dict
        ]

        # Return data needed by the frontend
        return {
            "attempt_id": test_attempt.id,
            "questions": ordered_questions,  # Return the ordered list/queryset
        }


class LevelAssessmentAnswerSerializer(serializers.Serializer):
    """Serializer for individual answers within the submission."""

    question_id = serializers.IntegerField()
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )


class LevelAssessmentSubmitSerializer(serializers.Serializer):
    """Serializer for submitting all answers for a level assessment attempt."""

    answers = LevelAssessmentAnswerSerializer(many=True)

    def validate(self, data):
        user = self.context["request"].user
        view = self.context["view"]
        attempt_id = view.kwargs.get("attempt_id")

        try:
            test_attempt = UserTestAttempt.objects.get(pk=attempt_id, user=user)
        except UserTestAttempt.DoesNotExist:
            raise serializers.ValidationError(
                _("Assessment attempt not found or does not belong to you.")
            )

        if test_attempt.status != UserTestAttempt.Status.STARTED:
            raise serializers.ValidationError(
                _(
                    "This assessment attempt is not active or has already been submitted."
                )
            )

        submitted_question_ids = {answer["question_id"] for answer in data["answers"]}
        expected_question_ids = set(test_attempt.question_ids)

        if submitted_question_ids != expected_question_ids:
            missing = expected_question_ids - submitted_question_ids
            extra = submitted_question_ids - expected_question_ids
            errors = {}
            if missing:
                errors["missing_answers_for_ids"] = list(missing)
            if extra:
                errors["unexpected_answers_for_ids"] = list(extra)
            raise serializers.ValidationError(
                {
                    "answers": _(
                        "Mismatch between submitted answers and questions in the assessment attempt."
                    ),
                    **errors,
                }
            )

        # Add test_attempt to context for the save method
        self.context["test_attempt"] = test_attempt
        return data

    @transaction.atomic  # Ensure all updates happen or none do
    def save(self, **kwargs):
        test_attempt = self.context["test_attempt"]
        answers_data = self.validated_data["answers"]
        user = self.context["request"].user

        question_map = {q.id: q for q in test_attempt.get_questions_queryset()}

        question_attempts = []
        for answer_data in answers_data:
            question_id = answer_data["question_id"]
            question = question_map.get(question_id)
            if not question:
                # This should theoretically be caught by validation, but double-check
                logger.error(
                    f"Question ID {question_id} in submit data but not found for test attempt {test_attempt.id}"
                )
                continue  # Or raise error

            is_correct = answer_data["selected_answer"] == question.correct_answer

            attempt = UserQuestionAttempt(
                user=user,
                question=question,
                test_attempt=test_attempt,
                selected_answer=answer_data["selected_answer"],
                time_taken_seconds=answer_data.get("time_taken_seconds"),
                mode=UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
                is_correct=is_correct,
            )
            question_attempts.append(attempt)

        # Bulk create for efficiency
        UserQuestionAttempt.objects.bulk_create(question_attempts)

        # --- Calculate Scores ---
        # Reload attempts from DB to be safe
        final_attempts = test_attempt.question_attempts.all()
        total_questions = final_attempts.count()
        correct_answers = final_attempts.filter(is_correct=True).count()

        # Calculate Overall Score
        overall_score = (
            (correct_answers / total_questions * 100) if total_questions > 0 else 0.0
        )

        # Calculate Section Scores (Verbal/Quantitative)
        verbal_correct = 0
        verbal_total = 0
        quant_correct = 0
        quant_total = 0
        # Store results per subsection for summary
        results_summary = {}

        for attempt in final_attempts:
            subsection = attempt.question.subsection
            section_slug = (
                subsection.section.slug
                if subsection and subsection.section
                else "unknown"
            )
            subsection_slug = subsection.slug if subsection else "unknown"

            # Initialize subsection summary if not present
            if subsection_slug not in results_summary:
                results_summary[subsection_slug] = {
                    "correct": 0,
                    "total": 0,
                    "name": subsection.name if subsection else "Unknown",
                }

            results_summary[subsection_slug]["total"] += 1

            if section_slug == "verbal":
                verbal_total += 1
                if attempt.is_correct:
                    verbal_correct += 1
                    results_summary[subsection_slug]["correct"] += 1
            elif section_slug == "quantitative":
                quant_total += 1
                if attempt.is_correct:
                    quant_correct += 1
                    results_summary[subsection_slug]["correct"] += 1
            # Handle other sections if they exist

        verbal_score = (
            (verbal_correct / verbal_total * 100) if verbal_total > 0 else 0.0
        )
        quantitative_score = (
            (quant_correct / quant_total * 100) if quant_total > 0 else 0.0
        )

        # Calculate subsection scores for the summary
        for slug, data in results_summary.items():
            data["score"] = (
                (data["correct"] / data["total"] * 100) if data["total"] > 0 else 0.0
            )

        # --- Update Test Attempt ---
        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()
        test_attempt.score_percentage = round(overall_score, 2)
        test_attempt.score_verbal = round(verbal_score, 2)
        test_attempt.score_quantitative = round(quantitative_score, 2)
        test_attempt.results_summary = results_summary
        test_attempt.save()

        # --- Update User Profile ---
        profile = user.profile
        profile.current_level_verbal = test_attempt.score_verbal
        profile.current_level_quantitative = test_attempt.score_quantitative
        # profile.level_determined = True  # Mark level as determined
        profile.save()

        # --- Award Points ---
        # TODO: Implement PointLog creation later (needs Gamification app)
        # points_earned = settings.POINTS_LEVEL_ASSESSMENT_COMPLETED # Example setting
        # PointLog.objects.create(user=user, points_change=points_earned, reason_code="LEVEL_ASSESSMENT_COMPLETED", ...)

        # --- Return Result Data ---
        return {
            "attempt_id": test_attempt.id,
            "results": {
                "overall_score": test_attempt.score_percentage,
                "verbal_score": test_attempt.score_verbal,
                "quantitative_score": test_attempt.score_quantitative,
                "proficiency_summary": results_summary,  # More detailed than just scores
                "message": _(
                    "Your level assessment is complete. Your personalized learning path is now adjusted!"
                ),
            },
            "updated_profile": {  # Return relevant updated fields
                "current_level_verbal": profile.current_level_verbal,
                "current_level_quantitative": profile.current_level_quantitative,
                "level_determined": profile.level_determined,
            },
        }


class LevelAssessmentResponseSerializer(serializers.Serializer):
    """Response serializer for the start assessment endpoint."""

    attempt_id = serializers.IntegerField()
    questions = QuestionListSerializer(many=True, read_only=True)


class LevelAssessmentResultSerializer(serializers.Serializer):
    """Response serializer for the submit assessment endpoint."""

    attempt_id = serializers.IntegerField()
    results = serializers.JSONField()  # Contains scores and summary
    updated_profile = serializers.JSONField()  # Contains updated profile fields
