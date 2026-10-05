from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile

User = get_user_model()


class GoogleLoginSerializer(serializers.Serializer):
    """
    Request body for Google authentication.
    """

    id_token = serializers.CharField(
        required=True,
        write_only=True,
        help_text=(
            "Google OAuth 2.0 / OpenID Connect ID token obtained from the "
            "Google Sign-In flow."
        ),
    )

    class Meta:
        ref_name = "GoogleLoginRequest"


class UserSerializer(serializers.ModelSerializer):
    """
    Public authenticated-user representation.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "date_joined",
        )
        read_only_fields = fields
        ref_name = "User"


class WalletSummarySerializer(serializers.Serializer):
    """
    Wallet information returned during authentication.
    """

    address = serializers.CharField(
        read_only=True,
        help_text="User's dedicated BNB Smart Chain deposit address.",
    )
    network = serializers.CharField(
        read_only=True,
        help_text="Blockchain network used by the wallet.",
    )
    status = serializers.CharField(
        read_only=True,
        help_text="Current wallet status.",
    )

    class Meta:
        ref_name = "WalletSummary"


class GoogleLoginResponseSerializer(serializers.Serializer):
    """
    Successful Google authentication response.
    """

    access = serializers.CharField(
        read_only=True,
        help_text="JWT access token used to authenticate API requests.",
    )
    refresh = serializers.CharField(
        read_only=True,
        help_text="JWT refresh token used to obtain a new access token.",
    )
    user = UserSerializer(
        read_only=True,
        help_text="Authenticated user.",
    )
    wallet = WalletSummarySerializer(
        read_only=True,
        help_text="Dedicated deposit wallet automatically assigned to the user.",
    )

    class Meta:
        ref_name = "GoogleLoginResponse"


class TokenRefreshRequestSerializer(serializers.Serializer):
    """
    Request body for refreshing a JWT access token.
    """

    refresh = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Valid JWT refresh token.",
    )

    class Meta:
        ref_name = "TokenRefreshRequest"


class TokenRefreshResponseSerializer(serializers.Serializer):
    """
    Successful JWT refresh response.
    """

    access = serializers.CharField(
        read_only=True,
        help_text="New JWT access token.",
    )

    class Meta:
        ref_name = "TokenRefreshResponse"


class ErrorResponseSerializer(serializers.Serializer):
    """
    Generic API error response.
    """

    detail = serializers.CharField(
        read_only=True,
        help_text="Human-readable error message.",
    )

    class Meta:
        ref_name = "ErrorResponse"


def tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)
