from decimal import Decimal

from rest_framework import serializers
from web3 import Web3

from .models import Withdrawal


class WithdrawalCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=36,
        decimal_places=18,
        min_value=Decimal("0.000001"),
        help_text="Amount of USDT to withdraw.",
    )

    destination_address = serializers.CharField(
        max_length=42,
        help_text=(
            "Destination BNB Smart Chain wallet address. "
            "Must be a valid EVM/BSC address."
        ),
    )

    idempotency_key = serializers.CharField(
        max_length=128,
        help_text=(
            "Unique client-generated key. Reusing the same key prevents "
            "accidental duplicate withdrawals."
        ),
    )

    def validate_destination_address(self, value):
        if not Web3.is_address(value):
            raise serializers.ValidationError(
                "Invalid BNB Smart Chain wallet address."
            )

        return Web3.to_checksum_address(value)


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = (
            "id",
            "asset",
            "network",
            "amount",
            "fee",
            "destination_address",
            "status",
            "tx_hash",
            "idempotency_key",
            "error_message",
            "created_at",
            "updated_at",
            "completed_at",
        )
        read_only_fields = (
            "id",
            "asset",
            "network",
            "fee",
            "status",
            "tx_hash",
            "error_message",
            "created_at",
            "updated_at",
            "completed_at",
        )


class BalanceSerializer(serializers.Serializer):
    asset = serializers.CharField()
    network = serializers.CharField()
    available = serializers.DecimalField(
        max_digits=36,
        decimal_places=18,
    )
    pending_withdrawals = serializers.DecimalField(
        max_digits=36,
        decimal_places=18,
    )
