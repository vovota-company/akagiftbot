from django.conf import settings
from django.db import models
import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    google_sub = models.CharField(
        max_length=255,
        unique=True
    )

    referral_code = models.CharField(
        max_length=32,
        unique=True,
        null=True,
        blank=True
    )

    referred_by = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='referrals'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = uuid.uuid4().hex[:12].upper()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.email
