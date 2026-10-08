from django.shortcuts import render

# Create your views here.
from uuid import uuid4

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
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
    BotStatus,
    OrderStatus,
)
from .serializers import (
    AccountBalanceSerializer,
    AuditLogSerializer,
    BotConfigurationSerializer,
    ExchangeAccountSerializer,
    FundingPaymentSerializer,
    OrderFillSerializer,
    OrderSerializer,
    PositionSerializer,
    RiskEventSerializer,
    StrategySerializer,
    TradeSerializer,
    TradingBotSerializer,
    TradingEventSerializer,
)


# ============================================================
# COMMON RESPONSE SCHEMAS
# ============================================================


ActionResponseSerializer = inline_serializer(
    name="TradingActionResponse",
    fields={
        "success": serializers.BooleanField(),
        "message": serializers.CharField(),
        "status": serializers.CharField(),
    },
)


# ============================================================
# EXCHANGE ACCOUNTS
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List exchange accounts",
        description=(
            "Returns exchange accounts belonging to the authenticated user. "
            "Credentials are never returned."
        ),
        responses=ExchangeAccountSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get exchange account",
        responses=ExchangeAccountSerializer,
    ),
    create=extend_schema(
        summary="Create exchange account",
        description=(
            "Creates an exchange account connection for the authenticated user. "
            "API credentials are accepted only through the request and are never "
            "returned in API responses."
        ),
        request=ExchangeAccountSerializer,
        responses={
            201: ExchangeAccountSerializer,
            400: OpenApiResponse(description="Invalid exchange account data."),
        },
        examples=[
            OpenApiExample(
                "Binance account",
                value={
                    "exchange": "BINANCE",
                    "name": "My Binance Account",
                    "encrypted_api_key": "encrypted-value",
                    "encrypted_api_secret": "encrypted-value",
                    "enabled": True,
                    "can_trade": True,
                },
                request_only=True,
            ),
        ],
    ),
    update=extend_schema(
        summary="Update exchange account",
        request=ExchangeAccountSerializer,
        responses=ExchangeAccountSerializer,
    ),
    partial_update=extend_schema(
        summary="Partially update exchange account",
        request=ExchangeAccountSerializer,
        responses=ExchangeAccountSerializer,
    ),
    destroy=extend_schema(
        summary="Delete exchange account",
        description="Deletes an exchange account belonging to the authenticated user.",
        responses={204: OpenApiResponse(description="Exchange account deleted.")},
    ),
)
class ExchangeAccountViewSet(viewsets.ModelViewSet):
    serializer_class = ExchangeAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            ExchangeAccount.objects
            .filter(user=self.request.user)
            .select_related("user")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()

        if instance.user_id != self.request.user.id:
            raise PermissionDenied("You do not own this exchange account.")

        serializer.save(user=self.request.user)


# ============================================================
# STRATEGIES
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List trading strategies",
        description=(
            "Returns enabled strategies available to the trading platform."
        ),
        responses=StrategySerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get trading strategy",
        responses=StrategySerializer,
    ),
)
class StrategyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Strategy.objects.filter(enabled=True).order_by("name")


# ============================================================
# TRADING BOTS
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List trading bots",
        description="Returns only trading bots belonging to the authenticated user.",
        responses=TradingBotSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get trading bot",
        responses=TradingBotSerializer,
    ),
    create=extend_schema(
        summary="Create trading bot",
        request=TradingBotSerializer,
        responses={
            201: TradingBotSerializer,
            400: OpenApiResponse(description="Invalid bot configuration."),
        },
    ),
    update=extend_schema(
        summary="Update trading bot",
        request=TradingBotSerializer,
        responses=TradingBotSerializer,
    ),
    partial_update=extend_schema(
        summary="Partially update trading bot",
        request=TradingBotSerializer,
        responses=TradingBotSerializer,
    ),
    destroy=extend_schema(
        summary="Delete trading bot",
        responses={204: OpenApiResponse(description="Trading bot deleted.")},
    ),
)
class TradingBotViewSet(viewsets.ModelViewSet):
    serializer_class = TradingBotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            TradingBot.objects
            .filter(user=self.request.user)
            .select_related(
                "user",
                "exchange_account",
                "strategy",
            )
            .order_by("-created_at")
        )

    def _validate_exchange_account(self, exchange_account):
        if exchange_account.user_id != self.request.user.id:
            raise PermissionDenied(
                "The exchange account does not belong to you."
            )

        if not exchange_account.enabled:
            raise ValidationError(
                {"exchange_account": "This exchange account is disabled."}
            )

    def perform_create(self, serializer):
        exchange_account = serializer.validated_data["exchange_account"]

        self._validate_exchange_account(exchange_account)

        if not exchange_account.can_trade:
            raise ValidationError(
                {"exchange_account": "Trading is disabled for this account."}
            )

        serializer.save(
            user=self.request.user,
            status=BotStatus.CREATED,
        )

    def perform_update(self, serializer):
        bot = self.get_object()

        if bot.user_id != self.request.user.id:
            raise PermissionDenied("You do not own this bot.")

        if "exchange_account" in serializer.validated_data:
            self._validate_exchange_account(
                serializer.validated_data["exchange_account"]
            )

        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Start trading bot",
        description=(
            "Starts a trading bot. The trading worker is responsible for "
            "actual market execution."
        ),
        request=None,
        responses={
            200: ActionResponseSerializer,
            400: OpenApiResponse(description="Bot cannot be started."),
        },
    )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def start(self, request, pk=None):
        bot = self.get_object()

        if bot.status == BotStatus.RUNNING:
            return Response(
                {
                    "success": True,
                    "message": "Trading bot is already running.",
                    "status": bot.status,
                }
            )

        if not bot.exchange_account.enabled:
            raise ValidationError(
                {"exchange_account": "The exchange account is disabled."}
            )

        if not bot.exchange_account.can_trade:
            raise ValidationError(
                {"exchange_account": "Trading is disabled for this account."}
            )

        if not bot.strategy.enabled:
            raise ValidationError(
                {"strategy": "The selected strategy is disabled."}
            )

        bot.status = BotStatus.RUNNING
        bot.enabled = True
        bot.save(
            update_fields=[
                "status",
                "enabled",
                "updated_at",
            ]
        )

        return Response(
            {
                "success": True,
                "message": "Trading bot started.",
                "status": bot.status,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Pause trading bot",
        description=(
            "Pauses a running trading bot. Existing exchange positions are "
            "not automatically closed by this API action."
        ),
        request=None,
        responses={
            200: ActionResponseSerializer,
            400: OpenApiResponse(description="Bot cannot be paused."),
        },
    )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def pause(self, request, pk=None):
        bot = self.get_object()

        if bot.status == BotStatus.PAUSED:
            return Response(
                {
                    "success": True,
                    "message": "Trading bot is already paused.",
                    "status": bot.status,
                }
            )

        bot.status = BotStatus.PAUSED
        bot.enabled = False
        bot.save(
            update_fields=[
                "status",
                "enabled",
                "updated_at",
            ]
        )

        return Response(
            {
                "success": True,
                "message": "Trading bot paused.",
                "status": bot.status,
            }
        )

    @extend_schema(
        summary="Stop trading bot",
        description=(
            "Stops a trading bot. This does not automatically close an "
            "existing exchange position."
        ),
        request=None,
        responses={
            200: ActionResponseSerializer,
            400: OpenApiResponse(description="Bot cannot be stopped."),
        },
    )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def stop(self, request, pk=None):
        bot = self.get_object()

        bot.status = BotStatus.STOPPED
        bot.enabled = False

        bot.save(
            update_fields=[
                "status",
                "enabled",
                "updated_at",
            ]
        )

        return Response(
            {
                "success": True,
                "message": "Trading bot stopped.",
                "status": bot.status,
            }
        )


# ============================================================
# BOT CONFIGURATION
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List bot configurations",
        responses=BotConfigurationSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get bot configuration",
        responses=BotConfigurationSerializer,
    ),
    create=extend_schema(
        summary="Create bot configuration",
        request=BotConfigurationSerializer,
        responses=BotConfigurationSerializer,
    ),
    update=extend_schema(
        summary="Update bot configuration",
        request=BotConfigurationSerializer,
        responses=BotConfigurationSerializer,
    ),
    partial_update=extend_schema(
        summary="Partially update bot configuration",
        request=BotConfigurationSerializer,
        responses=BotConfigurationSerializer,
    ),
    destroy=extend_schema(
        summary="Delete bot configuration",
        responses={204: OpenApiResponse(description="Configuration deleted.")},
    ),
)
class BotConfigurationViewSet(viewsets.ModelViewSet):
    serializer_class = BotConfigurationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            BotConfiguration.objects
            .filter(bot__user=self.request.user)
            .select_related("bot")
            .order_by("-updated_at")
        )

    def perform_create(self, serializer):
        bot = serializer.validated_data["bot"]

        if bot.user_id != self.request.user.id:
            raise PermissionDenied("You do not own this bot.")

        serializer.save()

    def perform_update(self, serializer):
        configuration = self.get_object()

        if configuration.bot.user_id != self.request.user.id:
            raise PermissionDenied("You do not own this configuration.")

        serializer.save()


# ============================================================
# POSITIONS
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List positions",
        description="Returns positions belonging to the authenticated user.",
        responses=PositionSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get position",
        responses=PositionSerializer,
    ),
)
class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Position.objects
            .filter(bot__user=self.request.user)
            .select_related("bot", "exchange_account")
            .order_by("-opened_at")
        )


# ============================================================
# ORDERS
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List orders",
        description="Returns orders belonging to the authenticated user.",
        responses=OrderSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get order",
        responses=OrderSerializer,
    ),
    create=extend_schema(
        summary="Create trading order",
        description=(
            "Creates a local trading order request. Actual exchange submission "
            "must be performed by the trading engine/order manager."
        ),
        request=OrderSerializer,
        responses={
            201: OrderSerializer,
            400: OpenApiResponse(description="Invalid order."),
        },
    ),
)
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "post",
        "head",
        "options",
    ]

    def get_queryset(self):
        return (
            Order.objects
            .filter(bot__user=self.request.user)
            .select_related(
                "bot",
                "exchange_account",
                "position",
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        bot = serializer.validated_data["bot"]
        exchange_account = serializer.validated_data["exchange_account"]

        if bot.user_id != self.request.user.id:
            raise PermissionDenied("You do not own this bot.")

        if exchange_account.user_id != self.request.user.id:
            raise PermissionDenied(
                "You do not own this exchange account."
            )

        if bot.exchange_account_id != exchange_account.id:
            raise ValidationError(
                {
                    "exchange_account": (
                        "The exchange account must belong to the selected bot."
                    )
                }
            )

        if not exchange_account.enabled:
            raise ValidationError(
                {"exchange_account": "The exchange account is disabled."}
            )

        if not exchange_account.can_trade:
            raise ValidationError(
                {"exchange_account": "Trading is disabled for this account."}
            )

        client_order_id = f"bot-{bot.id}-{uuid4().hex}"

        serializer.save(
            client_order_id=client_order_id,
            status=OrderStatus.NEW,
        )

    @extend_schema(
        summary="Cancel order",
        description=(
            "Requests cancellation of an order. The exchange adapter/order "
            "manager must perform the actual Binance cancellation."
        ),
        request=None,
        responses={
            200: ActionResponseSerializer,
            400: OpenApiResponse(description="Order cannot be cancelled."),
        },
    )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        order = self.get_object()

        if order.status in {
            OrderStatus.FILLED,
            OrderStatus.CANCELED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
            OrderStatus.EXPIRED_IN_MATCH,
        }:
            raise ValidationError(
                {
                    "status": (
                        f"Order with status {order.status} "
                        "cannot be cancelled."
                    )
                }
            )

        # This is deliberately only a local state transition for now.
        # The exchange cancellation will be handled by OrderManager.
        order.status = OrderStatus.CANCELED
        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        return Response(
            {
                "success": True,
                "message": "Order cancellation requested.",
                "status": order.status,
            }
        )


# ============================================================
# ORDER FILLS
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List order fills",
        description="Returns fills belonging to the authenticated user.",
        responses=OrderFillSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get order fill",
        responses=OrderFillSerializer,
    ),
)
class OrderFillViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderFillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            OrderFill.objects
            .filter(order__bot__user=self.request.user)
            .select_related("order")
            .order_by("-executed_at")
        )


# ============================================================
# TRADES
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List trades",
        description="Returns completed and open trades belonging to the user.",
        responses=TradeSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get trade",
        responses=TradeSerializer,
    ),
)
class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Trade.objects
            .filter(bot__user=self.request.user)
            .select_related(
                "bot",
                "exchange_account",
                "position",
            )
            .order_by("-opened_at")
        )


# ============================================================
# ACCOUNT BALANCES
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List account balances",
        description="Returns balance snapshots belonging to the user.",
        responses=AccountBalanceSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get account balance",
        responses=AccountBalanceSerializer,
    ),
)
class AccountBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccountBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            AccountBalance.objects
            .filter(exchange_account__user=self.request.user)
            .select_related("exchange_account")
            .order_by("-snapshot_at")
        )


# ============================================================
# FUNDING PAYMENTS
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List funding payments",
        responses=FundingPaymentSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get funding payment",
        responses=FundingPaymentSerializer,
    ),
)
class FundingPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FundingPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            FundingPayment.objects
            .filter(exchange_account__user=self.request.user)
            .select_related(
                "exchange_account",
                "bot",
            )
            .order_by("-occurred_at")
        )


# ============================================================
# RISK EVENTS
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List risk events",
        responses=RiskEventSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get risk event",
        responses=RiskEventSerializer,
    ),
)
class RiskEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RiskEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            RiskEvent.objects
            .filter(
                exchange_account__user=self.request.user,
            )
            .select_related(
                "bot",
                "exchange_account",
            )
            .order_by("-occurred_at")
        )


# ============================================================
# TRADING EVENTS
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List trading events",
        responses=TradingEventSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get trading event",
        responses=TradingEventSerializer,
    ),
)
class TradingEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TradingEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            TradingEvent.objects
            .filter(
                exchange_account__user=self.request.user,
            )
            .select_related(
                "bot",
                "exchange_account",
            )
            .order_by("-occurred_at")
        )


# ============================================================
# AUDIT LOGS
# ============================================================


@extend_schema_view(
    list=extend_schema(
        summary="List audit logs",
        description="Returns audit logs belonging to the authenticated user.",
        responses=AuditLogSerializer(many=True),
    ),
    retrieve=extend_schema(
        summary="Get audit log",
        responses=AuditLogSerializer,
    ),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            AuditLog.objects
            .filter(user=self.request.user)
            .order_by("-created_at")
        )
