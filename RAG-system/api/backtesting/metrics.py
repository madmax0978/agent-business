"""
Calcul des métriques de performance pour le backtesting

Implémentation des indicateurs standards:
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Calmar Ratio
- Win Rate
- Profit Factor
"""

import numpy as np
import pandas as pd
from typing import List, Tuple


class PerformanceMetrics:
    """
    Classe pour calculer les métriques de performance d'un backtest

    Toutes les métriques utilisent des calculs standards de l'industrie
    """

    @staticmethod
    def calculate_returns(equity_curve: List[float]) -> np.ndarray:
        """
        Calcule les rendements périodiques

        Args:
            equity_curve: Liste des valeurs du portfolio

        Returns:
            Array des rendements
        """
        equity = np.array(equity_curve)
        returns = np.diff(equity) / equity[:-1]
        return returns

    @staticmethod
    def calculate_total_return(initial_capital: float, final_capital: float) -> float:
        """
        Calcule le rendement total en %

        Args:
            initial_capital: Capital initial
            final_capital: Capital final

        Returns:
            Rendement total en %
        """
        return ((final_capital - initial_capital) / initial_capital) * 100

    @staticmethod
    def calculate_annualized_return(total_return: float, days: int) -> float:
        """
        Calcule le rendement annualisé

        Args:
            total_return: Rendement total en %
            days: Nombre de jours de trading

        Returns:
            Rendement annualisé en %
        """
        if days <= 0:
            return 0.0

        years = days / 252  # 252 jours de trading par an
        if years <= 0:
            return 0.0

        annualized = ((1 + total_return / 100) ** (1 / years) - 1) * 100
        return annualized

    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """
        Calcule le Sharpe Ratio (rendement ajusté au risque)

        Formule: (Rendement moyen - Taux sans risque) / Écart-type des rendements

        Args:
            returns: Array des rendements
            risk_free_rate: Taux sans risque annuel (défaut: 2%)

        Returns:
            Sharpe Ratio
        """
        if len(returns) == 0:
            return 0.0

        # Rendement moyen journalier
        mean_return = np.mean(returns)

        # Écart-type des rendements
        std_return = np.std(returns, ddof=1)

        if std_return == 0:
            return 0.0

        # Taux sans risque journalier
        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1

        # Sharpe Ratio annualisé
        sharpe = (mean_return - daily_rf) / std_return * np.sqrt(252)

        return sharpe

    @staticmethod
    def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """
        Calcule le Sortino Ratio (comme Sharpe mais utilise seulement la volatilité négative)

        Formule: (Rendement moyen - Taux sans risque) / Écart-type des rendements négatifs

        Args:
            returns: Array des rendements
            risk_free_rate: Taux sans risque annuel (défaut: 2%)

        Returns:
            Sortino Ratio
        """
        if len(returns) == 0:
            return 0.0

        # Rendement moyen journalier
        mean_return = np.mean(returns)

        # Écart-type des rendements négatifs seulement (downside deviation)
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return np.inf  # Pas de rendements négatifs = ratio infini

        downside_std = np.std(negative_returns, ddof=1)

        if downside_std == 0:
            return np.inf

        # Taux sans risque journalier
        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1

        # Sortino Ratio annualisé
        sortino = (mean_return - daily_rf) / downside_std * np.sqrt(252)

        return sortino

    @staticmethod
    def calculate_max_drawdown(equity_curve: List[float]) -> Tuple[float, int, int]:
        """
        Calcule le Maximum Drawdown (perte maximale depuis un pic)

        Args:
            equity_curve: Liste des valeurs du portfolio

        Returns:
            Tuple (max_drawdown_pct, peak_idx, trough_idx)
        """
        equity = np.array(equity_curve)

        # Calculer les pics cumulatifs
        cummax = np.maximum.accumulate(equity)

        # Calculer les drawdowns
        drawdowns = (equity - cummax) / cummax

        # Trouver le drawdown maximum
        max_dd_idx = np.argmin(drawdowns)
        max_dd = drawdowns[max_dd_idx] * 100

        # Trouver le pic correspondant
        peak_idx = np.argmax(cummax[:max_dd_idx + 1]) if max_dd_idx > 0 else 0

        return max_dd, peak_idx, max_dd_idx

    @staticmethod
    def calculate_calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
        """
        Calcule le Calmar Ratio (rendement annualisé / max drawdown)

        Args:
            annualized_return: Rendement annualisé en %
            max_drawdown: Maximum drawdown en % (négatif)

        Returns:
            Calmar Ratio
        """
        if max_drawdown >= 0:
            return 0.0

        calmar = annualized_return / abs(max_drawdown)
        return calmar

    @staticmethod
    def calculate_volatility(returns: np.ndarray) -> float:
        """
        Calcule la volatilité annualisée

        Args:
            returns: Array des rendements

        Returns:
            Volatilité annualisée en %
        """
        if len(returns) == 0:
            return 0.0

        std_return = np.std(returns, ddof=1)
        annual_vol = std_return * np.sqrt(252) * 100

        return annual_vol

    @staticmethod
    def calculate_trade_metrics(trades: List) -> dict:
        """
        Calcule les métriques liées aux trades

        Args:
            trades: Liste des trades (objets Trade)

        Returns:
            Dict avec win_rate, profit_factor, avg_trade, etc.
        """
        if not trades:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'num_trades': 0,
                'avg_trade': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_win': 0.0,
                'max_loss': 0.0,
            }

        # Ne considérer que les trades de vente (ceux avec profit)
        sell_trades = [t for t in trades if t.type == 'SELL' and t.return_pct is not None]

        if not sell_trades:
            return {
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'num_trades': len(trades),
                'avg_trade': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_win': 0.0,
                'max_loss': 0.0,
            }

        # Séparer gains et pertes
        winning_trades = [t for t in sell_trades if t.return_pct > 0]
        losing_trades = [t for t in sell_trades if t.return_pct <= 0]

        # Win Rate
        win_rate = (len(winning_trades) / len(sell_trades)) * 100 if sell_trades else 0.0

        # Profit Factor = Total gains / Total pertes
        total_wins = sum(t.profit for t in winning_trades) if winning_trades else 0.0
        total_losses = abs(sum(t.profit for t in losing_trades)) if losing_trades else 0.0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else (np.inf if total_wins > 0 else 0.0)

        # Moyenne des trades
        avg_trade = np.mean([t.return_pct for t in sell_trades]) if sell_trades else 0.0

        # Moyenne des gains
        avg_win = np.mean([t.return_pct for t in winning_trades]) if winning_trades else 0.0

        # Moyenne des pertes
        avg_loss = np.mean([t.return_pct for t in losing_trades]) if losing_trades else 0.0

        # Max gain et max perte
        max_win = max([t.return_pct for t in winning_trades]) if winning_trades else 0.0
        max_loss = min([t.return_pct for t in losing_trades]) if losing_trades else 0.0

        return {
            'win_rate': win_rate,
            'profit_factor': min(profit_factor, 999.99),  # Cap à 999.99 pour éviter l'infini
            'num_trades': len(trades),
            'avg_trade': avg_trade,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_win': max_win,
            'max_loss': max_loss,
        }
