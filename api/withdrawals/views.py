from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Withdrawal
from .serializers import (
    BalanceSerializer,
    WithdrawalCreateSerializer,
    WithdrawalSerializer,
)
from .services import (
    create_withdrawal,
    execute_withdrawal,
    user_available_balance,
)


class BalanceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Withdrawals"],
        operation_id="getBalance",
        summary="Get available USDT balance",
        description=(
            "Returns the authenticated user's available USDT balance. "
            "Pending and processing withdrawals are excluded from the "
            "available amount."
        ),
        responses={
            200: BalanceSerializer,
        },
    )
    def get(self, request):
        available, pending = user_available_balance(
            request.user
        )

        return Response(
            {
                "asset": "USDT",
                "network": "bsc",
                "available": available,
                "pending_withdrawals": pending,
            }
        )


class WithdrawalListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Withdrawals"],
        operation_id="listWithdrawals",
        summary="List user's withdrawals",
        description=(
            "Returns withdrawal requests belonging only to the "
            "authenticated user."
        ),
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=[
                    "pending",
                    "processing",
                    "completed",
                    "failed",
                    "cancelled",
                ],
                description="Filter withdrawals by processing status.",
            ),
        ],
        responses={
            200: WithdrawalSerializer(many=True),
        },
    )
    def get(self, request):
        queryset = Withdrawal.objects.filter(
            user=request.user
        )

        withdrawal_status = request.query_params.get("status")

        if withdrawal_status:
            queryset = queryset.filter(
                status=withdrawal_status
            )

        return Response(
            WithdrawalSerializer(
                queryset,
                many=True,
            ).data
        )

    @extend_schema(
        tags=["Withdrawals"],
        operation_id="createWithdrawal",
        summary="Withdraw USDT to an external BSC wallet",
        description=(
            "Creates a USDT withdrawal from the user's available balance "
            "to an external BNB Smart Chain wallet.\n\n"
            "The destination must be a valid EVM/BSC address.\n\n"
            "The request requires an idempotency key so retrying the same "
            "request does not accidentally create a second withdrawal.\n\n"
            "The actual blockchain transaction is sent from the central "
            "wallet, not from the user's deposit wallet.\n\n"
            "The response contains the blockchain transaction hash when "
            "the transfer has completed successfully."
        ),
        request=WithdrawalCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=WithdrawalSerializer,
                description="Withdrawal created and processed successfully.",
            ),
            400: OpenApiResponse(
                description="Invalid address, amount, balance, or request.",
            ),
            409: OpenApiResponse(
                description="Withdrawal could not be created because the idempotency key conflicts.",
            ),
        },
        examples=[
            OpenApiExample(
                "USDT withdrawal",
                request_only=True,
                value={
                    "amount": "25.00",
                    "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
                    "idempotency_key": "withdrawal-2026-000001",
                },
            ),
            OpenApiExample(
                "Successful withdrawal",
                response_only=True,
                value={
                    "id": 1,
                    "asset": "USDT",
                    "network": "bsc",
                    "amount": "25.000000000000000000",
                    "fee": "0.000000000000000000",
                    "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
                    "status": "completed",
                    "tx_hash": "0xabcdef...",
                    "idempotency_key": "withdrawal-2026-000001",
                    "error_message": "",
                    "created_at": "2026-09-28T12:00:00Z",
                    "updated_at": "2026-09-28T12:00:10Z",
                    "completed_at": "2026-09-28T12:00:10Z",
                },
            ),
        ],
    )
    def post(self, request):
        serializer = WithdrawalCreateSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            withdrawal = create_withdrawal(
                user=request.user,
                amount=serializer.validated_data["amount"],
                destination_address=serializer.validated_data[
                    "destination_address"
                ],
                idempotency_key=serializer.validated_data[
                    "idempotency_key"
                ],
            )

            withdrawal = execute_withdrawal(
                withdrawal
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as exc:
            return Response(
                {
                    "detail": str(exc),
                    "withdrawal_id": withdrawal.id
                    if "withdrawal" in locals()
                    else None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            WithdrawalSerializer(
                withdrawal
            ).data,
            status=status.HTTP_201_CREATED,
        )


class WithdrawalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Withdrawals"],
        operation_id="getWithdrawal",
        summary="Get withdrawal details",
        description=(
            "Returns one withdrawal belonging to the authenticated user."
        ),
        responses={
            200: WithdrawalSerializer,
            404: OpenApiResponse(
                description="Withdrawal does not exist.",
            ),
        },
    )
    def get(self, request, pk):
        try:
            withdrawal = Withdrawal.objects.get(
                pk=pk,
                user=request.user,
            )
        except Withdrawal.DoesNotExist:
            return Response(
                {"detail": "Withdrawal not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            WithdrawalSerializer(
                withdrawal
            ).data
        )
