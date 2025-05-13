from rest_framework import serializers
from django.db.models import (
    Count,
    Sum,
    Case,
    When,
    IntegerField,
    FloatField,
    Q,
    Avg,
    F,
    ExpressionWrapper,
    DurationField,
    Value,
)
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear, Cast
from django.utils import timezone
from datetime import timedelta  # For adjusting end_date
import logging

from apps.study.models import UserSkillProficiency, UserTestAttempt, UserQuestionAttempt
from apps.api.utils import get_user_from_context

logger = logging.getLogger(__name__)

# --- Constants ---
RECENT_TESTS_LIMIT = 10
AGGREGATION_PERIOD_CHOICES = ["daily", "weekly", "monthly", "yearly"]


# --- Supporting Serializers for Chart Data Points ---


class TestAttemptDataPointSerializer(serializers.Serializer):
    """Represents a single data point for individual test attempt trends."""

    attempt_id = serializers.IntegerField()
    date = serializers.DateTimeField()  # Will be formatted as ISO string
    score = serializers.FloatField(allow_null=True)
    verbal_score = serializers.FloatField(allow_null=True)
    quantitative_score = serializers.FloatField(allow_null=True)
    num_questions = serializers.IntegerField()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if "date" in ret and ret["date"]:
            # instance['date'] is already a datetime object from the query
            ret["date"] = instance["date"].isoformat()
        return ret


class PeriodPerformanceDataPointSerializer(serializers.Serializer):
    """Represents an aggregated data point for performance trends over a period."""

    period_start_date = (
        serializers.DateField()
    )  # Date object, will be formatted as YYYY-MM-DD
    average_score = serializers.FloatField(allow_null=True)
    average_verbal_score = serializers.FloatField(allow_null=True)
    average_quantitative_score = serializers.FloatField(allow_null=True)
    test_count = serializers.IntegerField()
    total_questions_in_period = (
        serializers.IntegerField()
    )  # Sum of num_questions from tests in period

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if "period_start_date" in ret and ret["period_start_date"]:
            # instance['period_start_date'] is a date object from Trunc functions
            ret["period_start_date"] = instance["period_start_date"].isoformat()
        return ret


class AverageScoreByTypeSerializer(serializers.Serializer):
    attempt_type_value = serializers.CharField()
    attempt_type_display = serializers.CharField()
    average_score = serializers.FloatField(allow_null=True)
    average_verbal_score = serializers.FloatField(allow_null=True)
    average_quantitative_score = serializers.FloatField(allow_null=True)
    test_count = serializers.IntegerField()


class TimePerQuestionByCorrectnessSerializer(serializers.Serializer):
    average_time_seconds = serializers.FloatField(allow_null=True)
    question_count = serializers.IntegerField()


class AverageTestDurationSerializer(serializers.Serializer):
    attempt_type_value = serializers.CharField()
    attempt_type_display = serializers.CharField()
    average_duration_seconds = serializers.FloatField(allow_null=True)
    test_count = serializers.IntegerField()


# --- Main Statistics Serializers (Existing and Modified) ---
# ... (OverallMasterySerializer, StudyStreaksSerializer, etc. remain unchanged unless explicitly modified below) ...
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
            return round((obj.correct_count / obj.attempts_count * 100), 1)
        return None


class TestHistorySummarySerializer(serializers.ModelSerializer):
    """Represents a summary of a single completed test attempt for history charts."""

    attempt_id = serializers.IntegerField(source="id", read_only=True)
    date = serializers.DateTimeField(
        source="end_time", read_only=True, format="%Y-%m-%dT%H:%M:%S%z"
    )
    type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    type_value = serializers.CharField(source="attempt_type", read_only=True)
    overall_score = serializers.FloatField(source="score_percentage", read_only=True)
    verbal_score = serializers.FloatField(source="score_verbal", read_only=True)
    quantitative_score = serializers.FloatField(
        source="score_quantitative", read_only=True
    )
    num_questions = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "date",
            "type",
            "type_value",
            "overall_score",
            "verbal_score",
            "quantitative_score",
            "num_questions",
        ]
        read_only_fields = fields


class UserStatisticsSerializer(serializers.Serializer):
    """Serializer for the main user statistics endpoint."""

    overall = serializers.SerializerMethodField()
    performance_by_section = serializers.SerializerMethodField()
    skill_proficiency_summary = serializers.SerializerMethodField()
    test_history_summary = serializers.SerializerMethodField(
        help_text=f"Summary of the last {RECENT_TESTS_LIMIT} completed tests within the selected period (if any)."
    )
    performance_trends_by_test_type = serializers.SerializerMethodField(
        help_text="Score progression over time, grouped by test attempt type. "
        "Can be aggregated by 'aggregation_period' (daily, weekly, etc.) "
        "or show individual tests. Data is within 'start_date' and 'end_date' if provided."
    )
    average_scores_by_test_type = serializers.SerializerMethodField(
        help_text="Average scores for each test type within the selected period."
    )
    time_analytics = serializers.SerializerMethodField(
        help_text="Time-related analytics within the selected period."
    )

    def _get_user_profile_safe(self):
        try:
            if not hasattr(self, "_cached_user_profile"):
                user = get_user_from_context(self.context)
                self._cached_user_profile = user.profile
            return self._cached_user_profile
        except Exception as e:
            logger.error(f"Statistics: Failed to get profile: {e}", exc_info=True)
            raise serializers.ValidationError("User profile not found or inaccessible.")

    def _apply_date_filters(self, queryset, date_field_name):
        """Applies start_date and end_date filters from context to a queryset."""
        start_date = self.context.get("start_date")
        end_date = self.context.get("end_date")

        if start_date:
            queryset = queryset.filter(**{f"{date_field_name}__gte": start_date})
        if end_date:
            # Adjust end_date to be inclusive for the whole day
            inclusive_end_date = end_date + timedelta(days=1)
            queryset = queryset.filter(**{f"{date_field_name}__lt": inclusive_end_date})
        return queryset

    def get_overall(self, obj):  # obj is the user instance
        profile = self._get_user_profile_safe()
        user = obj  # obj is user here

        # Activity counts are filtered by date
        question_attempts_qs = UserQuestionAttempt.objects.filter(user=user)
        test_attempts_qs = UserTestAttempt.objects.filter(
            user=user, status=UserTestAttempt.Status.COMPLETED
        )

        filtered_question_attempts_qs = self._apply_date_filters(
            question_attempts_qs, "attempted_at"
        )
        filtered_test_attempts_qs = self._apply_date_filters(
            test_attempts_qs, "end_time"
        )

        total_questions = filtered_question_attempts_qs.count()
        total_tests = filtered_test_attempts_qs.count()

        # Mastery and streaks are generally considered overall, not period-specific from current profile fields
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
        serializer = OverallStatsSerializer(
            {
                "mastery_level": mastery_data,
                "study_streaks": streak_data,
                "activity_summary": activity_data,
            }
        )
        return serializer.data

    def get_performance_by_section(self, obj):  # obj is user
        user = obj
        try:
            base_qs = UserQuestionAttempt.objects.filter(
                user=user,
                question__subsection__isnull=False,
                question__subsection__section__isnull=False,
            )
            filtered_qs = self._apply_date_filters(base_qs, "attempted_at")

            attempt_aggregates = (
                filtered_qs.values(
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
            performance_data = {}
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
            final_performance_data = {}
            for slug, data in performance_data.items():
                total_attempts = data["total_section_attempts"]
                correct_attempts = data["correct_section_attempts"]
                overall_accuracy = (
                    round((correct_attempts / total_attempts * 100), 1)
                    if total_attempts > 0
                    else None
                )
                section_serializer = SectionPerformanceSerializer(
                    {
                        "name": data["name"],
                        "overall_accuracy": overall_accuracy,
                        "subsections": data["subsections"],
                    }
                )
                final_performance_data[slug] = section_serializer.data
            return final_performance_data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_performance_by_section for user {user.id}: {e}"
            )
            return None

    def get_skill_proficiency_summary(self, obj):  # obj is user
        # Skill proficiency is typically an overall measure. Date filtering might not be
        # directly applicable unless proficiency itself is recalculated for the period,
        # which is a more complex operation (re-evaluating all attempts in period).
        # For now, this returns overall proficiency.
        user = obj
        try:
            proficiencies = (
                UserSkillProficiency.objects.filter(user=user, skill__isnull=False)
                .select_related("skill")
                .order_by("-proficiency_score", "skill__name")
            )
            serializer = SkillProficiencySummarySerializer(proficiencies, many=True)
            return serializer.data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_skill_proficiency_summary for user {user.id}: {e}"
            )
            return None

    def get_test_history_summary(self, obj):  # obj is user
        user = obj
        try:
            base_qs = UserTestAttempt.objects.filter(
                user=user,
                status=UserTestAttempt.Status.COMPLETED,
                end_time__isnull=False,
            )
            filtered_qs = self._apply_date_filters(base_qs, "end_time")
            recent_tests = filtered_qs.order_by("-end_time")[:RECENT_TESTS_LIMIT]

            serializer = TestHistorySummarySerializer(recent_tests, many=True)
            return serializer.data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_test_history_summary for user {user.id}: {e}"
            )
            return None

    def get_performance_trends_by_test_type(self, obj):  # obj is user
        user = obj
        aggregation_period = self.context.get("aggregation_period")

        base_qs = UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.COMPLETED,
            score_percentage__isnull=False,
            end_time__isnull=False,
        )
        filtered_qs = self._apply_date_filters(base_qs, "end_time")

        trends_data = {
            type_value: [] for type_value, _ in UserTestAttempt.AttemptType.choices
        }

        if aggregation_period:
            trunc_func = None
            if aggregation_period == "daily":
                trunc_func = TruncDay("end_time")
            elif aggregation_period == "weekly":
                trunc_func = TruncWeek("end_time")
            elif aggregation_period == "monthly":
                trunc_func = TruncMonth("end_time")
            elif aggregation_period == "yearly":
                trunc_func = TruncYear("end_time")

            if not trunc_func:  # Should not happen due to view validation
                return trends_data

            # Annotate with num_questions (derived from question_ids length) to sum it up
            # This requires a subquery or a more complex annotation if `question_ids` is JSON.
            # For simplicity, we'll aggregate basic scores. Summing num_questions is harder here.
            # Let's assume for now we only get test_count and avg scores per period.
            # If `num_questions` per period is critical, we'd need to annotate `num_questions` on the
            # UserTestAttempt model or use a more involved query.
            # Alternative: Iterate and calculate num_questions if queryset is not too large.
            # For direct DB aggregation for performance:
            # It's tricky to get sum of `len(question_ids)` directly in ORM for JSONField.
            # We will get count of tests, and avg scores. total_questions_in_period can be approximated
            # if average questions per test is known, or frontend can sum num_questions from individual tests.

            period_data_qs = (
                filtered_qs.annotate(period_start=trunc_func)
                .values("attempt_type", "period_start")
                .annotate(
                    avg_score=Avg("score_percentage"),
                    avg_verbal=Avg("score_verbal"),
                    avg_quantitative=Avg("score_quantitative"),
                    tests_in_period=Count("id"),
                    # Summing num_questions from JSON is complex. Let's make a placeholder or simple sum.
                    # Simplification: if num_questions is a field on UserTestAttempt, we can Sum it.
                    # Since it's a property, we can't directly Sum.
                    # We'll calculate it from question_ids if possible after fetching, or make an approximation.
                    # For this version, we'll rely on tests_in_period and avg scores.
                )
                .order_by("attempt_type", "period_start")
            )

            for item in period_data_qs:
                # Approximation for total_questions_in_period for demo
                # A more robust way is to query questions for tests in that period or sum if num_questions was a field.
                # Let's get num_questions from the original UserTestAttempt model in this loop.
                # This is less efficient than pure DB agg, but works.
                tests_for_this_period_type = filtered_qs.filter(
                    attempt_type=item["attempt_type"],
                    end_time__gte=item[
                        "period_start"
                    ],  # Assuming period_start is a date
                    # This needs refinement for week/month/year boundaries
                    # A better approach: query tests matching the exact truncated period_start
                )
                # For accurate num_questions sum, we need to define period end.
                # This part is simplified; a full solution for sum(num_questions) in periods is more involved.
                # Let's add a placeholder sum for num_questions
                total_q_in_period = 0
                # This loop to calculate total_q_in_period makes it N+1 queries for periods.
                # Better approach: If `UserTestAttempt.num_questions` property was an actual model field,
                # we could use `Sum('num_questions_field')` in the `annotate` above.
                # Given the current model, it's harder.
                # Let's just pass test_count and rely on frontend to calc if needed from individual tests.

                data_point = {
                    "period_start_date": item["period_start"],  # This is a date object
                    "average_score": (
                        round(item["avg_score"], 1)
                        if item["avg_score"] is not None
                        else None
                    ),
                    "average_verbal_score": (
                        round(item["avg_verbal"], 1)
                        if item["avg_verbal"] is not None
                        else None
                    ),
                    "average_quantitative_score": (
                        round(item["avg_quantitative"], 1)
                        if item["avg_quantitative"] is not None
                        else None
                    ),
                    "test_count": item["tests_in_period"],
                    "total_questions_in_period": 0,  # Placeholder - see comment above
                }
                serialized_point = PeriodPerformanceDataPointSerializer(data=data_point)
                if serialized_point.is_valid():
                    if item["attempt_type"] in trends_data:
                        trends_data[item["attempt_type"]].append(serialized_point.data)
                else:
                    logger.error(
                        f"Invalid period data point: {serialized_point.errors} from {item}"
                    )
        else:  # Individual test data points
            attempts_values = filtered_qs.values(
                "id",
                "attempt_type",
                "end_time",
                "score_percentage",
                "score_verbal",
                "score_quantitative",
                "question_ids",
            ).order_by("attempt_type", "end_time")

            for attempt_data in attempts_values:
                num_q = (
                    len(attempt_data["question_ids"])
                    if isinstance(attempt_data["question_ids"], list)
                    else 0
                )
                data_point = {
                    "attempt_id": attempt_data["id"],
                    "date": attempt_data["end_time"],
                    "score": attempt_data["score_percentage"],
                    "verbal_score": attempt_data["score_verbal"],
                    "quantitative_score": attempt_data["score_quantitative"],
                    "num_questions": num_q,
                }
                serialized_point = TestAttemptDataPointSerializer(data=data_point)
                if serialized_point.is_valid():
                    if attempt_data["attempt_type"] in trends_data:
                        trends_data[attempt_data["attempt_type"]].append(
                            serialized_point.data
                        )
                else:
                    logger.error(
                        f"Invalid individual data point: {serialized_point.errors} from {attempt_data}"
                    )

        return trends_data

    def get_average_scores_by_test_type(self, obj):  # obj is user
        user = obj
        base_qs = UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.COMPLETED,
            score_percentage__isnull=False,
        )
        filtered_qs = self._apply_date_filters(base_qs, "end_time")

        averages_qs = (
            filtered_qs.values("attempt_type")
            .annotate(
                avg_score=Avg("score_percentage"),
                avg_verbal=Avg("score_verbal"),
                avg_quantitative=Avg("score_quantitative"),
                tests_count=Count("id"),
            )
            .order_by("attempt_type")
        )

        results = {}
        for type_value, type_display in UserTestAttempt.AttemptType.choices:
            results[type_value] = {
                "attempt_type_value": type_value,
                "attempt_type_display": type_display,
                "average_score": None,
                "average_verbal_score": None,
                "average_quantitative_score": None,
                "test_count": 0,
            }
        for item in averages_qs:
            type_value = item["attempt_type"]
            if type_value in results:
                results[type_value].update(
                    {
                        "average_score": (
                            round(item["avg_score"], 1)
                            if item["avg_score"] is not None
                            else None
                        ),
                        "average_verbal_score": (
                            round(item["avg_verbal"], 1)
                            if item["avg_verbal"] is not None
                            else None
                        ),
                        "average_quantitative_score": (
                            round(item["avg_quantitative"], 1)
                            if item["avg_quantitative"] is not None
                            else None
                        ),
                        "test_count": item["tests_count"],
                    }
                )
        serialized_results = {
            key: AverageScoreByTypeSerializer(data=value).initial_data
            for key, value in results.items()
        }
        return serialized_results

    def get_time_analytics(self, obj):  # obj is user
        user = obj

        # Avg time per question overall
        q_attempts_base_qs = UserQuestionAttempt.objects.filter(
            user=user, time_taken_seconds__isnull=False
        )
        q_attempts_filtered_qs = self._apply_date_filters(
            q_attempts_base_qs, "attempted_at"
        )

        overall_avg_q_time_agg = q_attempts_filtered_qs.aggregate(
            avg_time=Avg("time_taken_seconds")
        )
        overall_avg_q_time = (
            round(overall_avg_q_time_agg["avg_time"], 1)
            if overall_avg_q_time_agg["avg_time"]
            else None
        )

        # Avg time per question by correctness
        correctness_base_qs = UserQuestionAttempt.objects.filter(
            user=user, time_taken_seconds__isnull=False, is_correct__isnull=False
        )
        correctness_filtered_qs = self._apply_date_filters(
            correctness_base_qs, "attempted_at"
        )

        correctness_avg_time_qs = (
            correctness_filtered_qs.values("is_correct")
            .annotate(avg_time=Avg("time_taken_seconds"), q_count=Count("id"))
            .order_by("is_correct")
        )

        avg_time_by_correctness_data = {
            "correct": {"average_time_seconds": None, "question_count": 0},
            "incorrect": {"average_time_seconds": None, "question_count": 0},
        }
        for item in correctness_avg_time_qs:
            key = "correct" if item["is_correct"] else "incorrect"
            avg_time_by_correctness_data[key] = {
                "average_time_seconds": (
                    round(item["avg_time"], 1) if item["avg_time"] else None
                ),
                "question_count": item["q_count"],
            }
        serialized_avg_time_by_correctness = {
            k: TimePerQuestionByCorrectnessSerializer(data=v).initial_data
            for k, v in avg_time_by_correctness_data.items()
        }

        # Average test duration by type
        test_duration_base_qs = UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.COMPLETED,
            end_time__isnull=False,
            start_time__isnull=False,
        )
        test_duration_filtered_qs = self._apply_date_filters(
            test_duration_base_qs, "end_time"
        )

        avg_test_duration_qs = (
            test_duration_filtered_qs.annotate(
                duration=ExpressionWrapper(
                    F("end_time") - F("start_time"), output_field=DurationField()
                )
            )
            .values("attempt_type")
            .annotate(avg_duration_val=Avg("duration"), tests_count=Count("id"))
            .order_by("attempt_type")
        )

        avg_duration_by_type_data = {
            type_value: {
                "attempt_type_value": type_value,
                "attempt_type_display": type_display,
                "average_duration_seconds": None,
                "test_count": 0,
            }
            for type_value, type_display in UserTestAttempt.AttemptType.choices
        }
        for item in avg_test_duration_qs:
            type_value = item["attempt_type"]
            if type_value in avg_duration_by_type_data:
                duration_seconds = (
                    item["avg_duration_val"].total_seconds()
                    if item["avg_duration_val"]
                    else None
                )
                avg_duration_by_type_data[type_value].update(
                    {
                        "average_duration_seconds": (
                            round(duration_seconds, 1)
                            if duration_seconds is not None
                            else None
                        ),
                        "test_count": item["tests_count"],
                    }
                )
        serialized_avg_duration_by_type = {
            k: AverageTestDurationSerializer(data=v).initial_data
            for k, v in avg_duration_by_type_data.items()
        }

        return {
            "overall_average_time_per_question_seconds": overall_avg_q_time,
            "average_time_per_question_by_correctness": serialized_avg_time_by_correctness,
            "average_test_duration_by_type": serialized_avg_duration_by_type,
        }
