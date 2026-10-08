from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


class GoogleLoginSerializer(serializers.Serializer):
    credential = serializers.CharField(
        required=True,
        help_text="Google Identity Services ID token credential."
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
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    referred_by = serializers.CharField(
        allow_null=True,
        required=False,
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
