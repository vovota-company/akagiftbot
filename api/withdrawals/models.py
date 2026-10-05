from django.conf import settings
from django.db import models


class Withdrawal(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    ASSET_USDT = "USDT"
    ASSET_CHOICES = [
        (ASSET_USDT, "USDT"),
    ]

    NETWORK_BSC = "bsc"
    NETWORK_CHOICES = [
        (NETWORK_BSC, "BNB Smart Chain"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="withdrawals",
    )

    asset = models.CharField(
        max_length=16,
        choices=ASSET_CHOICES,
        default=ASSET_USDT,
    )

    network = models.CharField(
        max_length=20,
        choices=NETWORK_CHOICES,
        default=NETWORK_BSC,
    )

    amount = models.DecimalField(
        max_digits=36,
        decimal_places=18,
    )

    fee = models.DecimalField(
        max_digits=36,
        decimal_places=18,
        default=0,
    )

    destination_address = models.CharField(
        max_length=42,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    tx_hash = models.CharField(
        max_length=66,
        blank=True,
        default="",
        db_index=True,
    )

    idempotency_key = models.CharField(
        max_length=128,
        unique=True,
    )

    error_message = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.email} -> "
            f"{self.destination_address} "
            f"{self.amount} {self.asset}"
        )
