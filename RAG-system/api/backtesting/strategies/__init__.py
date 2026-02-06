"""
Stratégies de trading disponibles
"""

from .base import Strategy, Signal
from .ma_crossover import MovingAverageCrossover
from .rsi_strategy import RSIMeanReversion
from .bollinger import BollingerBandsBreakout
from .macd import MACDCrossover
from .momentum import MomentumStrategy
from .buy_and_hold import BuyAndHold

__all__ = [
    'Strategy',
    'Signal',
    'MovingAverageCrossover',
    'RSIMeanReversion',
    'BollingerBandsBreakout',
    'MACDCrossover',
    'MomentumStrategy',
    'BuyAndHold',
]

# Registre des stratégies disponibles
AVAILABLE_STRATEGIES = {
    'ma_crossover': MovingAverageCrossover,
    'rsi': RSIMeanReversion,
    'bollinger': BollingerBandsBreakout,
    'macd': MACDCrossover,
    'momentum': MomentumStrategy,
    'buy_and_hold': BuyAndHold,
}
