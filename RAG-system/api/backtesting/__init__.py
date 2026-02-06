"""
Module de backtesting multi-stratégies pour RAG-PEA
"""

from .engine import BacktestEngine
from .strategies.base import Strategy, Signal
from .portfolio import BacktestPortfolio
from .metrics import PerformanceMetrics
from .reports import BacktestResult, Trade

__all__ = [
    'BacktestEngine',
    'Strategy',
    'Signal',
    'BacktestPortfolio',
    'PerformanceMetrics',
    'BacktestResult',
    'Trade',
]

__version__ = '1.0.0'
