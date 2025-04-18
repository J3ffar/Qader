# qader_backend/apps/study/api/serializers/statistics.py
from rest_framework import serializers
from django.db.models import Count, Sum, Case, When, IntegerField, FloatField, Q
import logging

from apps.study.models import UserSkillProficiency, UserTestAttempt, UserQuestionAttempt
from apps.api.utils import get_user_from_context  # Import the helper

logger = logging.getLogger(__name__)

# --- Constants ---
RECENT_TESTS_LIMIT = 10

# --- Statistics Serializers ---


class OverallMasterySerializer(serializers.Serializer):
    """Represents the overall mastery levels."""

    verbal = serializers.FloatField(allow_null=True)
    quantitative = serializers.FloatField(allow_null=True)


class StudyStreaksSerializer(serializers.Serializer):
    """Represents study streak information."""

    current_days = serializers.IntegerField()
    longest_days = serializers.IntegerField()


class ActivitySummarySerializer(serializers.Serializer):
    """Represents overall activity counts."""

    total_questions_answered = serializers.IntegerField()
    total_tests_completed = serializers.IntegerField()


class OverallStatsSerializer(serializers.Serializer):
    """Combines overall statistics."""

    mastery_level = OverallMasterySerializer()
    study_streaks = StudyStreaksSerializer()
    activity_summary = ActivitySummarySerializer()


class SubsectionPerformanceSerializer(serializers.Serializer):
    """Represents performance metrics for a specific subsection."""

    name = serializers.CharField()
    accuracy = serializers.FloatField(allow_null=True)
    attempts = serializers.IntegerField()


class SectionPerformanceSerializer(serializers.Serializer):
    """Represents performance metrics for a main section (Verbal/Quant)."""

    name = serializers.CharField()
    overall_accuracy = serializers.FloatField(allow_null=True)
    # Use DictField for variable subsection slugs as keys
    subsections = serializers.DictField(child=SubsectionPerformanceSerializer())


class SkillProficiencySummarySerializer(serializers.ModelSerializer):
    """Represents proficiency for a single skill."""

    skill_slug = serializers.SlugField(source="skill.slug", read_only=True)
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    accuracy = serializers.SerializerMethodField()
    attempts = serializers.IntegerField(source="attempts_count", read_only=True)

    class Meta:
        model = UserSkillProficiency
        fields = [
            "skill_slug",
            "skill_name",
            "proficiency_score",
            "accuracy",
            "attempts",
        ]
        read_only_fields = fields

    def get_accuracy(self, obj):
        if obj.attempts_count > 0:
            # Calculate accuracy directly from counts for consistency
            return round((obj.correct_count / obj.attempts_count * 100), 1)
        return None


class TestHistorySummarySerializer(serializers.ModelSerializer):
    """Represents a summary of a single completed test attempt for history charts."""

    attempt_id = serializers.IntegerField(source="id", read_only=True)
    date = serializers.DateTimeField(
        source="end_time", read_only=True
    )  # Use end_time for completed tests
    type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    overall_score = serializers.FloatField(source="score_percentage", read_only=True)
    verbal_score = serializers.FloatField(source="score_verbal", read_only=True)
    quantitative_score = serializers.FloatField(
        source="score_quantitative", read_only=True
    )

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "date",
            "type",
            "overall_score",
            "verbal_score",
            "quantitative_score",
        ]
        read_only_fields = fields


class UserStatisticsSerializer(serializers.Serializer):
    """Serializer for the main user statistics endpoint."""

    overall = serializers.SerializerMethodField()
    performance_by_section = serializers.SerializerMethodField()
    skill_proficiency_summary = serializers.SerializerMethodField()
    test_history_summary = serializers.SerializerMethodField()

    def _get_user_profile_safe(self):
        """Safely retrieves the user profile, returning None on failure."""
        try:
            # Cache profile on the serializer instance for the request duration
            if not hasattr(self, "_cached_user_profile"):
                user = get_user_from_context(self.context)  # Use helper
                self._cached_user_profile = user.profile
            return self._cached_user_profile
        except Exception as e:
            logger.error(f"Statistics: Failed to get profile: {e}", exc_info=True)
            # Raising validation error propagates a 400 to the client, which is appropriate
            raise serializers.ValidationError("User profile not found or inaccessible.")

    def get_overall(self, obj):
        """Gathers overall statistics."""
        profile = (
            self._get_user_profile_safe()
        )  # Will raise ValidationError if profile missing
        user = profile.user

        try:
            total_questions = UserQuestionAttempt.objects.filter(user=user).count()
            total_tests = UserTestAttempt.objects.filter(
                user=user, status=UserTestAttempt.Status.COMPLETED
            ).count()

            mastery_data = {
                "verbal": profile.current_level_verbal,
                "quantitative": profile.current_level_quantitative,
            }
            streak_data = {
                "current_days": profile.current_streak_days,
                "longest_days": profile.longest_streak_days,
            }
            activity_data = {
                "total_questions_answered": total_questions,
                "total_tests_completed": total_tests,
            }

            # Use the specific serializers defined above
            serializer = OverallStatsSerializer(
                {
                    "mastery_level": mastery_data,
                    "study_streaks": streak_data,
                    "activity_summary": activity_data,
                }
            )
            return serializer.data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_overall for user {user.id}: {e}"
            )
            return None  # Return None for unexpected errors within this calculation

    def get_performance_by_section(self, obj):
        """Calculates performance aggregated by section and subsection."""
        profile = self._get_user_profile_safe()
        user = profile.user

        try:
            performance_data = {}
            # Efficient aggregation at the database level
            attempt_aggregates = (
                UserQuestionAttempt.objects.filter(
                    user=user,
                    question__subsection__isnull=False,
                    question__subsection__section__isnull=False,
                )
                .values(
                    "question__subsection__section__slug",
                    "question__subsection__section__name",
                    "question__subsection__slug",
                    "question__subsection__name",
                )
                .annotate(
                    total_attempts=Count("id"),
                    correct_attempts=Sum(
                        Case(
                            When(is_correct=True, then=1),
                            default=0,
                            output_field=IntegerField(),
                        )
                    ),
                )
                .order_by(
                    "question__subsection__section__slug", "question__subsection__slug"
                )
            )

            # Process aggregates into nested structure
            for agg in attempt_aggregates:
                section_slug = agg["question__subsection__section__slug"]
                section_name = agg["question__subsection__section__name"]
                sub_slug = agg["question__subsection__slug"]
                sub_name = agg["question__subsection__name"]
                attempts = agg["total_attempts"]
                correct = agg["correct_attempts"]

                if section_slug not in performance_data:
                    performance_data[section_slug] = {
                        "name": section_name,
                        "total_section_attempts": 0,
                        "correct_section_attempts": 0,
                        "subsections": {},
                    }

                sub_accuracy = (
                    round((correct / attempts * 100), 1) if attempts > 0 else None
                )
                performance_data[section_slug]["subsections"][sub_slug] = {
                    "name": sub_name,
                    "accuracy": sub_accuracy,
                    "attempts": attempts,
                }
                performance_data[section_slug]["total_section_attempts"] += attempts
                performance_data[section_slug]["correct_section_attempts"] += correct

            # Calculate overall section accuracy and serialize
            final_performance_data = {}
            for slug, data in performance_data.items():
                total_attempts = data["total_section_attempts"]
                correct_attempts = data["correct_section_attempts"]
                overall_accuracy = (
                    round((correct_attempts / total_attempts * 100), 1)
                    if total_attempts > 0
                    else None
                )

                # Serialize using SectionPerformanceSerializer
                section_serializer = SectionPerformanceSerializer(
                    {
                        "name": data["name"],
                        "overall_accuracy": overall_accuracy,
                        "subsections": data[
                            "subsections"
                        ],  # Pass the processed subsection dict
                    }
                )
                # No need to call is_valid here, assuming internal data is correct
                final_performance_data[slug] = section_serializer.data

            return final_performance_data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_performance_by_section for user {user.id}: {e}"
            )
            return None

    def get_skill_proficiency_summary(self, obj):
        """Retrieves skill proficiency data."""
        profile = self._get_user_profile_safe()
        user = profile.user

        try:
            proficiencies = (
                UserSkillProficiency.objects.filter(user=user, skill__isnull=False)
                .select_related("skill")
                .order_by("-proficiency_score", "skill__name")  # Order for consistency
            )
            serializer = SkillProficiencySummarySerializer(proficiencies, many=True)
            return serializer.data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_skill_proficiency_summary for user {user.id}: {e}"
            )
            return None

    def get_test_history_summary(self, obj):
        """Retrieves a summary of the N most recent completed tests."""
        profile = self._get_user_profile_safe()
        user = profile.user

        try:
            recent_tests = UserTestAttempt.objects.filter(
                user=user, status=UserTestAttempt.Status.COMPLETED
            ).order_by("-end_time")[:RECENT_TESTS_LIMIT]

            serializer = TestHistorySummarySerializer(recent_tests, many=True)
            return serializer.data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_test_history_summary for user {user.id}: {e}"
            )
            return None
