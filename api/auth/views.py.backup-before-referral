from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    ErrorResponseSerializer,
    GoogleLoginResponseSerializer,
    GoogleLoginSerializer,
    TokenRefreshRequestSerializer,
    TokenRefreshResponseSerializer,
    UserSerializer,
    tokens_for_user,
)
from .services import login_or_create_from_google, verify_google_id_token


class GoogleLoginView(APIView):
    """
    Authenticate or register a user using a Google ID token.

    The API never accepts or stores a normal password for application users.
    Google email is used as the account identity.

    On the first successful login:
    - A Django user is created.
    - The Google identity is stored.
    - A dedicated BSC deposit wallet is created.
    - JWT access and refresh tokens are returned.

    On subsequent logins:
    - The existing user is authenticated.
    - The user's existing wallet is returned.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        operation_id="googleLogin",
        summary="Login or register with Google",
        description=(
            "Authenticate a user using a Google OpenID Connect ID token. "
            "The backend verifies the token with Google, validates that the "
            "email is verified, and uses the verified email as the account "
            "identity. No application password is accepted or stored.\n\n"
            "If the email does not already exist, a new user and dedicated "
            "BNB Smart Chain deposit wallet are created automatically."
        ),
        request=GoogleLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=GoogleLoginResponseSerializer,
                description="Google authentication succeeded.",
            ),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Request validation failed.",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Google token is invalid, expired, or unverified.",
            ),
        },
        examples=[
            OpenApiExample(
                "Google login request",
                request_only=True,
                value={
                    "credential": "eyJhbGciOiJSUzI1NiIs..."
                },
            ),
            OpenApiExample(
                "Successful response",
                response_only=True,
                value={
                    "access": "eyJhbGciOiJIUzI1NiIs...",
                    "refresh": "eyJhbGciOiJIUzI1NiIs...",
                    "user": {
                        "id": 1,
                        "email": "user@gmail.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "date_joined": "2026-09-28T12:00:00Z",
                    },
                    "wallet": {
                        "address": "0x1234567890abcdef1234567890abcdef12345678",
                        "network": "bsc",
                        "status": "active",
                    },
                },
            ),
        ],
    )
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payload = verify_google_id_token(
            serializer.validated_data["credential"]
        )

        user, wallet = login_or_create_from_google(payload)

        access, refresh = tokens_for_user(user)

        return Response(
            {
                "access": access,
                "refresh": refresh,
                "user": UserSerializer(user).data,
                "wallet": {
                    "address": wallet.address,
                    "network": wallet.network,
                    "status": wallet.status,
                },
            }
        )


class ApiTokenRefreshView(TokenRefreshView):
    """
    Exchange a valid JWT refresh token for a new access token.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Authentication"],
        operation_id="refreshAccessToken",
        summary="Refresh JWT access token",
        description=(
            "Submit a valid refresh token to obtain a new JWT access token. "
            "The refresh token itself remains valid according to the configured "
            "JWT lifetime."
        ),
        request=TokenRefreshRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenRefreshResponseSerializer,
                description="A new access token was generated.",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The refresh token is invalid or expired.",
            ),
        },
        examples=[
            OpenApiExample(
                "Refresh request",
                request_only=True,
                value={
                    "refresh": "eyJhbGciOiJIUzI1NiIs..."
                },
            ),
            OpenApiExample(
                "Refresh response",
                response_only=True,
                value={
                    "access": "eyJhbGciOiJIUzI1NiIs..."
                },
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MeView(APIView):
    """
    Return the currently authenticated user.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Users"],
        operation_id="getCurrentUser",
        summary="Get authenticated user",
        description=(
            "Returns the profile associated with the JWT access token. "
            "Authentication is required."
        ),
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Authenticated user's profile.",
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Authentication credentials were not provided or are invalid.",
            ),
        },
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)
