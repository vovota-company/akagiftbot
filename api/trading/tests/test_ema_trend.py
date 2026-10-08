from datetime import datetime, timezone
from decimal import Decimal

from django.test import SimpleTestCase

from api.trading.strategies import (
    Candle,
    MarketData,
    StrategyContext,
    SIGNAL_BUY,
    SIGNAL_HOLD,
    SIGNAL_SELL,
    StrategyRegistry,
)
from api.trading.strategies.ema_trend import EMATrendStrategy


class EMATrendStrategyTests(SimpleTestCase):
    def setUp(self):
        self.strategy = EMATrendStrategy(
            {
                "fast_period": 3,
                "slow_period": 5,
            }
        )

        self.context = StrategyContext(
            bot_id=1,
            strategy_id=1,
            symbol="BTCUSDT",
            timeframe="1m",
            market_type="SPOT",
            parameters={
                "fast_period": 3,
                "slow_period": 5,
            },
        )

        self.timestamp = datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        )

    def make_market_data(self, closes):
        candles = tuple(
            Candle(
                timestamp=self.timestamp,
                open=Decimal(str(close)),
                high=Decimal(str(close)),
                low=Decimal(str(close)),
                close=Decimal(str(close)),
                volume=Decimal("1"),
            )
            for close in closes
        )

        return MarketData(
            symbol="BTCUSDT",
            timeframe="1m",
            candles=candles,
            current_price=candles[-1].close if candles else None,
            timestamp=self.timestamp,
        )

    def test_strategy_is_registered(self):
        self.assertIn(
            "ema_trend",
            StrategyRegistry.keys(),
        )

    def test_insufficient_candles_returns_hold(self):
        market_data = self.make_market_data(
            [100, 101, 102, 103]
        )

        signal = self.strategy.generate_signal(
            market_data,
            self.context,
        )

        self.assertEqual(signal.signal, SIGNAL_HOLD)
        self.assertIn("Not enough candles", signal.reason)

    def test_bullish_market_returns_buy(self):
        market_data = self.make_market_data(
            [100, 100, 100, 110, 120, 130]
        )

        signal = self.strategy.generate_signal(
            market_data,
            self.context,
        )

        self.assertEqual(signal.signal, SIGNAL_BUY)
        self.assertGreaterEqual(
            signal.confidence,
            Decimal("0"),
        )
        self.assertLessEqual(
            signal.confidence,
            Decimal("1"),
        )
        self.assertEqual(
            signal.metadata["fast_period"],
            3,
        )
        self.assertEqual(
            signal.metadata["slow_period"],
            5,
        )

    def test_bearish_market_returns_sell(self):
        market_data = self.make_market_data(
            [130, 130, 130, 120, 110, 100]
        )

        signal = self.strategy.generate_signal(
            market_data,
            self.context,
        )

        self.assertEqual(signal.signal, SIGNAL_SELL)
        self.assertGreaterEqual(
            signal.confidence,
            Decimal("0"),
        )
        self.assertLessEqual(
            signal.confidence,
            Decimal("1"),
        )

    def test_custom_periods_are_applied(self):
        strategy = EMATrendStrategy(
            {
                "fast_period": 5,
                "slow_period": 20,
            }
        )

        self.assertEqual(strategy.fast_period, 5)
        self.assertEqual(strategy.slow_period, 20)
        self.assertEqual(strategy.minimum_candles, 20)

    def test_fast_period_must_be_smaller_than_slow_period(self):
        with self.assertRaisesMessage(
            ValueError,
            "fast_period must be smaller than slow_period.",
        ):
            EMATrendStrategy(
                {
                    "fast_period": 20,
                    "slow_period": 5,
                }
            )

    def test_period_must_be_positive(self):
        with self.assertRaisesMessage(
            ValueError,
            "Strategy parameter 'fast_period' must be a positive integer.",
        ):
            EMATrendStrategy(
                {
                    "fast_period": 0,
                    "slow_period": 20,
                }
            )

    def test_symbol_mismatch_is_rejected(self):
        market_data = self.make_market_data(
            [100, 101, 102, 103, 104]
        )

        market_data = MarketData(
            symbol="ETHUSDT",
            timeframe=market_data.timeframe,
            candles=market_data.candles,
            current_price=market_data.current_price,
            timestamp=market_data.timestamp,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Market data symbol does not match strategy context.",
        ):
            self.strategy.generate_signal(
                market_data,
                self.context,
            )

    def test_timeframe_mismatch_is_rejected(self):
        market_data = self.make_market_data(
            [100, 101, 102, 103, 104]
        )

        market_data = MarketData(
            symbol=market_data.symbol,
            timeframe="5m",
            candles=market_data.candles,
            current_price=market_data.current_price,
            timestamp=market_data.timestamp,
        )

        with self.assertRaisesMessage(
            ValueError,
            "Market data timeframe does not match strategy context.",
        ):
            self.strategy.generate_signal(
                market_data,
                self.context,
            )
