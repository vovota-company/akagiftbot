from rest_framework import serializers

from .models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    """
    Dedicated deposit wallet belonging to the authenticated user.
    """

    network = serializers.CharField(
        read_only=True,
        help_text="Blockchain network. Currently BNB Smart Chain (BSC).",
    )

    address = serializers.CharField(
        read_only=True,
        help_text=(
            "Checksummed BSC address assigned to the authenticated user. "
            "This is the address to which USDT BEP-20 deposits should be sent."
        ),
    )

    status = serializers.CharField(
        read_only=True,
        help_text=(
            "Wallet operational status. "
            "Possible values: active, paused."
        ),
    )

    created_at = serializers.DateTimeField(
        read_only=True,
        help_text="UTC timestamp when the wallet was created.",
    )

    class Meta:
        model = Wallet
        fields = (
            "network",
            "address",
            "status",
            "created_at",
        )
        read_only_fields = fields
        ref_name = "Wallet"
