from rest_framework import serializers

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


# --- Export Serializers (Optional) ---
class AdminStatisticsExportSerializer(serializers.Serializer):
    """Serializer for validating export request parameters"""

    format = serializers.ChoiceField(choices=["csv", "xlsx"], default="csv")
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    # Add other filter fields if complex validation is needed

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class ExportTaskResponseSerializer(serializers.Serializer):
    """Response after triggering an export task"""

    task_id = serializers.CharField()
    message = serializers.CharField()
    status_check_url = serializers.URLField(required=False, allow_null=True)
