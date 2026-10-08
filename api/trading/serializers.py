from rest_framework import serializers

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


class ExchangeAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeAccount
        fields = [
            "id",
            "user",
            "exchange",
            "name",
            "encrypted_api_key",
            "encrypted_api_secret",
            "enabled",
            "can_trade",
            "can_withdraw",
            "last_connected_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "can_withdraw",
            "last_connected_at",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "encrypted_api_key": {
                "write_only": True,
            },
            "encrypted_api_secret": {
                "write_only": True,
            },
        }


# ============================================================
# STRATEGY
# ============================================================


class StrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = Strategy
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "version",
            "implementation_key",
            "enabled",
            "is_system",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


# ============================================================
# TRADING BOT
# ============================================================


class TradingBotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingBot
        fields = [
            "id",
            "user",
            "exchange_account",
            "strategy",
            "name",
            "market_type",
            "symbol",
            "timeframe",
            "leverage",
            "margin_type",
            "position_mode",
            "risk_per_trade",
            "max_daily_loss",
            "max_open_positions",
            "status",
            "enabled",
            "last_heartbeat_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "last_heartbeat_at",
            "created_at",
            "updated_at",
        ]


# ============================================================
# BOT CONFIGURATION
# ============================================================


class BotConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotConfiguration
        fields = [
            "id",
            "bot",
            "parameters",
            "version",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "version",
            "created_at",
            "updated_at",
        ]


# ============================================================
# POSITION
# ============================================================


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = [
            "id",
            "bot",
            "exchange_account",
            "symbol",
            "market_type",
            "side",
            "quantity",
            "entry_price",
            "mark_price",
            "liquidation_price",
            "stop_loss",
            "take_profit",
            "leverage",
            "margin_type",
            "unrealized_pnl",
            "realized_pnl",
            "status",
            "opened_at",
            "closed_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "unrealized_pnl",
            "realized_pnl",
            "status",
            "opened_at",
            "closed_at",
            "updated_at",
        ]


# ============================================================
# ORDER
# ============================================================


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "bot",
            "exchange_account",
            "position",
            "client_order_id",
            "exchange_order_id",
            "symbol",
            "market_type",
            "side",
            "order_type",
            "quantity",
            "price",
            "stop_price",
            "filled_quantity",
            "average_price",
            "status",
            "reduce_only",
            "post_only",
            "created_at",
            "updated_at",
            "exchange_created_at",
            "exchange_updated_at",
        ]
        read_only_fields = [
            "id",
            "client_order_id",
            "exchange_order_id",
            "filled_quantity",
            "average_price",
            "status",
            "created_at",
            "updated_at",
            "exchange_created_at",
            "exchange_updated_at",
        ]


# ============================================================
# ORDER FILL
# ============================================================


class OrderFillSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderFill
        fields = [
            "id",
            "order",
            "exchange_trade_id",
            "symbol",
            "side",
            "quantity",
            "price",
            "quote_quantity",
            "commission",
            "commission_asset",
            "is_maker",
            "executed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "exchange_trade_id",
            "quote_quantity",
            "commission",
            "commission_asset",
            "is_maker",
            "executed_at",
            "created_at",
        ]


# ============================================================
# TRADE
# ============================================================


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = [
            "id",
            "bot",
            "exchange_account",
            "position",
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
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "gross_pnl",
            "fees",
            "funding",
            "net_pnl",
            "status",
            "closed_at",
            "created_at",
            "updated_at",
        ]


# ============================================================
# ACCOUNT BALANCE
# ============================================================


class AccountBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountBalance
        fields = [
            "id",
            "exchange_account",
            "asset",
            "market_type",
            "wallet_balance",
            "available_balance",
            "locked_balance",
            "unrealized_pnl",
            "snapshot_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "wallet_balance",
            "available_balance",
            "locked_balance",
            "unrealized_pnl",
            "snapshot_at",
            "created_at",
        ]


# ============================================================
# FUNDING PAYMENT
# ============================================================


class FundingPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingPayment
        fields = [
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
            "created_at",
        ]
        read_only_fields = [
            "id",
            "amount",
            "funding_rate",
            "exchange_transaction_id",
            "occurred_at",
            "created_at",
        ]


# ============================================================
# RISK EVENT
# ============================================================


class RiskEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskEvent
        fields = [
            "id",
            "bot",
            "exchange_account",
            "severity",
            "action",
            "code",
            "message",
            "metadata",
            "occurred_at",
        ]
        read_only_fields = [
            "id",
            "severity",
            "action",
            "code",
            "message",
            "metadata",
            "occurred_at",
        ]


# ============================================================
# TRADING EVENT
# ============================================================


class TradingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingEvent
        fields = [
            "id",
            "bot",
            "exchange_account",
            "event_type",
            "symbol",
            "message",
            "data",
            "occurred_at",
        ]
        read_only_fields = [
            "id",
            "event_type",
            "symbol",
            "message",
            "data",
            "occurred_at",
        ]


# ============================================================
# AUDIT LOG
# ============================================================


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
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
        ]
        read_only_fields = [
            "id",
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
        ]
