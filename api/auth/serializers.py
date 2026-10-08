from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


class GoogleLoginSerializer(serializers.Serializer):
    credential = serializers.CharField(
        required=True,
        help_text="Google Identity Services ID token credential.",
    )

    referred_by = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=True,
        help_text=(
            "Referral code of an existing user who referred this account. "
            "Leave empty if the user was not referred."
        ),
    )


class GoogleLoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = serializers.DictField()
    wallet = serializers.DictField()


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    date_joined = serializers.DateTimeField()

    referral_code = serializers.CharField(
        source="profile.referral_code",
        allow_null=True,
        read_only=True,
    )

    referred_by = serializers.CharField(
        source="profile.referred_by.referral_code",
        allow_null=True,
        read_only=True,
    )

    is_active = serializers.BooleanField(
        source="profile.is_active",
        read_only=True,
    )


class UserProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    referral_code = serializers.CharField(
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    referred_by = serializers.CharField(
        allow_null=True,
        required=False,
    )


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=True,
        help_text="JWT refresh token."
    )


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    error = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    message = serializers.CharField(
        required=False,
        allow_blank=True,
    )


def tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return str(refresh.access_token), str(refresh)
