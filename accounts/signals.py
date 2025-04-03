from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User, UserPreference


@receiver(post_save, sender=User)
def create_user_preference(sender, instance, created, **kwargs):
    """
    Create a UserPreference object when a new User is created.
    """
    if created:
        UserPreference.objects.get_or_create(user=instance)


@receiver(pre_save, sender=User)
def update_profile_status(sender, instance, **kwargs):
    """
    Update profile status based on verification status.
    """
    if not instance.pk:  # Skip for new users
        return

    try:
        old_instance = User.objects.get(pk=instance.pk)

        # If email or phone verification status changed to True
        if (not old_instance.email_verified and instance.email_verified) or \
                (not old_instance.phone_verified and instance.phone_verified):

            # Check if both are verified and profile is pending
            if instance.email_verified and instance.phone_verified and instance.profile_status == User.ProfileStatus.PENDING:
                instance.profile_status = User.ProfileStatus.ACTIVE

    except User.DoesNotExist:
        pass