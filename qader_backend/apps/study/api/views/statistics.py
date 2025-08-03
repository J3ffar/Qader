from rest_framework import generics, status, views, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes
from django.utils.translation import gettext_lazy as _
from django.utils.dateparse import parse_date
import logging

from apps.api.permissions import IsSubscribed
from apps.study.api.serializers.statistics import (
    RECENT_TESTS_LIMIT,
    UserStatisticsSerializer,
    # Import nested serializers for explicit schema examples if needed,
    # though drf-spectacular usually infers them well from UserStatisticsSerializer
    OverallStatsSerializer,
    SectionPerformanceSerializer,
    SkillProficiencySummarySerializer,
    TestHistorySummarySerializer,
    TestAttemptDataPointSerializer,  # For individual trends
    PeriodPerformanceDataPointSerializer,  # For aggregated trends
    AverageScoreByTypeSerializer,
    # TimePerQuestionByCorrectnessSerializer, # Part of TimeAnalytics
    # AverageTestDurationSerializer, # Part of TimeAnalytics
)
from apps.study.models import UserTestAttempt  # For attempt type choices in docs

logger = logging.getLogger(__name__)

# Define allowed aggregation periods for schema and validation
AGGREGATION_PERIOD_CHOICES = ["daily", "weekly", "monthly", "yearly"]

# --- Detailed Documentation for Response Fields ---
# This can be formatted as Markdown for better readability in Swagger UI

RESPONSE_FIELD_DESCRIPTIONS = f"""
The response is a JSON object containing various statistical breakdowns:

- **`overall`**: (Object) General overview of the student's progress.
    - `mastery_level`: (Object) Current estimated mastery levels.
        - `verbal`: (Float|null) Verbal mastery score/level (e.g., 0-100 or a scaled value).
        - `quantitative`: (Float|null) Quantitative mastery score/level.
    - `study_streaks`: (Object) Information about study consistency.
        - `current_days`: (Integer) Number of consecutive days the student has studied.
        - `longest_days`: (Integer) The longest streak of consecutive study days achieved.
    - `activity_summary`: (Object) Counts of key activities within the selected period (if `start_date`/`end_date` are used, otherwise all-time).
        - `total_questions_answered`: (Integer) Total questions attempted.
        - `total_tests_completed`: (Integer) Total tests marked as completed.
        
- **`performance_by_section`**: (Object) Performance breakdown by main sections (e.g., "verbal", "quantitative"). Keys are section slugs.
    - `[section_slug]`: (Object) Data for a specific section.
        - `name`: (String) Display name of the section (e.g., "القسم اللفظي").
        - `overall_accuracy`: (Float|null) Overall accuracy percentage for this section (0.0 to 100.0).
        - `subsections`: (Object) Performance breakdown for subsections within this main section. Keys are subsection slugs.
            - `[subsection_slug]`: (Object) Data for a specific subsection.
                - `name`: (String) Display name of the subsection.
                - `accuracy`: (Float|null) Accuracy percentage for this subsection.
                - `attempts`: (Integer) Number of questions attempted in this subsection.
    *Example Chart Use*: Bar chart for `overall_accuracy` per section. Nested bar charts or tables for subsection accuracies.

- **`skill_proficiency_summary`**: (Array of Objects) Proficiency details for individual skills. Typically reflects overall proficiency, not affected by date filters unless proficiency calculation itself is period-based.
    - `skill_slug`: (String) Unique slug for the skill.
    - `skill_name`: (String) Display name of the skill.
    - `proficiency_score`: (Float) Calculated proficiency score (e.g., 0.0 to 1.0).
    - `accuracy`: (Float|null) Accuracy percentage on questions related to this skill.
    - `attempts`: (Integer) Number of questions attempted for this skill.
    *Example Chart Use*: Pie/Donut chart for `proficiency_score` distribution across top skills. Bar chart for accuracy per skill.

- **`test_history_summary`**: (Array of Objects) Summary of the {RECENT_TESTS_LIMIT} most recent completed tests *within the selected date range* (if specified).
    - `attempt_id`: (Integer) Unique ID of the test attempt.
    - `date`: (String - ISO 8601 DateTime) Date and time the test was completed.
    - `type`: (String) Display name of the test type (e.g., "Level Assessment").
    - `type_value`: (String) Internal value of the test type (e.g., "{UserTestAttempt.AttemptType.LEVEL_ASSESSMENT.value}").
    - `overall_score`: (Float|null) Overall percentage score for the test.
    - `verbal_score`: (Float|null) Verbal section score.
    - `quantitative_score`: (Float|null) Quantitative section score.
    - `num_questions`: (Integer) Number of questions in this test attempt.
    *Example Use*: Displayed as a list/table of recent test activities.

- **`performance_trends_by_test_type`**: (Object) Score progression over time, keyed by test attempt type values (e.g., "{UserTestAttempt.AttemptType.PRACTICE.value}", "{UserTestAttempt.AttemptType.SIMULATION.value}").
    The structure of the array items depends on the `aggregation_period` query parameter:
    - **If `aggregation_period` is NOT provided**:
        - Each value is an array of *individual test attempt data points*:
            - `attempt_id`: (Integer) Unique ID of the test attempt.
            - `date`: (String - ISO 8601 DateTime) Completion date/time.
            - `score`: (Float|null) Overall score for this test.
            - `verbal_score`: (Float|null) Verbal score for this test.
            - `quantitative_score`: (Float|null) Quantitative score for this test.
            - `num_questions`: (Integer) Number of questions in this test.
    - **If `aggregation_period` IS provided (e.g., "daily", "weekly")**:
        - Each value is an array of *aggregated period data points*:
            - `period_start_date`: (String - ISO 8601 Date) The start date of the aggregation period (e.g., "2023-10-01" for monthly).
            - `average_score`: (Float|null) Average overall score for tests completed in this period.
            - `average_verbal_score`: (Float|null) Average verbal score for tests in this period.
            - `average_quantitative_score`: (Float|null) Average quantitative score for tests in this period.
            - `test_count`: (Integer) Number of tests completed in this period.
            - `total_questions_in_period`: (Integer) Placeholder for sum of questions from tests in this period (currently 0, frontend might need to sum from individual tests if required).
    *Example Chart Use*: Line charts showing score (`score` or `average_score`) vs. `date`/`period_start_date` for each test type.

- **`average_scores_by_test_type`**: (Object) Average scores for each test type, calculated *within the selected date range*. Keys are test attempt type values.
    - `[test_type_value]`: (Object)
        - `attempt_type_value`: (String) The test type key (e.g., "{UserTestAttempt.AttemptType.LEVEL_ASSESSMENT.value}").
        - `attempt_type_display`: (String) Display name of the test type.
        - `average_score`: (Float|null) Average overall score.
        - `average_verbal_score`: (Float|null) Average verbal score.
        - `average_quantitative_score`: (Float|null) Average quantitative score.
        - `test_count`: (Integer) Number of tests of this type completed.
    *Example Chart Use*: Bar chart comparing `average_score` across different test types.

- **`time_analytics`**: (Object) Various time-related analytics, calculated *within the selected date range*.
    - `overall_average_time_per_question_seconds`: (Float|null) Average time in seconds spent per question across all attempts.
    - `average_time_per_question_by_correctness`: (Object)
        - `correct`: (Object)
            - `average_time_seconds`: (Float|null) Average time for correctly answered questions.
            - `question_count`: (Integer) Number of correctly answered questions with time data.
        - `incorrect`: (Object)
            - `average_time_seconds`: (Float|null) Average time for incorrectly answered questions.
            - `question_count`: (Integer) Number of incorrectly answered questions with time data.
    - `average_test_duration_by_type`: (Object) Average duration of completed tests, keyed by test attempt type values.
        - `[test_type_value]`: (Object)
            - `attempt_type_value`: (String) The test type key.
            - `attempt_type_display`: (String) Display name of the test type.
            - `average_duration_seconds`: (Float|null) Average duration of tests of this type in seconds.
            - `test_count`: (Integer) Number of tests of this type with duration data.
    *Example Chart Use*: Bar chart for `average_time_seconds` (correct vs. incorrect). Bar chart for `average_duration_seconds` by test type.
"""


# Example data for OpenApiExample (simplified for brevity in the decorator)
# A full example like the one you provided would be too verbose for the decorator itself.
# drf-spectacular will generate a more complete example based on serializers.
# This is more for a quick visual in the Swagger UI description if needed.
EXAMPLE_STATISTICS_OUTPUT_BRIEF = {
    "overall": {"mastery_level": {"verbal": 75.0, "quantitative": 60.0}, "...": "..."},
    "performance_by_section": {
        "verbal": {
            "name": "Verbal",
            "overall_accuracy": 70.0,
            "subsections": {"reading": {"accuracy": 65.0}},
        },
        "...": "...",
    },
    "skill_proficiency_summary": [
        {"skill_name": "Main Idea", "proficiency_score": 0.8, "...": "..."}
    ],
    # ... other keys with brief examples
}


@extend_schema(
    tags=["Study - Statistics & Progress"],
    summary="Retrieve User Statistics with Optional Filtering and Aggregation",
    description=(
        "Fetches aggregated statistics for the authenticated user, including overall progress, "
        "performance breakdown by section/subsection/skill, and recent test history.\n\n"
        "**Filtering and Aggregation (Query Parameters):**\n"
        "- `start_date` (YYYY-MM-DD): Filter data from this date (inclusive). Affects most metrics except potentially `overall.mastery_level` and `skill_proficiency_summary` which are typically holistic.\n"
        "- `end_date` (YYYY-MM-DD): Filter data up to this date (inclusive).\n"
        "- `aggregation_period` (string): Group time-series data in `performance_trends_by_test_type` "
        f"by a specific period. Allowed values: `{'`, `'.join(AGGREGATION_PERIOD_CHOICES)}`. "
        "If not provided, `performance_trends_by_test_type` shows individual test attempts. "
        "If provided, it shows averages for each period (e.g., average score per week)."
    ),
    parameters=[
        OpenApiParameter(
            name="start_date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Start date for filtering (YYYY-MM-DD).",
        ),
        OpenApiParameter(
            name="end_date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=False,
            description="End date for filtering (YYYY-MM-DD).",
        ),
        OpenApiParameter(
            name="aggregation_period",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            enum=AGGREGATION_PERIOD_CHOICES,
            description=f"Period for aggregating `performance_trends_by_test_type`. "
            f"Choices: {', '.join(AGGREGATION_PERIOD_CHOICES)}.",
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=UserStatisticsSerializer,  # drf-spectacular will use this to generate the detailed schema
            description=f"Successful retrieval of user statistics.\n\n"
            f"**Understanding the Response Fields:**\n{RESPONSE_FIELD_DESCRIPTIONS}",
            examples=[
                OpenApiExample(
                    name="Sample User Statistics Response",
                    summary="Illustrative example of the statistics output structure.",
                    # You can put a stringified version of your full example here if it's not too massive,
                    # or a more concise one. For complex examples, it's often better to rely on
                    # drf-spectacular's schema generation from serializers.
                    # value=EXAMPLE_STATISTICS_OUTPUT_BRIEF # Using a brief example here
                    # For the full example, it would be:
                    # import json
                    # value=json.loads("""<your full JSON example here>""")
                    # This will be very long, so usually relying on the serializer schema is better.
                    # The description above is more key for frontend devs.
                    value="See the schema and the detailed field descriptions above for the full structure. "
                    "The example output you provided in the prompt is a good representation of what to expect.",
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad Request (e.g., Invalid date format, invalid aggregation period, User profile missing, start_date after end_date)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Authentication/Subscription)."
        ),
        500: OpenApiResponse(
            description="Internal Server Error during statistics calculation."
        ),
    },
)
class UserStatisticsView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        aggregation_period = request.query_params.get("aggregation_period")

        start_date, end_date = None, None

        if start_date_str:
            start_date = parse_date(start_date_str)
            if not start_date:
                return Response(
                    {"detail": _("Invalid start_date format. Use YYYY-MM-DD.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if end_date_str:
            end_date = parse_date(end_date_str)
            if not end_date:
                return Response(
                    {"detail": _("Invalid end_date format. Use YYYY-MM-DD.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if start_date and end_date and start_date > end_date:
            return Response(
                {"detail": _("start_date cannot be after end_date.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if aggregation_period and aggregation_period not in AGGREGATION_PERIOD_CHOICES:
            return Response(
                {
                    "detail": _(
                        f"Invalid aggregation_period. Allowed values are: {', '.join(AGGREGATION_PERIOD_CHOICES)}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer_context = {
            "request": request,
            "start_date": start_date,
            "end_date": end_date,
            "aggregation_period": aggregation_period,
        }

        try:
            serializer = UserStatisticsSerializer(
                instance=request.user, context=serializer_context
            )
            data = serializer.data
            return Response(data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            logger.warning(
                f"Validation error during statistics generation for user {request.user.id}: {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error generating statistics for user {request.user.id}: {e}"
            )
            return Response(
                {
                    "detail": _(
                        "An unexpected error occurred while generating statistics."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
