from django.conf import settings
from django.db import models
import secrets
import string


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    google_sub = models.CharField(
        max_length=255,
        unique=True,
    )

    referral_code = models.CharField(
        max_length=6,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )

    referred_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="referrals",
    )

    is_active = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    @classmethod
    def generate_referral_code(cls):
        alphabet = string.ascii_uppercase + string.digits

        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(6))

            if not cls.objects.filter(referral_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.email
