# qader_backend/apps/users/management/commands/generate_serial_codes.py
import uuid
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _  # Import gettext

# Import constants and models
from apps.users.models import SerialCode
from apps.users.constants import SubscriptionTypeChoices, SUBSCRIPTION_PLANS_CONFIG


class Command(BaseCommand):
    help = (
        "Generates serial codes for specified subscription plan(s) using centralized config. "
        "If --plan is omitted, generates codes for all standard plans defined in config."
    )

    # Get choices dynamically from the config
    PLAN_CLI_CHOICES = [
        config["cli_name"]
        for config in SUBSCRIPTION_PLANS_CONFIG.values()
        if "cli_name" in config  # Only include plans that have a cli_name defined
    ]

    DEFAULT_QUANTITY_ALL_PLANS = 100

    def add_arguments(self, parser):
        parser.add_argument(
            "--plan",
            required=False,
            choices=self.PLAN_CLI_CHOICES,  # Use dynamic choices
            help=(
                f"The subscription plan type ({', '.join(self.PLAN_CLI_CHOICES)}). "
                f"If omitted, generates {self.DEFAULT_QUANTITY_ALL_PLANS} codes (or --quantity) for all standard plans."
            ),
        )
        parser.add_argument(
            "--quantity",
            type=int,
            help=(
                "Number of codes to generate. Defaults to 1 if --plan is specified, "
                f"or {self.DEFAULT_QUANTITY_ALL_PLANS} if --plan is omitted."
            ),
        )
        parser.add_argument(
            "--creator",
            type=str,
            default=None,
            help="Username of the admin/staff user creating these codes.",
        )
        parser.add_argument(
            "--notes",
            type=str,
            default="",
            help="Optional administrative notes for the generated codes.",
        )
        parser.add_argument(
            "--code-length",
            type=int,
            default=12,  # Length of the random part after the prefix
            help="Length of the random hexadecimal part of the code.",
        )

    def _generate_codes_for_plan(
        self, type_enum, config, quantity, creator, notes, code_random_part_length
    ):
        """Helper method to generate codes for a single specific plan using config."""
        prefix = config.get("prefix", "QDRGEN")  # Use prefix from config, fallback
        duration = config.get("duration_days")
        plan_cli_name = config.get(
            "cli_name", type_enum.value
        )  # Use cli_name or enum value
        plan_label = type_enum.label

        if duration is None and type_enum != SubscriptionTypeChoices.CUSTOM:
            self.stdout.write(
                self.style.ERROR(
                    f"Skipping plan '{plan_label}': duration_days not defined in config."
                )
            )
            return [], 0  # Skip if duration is missing for non-custom

        self.stdout.write(
            self.style.NOTICE(
                f"Generating {quantity} serial code(s) for plan '{plan_cli_name}' ({plan_label}) "
                f"with prefix '{prefix}' and duration {duration or 'N/A'} days..."
            )
        )

        generated_codes = []
        failed_count = 0
        try:
            with transaction.atomic():
                for i in range(quantity):
                    attempts = 0
                    max_attempts = 5
                    while attempts < max_attempts:
                        # Use prefix from config
                        random_part = uuid.uuid4().hex[:code_random_part_length].upper()
                        new_code = f"{prefix}-{random_part}"

                        # Check uniqueness (case-insensitive)
                        if not SerialCode.objects.filter(
                            code__iexact=new_code
                        ).exists():
                            break
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Collision detected for {new_code}, regenerating..."
                                )
                            )
                            attempts += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to generate unique code for plan {plan_cli_name} after {max_attempts} attempts."
                            )
                        )
                        failed_count += 1
                        continue

                    # Handle potentially missing duration for CUSTOM type (if allowed)
                    if duration is None:
                        # Decide default duration for custom codes generated via command, or error out
                        # Let's assume custom codes *require* duration specification elsewhere
                        # and shouldn't be generated by this command without modification.
                        self.stdout.write(
                            self.style.ERROR(
                                f"Cannot generate code for plan {plan_cli_name}: Duration is required but not set."
                            )
                        )
                        failed_count += 1
                        continue

                    serial = SerialCode.objects.create(
                        code=new_code,
                        subscription_type=type_enum,
                        duration_days=duration,  # Use duration from config
                        is_active=True,
                        is_used=False,
                        created_by=creator,
                        notes=notes,
                    )
                    generated_codes.append(serial.code)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"An error occurred during code generation for plan {plan_cli_name}: {e}"
                )
            )
            return [], quantity

        if failed_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Failed to generate {failed_count} codes for plan {plan_cli_name} due to collisions or missing duration."
                )
            )

        return generated_codes, failed_count

    def handle(self, *args, **options):
        plan_cli_name = options["plan"]
        provided_quantity = options["quantity"]
        creator_username = options["creator"]
        notes = options["notes"]
        code_random_part_length = options["code_length"]

        if code_random_part_length <= 0:
            raise CommandError("Code length must be a positive integer.")

        if plan_cli_name:
            quantity = provided_quantity if provided_quantity is not None else 1
        else:
            quantity = (
                provided_quantity
                if provided_quantity is not None
                else self.DEFAULT_QUANTITY_ALL_PLANS
            )

        if quantity <= 0:
            raise CommandError("Quantity must be a positive integer.")

        creator = None
        if creator_username:
            try:
                creator = User.objects.get(username=creator_username, is_staff=True)
                self.stdout.write(
                    self.style.NOTICE(f"Codes will be created by: {creator.username}")
                )
            except User.DoesNotExist:
                raise CommandError(f"Admin/Staff user '{creator_username}' not found.")
            except User.MultipleObjectsReturned:
                raise CommandError(
                    f"Multiple staff users found for username '{creator_username}'."
                )

        total_generated_count = 0
        total_failed_count = 0
        all_generated_codes = {}

        if plan_cli_name:
            # Find the enum and config based on the provided cli_name
            selected_config = None
            selected_type_enum = None
            for type_enum, config in SUBSCRIPTION_PLANS_CONFIG.items():
                if config.get("cli_name") == plan_cli_name:
                    selected_config = config
                    selected_type_enum = type_enum
                    break

            if not selected_config or not selected_type_enum:
                raise CommandError(
                    f"Invalid plan type specified or config missing: {plan_cli_name}"
                )

            # Skip generating CUSTOM codes via this command unless specifically handled
            if selected_type_enum == SubscriptionTypeChoices.CUSTOM:
                raise CommandError(
                    "Generating 'custom' plan codes via this command is not supported by default. Please create them manually or adjust the command."
                )

            generated_codes, failed_count = self._generate_codes_for_plan(
                selected_type_enum,
                selected_config,
                quantity,
                creator,
                notes,
                code_random_part_length,
            )
            all_generated_codes[plan_cli_name] = generated_codes
            total_generated_count += len(generated_codes)
            total_failed_count += failed_count
        else:
            # Generate for all standard plans defined in the config
            self.stdout.write(
                self.style.NOTICE(
                    f"No specific plan specified. Generating {quantity} codes for all standard plans defined in config..."
                )
            )
            for type_enum, config in SUBSCRIPTION_PLANS_CONFIG.items():
                # Skip CUSTOM type by default when generating all
                if type_enum == SubscriptionTypeChoices.CUSTOM:
                    continue
                # Skip if cli_name or duration is missing (indicates incomplete config for generation)
                if "cli_name" not in config or "duration_days" not in config:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping plan '{type_enum.label}': Missing 'cli_name' or 'duration_days' in config."
                        )
                    )
                    continue

                generated_codes, failed_count = self._generate_codes_for_plan(
                    type_enum, config, quantity, creator, notes, code_random_part_length
                )
                all_generated_codes[config["cli_name"]] = generated_codes
                total_generated_count += len(generated_codes)
                total_failed_count += failed_count

        # Final summary
        self.stdout.write("\n" + "=" * 30 + " Summary " + "=" * 30)
        if total_failed_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Total codes failed generation: {total_failed_count}"
                )
            )

        if total_generated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated a total of {total_generated_count} serial code(s)."
                )
            )
            for plan_name, codes in all_generated_codes.items():
                if codes:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\n--- Codes for Plan: {plan_name} ({len(codes)}) ---"
                        )
                    )
                    for code in codes:
                        self.stdout.write(code)
        else:
            self.stdout.write(self.style.WARNING("No codes were generated."))
