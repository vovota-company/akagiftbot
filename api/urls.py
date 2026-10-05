from django.urls import include, path

from api.auth.views import (
    ApiTokenRefreshView,
    GoogleLoginView,
    MeView,
)
from api.deposits.views import (
    DepositListView,
    TransactionListView,
)
from api.wallets.views import WalletView


urlpatterns = [
    path(
        "auth/google/",
        GoogleLoginView.as_view(),
        name="google-login",
    ),
    path(
        "auth/token/refresh/",
        ApiTokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "me/",
        MeView.as_view(),
        name="me",
    ),
    path(
        "wallet/",
        WalletView.as_view(),
        name="wallet",
    ),
    path(
        "deposits/",
        DepositListView.as_view(),
        name="deposits",
    ),
    path(
        "transactions/",
        TransactionListView.as_view(),
        name="transactions",
    ),

    # Balance and withdrawals
    path(
        "",
        include("api.withdrawals.urls"),
    ),
]
