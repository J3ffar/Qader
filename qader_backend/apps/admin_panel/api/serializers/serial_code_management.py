from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from apps.users.models import SerialCode, SubscriptionTypeChoices
from apps.users.api.serializers import (
    SimpleUserSerializer,
)  # Reuse for nested user info

User = get_user_model()


class SerialCodeListSerializer(serializers.ModelSerializer):
    """Serializer for listing Serial Codes in the admin panel."""

    used_by = SimpleUserSerializer(read_only=True)
    created_by = SimpleUserSerializer(read_only=True)
    subscription_type_display = serializers.CharField(
        source="get_subscription_type_display", read_only=True
    )

    class Meta:
        model = SerialCode
        fields = [
            "id",
            "code",
            "subscription_type",
            "subscription_type_display",
            "duration_days",
            "is_active",
            "is_used",
            "used_by",
            "used_at",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields


class SerialCodeDetailSerializer(SerialCodeListSerializer):
    """Serializer for retrieving Serial Code details, includes notes."""

    class Meta(SerialCodeListSerializer.Meta):
        fields = SerialCodeListSerializer.Meta.fields + ["notes", "updated_at"]
        read_only_fields = fields


class SerialCodeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Serial Code fields allowed by admin (e.g., status, notes)."""

    class Meta:
        model = SerialCode
        fields = [
            "is_active",
            "notes",
            # Optionally allow updating type/duration if business logic allows,
            # but typically they are fixed after generation.
            # "subscription_type",
            # "duration_days",
        ]
        extra_kwargs = {
            "is_active": {"required": False},
            "notes": {"required": False, "allow_blank": True, "allow_null": True},
        }

    def validate(self, attrs):
        # Add any specific validation rules for updates if needed
        # e.g., prevent reactivating an already used code if that's a rule.
        instance = self.instance
        if instance and instance.is_used and attrs.get("is_active", instance.is_active):
            # Example: Disallow making an already used code active again.
            # You might want different logic (e.g., allow reactivation for specific cases).
            # Adjust based on requirements. This is a common pattern.
            pass
            # Uncomment below if reactivation of used codes is disallowed:
            # if 'is_active' in attrs and attrs['is_active'] == True:
            #    raise serializers.ValidationError(
            #        {"is_active": _("Cannot reactivate a code that has already been used.")}
            #    )
        return attrs


class SerialCodeGenerateSerializer(serializers.Serializer):
    """Serializer for validating input for generating a batch of serial codes."""

    plan_type = serializers.ChoiceField(
        choices=SubscriptionTypeChoices.choices,
        required=True,
        label=_("Subscription Plan Type"),
        help_text=_("Select the plan type (e.g., 1 Month, 6 Months) for the codes."),
    )
    count = serializers.IntegerField(
        min_value=1,
        max_value=1000,  # Set a reasonable max batch size
        required=True,
        label=_("Number of Codes"),
        help_text=_("How many codes to generate in this batch (1-1000)."),
    )
    subscription_type = serializers.ChoiceField(
        choices=SubscriptionTypeChoices.choices,
        required=True,
        label=_("Subscription Type"),
        help_text=_("Categorizes the intended duration or type of the code."),
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        label=_("Batch Notes"),
        style={"base_template": "textarea.html"},
        help_text=_("Optional notes for this batch (e.g., 'For School X Campaign')."),
    )

    def validate_plan_type(self, value):
        """Optionally prevent generating 'Custom' type via batch."""
        if value == SubscriptionTypeChoices.CUSTOM:
            raise serializers.ValidationError(
                _(
                    "Generating 'Custom' type codes via this batch endpoint is not supported. Use the standard POST method to create individual custom codes."
                )
            )
        return value


class SerialCodeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a single Serial Code via standard POST."""

    # Allow specifying code, but validate uniqueness (case-insensitive)
    code = serializers.CharField(
        max_length=50,
        required=True,  # Make it required for explicit creation
        help_text=_(
            "The unique serial code string (case-insensitive). Will be uppercased."
        ),
        validators=[
            UniqueValidator(
                queryset=SerialCode.objects.all(),
                lookup="iexact",  # Case-insensitive check
                message=_("A serial code with this value already exists."),
            )
        ],
    )
    subscription_type = serializers.ChoiceField(
        choices=SubscriptionTypeChoices.choices,
        required=True,
        label=_("Subscription Type"),
    )
    duration_days = serializers.IntegerField(
        min_value=1,
        required=True,
        label=_("Duration (Days)"),
    )
    is_active = serializers.BooleanField(
        default=True, required=False, label=_("Is Active?")
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        label=_("Notes"),
        style={"base_template": "textarea.html"},
    )

    class Meta:
        model = SerialCode
        fields = [
            "code",
            "subscription_type",
            "duration_days",
            "is_active",
            "notes",
        ]
        # created_by is set in perform_create
        # is_used defaults to False

    def validate_code(self, value):
        """Ensure code is uppercased."""
        return value.upper()

    def validate(self, attrs):
        # Add custom cross-field validation if needed, e.g., duration based on type
        # Relying on model's clean method is also an option, but DRF validation is often preferred.
        return attrs
