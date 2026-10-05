from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """
    Blockchain transaction/deposit representation.
    """

    id = serializers.IntegerField(
        read_only=True,
        help_text="Internal transaction identifier.",
    )

    type = serializers.ChoiceField(
        choices=Transaction.TYPE_CHOICES,
        read_only=True,
        help_text=(
            "Transaction type: deposit, sweep, or gas_topup."
        ),
    )

    asset = serializers.CharField(
        read_only=True,
        help_text="Blockchain asset involved in the transaction, normally USDT.",
    )

    network = serializers.CharField(
        read_only=True,
        help_text="Blockchain network, currently BSC.",
    )

    amount = serializers.DecimalField(
        max_digits=36,
        decimal_places=18,
        read_only=True,
        help_text="Transaction amount in the asset's native decimal representation.",
    )

    fee = serializers.DecimalField(
        max_digits=36,
        decimal_places=18,
        read_only=True,
        help_text="Recorded transaction fee.",
    )

    tx_hash = serializers.CharField(
        read_only=True,
        help_text="Blockchain transaction hash of the original transaction.",
    )

    block_number = serializers.IntegerField(
        read_only=True,
        help_text="BSC block containing the transaction.",
    )

    confirmations = serializers.IntegerField(
        read_only=True,
        help_text="Number of blockchain confirmations currently observed.",
    )

    status = serializers.ChoiceField(
        choices=Transaction.STATUS_CHOICES,
        read_only=True,
        help_text=(
            "Deposit processing status: detected, confirmed, processing, "
            "collected, or failed."
        ),
    )

    collected_tx_hash = serializers.CharField(
        read_only=True,
        help_text=(
            "Transaction hash of the USDT sweep from the user's deposit "
            "wallet to the central wallet. Empty until collection occurs."
        ),
    )

    error_message = serializers.CharField(
        read_only=True,
        help_text="Processing error message when the transaction enters failed status.",
    )

    detected_at = serializers.DateTimeField(
        read_only=True,
        help_text="UTC timestamp when the blockchain transaction was detected.",
    )

    updated_at = serializers.DateTimeField(
        read_only=True,
        help_text="UTC timestamp when the transaction record was last updated.",
    )

    class Meta:
        model = Transaction
        fields = (
            "id",
            "type",
            "asset",
            "network",
            "amount",
            "fee",
            "tx_hash",
            "block_number",
            "confirmations",
            "status",
            "collected_tx_hash",
            "error_message",
            "detected_at",
            "updated_at",
        )
        read_only_fields = fields
        ref_name = "Transaction"
