from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping, Optional


# ============================================================
# ENUM-LIKE CONSTANTS
# ============================================================


SIGNAL_BUY = "BUY"
SIGNAL_SELL = "SELL"
SIGNAL_HOLD = "HOLD"


SIGNALS = {
    SIGNAL_BUY,
    SIGNAL_SELL,
    SIGNAL_HOLD,
}


# ============================================================
# MARKET DATA
# ============================================================


@dataclass(frozen=True)
class Candle:
    """
    Single OHLCV candle.

    All prices and quantities use Decimal rather than float
    because trading calculations must avoid binary floating-point
    errors.
    """

    timestamp: datetime

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal

    volume: Decimal

    quote_volume: Optional[Decimal] = None

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open


@dataclass(frozen=True)
class MarketData:
    """
    Market data supplied to a strategy.

    The strategy does not fetch Binance data itself.
    The market-data layer/worker supplies it.
    """

    symbol: str
    timeframe: str

    candles: tuple[Candle, ...]

    current_price: Optional[Decimal] = None

    timestamp: Optional[datetime] = None

    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def latest_candle(self) -> Optional[Candle]:
        if not self.candles:
            return None

        return self.candles[-1]

    @property
    def previous_candle(self) -> Optional[Candle]:
        if len(self.candles) < 2:
            return None

        return self.candles[-2]

    def has_enough_candles(self, minimum: int) -> bool:
        return len(self.candles) >= minimum


# ============================================================
# STRATEGY SIGNAL
# ============================================================


@dataclass(frozen=True)
class StrategySignal:
    """
    Result returned by a strategy.

    IMPORTANT:
    A strategy produces a signal only.

    It does NOT:
        - place orders
        - call Binance
        - modify positions
        - modify balances
        - bypass risk management
    """

    signal: str

    symbol: str

    timeframe: str

    timestamp: datetime

    confidence: Optional[Decimal] = None

    reason: Optional[str] = None

    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.signal not in SIGNALS:
            raise ValueError(
                f"Invalid strategy signal: {self.signal}"
            )

        if self.confidence is not None:
            if self.confidence < Decimal("0"):
                raise ValueError(
                    "Confidence cannot be below 0."
                )

            if self.confidence > Decimal("1"):
                raise ValueError(
                    "Confidence cannot be above 1."
                )


# ============================================================
# STRATEGY CONTEXT
# ============================================================


@dataclass(frozen=True)
class StrategyContext:
    """
    Runtime context supplied to a strategy.

    This intentionally contains read-only information.

    A strategy cannot directly modify the trading account.
    """

    bot_id: int

    strategy_id: int

    symbol: str

    timeframe: str

    market_type: str

    parameters: Mapping[str, Any]

    current_position_side: Optional[str] = None

    current_position_quantity: Optional[Decimal] = None

    available_balance: Optional[Decimal] = None

    metadata: Mapping[str, Any] = field(default_factory=dict)


# ============================================================
# STRATEGY BASE CLASS
# ============================================================


class BaseStrategy(ABC):
    """
    Base interface for every trading strategy.

    Every strategy must implement:
        - name
        - implementation_key
        - version
        - generate_signal()

    Strategies must remain deterministic for the same input
    market data and configuration whenever possible.
    """

    name: str = "Base Strategy"

    implementation_key: str = "base"

    version: str = "1.0.0"

    minimum_candles: int = 1

    def __init__(
        self,
        parameters: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.parameters = dict(parameters or {})

        self.validate_parameters()

    # --------------------------------------------------------
    # PARAMETER VALIDATION
    # --------------------------------------------------------

    def validate_parameters(self) -> None:
        """
        Validate strategy configuration.

        Individual strategies should override this method.

        Example:

            period = self.parameters.get("period")

            if not isinstance(period, int):
                raise ValueError("period must be an integer")

            if period < 2:
                raise ValueError("period must be >= 2")
        """

    # --------------------------------------------------------
    # SIGNAL GENERATION
    # --------------------------------------------------------

    @abstractmethod
    def generate_signal(
        self,
        market_data: MarketData,
        context: StrategyContext,
    ) -> StrategySignal:
        """
        Generate a trading signal.

        Implementations must return BUY, SELL, or HOLD.

        They must NOT place orders or modify database state.
        """
        raise NotImplementedError

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    def hold_signal(
        self,
        market_data: MarketData,
        reason: str,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> StrategySignal:
        """
        Convenience method for strategies that decide to HOLD.
        """

        timestamp = (
            market_data.timestamp
            or market_data.latest_candle.timestamp
        )

        return StrategySignal(
            signal=SIGNAL_HOLD,
            symbol=market_data.symbol,
            timeframe=market_data.timeframe,
            timestamp=timestamp,
            reason=reason,
            metadata=dict(metadata or {}),
        )

    def buy_signal(
        self,
        market_data: MarketData,
        reason: str,
        confidence: Optional[Decimal] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> StrategySignal:
        """
        Convenience method for a BUY signal.
        """

        timestamp = (
            market_data.timestamp
            or market_data.latest_candle.timestamp
        )

        return StrategySignal(
            signal=SIGNAL_BUY,
            symbol=market_data.symbol,
            timeframe=market_data.timeframe,
            timestamp=timestamp,
            confidence=confidence,
            reason=reason,
            metadata=dict(metadata or {}),
        )

    def sell_signal(
        self,
        market_data: MarketData,
        reason: str,
        confidence: Optional[Decimal] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> StrategySignal:
        """
        Convenience method for a SELL signal.
        """

        timestamp = (
            market_data.timestamp
            or market_data.latest_candle.timestamp
        )

        return StrategySignal(
            signal=SIGNAL_SELL,
            symbol=market_data.symbol,
            timeframe=market_data.timeframe,
            timestamp=timestamp,
            confidence=confidence,
            reason=reason,
            metadata=dict(metadata or {}),
        )

    # --------------------------------------------------------
    # STRATEGY INFORMATION
    # --------------------------------------------------------

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        """
        Metadata used by the strategy registry and API.
        """

        return {
            "name": cls.name,
            "implementation_key": cls.implementation_key,
            "version": cls.version,
            "minimum_candles": cls.minimum_candles,
        }
