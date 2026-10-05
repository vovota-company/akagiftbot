from django.db.models.signals import post_save
from django.dispatch import receiver

from api.auth.models import UserProfile

from .models import ReferralEvent
from .services import process_new_referral


@receiver(
    post_save,
    sender=UserProfile,
)
def process_user_referral(
    sender,
    instance,
    created,
    **kwargs,
):
    """
    When a UserProfile has a sponsor, process the referral
    exactly once.

    This works whether referred_by was assigned during
    profile creation or immediately afterward.
    """

    if not instance.referred_by_id:
        return

    if ReferralEvent.objects.filter(
        new_user=instance
    ).exists():
        return

    # Run after the current DB transaction successfully commits.
    from django.db import transaction

    transaction.on_commit(
        lambda: process_new_referral(instance.pk)
    )
