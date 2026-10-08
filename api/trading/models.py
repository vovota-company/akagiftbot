from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# ============================================================
# ENUMS / CHOICES
# ============================================================


class ExchangeType(models.TextChoices):
    BINANCE = "BINANCE", "Binance"


class MarketType(models.TextChoices):
    SPOT = "SPOT", "Spot"
    FUTURES = "FUTURES", "Futures"


class BotStatus(models.TextChoices):
    CREATED = "CREATED", "Created"
    RUNNING = "RUNNING", "Running"
    PAUSED = "PAUSED", "Paused"
    STOPPED = "STOPPED", "Stopped"
    ERROR = "ERROR", "Error"


class OrderSide(models.TextChoices):
    BUY = "BUY", "Buy"
    SELL = "SELL", "Sell"


class OrderType(models.TextChoices):
    MARKET = "MARKET", "Market"
    LIMIT = "LIMIT", "Limit"
    STOP_MARKET = "STOP_MARKET", "Stop Market"
    STOP_LIMIT = "STOP_LIMIT", "Stop Limit"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET", "Take Profit Market"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT", "Take Profit Limit"


class OrderStatus(models.TextChoices):
    NEW = "NEW", "New"
    PARTIALLY_FILLED = "PARTIALLY_FILLED", "Partially Filled"
    FILLED = "FILLED", "Filled"
    CANCELED = "CANCELED", "Canceled"
    REJECTED = "REJECTED", "Rejected"
    EXPIRED = "EXPIRED", "Expired"
    EXPIRED_IN_MATCH = "EXPIRED_IN_MATCH", "Expired in Match"


class PositionSide(models.TextChoices):
    LONG = "LONG", "Long"
    SHORT = "SHORT", "Short"


class PositionStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class MarginType(models.TextChoices):
    ISOLATED = "ISOLATED", "Isolated"
    CROSS = "CROSS", "Cross"


class PositionMode(models.TextChoices):
    ONE_WAY = "ONE_WAY", "One Way"
    HEDGE = "HEDGE", "Hedge"


class TradeStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    CLOSED = "CLOSED", "Closed"


class RiskSeverity(models.TextChoices):
    INFO = "INFO", "Info"
    WARNING = "WARNING", "Warning"
    CRITICAL = "CRITICAL", "Critical"


class RiskAction(models.TextChoices):
    ALLOW = "ALLOW", "Allow"
    BLOCK = "BLOCK", "Block"
    REDUCE = "REDUCE", "Reduce"
    CLOSE = "CLOSE", "Close"
    STOP_BOT = "STOP_BOT", "Stop Bot"


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"
    ENABLE = "ENABLE", "Enable"
    DISABLE = "DISABLE", "Disable"
    START = "START", "Start"
    STOP = "STOP", "Stop"


# ============================================================
# EXCHANGE ACCOUNT
# ============================================================


class ExchangeAccount(models.Model):
    """
    Connection between one platform user and an exchange account.

    IMPORTANT:
    The owner is the Django AUTH_USER_MODEL.

    UserProfile remains a profile/extension of that user and is
    NOT used as the owner of trading records.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exchange_accounts",
    )

    exchange = models.CharField(
        max_length=30,
        choices=ExchangeType.choices,
    )

    name = models.CharField(
        max_length=100,
    )

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    # These must contain encrypted values.
    # Never store Binance API credentials in plaintext.
    encrypted_api_key = models.TextField()

    encrypted_api_secret = models.TextField()

    enabled = models.BooleanField(
        default=True,
    )

    # Platform-level permission to use this account for trading.
    can_trade = models.BooleanField(
        default=True,
    )

    # Withdrawal functionality is intentionally disabled.
    # Do not expose this as a user-editable field.
    can_withdraw = models.BooleanField(
        default=False,
        editable=False,
    )

    last_connected_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "exchange"],
            ),
            models.Index(
                fields=["enabled"],
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.exchange}"


# ============================================================
# STRATEGY
# ============================================================


class Strategy(models.Model):
    """
    Defines an available trading strategy.

    This model describes the strategy.

    The actual Python implementation lives in:
        api/trading/strategies/
    """

    name = models.CharField(
        max_length=100,
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(
        blank=True,
    )

    # Example:
    # 1.0.0
    version = models.CharField(
        max_length=30,
        default="1.0.0",
    )

    # Maps to a Python implementation.
    #
    # Examples:
    # rsi_v1
    # ema_cross_v1
    # breakout_v1
    implementation_key = models.CharField(
        max_length=100,
    )

    enabled = models.BooleanField(
        default=True,
    )

    # True = strategy provided by the platform.
    # False = potentially user-created strategy metadata.
    is_system = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["enabled"],
            ),
            models.Index(
                fields=["implementation_key"],
            ),
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


# ============================================================
# TRADING BOT
# ============================================================


class TradingBot(models.Model):
    """
    One automated trading configuration belonging to one user.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trading_bots",
    )

    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.PROTECT,
        related_name="trading_bots",
    )

    strategy = models.ForeignKey(
        Strategy,
        on_delete=models.PROTECT,
        related_name="bots",
    )

    name = models.CharField(
        max_length=100,
    )

    market_type = models.CharField(
        max_length=20,
        choices=MarketType.choices,
    )

    symbol = models.CharField(
        max_length=30,
    )

    timeframe = models.CharField(
        max_length=20,
    )

    # --------------------------------------------------------
    # FUTURES SETTINGS
    # --------------------------------------------------------

    # Futures only.
    leverage = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
        ],
    )

    # Futures only.
    margin_type = models.CharField(
        max_length=20,
        choices=MarginType.choices,
        null=True,
        blank=True,
    )

    # Futures only.
    position_mode = models.CharField(
        max_length=20,
        choices=PositionMode.choices,
        null=True,
        blank=True,
    )

    # --------------------------------------------------------
    # RISK SETTINGS
    # --------------------------------------------------------

    # 0.0100 = 1%
    # 0.0050 = 0.5%
    # 0.0200 = 2%
    risk_per_trade = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        validators=[
            MinValueValidator(Decimal("0.0001")),
            MaxValueValidator(Decimal("1.0000")),
        ],
    )

    # Maximum monetary loss allowed per day.
    max_daily_loss = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0")),
        ],
    )

    max_open_positions = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=BotStatus.choices,
        default=BotStatus.CREATED,
    )

    enabled = models.BooleanField(
        default=False,
    )

    last_heartbeat_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "status"],
            ),
            models.Index(
                fields=["exchange_account"],
            ),
            models.Index(
                fields=["symbol", "market_type"],
            ),
            models.Index(
                fields=["enabled"],
            ),
        ]

    def clean(self):
        errors = {}

        # ----------------------------------------------------
        # Ownership
        # ----------------------------------------------------

        if (
            self.exchange_account_id
            and self.user_id
            and self.exchange_account.user_id != self.user_id
        ):
            errors["exchange_account"] = (
                "The exchange account must belong to the same user as the bot."
            )

        # ----------------------------------------------------
        # Spot / Futures
        # ----------------------------------------------------

        if self.market_type == MarketType.SPOT:
            if self.leverage is not None:
                errors["leverage"] = (
                    "Leverage is only available for Futures."
                )

            if self.margin_type is not None:
                errors["margin_type"] = (
                    "Margin type is only available for Futures."
                )

            if self.position_mode is not None:
                errors["position_mode"] = (
                    "Position mode is only available for Futures."
                )

        if self.market_type == MarketType.FUTURES:
            if self.leverage is None:
                errors["leverage"] = (
                    "Leverage is required for Futures."
                )

            if self.margin_type is None:
                errors["margin_type"] = (
                    "Margin type is required for Futures."
                )

            if self.position_mode is None:
                errors["position_mode"] = (
                    "Position mode is required for Futures."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


# ============================================================
# BOT CONFIGURATION
# ============================================================


class BotConfiguration(models.Model):
    """
    Strategy-specific configuration.

    Example:

    {
        "rsi_period": 14,
        "oversold": 30,
        "overbought": 70
    }
    """

    bot = models.OneToOneField(
        TradingBot,
        on_delete=models.CASCADE,
        related_name="configuration",
    )

    parameters = models.JSONField(
        default=dict,
    )

    # Increment whenever configuration is changed.
    version = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"Configuration - {self.bot.name}"


# ============================================================
# POSITION
# ============================================================


class Position(models.Model):
    """
    Current market exposure.

    Spot:
        normally LONG only.

    Futures:
        LONG or SHORT.
    """

    bot = models.ForeignKey(
        TradingBot,
        on_delete=models.PROTECT,
        related_name="positions",
    )

    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.PROTECT,
        related_name="positions",
    )

    symbol = models.CharField(
        max_length=30,
    )

    market_type = models.CharField(
        max_length=20,
        choices=MarketType.choices,
    )

    side = models.CharField(
        max_length=10,
        choices=PositionSide.choices,
    )

    quantity = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    entry_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    mark_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )

    # Futures only.
    liquidation_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )

    stop_loss = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )

    take_profit = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )

    # Futures only.
    leverage = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
        ],
    )

    # Futures only.
    margin_type = models.CharField(
        max_length=20,
        choices=MarginType.choices,
        null=True,
        blank=True,
    )

    unrealized_pnl = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    realized_pnl = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    status = models.CharField(
        max_length=20,
        choices=PositionStatus.choices,
        default=PositionStatus.OPEN,
    )

    opened_at = models.DateTimeField(
        auto_now_add=True,
    )

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["bot", "status"],
            ),
            models.Index(
                fields=["exchange_account", "symbol"],
            ),
            models.Index(
                fields=["symbol", "market_type", "status"],
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.exchange_account_id
            and self.bot_id
            and self.exchange_account.user_id != self.bot.user_id
        ):
            errors["exchange_account"] = (
                "The exchange account must belong to the bot owner."
            )

        if self.market_type == MarketType.SPOT:
            if self.side == PositionSide.SHORT:
                errors["side"] = (
                    "Spot positions cannot be SHORT."
                )

            if self.leverage is not None:
                errors["leverage"] = (
                    "Spot positions cannot have leverage."
                )

            if self.margin_type is not None:
                errors["margin_type"] = (
                    "Spot positions cannot have margin type."
                )

        if self.market_type == MarketType.FUTURES:
            if self.leverage is None:
                errors["leverage"] = (
                    "Futures positions require leverage."
                )

            if self.margin_type is None:
                errors["margin_type"] = (
                    "Futures positions require margin type."
                )

        if self.status == PositionStatus.CLOSED:
            if self.closed_at is None:
                errors["closed_at"] = (
                    "A closed position must have closed_at."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.symbol} {self.side} {self.quantity}"


# ============================================================
# ORDER
# ============================================================


class Order(models.Model):
    """
    An instruction/request sent to the exchange.

    Order != Fill
    Order != Position
    """

    bot = models.ForeignKey(
        TradingBot,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    # ID generated by our application.
    # Used for idempotency.
    client_order_id = models.CharField(
        max_length=100,
        unique=True,
    )

    # Binance order ID.
    exchange_order_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    symbol = models.CharField(
        max_length=30,
    )

    market_type = models.CharField(
        max_length=20,
        choices=MarketType.choices,
    )

    side = models.CharField(
        max_length=10,
        choices=OrderSide.choices,
    )

    order_type = models.CharField(
        max_length=30,
        choices=OrderType.choices,
    )

    quantity = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )

    stop_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )

    filled_quantity = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    average_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=OrderStatus.choices,
        default=OrderStatus.NEW,
    )

    reduce_only = models.BooleanField(
        default=False,
    )

    post_only = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    exchange_created_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    exchange_updated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["bot", "status"],
            ),
            models.Index(
                fields=["exchange_account", "status"],
            ),
            models.Index(
                fields=["symbol", "market_type"],
            ),
            models.Index(
                fields=["exchange_order_id"],
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.exchange_account_id
            and self.bot_id
            and self.exchange_account.user_id != self.bot.user_id
        ):
            errors["exchange_account"] = (
                "The exchange account must belong to the bot owner."
            )

        if self.market_type == MarketType.SPOT:
            if self.reduce_only:
                errors["reduce_only"] = (
                    "reduce_only is only supported for Futures."
                )

        if self.order_type == OrderType.LIMIT:
            if self.price is None:
                errors["price"] = (
                    "LIMIT orders require a price."
                )

        if self.order_type in {
            OrderType.STOP_MARKET,
            OrderType.STOP_LIMIT,
            OrderType.TAKE_PROFIT_MARKET,
            OrderType.TAKE_PROFIT_LIMIT,
        }:
            if self.stop_price is None:
                errors["stop_price"] = (
                    "This order type requires stop_price."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.symbol} {self.side} {self.order_type}"


# ============================================================
# ORDER FILL
# ============================================================


class OrderFill(models.Model):
    """
    One actual execution of an order.

    One order can have multiple fills.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="fills",
    )

    # Binance trade/fill ID.
    exchange_trade_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    symbol = models.CharField(
        max_length=30,
    )

    side = models.CharField(
        max_length=10,
        choices=OrderSide.choices,
    )

    quantity = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    quote_quantity = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )

    commission = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    commission_asset = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )

    is_maker = models.BooleanField(
        null=True,
        blank=True,
    )

    executed_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["order", "executed_at"],
            ),
            models.Index(
                fields=["symbol", "executed_at"],
            ),
            models.Index(
                fields=["exchange_trade_id"],
            ),
        ]

    def __str__(self):
        return f"{self.symbol} fill {self.quantity}"


# ============================================================
# TRADE
# ============================================================


class Trade(models.Model):
    """
    A completed trading cycle / accounting record.

    Example:

        LONG BTCUSDT
        entry = 100000
        exit = 101000

    Trade records PnL.

    Order records exchange instructions.
    Position records exposure.
    """

    bot = models.ForeignKey(
        TradingBot,
        on_delete=models.PROTECT,
        related_name="trades",
    )

    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.PROTECT,
        related_name="trades",
    )

    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trades",
    )

    symbol = models.CharField(
        max_length=30,
    )

    market_type = models.CharField(
        max_length=20,
        choices=MarketType.choices,
    )

    side = models.CharField(
        max_length=10,
        choices=PositionSide.choices,
    )

    quantity = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    entry_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    # Nullable because an OPEN trade has not exited yet.
    exit_price = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        null=True,
        blank=True,
    )

    gross_pnl = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    fees = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    funding = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    net_pnl = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    status = models.CharField(
        max_length=20,
        choices=TradeStatus.choices,
        default=TradeStatus.OPEN,
    )

    opened_at = models.DateTimeField()

    closed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["bot", "status"],
            ),
            models.Index(
                fields=["bot", "closed_at"],
            ),
            models.Index(
                fields=["symbol", "closed_at"],
            ),
            models.Index(
                fields=["market_type", "closed_at"],
            ),
        ]

    def clean(self):
        errors = {}

        if self.status == TradeStatus.OPEN:
            if self.exit_price is not None:
                errors["exit_price"] = (
                    "An open trade cannot have an exit price."
                )

            if self.closed_at is not None:
                errors["closed_at"] = (
                    "An open trade cannot have closed_at."
                )

        if self.status == TradeStatus.CLOSED:
            if self.exit_price is None:
                errors["exit_price"] = (
                    "A closed trade must have an exit price."
                )

            if self.closed_at is None:
                errors["closed_at"] = (
                    "A closed trade must have closed_at."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.symbol} trade"


# ============================================================
# ACCOUNT BALANCE
# ============================================================


class AccountBalance(models.Model):
    """
    Historical exchange balance snapshot.

    This is NOT the same thing as the platform's internal wallet.
    """

    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.PROTECT,
        related_name="balances",
    )

    asset = models.CharField(
        max_length=30,
    )

    market_type = models.CharField(
        max_length=20,
        choices=MarketType.choices,
    )

    wallet_balance = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    available_balance = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    locked_balance = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    unrealized_pnl = models.DecimalField(
        max_digits=30,
        decimal_places=12,
        default=Decimal("0"),
    )

    snapshot_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "exchange_account",
                    "asset",
                    "market_type",
                    "snapshot_at",
                ],
            ),
        ]

    def __str__(self):
        return f"{self.asset} balance"


# ============================================================
# FUNDING PAYMENT
# ============================================================


class FundingPayment(models.Model):
    """
    Futures funding payment received/paid by the exchange account.
    """

    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.PROTECT,
        related_name="funding_payments",
    )

    bot = models.ForeignKey(
        TradingBot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="funding_payments",
    )

    symbol = models.CharField(
        max_length=30,
    )

    asset = models.CharField(
        max_length=30,
    )

    amount = models.DecimalField(
        max_digits=30,
        decimal_places=12,
    )

    funding_rate = models.DecimalField(
        max_digits=20,
        decimal_places=12,
        null=True,
        blank=True,
    )

    position_side = models.CharField(
        max_length=10,
        choices=PositionSide.choices,
        null=True,
        blank=True,
    )

    exchange_transaction_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    occurred_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "exchange_account",
                    "occurred_at",
                ],
            ),
            models.Index(
                fields=[
                    "symbol",
                    "occurred_at",
                ],
            ),
            models.Index(
                fields=[
                    "exchange_transaction_id",
                ],
            ),
        ]

    def __str__(self):
        return f"{self.symbol} funding"


# ============================================================
# RISK EVENT
# ============================================================


class RiskEvent(models.Model):
    """
    Immutable-ish record of a risk decision.

    Examples:
        DAILY_LOSS_LIMIT
        INSUFFICIENT_MARGIN
        MAX_POSITION_SIZE
        LEVERAGE_TOO_HIGH
        ACCOUNT_DISABLED
        MARKET_DATA_STALE
    """

    bot = models.ForeignKey(
        TradingBot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_events",
    )

    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_events",
    )

    severity = models.CharField(
        max_length=20,
        choices=RiskSeverity.choices,
    )

    action = models.CharField(
        max_length=20,
        choices=RiskAction.choices,
    )

    code = models.CharField(
        max_length=100,
    )

    message = models.TextField()

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    occurred_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["bot", "occurred_at"],
            ),
            models.Index(
                fields=["severity", "occurred_at"],
            ),
            models.Index(
                fields=["code", "occurred_at"],
            ),
        ]

    def __str__(self):
        return f"{self.severity}: {self.code}"


# ============================================================
# TRADING EVENT
# ============================================================


class TradingEvent(models.Model):
    """
    Operational/event timeline.

    Examples:

        SIGNAL_GENERATED
        ORDER_CREATED
        ORDER_SUBMITTED
        ORDER_FILLED
        POSITION_OPENED
        POSITION_CLOSED
        STOP_LOSS_TRIGGERED
        TAKE_PROFIT_TRIGGERED
        BOT_STARTED
        BOT_STOPPED
        RECONCILIATION_FAILED
    """

    bot = models.ForeignKey(
        TradingBot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trading_events",
    )

    exchange_account = models.ForeignKey(
        ExchangeAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trading_events",
    )

    event_type = models.CharField(
        max_length=100,
    )

    symbol = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )

    message = models.TextField()

    data = models.JSONField(
        default=dict,
        blank=True,
    )

    occurred_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["bot", "occurred_at"],
            ),
            models.Index(
                fields=["event_type", "occurred_at"],
            ),
            models.Index(
                fields=["symbol", "occurred_at"],
            ),
        ]

    def __str__(self):
        return self.event_type


# ============================================================
# AUDIT LOG
# ============================================================


class AuditLog(models.Model):
    """
    Security/audit trail.

    Example:

        User changed bot leverage from 5x to 10x.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=30,
        choices=AuditAction.choices,
    )

    resource_type = models.CharField(
        max_length=100,
    )

    resource_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
    )

    old_values = models.JSONField(
        default=dict,
        blank=True,
    )

    new_values = models.JSONField(
        default=dict,
        blank=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "created_at"],
            ),
            models.Index(
                fields=[
                    "resource_type",
                    "resource_id",
                ],
            ),
            models.Index(
                fields=["action", "created_at"],
            ),
        ]

    def __str__(self):
        return f"{self.action} {self.resource_type}"
