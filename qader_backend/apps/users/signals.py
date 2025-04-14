from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

import logging  # Use standard logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance: User, created: bool, **kwargs):
    """
    Signal handler to create or update UserProfile when a User object is saved.
    """
    if created:
        # Only create profile if user is newly created
        UserProfile.objects.create(user=instance)
        logger.info(
            f"UserProfile created for new user {instance.username} (ID: {instance.id})"
        )
    else:
        # If user is updated, ensure profile exists (defensive check)
        # Typically, profile updates should happen via profile-specific views/serializers
        try:
            instance.profile.save()  # Trigger profile save to update `updated_at` if needed
            logger.debug(
                f"UserProfile updated for existing user {instance.username} (ID: {instance.id})"
            )
        except UserProfile.DoesNotExist:
            # This indicates a problem - profile should exist for existing users
            logger.error(
                f"UserProfile missing for existing user {instance.username} (ID: {instance.id}). Creating profile now."
            )
            UserProfile.objects.create(user=instance)
