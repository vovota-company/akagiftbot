from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import requests


class BinanceAPIError(Exception):
    pass


class BinanceConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class BinanceConfig:
    api_key: str | None = None
    api_secret: str | None = None
    spot_base_url: str = "https://api.binance.com"
    futures_base_url: str = "https://fapi.binance.com"
    recv_window: int = 5000
    timeout: float = 10.0


class BinanceClient:
    def __init__(self, config: BinanceConfig | None = None):
        self.config = config or BinanceConfig()
        self.session = requests.Session()

    def _base_url(self, market: str) -> str:
        market = market.upper()
        if market == "SPOT":
            return self.config.spot_base_url.rstrip("/")
        if market == "FUTURES":
            return self.config.futures_base_url.rstrip("/")
        raise BinanceConfigurationError("market must be SPOT or FUTURES")

    def _require_credentials(self) -> None:
        if not self.config.api_key or not self.config.api_secret:
            raise BinanceConfigurationError("Binance API credentials are required")

    def _sign_params(self, params: dict[str, Any]) -> dict[str, Any]:
        self._require_credentials()
        signed = dict(params)
        signed["timestamp"] = int(time.time() * 1000)
        signed["recvWindow"] = self.config.recv_window
        query = urlencode(signed, doseq=True)
        signed["signature"] = hmac.new(
            self.config.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signed

    def _request(
        self,
        method: str,
        path: str,
        market: str = "SPOT",
        params: dict[str, Any] | None = None,
        signed: bool = False,
    ) -> Any:
        url = self._base_url(market) + path
        request_params = dict(params or {})
        headers: dict[str, str] = {}

        if signed:
            request_params = self._sign_params(request_params)
            headers["X-MBX-APIKEY"] = self.config.api_key or ""
        elif self.config.api_key:
            headers["X-MBX-APIKEY"] = self.config.api_key

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=request_params,
                headers=headers,
                timeout=self.config.timeout,
            )
        except requests.RequestException as exc:
            raise BinanceAPIError(f"Binance request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError:
            data = {"message": response.text}

        if not response.ok:
            code = data.get("code") if isinstance(data, dict) else None
            message = data.get("msg") if isinstance(data, dict) else str(data)
            raise BinanceAPIError(f"Binance API error {code}: {message}")

        return data

    def ping(self, market: str = "SPOT") -> Any:
        path = "/api/v3/ping" if market.upper() == "SPOT" else "/fapi/v1/ping"
        return self._request("GET", path, market)

    def server_time(self, market: str = "SPOT") -> Any:
        path = "/api/v3/time" if market.upper() == "SPOT" else "/fapi/v1/time"
        return self._request("GET", path, market)

    def exchange_info(self, market: str = "SPOT") -> Any:
        path = "/api/v3/exchangeInfo" if market.upper() == "SPOT" else "/fapi/v1/exchangeInfo"
        return self._request("GET", path, market)

    def klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        market: str = "SPOT",
    ) -> Any:
        if not symbol:
            raise BinanceConfigurationError("symbol is required")
        if not interval:
            raise BinanceConfigurationError("interval is required")
        if limit < 1 or limit > 1500:
            raise BinanceConfigurationError("limit must be between 1 and 1500")

        path = "/api/v3/klines" if market.upper() == "SPOT" else "/fapi/v1/klines"
        return self._request(
            "GET",
            path,
            market,
            {"symbol": symbol.upper(), "interval": interval, "limit": limit},
        )

    def ticker_price(self, symbol: str, market: str = "SPOT") -> Decimal:
        if not symbol:
            raise BinanceConfigurationError("symbol is required")

        path = "/api/v3/ticker/price" if market.upper() == "SPOT" else "/fapi/v1/ticker/price"
        data = self._request("GET", path, market, {"symbol": symbol.upper()})
        return Decimal(str(data["price"]))

    def account_information(self, market: str = "SPOT") -> Any:
        path = "/api/v3/account" if market.upper() == "SPOT" else "/fapi/v2/account"
        return self._request("GET", path, market, signed=True)

    def balances(self) -> Any:
        data = self.account_information("SPOT")
        return data.get("balances", [])
