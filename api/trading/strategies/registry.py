from __future__ import annotations

from typing import Mapping, Type

from .base import BaseStrategy


class StrategyRegistry:
    """
    Central registry for all available trading strategies.

    The database stores only an implementation_key such as:

        ema_trend
        rsi_mean_reversion
        breakout
        ema_rsi

    The key is resolved through this explicit whitelist.

    We intentionally do NOT dynamically import arbitrary Python
    paths stored in the database.
    """

    _strategies: dict[str, Type[BaseStrategy]] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    @classmethod
    def register(
        cls,
        strategy_class: Type[BaseStrategy],
    ) -> Type[BaseStrategy]:
        """
        Register a strategy class.

        Can be used as:

            @StrategyRegistry.register
            class EMATrendStrategy(BaseStrategy):
                ...
        """

        implementation_key = strategy_class.implementation_key

        if not implementation_key:
            raise ValueError(
                "Strategy implementation_key cannot be empty."
            )

        if implementation_key == "base":
            raise ValueError(
                "The base strategy cannot be registered."
            )

        if implementation_key in cls._strategies:
            existing = cls._strategies[implementation_key]

            if existing is not strategy_class:
                raise ValueError(
                    "Strategy implementation_key "
                    f"'{implementation_key}' is already registered "
                    f"by {existing.__name__}."
                )

        cls._strategies[implementation_key] = strategy_class

        return strategy_class

    # ========================================================
    # LOOKUP
    # ========================================================

    @classmethod
    def get(
        cls,
        implementation_key: str,
    ) -> Type[BaseStrategy]:
        """
        Return the strategy class registered for a key.
        """

        try:
            return cls._strategies[implementation_key]
        except KeyError:
            available = ", ".join(
                sorted(cls._strategies.keys())
            )

            raise ValueError(
                f"Unknown strategy implementation: "
                f"'{implementation_key}'. "
                f"Available strategies: {available or 'none'}."
            )

    # ========================================================
    # INSTANCE CREATION
    # ========================================================

    @classmethod
    def create(
        cls,
        implementation_key: str,
        parameters: Mapping | None = None,
    ) -> BaseStrategy:
        """
        Create a strategy instance from its implementation key.
        """

        strategy_class = cls.get(implementation_key)

        return strategy_class(
            parameters=parameters or {},
        )

    # ========================================================
    # INSPECTION
    # ========================================================

    @classmethod
    def contains(
        cls,
        implementation_key: str,
    ) -> bool:
        """
        Check whether a strategy is registered.
        """

        return implementation_key in cls._strategies

    @classmethod
    def keys(cls) -> tuple[str, ...]:
        """
        Return all registered implementation keys.
        """

        return tuple(
            sorted(cls._strategies.keys())
        )

    @classmethod
    def classes(
        cls,
    ) -> Mapping[str, Type[BaseStrategy]]:
        """
        Return a read-only-style mapping of registered strategies.

        Callers should not modify the returned mapping.
        """

        return dict(cls._strategies)

    @classmethod
    def metadata(cls) -> list[dict]:
        """
        Return metadata for all registered strategies.

        Useful for administration, diagnostics, and eventually
        exposing available strategies through the API.
        """

        return [
            strategy_class.get_metadata()
            for strategy_class in cls._strategies.values()
        ]


# ============================================================
# PUBLIC REGISTRATION FUNCTION
# ============================================================


def register_strategy(
    strategy_class: Type[BaseStrategy],
) -> Type[BaseStrategy]:
    """
    Convenience decorator for strategy implementations.
    """

    return StrategyRegistry.register(
        strategy_class
    )
