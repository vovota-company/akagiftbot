from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Mapping

from .base import (
    BaseStrategy,
    MarketData,
    StrategyContext,
    StrategySignal,
    SIGNAL_BUY,
    SIGNAL_HOLD,
    SIGNAL_SELL,
)
from .registry import register_strategy


@register_strategy
class EMATrendStrategy(BaseStrategy):
    name = "EMA Trend"
    implementation_key = "ema_trend"
    version = "1.0.0"

    DEFAULT_FAST_PERIOD = 9
    DEFAULT_SLOW_PERIOD = 21

    def __init__(self, parameters: Mapping | None = None) -> None:
        self.parameters = dict(parameters or {})

        self.fast_period = self._get_positive_integer(
            "fast_period",
            self.DEFAULT_FAST_PERIOD,
        )
        self.slow_period = self._get_positive_integer(
            "slow_period",
            self.DEFAULT_SLOW_PERIOD,
        )

        self.minimum_candles = self.slow_period

        self.validate_parameters()

    def _get_positive_integer(self, name: str, default: int) -> int:
        raw_value = self.parameters.get(name, default)

        if isinstance(raw_value, bool):
            raise ValueError(
                f"Strategy parameter '{name}' must be a positive integer."
            )

        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Strategy parameter '{name}' must be a positive integer."
            )

        if value < 1:
            raise ValueError(
                f"Strategy parameter '{name}' must be a positive integer."
            )

        return value

    def validate_parameters(self) -> None:
        if self.fast_period >= self.slow_period:
            raise ValueError(
                "fast_period must be smaller than slow_period."
            )

    @staticmethod
    def _calculate_ema(
        prices: list[Decimal],
        period: int,
    ) -> Decimal:
        if len(prices) < period:
            raise ValueError(
                f"At least {period} prices are required to calculate EMA."
            )

        multiplier = Decimal("2") / Decimal(period + 1)

        ema = sum(prices[:period], Decimal("0")) / Decimal(period)

        for price in prices[period:]:
            ema = ((price - ema) * multiplier) + ema

        return ema

    @staticmethod
    def _calculate_confidence(
        fast_ema: Decimal,
        slow_ema: Decimal,
    ) -> Decimal:
        if slow_ema == 0:
            return Decimal("0")

        spread = abs(fast_ema - slow_ema)
        confidence = spread / abs(slow_ema)

        if confidence > Decimal("1"):
            confidence = Decimal("1")

        return confidence.quantize(Decimal("0.0001"))

    def generate_signal(
        self,
        market_data: MarketData,
        context: StrategyContext,
    ) -> StrategySignal:
        if market_data.symbol != context.symbol:
            raise ValueError(
                "Market data symbol does not match strategy context."
            )

        if market_data.timeframe != context.timeframe:
            raise ValueError(
                "Market data timeframe does not match strategy context."
            )

        if not market_data.has_enough_candles(self.minimum_candles):
            return self.hold_signal(
                market_data=market_data,
                reason=(
                    f"Not enough candles. "
                    f"Required: {self.minimum_candles}, "
                    f"available: {len(market_data.candles)}."
                ),
            )

        closes = [
            candle.close
            for candle in market_data.candles
        ]

        try:
            fast_ema = self._calculate_ema(
                closes,
                self.fast_period,
            )
            slow_ema = self._calculate_ema(
                closes,
                self.slow_period,
            )
        except (InvalidOperation, ValueError) as exc:
            return self.hold_signal(
                market_data=market_data,
                reason=f"EMA calculation unavailable: {exc}",
            )

        confidence = self._calculate_confidence(
            fast_ema,
            slow_ema,
        )

        metadata = {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "fast_ema": str(fast_ema),
            "slow_ema": str(slow_ema),
        }

        if fast_ema > slow_ema:
            return StrategySignal(
                signal=SIGNAL_BUY,
                symbol=market_data.symbol,
                timeframe=market_data.timeframe,
                timestamp=market_data.timestamp,
                confidence=confidence,
                reason=(
                    f"Fast EMA ({self.fast_period}) is above "
                    f"slow EMA ({self.slow_period})."
                ),
                metadata=metadata,
            )

        if fast_ema < slow_ema:
            return StrategySignal(
                signal=SIGNAL_SELL,
                symbol=market_data.symbol,
                timeframe=market_data.timeframe,
                timestamp=market_data.timestamp,
                confidence=confidence,
                reason=(
                    f"Fast EMA ({self.fast_period}) is below "
                    f"slow EMA ({self.slow_period})."
                ),
                metadata=metadata,
            )

        return StrategySignal(
            signal=SIGNAL_HOLD,
            symbol=market_data.symbol,
            timeframe=market_data.timeframe,
            timestamp=market_data.timestamp,
            confidence=Decimal("0"),
            reason="Fast EMA and slow EMA are equal.",
            metadata=metadata,
        )
