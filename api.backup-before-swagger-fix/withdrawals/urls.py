from django.urls import path

from .views import (
    BalanceView,
    WithdrawalDetailView,
    WithdrawalListCreateView,
)


urlpatterns = [
    path(
        "balance/",
        BalanceView.as_view(),
        name="balance",
    ),
    path(
        "withdrawals/",
        WithdrawalListCreateView.as_view(),
        name="withdrawals",
    ),
    path(
        "withdrawals/<int:pk>/",
        WithdrawalDetailView.as_view(),
        name="withdrawal-detail",
    ),
]
