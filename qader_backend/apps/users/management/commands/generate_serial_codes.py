import uuid
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

# Adjust the import path based on your project structure if needed
from apps.users.models import SerialCode, SubscriptionTypeChoices


class Command(BaseCommand):
    help = (
        "Generates serial codes for specified subscription plan(s) with unique patterns. "
        "If --plan is omitted, generates codes for all standard plans."
    )

    # Define prefixes for each plan type
    # Use items() later to iterate easily
    PLAN_CONFIG = {
        SubscriptionTypeChoices.MONTH_1: {
            "prefix": "QDR1M",
            "duration_days": 30,
            "cli_name": "1m",
        },
        SubscriptionTypeChoices.MONTH_6: {
            "prefix": "QDR6M",
            "duration_days": 183,
            "cli_name": "6m",
        },
        SubscriptionTypeChoices.MONTH_12: {
            "prefix": "QDR12M",
            "duration_days": 365,
            "cli_name": "12m",
        },
        # Keep custom definition separate if not generating automatically for it
        # SubscriptionTypeChoices.CUSTOM: { ... }
    }

    DEFAULT_QUANTITY_ALL_PLANS = 100

    def add_arguments(self, parser):
        parser.add_argument(
            "--plan",
            required=False,  # Make plan optional
            choices=[config["cli_name"] for config in self.PLAN_CONFIG.values()],
            help=(
                f"The subscription plan type ({', '.join([config['cli_name'] for config in self.PLAN_CONFIG.values()])}). "
                f"If omitted, generates {self.DEFAULT_QUANTITY_ALL_PLANS} codes (or --quantity) for all standard plans."
            ),
        )
        parser.add_argument(
            "--quantity",
            type=int,
            # Default is now handled based on whether --plan is set
            # default=1,
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
        """Helper method to generate codes for a single specific plan."""
        prefix = config["prefix"]
        duration = config["duration_days"]
        plan_cli_name = config["cli_name"]
        plan_label = type_enum.label

        self.stdout.write(
            self.style.NOTICE(
                f"Generating {quantity} serial code(s) for plan '{plan_cli_name}' ({plan_label}) "
                f"with prefix '{prefix}' and duration {duration} days..."
            )
        )

        generated_codes = []
        failed_count = 0
        try:
            # Using atomic transaction for each plan's batch
            with transaction.atomic():
                for i in range(quantity):
                    attempts = 0
                    max_attempts = (
                        5  # Prevent infinite loop on unlikely collision storm
                    )
                    while attempts < max_attempts:
                        random_part = uuid.uuid4().hex[:code_random_part_length].upper()
                        new_code = f"{prefix}-{random_part}"
                        if not SerialCode.objects.filter(code=new_code).exists():
                            break
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"Collision detected for {new_code}, regenerating..."
                                )
                            )
                            attempts += 1
                    else:
                        # Only reached if max_attempts exceeded
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to generate unique code for plan {plan_cli_name} after {max_attempts} attempts."
                            )
                        )
                        failed_count += 1
                        continue  # Skip creating this code

                    serial = SerialCode.objects.create(
                        code=new_code,
                        subscription_type=type_enum,
                        duration_days=duration,
                        is_active=True,
                        is_used=False,
                        created_by=creator,
                        notes=notes,
                    )
                    generated_codes.append(serial.code)

        except Exception as e:
            # Log error for this specific plan batch but continue if generating all
            self.stdout.write(
                self.style.ERROR(
                    f"An error occurred during code generation for plan {plan_cli_name}: {e}"
                )
            )
            return [], quantity  # Return failure for this batch

        if failed_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Failed to generate {failed_count} codes for plan {plan_cli_name} due to collisions."
                )
            )

        return generated_codes, failed_count

    def handle(self, *args, **options):
        plan_cli_name = options["plan"]
        provided_quantity = options["quantity"]  # Might be None if not provided
        creator_username = options["creator"]
        notes = options["notes"]
        code_random_part_length = options["code_length"]

        if code_random_part_length <= 0:
            raise CommandError("Code length must be a positive integer.")

        # Determine quantity
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

        # Find the creator user if provided
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
                    f"Multiple staff users found for username '{creator_username}'. Please use a unique username."
                )

        total_generated_count = 0
        total_failed_count = 0
        all_generated_codes = {}  # Store codes per plan

        if plan_cli_name:
            # Generate for a single specified plan
            selected_config = None
            selected_type_enum = None
            for type_enum, config in self.PLAN_CONFIG.items():
                if config["cli_name"] == plan_cli_name:
                    selected_config = config
                    selected_type_enum = type_enum
                    break

            if not selected_config:
                raise CommandError(f"Invalid plan type specified: {plan_cli_name}")

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
            # Generate for all standard plans
            self.stdout.write(
                self.style.NOTICE(
                    f"No specific plan specified. Generating {quantity} codes for all standard plans..."
                )
            )
            for type_enum, config in self.PLAN_CONFIG.items():
                # Optionally skip 'custom' type if defined and shouldn't be bulk generated
                # if type_enum == SubscriptionTypeChoices.CUSTOM:
                #     continue
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
                    f"Total codes failed due to collisions: {total_failed_count}"
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
