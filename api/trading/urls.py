from rest_framework.routers import DefaultRouter

from .views import (
    AccountBalanceViewSet,
    AuditLogViewSet,
    BotConfigurationViewSet,
    ExchangeAccountViewSet,
    FundingPaymentViewSet,
    OrderFillViewSet,
    OrderViewSet,
    PositionViewSet,
    RiskEventViewSet,
    StrategyViewSet,
    TradeViewSet,
    TradingBotViewSet,
    TradingEventViewSet,
)


router = DefaultRouter()

# ============================================================
# EXCHANGE ACCOUNTS
# ============================================================

router.register(
    r"exchange-accounts",
    ExchangeAccountViewSet,
    basename="exchange-account",
)


# ============================================================
# STRATEGIES
# ============================================================

router.register(
    r"strategies",
    StrategyViewSet,
    basename="strategy",
)


# ============================================================
# TRADING BOTS
# ============================================================

router.register(
    r"bots",
    TradingBotViewSet,
    basename="trading-bot",
)


# ============================================================
# BOT CONFIGURATIONS
# ============================================================

router.register(
    r"bot-configurations",
    BotConfigurationViewSet,
    basename="bot-configuration",
)


# ============================================================
# POSITIONS
# ============================================================

router.register(
    r"positions",
    PositionViewSet,
    basename="position",
)


# ============================================================
# ORDERS
# ============================================================

router.register(
    r"orders",
    OrderViewSet,
    basename="order",
)


# ============================================================
# ORDER FILLS
# ============================================================

router.register(
    r"order-fills",
    OrderFillViewSet,
    basename="order-fill",
)


# ============================================================
# TRADES
# ============================================================

router.register(
    r"trades",
    TradeViewSet,
    basename="trade",
)


# ============================================================
# ACCOUNT BALANCES
# ============================================================

router.register(
    r"account-balances",
    AccountBalanceViewSet,
    basename="account-balance",
)


# ============================================================
# FUNDING PAYMENTS
# ============================================================

router.register(
    r"funding-payments",
    FundingPaymentViewSet,
    basename="funding-payment",
)


# ============================================================
# RISK EVENTS
# ============================================================

router.register(
    r"risk-events",
    RiskEventViewSet,
    basename="risk-event",
)


# ============================================================
# TRADING EVENTS
# ============================================================

router.register(
    r"events",
    TradingEventViewSet,
    basename="trading-event",
)


# ============================================================
# AUDIT LOGS
# ============================================================

router.register(
    r"audit-logs",
    AuditLogViewSet,
    basename="audit-log",
)


urlpatterns = router.urls
