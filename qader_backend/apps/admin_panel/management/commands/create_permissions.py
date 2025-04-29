from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.admin_panel.models import AdminPermission
from django.contrib.auth.models import User
import logging

# Import the data list from the new file
from apps.admin_panel.data.admin_permissions_data import ADMIN_PERMISSIONS_DATA


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates or updates initial AdminPermission objects with translatable names and descriptions."

    def handle(self, *args, **options):
        self.stdout.write("Creating or updating Admin Permissions...")

        created_count = 0
        updated_count = 0

        # Use transaction.atomic for data integrity
        with transaction.atomic():
            for perm_data in ADMIN_PERMISSIONS_DATA:
                # Ensure slug is correctly formatted (e.g. view_users)
                # Note: Slugs themselves are usually not translated, as they are code identifiers
                slug = slugify(perm_data["slug"]).replace("-", "_")
                name = perm_data["name"]  # This is now a gettext_lazy object
                description = perm_data.get(
                    "description", ""
                )  # This is now a gettext_lazy object or empty string

                # Use get_or_create to avoid duplicates on re-run.
                # Django's ORM handles saving the gettext_lazy object (Promise)
                # to the database field correctly using the *current* active language.
                # The *lookup* for translation happens when the data is retrieved later
                # based on the request's active language.
                permission, created = AdminPermission.objects.get_or_create(
                    slug=slug, defaults={"name": name, "description": description}
                )

                if created:
                    created_count += 1
                    logger.info(
                        f"Created permission: {slug} (Name: {name})"
                    )  # Name here might show the lazy object or default lang
                    self.stdout.write(self.style.SUCCESS(f"Created permission: {slug}"))
                else:
                    # Optionally update name/description if they changed in the data source
                    # Compare against the *lazy* objects from the source data
                    if str(permission.name) != str(name) or str(
                        permission.description
                    ) != str(description):
                        permission.name = name  # Assign the lazy object
                        permission.description = description  # Assign the lazy object
                        permission.save()
                        updated_count += 1
                        logger.info(f"Updated permission: {slug} (Name: {name})")
                        self.stdout.write(
                            self.style.WARNING(f"Updated permission: {slug}")
                        )
                    # else:
                    # logger.debug(f"Permission already exists and is up-to-date: {slug}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Created {created_count} permissions, updated {updated_count} permissions."
            )
        )

        # Optional: Assign all permissions to the first superuser (if one exists)
        # This is just for convenience during initial setup
        try:
            superuser = User.objects.filter(is_superuser=True).first()
            if superuser and hasattr(superuser, "profile"):
                all_permissions = AdminPermission.objects.all()
                # Ensure profile exists (it should for superuser)
                # Use get_or_create on Profile might be safer if command runs before signal
                from apps.users.models import (
                    UserProfile,
                )  # Assuming UserProfile is in apps.users

                profile, _ = UserProfile.objects.get_or_create(
                    user=superuser
                )  # Use user field for get_or_create
                profile.admin_permissions.set(all_permissions)  # Assign all permissions
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Assigned all permissions to superuser: {superuser.username}"
                    )
                )
                logger.info(
                    f"Assigned all permissions to superuser: {superuser.username}"
                )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"Could not assign all permissions to superuser: {e}"
                )
            )
            logger.warning(f"Could not assign all permissions to superuser: {e}")
