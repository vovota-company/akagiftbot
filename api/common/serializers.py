from rest_framework import serializers


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField(
        read_only=True,
        help_text="API health status.",
    )
    service = serializers.CharField(
        read_only=True,
        help_text="API service name.",
    )


class AccountResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    referral_code = serializers.CharField(
        read_only=True,
        allow_null=True,
    )
    referred_by = serializers.DictField(
        read_only=True,
        allow_null=True,
    )


class ReferralResponseSerializer(serializers.Serializer):
    referral_code = serializers.CharField(read_only=True)
    referred_by = serializers.DictField(
        read_only=True,
        allow_null=True,
    )
    referrals_count = serializers.IntegerField(read_only=True)
    referral_reward = serializers.DecimalField(
        max_digits=20,
        decimal_places=8,
        read_only=True,
    )


class SubscriptionResponseSerializer(serializers.Serializer):
    status = serializers.CharField(read_only=True)
    starts_at = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
    )
    expires_at = serializers.DateTimeField(
        read_only=True,
        allow_null=True,
    )
    payment_tx_hash = serializers.CharField(
        read_only=True,
        allow_blank=True,
    )


class WalletResponseSerializer(serializers.Serializer):
    address = serializers.CharField(read_only=True)
    derivation_path = serializers.CharField(read_only=True)
    active = serializers.BooleanField(read_only=True)


class DepositResponseSerializer(serializers.Serializer):
    tx_hash = serializers.CharField(read_only=True)
    amount = serializers.CharField(read_only=True)
    token_contract = serializers.CharField(read_only=True)
    block_number = serializers.IntegerField(
        read_only=True,
        allow_null=True,
    )
    confirmations = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class WithdrawalResponseSerializer(serializers.Serializer):
    destination = serializers.CharField(read_only=True)
    amount = serializers.CharField(read_only=True)
    tx_hash = serializers.CharField(
        read_only=True,
        allow_blank=True,
    )
    gas_fee_bnb = serializers.CharField(
        read_only=True,
        allow_null=True,
    )
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class WithdrawalCreateRequestSerializer(serializers.Serializer):
    destination = serializers.CharField(
        max_length=42,
        required=True,
        help_text="External BSC wallet address.",
    )
    amount = serializers.DecimalField(
        max_digits=40,
        decimal_places=18,
        required=True,
        help_text="USDT amount to withdraw.",
    )
