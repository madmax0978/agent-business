"""
Structures de données pour les résultats de backtesting
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Trade:
    """Représente une transaction"""
    date: datetime
    type: str
    ticker: str
    price: float
    quantity: int
    commission: float
    slippage: float
    total: float
    profit: Optional[float] = None
    return_pct: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour JSON"""
        d = asdict(self)
        d['date'] = self.date.isoformat() if isinstance(self.date, datetime) else self.date
        return d


@dataclass
class BacktestResult:
    """
    Résultat complet d'un backtest

    Contient toutes les métriques de performance et l'historique des trades
    """
    # Informations générales
    strategy_name: str
    ticker: str
    start_date: str
    end_date: str

    # Capital
    initial_capital: float
    final_capital: float

    # Rendements
    total_return: float  # %
    annualized_return: float  # %

    # Risque
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float  # %
    calmar_ratio: float
    volatility: float  # Annualisée

    # Statistiques de trading
    win_rate: float  # %
    profit_factor: float
    num_trades: int
    avg_trade: float  # %
    avg_win: float  # %
    avg_loss: float  # %
    max_win: float  # %
    max_loss: float  # %

    # Historique
    trades: List[Trade]
    equity_curve: List[float]
    dates: List[datetime]

    # Paramètres
    strategy_params: Dict
    commission: float
    slippage: float

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour JSON"""
        return {
            'strategy_name': self.strategy_name,
            'ticker': self.ticker,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': round(self.total_return, 2),
            'annualized_return': round(self.annualized_return, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'calmar_ratio': round(self.calmar_ratio, 2),
            'volatility': round(self.volatility, 2),
            'win_rate': round(self.win_rate, 2),
            'profit_factor': round(self.profit_factor, 2),
            'num_trades': self.num_trades,
            'avg_trade': round(self.avg_trade, 2),
            'avg_win': round(self.avg_win, 2),
            'avg_loss': round(self.avg_loss, 2),
            'max_win': round(self.max_win, 2),
            'max_loss': round(self.max_loss, 2),
            'trades': [t.to_dict() for t in self.trades],
            'equity_curve': self.equity_curve,
            'dates': [d.isoformat() if isinstance(d, datetime) else d for d in self.dates],
            'strategy_params': self.strategy_params,
            'commission': self.commission,
            'slippage': self.slippage,
        }


@dataclass
class ComparisonResult:
    """
    Résultat de comparaison entre plusieurs stratégies

    Permet de comparer les performances de différentes stratégies
    """
    ticker: str
    start_date: str
    end_date: str
    strategies: List[BacktestResult]
    best_strategy: str
    comparison_metrics: Dict

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour JSON"""
        return {
            'ticker': self.ticker,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'strategies': [s.to_dict() for s in self.strategies],
            'best_strategy': self.best_strategy,
            'comparison_metrics': self.comparison_metrics,
        }
