from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import (
    AccountBalance,
    AuditLog,
    BotConfiguration,
    ExchangeAccount,
    FundingPayment,
    Order,
    OrderFill,
    Position,
    RiskEvent,
    Strategy,
    Trade,
    TradingBot,
    TradingEvent,
)


# ============================================================
# EXCHANGE ACCOUNT
# ============================================================

@admin.register(ExchangeAccount)
class ExchangeAccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "name",
        "exchange",
        "enabled",
        "can_trade",
        "can_withdraw",
        "last_connected_at",
        "created_at",
    )

    list_filter = (
        "exchange",
        "enabled",
        "can_trade",
        "created_at",
    )

    search_fields = (
        "name",
        "user__email",
        "user__username",
    )

    readonly_fields = (
        "can_withdraw",
        "last_connected_at",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)


# ============================================================
# STRATEGY
# ============================================================

@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "version",
        "implementation_key",
        "is_system",
        "enabled",
        "created_at",
    )

    list_filter = (
        "enabled",
        "is_system",
    )

    search_fields = (
        "name",
        "slug",
        "implementation_key",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    ordering = ("name",)


# ============================================================
# TRADING BOT
# ============================================================

@admin.register(TradingBot)
class TradingBotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "user",
        "exchange_account",
        "strategy",
        "market_type",
        "symbol",
        "timeframe",
        "leverage",
        "margin_type",
        "status",
        "enabled",
        "last_heartbeat_at",
        "created_at",
    )

    list_filter = (
        "market_type",
        "status",
        "enabled",
        "margin_type",
        "position_mode",
        "strategy",
    )

    search_fields = (
        "name",
        "symbol",
        "user__email",
        "user__username",
        "exchange_account__name",
    )

    readonly_fields = (
        "last_heartbeat_at",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "user",
        "exchange_account",
        "strategy",
    )

    ordering = ("-created_at",)


# ============================================================
# BOT CONFIGURATION
# ============================================================

@admin.register(BotConfiguration)
class BotConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bot",
        "version",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "bot__name",
        "bot__symbol",
        "bot__user__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "bot",
    )

    ordering = ("-updated_at",)


# ============================================================
# POSITION
# ============================================================

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bot",
        "exchange_account",
        "symbol",
        "market_type",
        "side",
        "quantity",
        "entry_price",
        "mark_price",
        "unrealized_pnl",
        "realized_pnl",
        "status",
        "opened_at",
        "closed_at",
    )

    list_filter = (
        "market_type",
        "side",
        "status",
        "margin_type",
    )

    search_fields = (
        "symbol",
        "bot__name",
        "bot__user__email",
        "exchange_account__name",
    )

    readonly_fields = (
        "opened_at",
        "updated_at",
    )

    autocomplete_fields = (
        "bot",
        "exchange_account",
    )

    ordering = ("-opened_at",)


# ============================================================
# ORDER
# ============================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bot",
        "symbol",
        "market_type",
        "side",
        "order_type",
        "quantity",
        "filled_quantity",
        "average_price",
        "status",
        "reduce_only",
        "post_only",
        "exchange_order_id",
        "created_at",
    )

    list_filter = (
        "market_type",
        "side",
        "order_type",
        "status",
        "reduce_only",
        "post_only",
    )

    search_fields = (
        "symbol",
        "client_order_id",
        "exchange_order_id",
        "bot__name",
        "bot__user__email",
    )

    readonly_fields = (
        "client_order_id",
        "exchange_order_id",
        "exchange_created_at",
        "exchange_updated_at",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "bot",
        "exchange_account",
        "position",
    )

    ordering = ("-created_at",)


# ============================================================
# ORDER FILL
# ============================================================

@admin.register(OrderFill)
class OrderFillAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "symbol",
        "side",
        "quantity",
        "price",
        "quote_quantity",
        "commission",
        "commission_asset",
        "is_maker",
        "executed_at",
    )

    list_filter = (
        "side",
        "is_maker",
        "commission_asset",
    )

    search_fields = (
        "symbol",
        "exchange_trade_id",
        "order__client_order_id",
        "order__exchange_order_id",
    )

    readonly_fields = (
        "created_at",
    )

    autocomplete_fields = (
        "order",
    )

    ordering = ("-executed_at",)


# ============================================================
# TRADE
# ============================================================

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bot",
        "symbol",
        "market_type",
        "side",
        "quantity",
        "entry_price",
        "exit_price",
        "gross_pnl",
        "fees",
        "funding",
        "net_pnl",
        "status",
        "opened_at",
        "closed_at",
    )

    list_filter = (
        "market_type",
        "side",
        "status",
    )

    search_fields = (
        "symbol",
        "bot__name",
        "bot__user__email",
        "exchange_account__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "bot",
        "exchange_account",
        "position",
    )

    ordering = ("-opened_at",)


# ============================================================
# ACCOUNT BALANCE
# ============================================================

@admin.register(AccountBalance)
class AccountBalanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "exchange_account",
        "asset",
        "market_type",
        "wallet_balance",
        "available_balance",
        "locked_balance",
        "unrealized_pnl",
        "snapshot_at",
    )

    list_filter = (
        "market_type",
        "asset",
    )

    search_fields = (
        "asset",
        "exchange_account__name",
        "exchange_account__user__email",
    )

    readonly_fields = (
        "created_at",
    )

    autocomplete_fields = (
        "exchange_account",
    )

    ordering = ("-snapshot_at",)


# ============================================================
# FUNDING PAYMENT
# ============================================================

@admin.register(FundingPayment)
class FundingPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "exchange_account",
        "bot",
        "symbol",
        "asset",
        "amount",
        "funding_rate",
        "position_side",
        "exchange_transaction_id",
        "occurred_at",
    )

    list_filter = (
        "asset",
        "position_side",
    )

    search_fields = (
        "symbol",
        "asset",
        "exchange_transaction_id",
        "exchange_account__name",
        "bot__name",
        "bot__user__email",
    )

    readonly_fields = (
        "created_at",
    )

    autocomplete_fields = (
        "exchange_account",
        "bot",
    )

    ordering = ("-occurred_at",)


# ============================================================
# RISK EVENT
# ============================================================

@admin.register(RiskEvent)
class RiskEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bot",
        "exchange_account",
        "severity",
        "action",
        "code",
        "occurred_at",
    )

    list_filter = (
        "severity",
        "action",
        "code",
    )

    search_fields = (
        "code",
        "message",
        "bot__name",
        "bot__user__email",
        "exchange_account__name",
    )

    readonly_fields = (
        "occurred_at",
    )

    autocomplete_fields = (
        "bot",
        "exchange_account",
    )

    ordering = ("-occurred_at",)


# ============================================================
# TRADING EVENT
# ============================================================

@admin.register(TradingEvent)
class TradingEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bot",
        "exchange_account",
        "event_type",
        "symbol",
        "occurred_at",
    )

    list_filter = (
        "event_type",
    )

    search_fields = (
        "event_type",
        "symbol",
        "message",
        "bot__name",
        "bot__user__email",
        "exchange_account__name",
    )

    readonly_fields = (
        "occurred_at",
    )

    autocomplete_fields = (
        "bot",
        "exchange_account",
    )

    ordering = ("-occurred_at",)


# ============================================================
# AUDIT LOG
# ============================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "created_at",
    )

    list_filter = (
        "action",
        "resource_type",
    )

    search_fields = (
        "resource_type",
        "resource_id",
        "user__email",
        "user__username",
        "ip_address",
    )

    readonly_fields = (
        "user",
        "action",
        "resource_type",
        "resource_id",
        "ip_address",
        "user_agent",
        "old_values",
        "new_values",
        "metadata",
        "created_at",
    )

    autocomplete_fields = (
        "user",
    )

    ordering = ("-created_at",)
