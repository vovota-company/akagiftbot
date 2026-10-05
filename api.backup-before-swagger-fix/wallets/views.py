from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import WalletSerializer
from .services import ensure_wallet_for_user


class WalletView(APIView):
    """
    Return the authenticated user's dedicated blockchain deposit wallet.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Wallets"],
        operation_id="getUserWallet",
        summary="Get user's deposit wallet",
        description=(
            "Returns the dedicated BNB Smart Chain deposit wallet assigned "
            "to the authenticated user.\n\n"
            "A wallet is automatically created if the authenticated user does "
            "not already have one.\n\n"
            "The returned address can be used to receive supported USDT "
            "BEP-20 deposits."
        ),
        responses={
            200: OpenApiResponse(
                response=WalletSerializer,
                description="User's dedicated deposit wallet.",
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided or are invalid.",
            ),
        },
    )
    def get(self, request):
        wallet = ensure_wallet_for_user(request.user)

        return Response(
            WalletSerializer(wallet).data
        )
