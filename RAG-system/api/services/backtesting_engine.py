"""
Moteur de backtesting pour valider les stratégies
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta


class BacktestingEngine:
    """Moteur de backtesting des stratégies d'investissement"""

    def __init__(self, initial_capital: float = 10000.0):
        """
        Args:
            initial_capital: Capital initial pour le backtest
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}  # {ticker: {quantity, avg_price}}
        self.trades = []
        self.portfolio_values = []

    def run_simple_ma_strategy(
        self,
        ticker: str,
        historical_data: pd.DataFrame,
        short_window: int = 50,
        long_window: int = 200
    ) -> Dict:
        """
        Backtest d'une stratégie simple basée sur les moyennes mobiles

        Règles:
        - Achat quand MA courte > MA longue (golden cross)
        - Vente quand MA courte < MA longue (death cross)

        Args:
            ticker: Ticker de l'action
            historical_data: DataFrame avec colonnes Date, Close
            short_window: Période de la MA courte
            long_window: Période de la MA longue

        Returns:
            Dict avec résultats du backtest
        """
        df = historical_data.copy()

        # Calculer les moyennes mobiles
        df['SMA_short'] = df['Close'].rolling(window=short_window).mean()
        df['SMA_long'] = df['Close'].rolling(window=long_window).mean()

        # Générer les signaux
        df['Signal'] = 0
        df['Signal'][short_window:] = np.where(
            df['SMA_short'][short_window:] > df['SMA_long'][short_window:], 1, 0
        )
        df['Position'] = df['Signal'].diff()

        # Simuler les trades
        self.current_capital = self.initial_capital
        position_size = 0
        entry_price = 0

        for index, row in df.iterrows():
            if pd.notna(row['Position']):
                if row['Position'] == 1:  # Signal d'achat
                    if position_size == 0:  # Pas déjà en position
                        # Acheter avec tout le capital
                        position_size = self.current_capital / row['Close']
                        entry_price = row['Close']
                        self.current_capital = 0

                        self.trades.append({
                            'date': index,
                            'type': 'BUY',
                            'price': row['Close'],
                            'quantity': position_size,
                            'capital': position_size * row['Close']
                        })

                elif row['Position'] == -1:  # Signal de vente
                    if position_size > 0:  # En position
                        # Vendre tout
                        self.current_capital = position_size * row['Close']
                        position_size = 0

                        self.trades.append({
                            'date': index,
                            'type': 'SELL',
                            'price': row['Close'],
                            'quantity': 0,
                            'capital': self.current_capital
                        })

            # Calculer la valeur du portefeuille
            portfolio_value = self.current_capital + (position_size * row['Close'])
            self.portfolio_values.append({
                'date': index,
                'value': portfolio_value
            })

        # Vendre la position finale si elle existe
        if position_size > 0:
            final_price = df.iloc[-1]['Close']
            self.current_capital = position_size * final_price

        # Calculer les statistiques
        stats = self._calculate_statistics(df)

        return stats

    def _calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """Calcule les statistiques de performance"""
        final_capital = self.current_capital
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100

        # Convertir en DataFrame pour analyse
        portfolio_df = pd.DataFrame(self.portfolio_values)
        if not portfolio_df.empty:
            portfolio_df.set_index('date', inplace=True)

            # Calculer les rendements quotidiens
            portfolio_df['daily_return'] = portfolio_df['value'].pct_change()

            # Rendement annualisé
            num_days = (portfolio_df.index[-1] - portfolio_df.index[0]).days
            annual_return = (((final_capital / self.initial_capital) ** (365 / num_days)) - 1) * 100

            # Volatilité annualisée
            volatility = portfolio_df['daily_return'].std() * np.sqrt(252) * 100

            # Ratio de Sharpe (en supposant taux sans risque = 2%)
            risk_free_rate = 2.0
            sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0

            # Maximum Drawdown
            cummax = portfolio_df['value'].cummax()
            drawdown = (portfolio_df['value'] - cummax) / cummax * 100
            max_drawdown = drawdown.min()

            # Win rate
            if self.trades:
                winning_trades = 0
                for i in range(1, len(self.trades)):
                    if self.trades[i]['type'] == 'SELL':
                        if i > 0 and self.trades[i-1]['type'] == 'BUY':
                            if self.trades[i]['capital'] > self.trades[i-1]['capital']:
                                winning_trades += 1

                num_trades = len([t for t in self.trades if t['type'] == 'SELL'])
                win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0
            else:
                win_rate = 0
                num_trades = 0

        else:
            annual_return = 0
            volatility = 0
            sharpe_ratio = 0
            max_drawdown = 0
            win_rate = 0
            num_trades = 0

        return {
            "initial_capital": self.initial_capital,
            "final_capital": final_capital,
            "total_return": total_return,
            "annual_return": annual_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "num_trades": num_trades,
            "win_rate": win_rate,
            "trades": self.trades
        }

    def compare_vs_benchmark(
        self,
        strategy_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Dict:
        """
        Compare la stratégie vs un benchmark (ex: CAC 40)

        Args:
            strategy_returns: Rendements de la stratégie
            benchmark_returns: Rendements du benchmark

        Returns:
            Dict avec statistiques comparatives
        """
        # Alpha: Rendement excédentaire vs benchmark
        alpha = strategy_returns.mean() - benchmark_returns.mean()

        # Beta: Sensibilité au marché
        covariance = np.cov(strategy_returns, benchmark_returns)[0][1]
        benchmark_variance = benchmark_returns.var()
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

        # Information Ratio
        tracking_error = (strategy_returns - benchmark_returns).std()
        information_ratio = alpha / tracking_error if tracking_error > 0 else 0

        return {
            "alpha": alpha * 100,
            "beta": beta,
            "information_ratio": information_ratio,
            "correlation": strategy_returns.corr(benchmark_returns)
        }
