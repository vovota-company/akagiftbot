from django.contrib import admin

from .models import (
    AssetBalance,
    AssetLedgerEntry,
    ReferralCommission,
    ReferralEvent,
    ReferralStats,
)


@admin.register(ReferralStats)
class ReferralStatsAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "level",
        "direct_count",
        "network_count",
        "v2_leader_count",
        "v3_leader_count",
        "v4_leader_count",
        "v5_leader_count",
    )
    search_fields = (
        "profile__user__email",
        "profile__referral_code",
    )
    list_filter = ("level",)


@admin.register(AssetBalance)
class AssetBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "available_usdt",
        "updated_at",
    )
    search_fields = (
        "profile__user__email",
    )


@admin.register(ReferralEvent)
class ReferralEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_id",
        "new_user",
        "sponsor",
        "created_at",
    )
    search_fields = (
        "new_user__user__email",
        "sponsor__user__email",
        "event_id",
    )


@admin.register(ReferralCommission)
class ReferralCommissionAdmin(admin.ModelAdmin):
    list_display = (
        "recipient",
        "source_user",
        "commission_type",
        "generation",
        "amount",
        "currency",
        "created_at",
    )
    search_fields = (
        "recipient__user__email",
        "source_user__user__email",
    )
    list_filter = (
        "commission_type",
        "generation",
    )


@admin.register(AssetLedgerEntry)
class AssetLedgerEntryAdmin(admin.ModelAdmin):
    list_display = (
        "profile",
        "direction",
        "entry_type",
        "amount",
        "balance_after",
        "currency",
        "created_at",
    )
    search_fields = (
        "profile__user__email",
        "reference",
    )
    list_filter = (
        "direction",
        "entry_type",
    )
