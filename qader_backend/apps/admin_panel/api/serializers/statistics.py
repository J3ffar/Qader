from rest_framework import serializers
from apps.admin_panel.models import ExportJob
from apps.users.models import RoleChoices

# --- Overview Serializers ---


class SimpleQuestionSerializer(serializers.Serializer):
    """Minimal representation for top/difficult questions"""

    id = serializers.IntegerField()
    question_text = serializers.CharField()
    # Add attempt count or difficulty score depending on context
    attempt_count = serializers.IntegerField(required=False)
    accuracy_rate = serializers.FloatField(required=False)


class DailyActivitySerializer(serializers.Serializer):
    """Data point for time-series charts"""

    date = serializers.DateField()
    questions_answered = serializers.IntegerField()
    tests_completed = serializers.IntegerField()


class SectionPerformanceSerializer(serializers.Serializer):
    """Performance metrics for a major section (Verbal/Quant)"""

    section_name = serializers.CharField()
    section_slug = serializers.SlugField()
    average_accuracy = serializers.FloatField(allow_null=True)
    total_attempts = serializers.IntegerField()


class AdminStatisticsOverviewSerializer(serializers.Serializer):
    """Structures the response for the admin statistics overview endpoint"""

    total_active_students = serializers.IntegerField()
    new_registrations_period = serializers.IntegerField()  # Based on date filter
    total_questions_answered_period = serializers.IntegerField()
    total_tests_completed_period = serializers.IntegerField()

    overall_average_test_score = serializers.FloatField(allow_null=True)
    overall_average_accuracy = serializers.FloatField(allow_null=True)

    performance_by_section = SectionPerformanceSerializer(many=True)

    most_attempted_questions = SimpleQuestionSerializer(many=True)
    lowest_accuracy_questions = SimpleQuestionSerializer(
        many=True
    )  # Questions with lowest correct %

    daily_activity = DailyActivitySerializer(many=True)  # Data for charts

    # Add more fields as needed based on aggregation results
    # e.g., average_time_per_question, user_engagement_metrics, etc.

    def create(self, validated_data):
        # This serializer is read-only for response formatting
        raise NotImplementedError()

    def update(self, instance, validated_data):
        # This serializer is read-only for response formatting
        raise NotImplementedError()


# --- Export Serializers ---
class AdminStatisticsExportSerializer(serializers.Serializer):
    """Serializer for validating export request parameters (the 'create' payload)"""

    format = serializers.ChoiceField(
        choices=ExportJob.Format.choices, default=ExportJob.Format.CSV
    )
    date_from = serializers.DateField(required=False, write_only=True)
    date_to = serializers.DateField(required=False, write_only=True)
    # This serializer is now for input validation, not output representation.
    # The 'create' and 'update' methods are correctly not implemented.


# --- NEW SERIALIZER FOR USER EXPORT ---
class UserExportRequestSerializer(serializers.Serializer):
    """Serializer for validating USER DATA export request parameters."""

    format = serializers.ChoiceField(
        choices=ExportJob.Format.choices, default=ExportJob.Format.CSV
    )
    # Allows for filtering by one or more roles.
    # If omitted or empty, all roles will be included.
    role = serializers.MultipleChoiceField(
        choices=RoleChoices.choices,
        required=False,
        allow_empty=True,
        help_text="A list of roles to include in the export (e.g., ['STUDENT', 'TEACHER']). Omitting this exports all roles.",
    )


class ExportJobSerializer(serializers.ModelSerializer):
    """Serializer for representing an ExportJob instance (for list/retrieve)"""

    status = serializers.CharField(source="get_status_display", read_only=True)
    requesting_user = serializers.StringRelatedField(read_only=True)

    # --- MODIFIED FIELD to generate absolute URL ---
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ExportJob
        fields = [
            "id",
            "requesting_user",
            "job_type",
            "status",
            "file_format",
            "file_url",  # Use our new method field
            "filters",
            "error_message",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields

    def get_file_url(self, obj: ExportJob) -> str | None:
        """
        Generate a full, absolute URL for the exported file.
        Returns None if the file doesn't exist yet.
        """
        # Check if the file field has a file associated with it
        if not obj.file:
            return None

        request = self.context.get("request")
        if request is None:
            # Fallback for contexts without a request (e.g., shell)
            return obj.file.url

        # Use the request to build the complete URI, including scheme and domain
        return request.build_absolute_uri(obj.file.url)


class ExportTaskResponseSerializer(serializers.Serializer):
    """Response after successfully triggering an export task"""

    job_id = serializers.UUIDField()
    message = serializers.CharField()
    status_check_url = serializers.URLField()
