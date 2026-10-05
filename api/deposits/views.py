from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Transaction
from .serializers import TransactionSerializer


DEPOSIT_STATUS_VALUES = [
    Transaction.STATUS_DETECTED,
    Transaction.STATUS_CONFIRMED,
    Transaction.STATUS_PROCESSING,
    Transaction.STATUS_COLLECTED,
    Transaction.STATUS_FAILED,
]

TRANSACTION_TYPE_VALUES = [
    Transaction.TYPE_DEPOSIT,
    Transaction.TYPE_SWEEP,
    Transaction.TYPE_GAS_TOPUP,
]


class DepositListView(ListAPIView):
    """
    List blockchain deposits belonging to the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    @extend_schema(
        tags=["Deposits"],
        operation_id="listDeposits",
        summary="List user's USDT deposits",
        description=(
            "Returns USDT deposits detected on the BNB Smart Chain for the "
            "authenticated user.\n\n"
            "Only transactions belonging to the authenticated user are "
            "returned.\n\n"
            "Deposits move through the blockchain processing lifecycle:\n\n"
            "1. detected - deposit transaction discovered on-chain.\n"
            "2. confirmed - required blockchain confirmations reached.\n"
            "3. processing - collection/sweep is being performed.\n"
            "4. collected - USDT has been swept toward the central wallet.\n"
            "5. failed - collection or processing failed."
        ),
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=DEPOSIT_STATUS_VALUES,
                description=(
                    "Optional status filter. If omitted, deposits of all "
                    "statuses are returned."
                ),
                examples=[
                    {
                        "value": "confirmed",
                        "summary": "Confirmed deposits",
                    },
                    {
                        "value": "collected",
                        "summary": "Collected deposits",
                    },
                    {
                        "value": "failed",
                        "summary": "Failed deposits",
                    },
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=TransactionSerializer(many=True),
                description="List of deposits belonging to the authenticated user.",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
            ),
        },
    )
    def get_queryset(self):
        queryset = Transaction.objects.filter(
            user=self.request.user,
            type=Transaction.TYPE_DEPOSIT,
        )

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset


class TransactionListView(ListAPIView):
    """
    List all blockchain transactions belonging to the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    @extend_schema(
        tags=["Transactions"],
        operation_id="listTransactions",
        summary="List user's blockchain transactions",
        description=(
            "Returns blockchain-related transactions belonging to the "
            "authenticated user.\n\n"
            "Transactions may represent:\n\n"
            "- deposit: USDT received by the user's deposit wallet.\n"
            "- sweep: USDT collected from the user's deposit wallet and "
            "sent toward the central wallet.\n"
            "- gas_topup: BNB sent to the user's deposit wallet when gas "
            "funding is required for collection."
        ),
        parameters=[
            OpenApiParameter(
                name="type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                enum=TRANSACTION_TYPE_VALUES,
                description=(
                    "Optional transaction-type filter."
                ),
                examples=[
                    {
                        "value": "deposit",
                        "summary": "USDT deposits",
                    },
                    {
                        "value": "sweep",
                        "summary": "USDT collection transactions",
                    },
                    {
                        "value": "gas_topup",
                        "summary": "BNB gas funding transactions",
                    },
                ],
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=TransactionSerializer(many=True),
                description="List of blockchain transactions.",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
            ),
        },
    )
    def get_queryset(self):
        queryset = Transaction.objects.filter(
            user=self.request.user
        )

        tx_type = self.request.query_params.get("type")

        if tx_type:
            queryset = queryset.filter(type=tx_type)

        return queryset
