from django.contrib import admin

from .models import Withdrawal


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "amount",
        "asset",
        "destination_address",
        "status",
        "tx_hash",
        "created_at",
    )

    list_filter = (
        "status",
        "asset",
        "network",
    )

    search_fields = (
        "user__email",
        "destination_address",
        "tx_hash",
        "idempotency_key",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "completed_at",
    )
