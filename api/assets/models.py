import uuid

from django.db import models


class ReferralStats(models.Model):
    V1 = "V1"
    V2 = "V2"
    V3 = "V3"
    V4 = "V4"
    V5 = "V5"
    V6 = "V6"

    LEVEL_CHOICES = [
        (V1, "V1"),
        (V2, "V2"),
        (V3, "V3"),
        (V4, "V4"),
        (V5, "V5"),
        (V6, "V6"),
    ]

    profile = models.OneToOneField(
        "api_auth.UserProfile",
        on_delete=models.CASCADE,
        related_name="referral_stats",
    )

    level = models.CharField(
        max_length=2,
        choices=LEVEL_CHOICES,
        default=V1,
    )

    direct_count = models.PositiveIntegerField(default=0)
    network_count = models.PositiveIntegerField(default=0)

    v2_leader_count = models.PositiveIntegerField(default=0)
    v3_leader_count = models.PositiveIntegerField(default=0)
    v4_leader_count = models.PositiveIntegerField(default=0)
    v5_leader_count = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.profile.user.email} - {self.level}"


class AssetBalance(models.Model):
    profile = models.OneToOneField(
        "api_auth.UserProfile",
        on_delete=models.CASCADE,
        related_name="asset_balance",
    )

    available_usdt = models.DecimalField(
        max_digits=40,
        decimal_places=18,
        default=0,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.profile.user.email}: {self.available_usdt} USDT"


class ReferralEvent(models.Model):
    event_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    new_user = models.OneToOneField(
        "api_auth.UserProfile",
        on_delete=models.PROTECT,
        related_name="referral_event",
    )

    sponsor = models.ForeignKey(
        "api_auth.UserProfile",
        on_delete=models.PROTECT,
        related_name="sponsored_referral_events",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_id} - {self.new_user.user.email}"


class ReferralCommission(models.Model):
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"

    COMMISSION_TYPES = [
        (DIRECT, "Direct"),
        (INDIRECT, "Indirect"),
    ]

    event = models.ForeignKey(
        ReferralEvent,
        on_delete=models.PROTECT,
        related_name="commissions",
    )

    recipient = models.ForeignKey(
        "api_auth.UserProfile",
        on_delete=models.PROTECT,
        related_name="referral_commissions_received",
    )

    source_user = models.ForeignKey(
        "api_auth.UserProfile",
        on_delete=models.PROTECT,
        related_name="referral_commissions_generated",
    )

    commission_type = models.CharField(
        max_length=10,
        choices=COMMISSION_TYPES,
    )

    generation = models.PositiveIntegerField(default=0)

    amount = models.DecimalField(
        max_digits=40,
        decimal_places=18,
    )

    currency = models.CharField(
        max_length=10,
        default="USDT",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "event",
                    "recipient",
                    "commission_type",
                    "generation",
                ],
                name="unique_referral_commission",
            )
        ]

    def __str__(self):
        return (
            f"{self.recipient.user.email} "
            f"{self.commission_type} "
            f"{self.amount} USDT"
        )


class AssetLedgerEntry(models.Model):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

    DIRECTIONS = [
        (CREDIT, "Credit"),
        (DEBIT, "Debit"),
    ]

    REFERRAL_DIRECT = "REFERRAL_DIRECT"
    REFERRAL_INDIRECT = "REFERRAL_INDIRECT"
    ADJUSTMENT = "ADJUSTMENT"

    ENTRY_TYPES = [
        (REFERRAL_DIRECT, "Referral direct"),
        (REFERRAL_INDIRECT, "Referral indirect"),
        (ADJUSTMENT, "Adjustment"),
    ]

    profile = models.ForeignKey(
        "api_auth.UserProfile",
        on_delete=models.PROTECT,
        related_name="asset_ledger",
    )

    direction = models.CharField(
        max_length=6,
        choices=DIRECTIONS,
    )

    entry_type = models.CharField(
        max_length=32,
        choices=ENTRY_TYPES,
    )

    amount = models.DecimalField(
        max_digits=40,
        decimal_places=18,
    )

    balance_after = models.DecimalField(
        max_digits=40,
        decimal_places=18,
    )

    currency = models.CharField(
        max_length=10,
        default="USDT",
    )

    referral_commission = models.OneToOneField(
        ReferralCommission,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ledger_entry",
    )

    reference = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.profile.user.email} "
            f"{self.direction} "
            f"{self.amount} USDT"
        )
