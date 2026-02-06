"""
Moteur principal de backtesting
Exécute les stratégies sur données historiques et calcule les performances
"""

import yfinance as yf
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime
import numpy as np

from .strategies.base import Strategy, Signal
from .portfolio import BacktestPortfolio
from .metrics import PerformanceMetrics
from .reports import BacktestResult, ComparisonResult
from .strategies import AVAILABLE_STRATEGIES


class BacktestEngine:
    """
    Moteur de backtesting multi-stratégies

    Permet de:
    - Tester une stratégie sur des données historiques
    - Comparer plusieurs stratégies
    - Optimiser les paramètres d'une stratégie
    """

    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001, slippage: float = 0.0005):
        """
        Initialise le moteur de backtesting

        Args:
            initial_capital: Capital initial en euros
            commission: Commission par trade (défaut: 0.1%)
            slippage: Slippage moyen (défaut: 0.05%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.strategies: List[Strategy] = []

    def add_strategy(self, strategy: Strategy) -> None:
        """
        Ajoute une stratégie à tester

        Args:
            strategy: Instance d'une stratégie
        """
        self.strategies.append(strategy)

    def load_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Charge les données historiques depuis Yahoo Finance

        Args:
            ticker: Symbole boursier (ex: 'MC.PA' pour LVMH)
            start_date: Date de début (format: 'YYYY-MM-DD')
            end_date: Date de fin (format: 'YYYY-MM-DD')

        Returns:
            DataFrame avec colonnes OHLCV
        """
        # Télécharger les données
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if data.empty:
            raise ValueError(f"Aucune donnée trouvée pour {ticker} entre {start_date} et {end_date}")

        # Vérifier les colonnes nécessaires
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Données incomplètes pour {ticker}")

        # Reset index pour avoir Date comme colonne
        data = data.reset_index()

        return data

    def run(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        strategy: Optional[Strategy] = None
    ) -> BacktestResult:
        """
        Lance un backtest pour une stratégie

        Args:
            ticker: Symbole boursier
            start_date: Date de début
            end_date: Date de fin
            strategy: Stratégie à tester (si None, utilise la première ajoutée)

        Returns:
            BacktestResult avec toutes les métriques
        """
        # Charger les données
        data = self.load_data(ticker, start_date, end_date)

        # Utiliser la stratégie fournie ou la première de la liste
        if strategy is None:
            if not self.strategies:
                raise ValueError("Aucune stratégie disponible. Utilisez add_strategy() d'abord.")
            strategy = self.strategies[0]

        # Initialiser le portfolio virtuel
        portfolio = BacktestPortfolio(
            initial_capital=self.initial_capital,
            commission=self.commission,
            slippage=self.slippage
        )

        # Boucle principale du backtest
        for idx in range(len(data)):
            current_date = data.iloc[idx]['Date']
            current_price = data.iloc[idx]['Close']

            # Obtenir le signal de la stratégie
            signal = strategy.on_bar(data, idx, portfolio.get_holdings())

            # Exécuter le trade selon le signal
            if signal == Signal.BUY:
                portfolio.buy(current_date, ticker, current_price)
            elif signal == Signal.SELL:
                portfolio.sell(current_date, ticker, current_price)

            # Mettre à jour la valeur du portfolio
            portfolio.update_equity(current_date, current_price)

        # Calculer les métriques de performance
        final_capital = portfolio.get_current_value(data.iloc[-1]['Close'])
        equity_curve = portfolio.get_equity_curve()
        trades = portfolio.get_trades()
        dates = portfolio.get_dates()

        # Calculer les rendements
        total_return = PerformanceMetrics.calculate_total_return(
            self.initial_capital, final_capital
        )

        # Nombre de jours de trading
        trading_days = len(data)

        # Rendement annualisé
        annualized_return = PerformanceMetrics.calculate_annualized_return(
            total_return, trading_days
        )

        # Calculer les rendements pour les ratios
        returns = PerformanceMetrics.calculate_returns(equity_curve)

        # Sharpe Ratio
        sharpe_ratio = PerformanceMetrics.calculate_sharpe_ratio(returns)

        # Sortino Ratio
        sortino_ratio = PerformanceMetrics.calculate_sortino_ratio(returns)

        # Maximum Drawdown
        max_drawdown, _, _ = PerformanceMetrics.calculate_max_drawdown(equity_curve)

        # Calmar Ratio
        calmar_ratio = PerformanceMetrics.calculate_calmar_ratio(
            annualized_return, max_drawdown
        )

        # Volatilité
        volatility = PerformanceMetrics.calculate_volatility(returns)

        # Métriques de trading
        trade_metrics = PerformanceMetrics.calculate_trade_metrics(trades)

        # Créer le résultat
        result = BacktestResult(
            strategy_name=strategy.get_name(),
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            volatility=volatility,
            win_rate=trade_metrics['win_rate'],
            profit_factor=trade_metrics['profit_factor'],
            num_trades=trade_metrics['num_trades'],
            avg_trade=trade_metrics['avg_trade'],
            avg_win=trade_metrics['avg_win'],
            avg_loss=trade_metrics['avg_loss'],
            max_win=trade_metrics['max_win'],
            max_loss=trade_metrics['max_loss'],
            trades=trades,
            equity_curve=equity_curve,
            dates=dates,
            strategy_params=strategy.get_params(),
            commission=self.commission,
            slippage=self.slippage,
        )

        return result

    def compare_strategies(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        strategies: Optional[List[Strategy]] = None
    ) -> ComparisonResult:
        """
        Compare plusieurs stratégies sur les mêmes données

        Args:
            ticker: Symbole boursier
            start_date: Date de début
            end_date: Date de fin
            strategies: Liste de stratégies à comparer (si None, utilise toutes les stratégies ajoutées)

        Returns:
            ComparisonResult avec les résultats de toutes les stratégies
        """
        if strategies is None:
            strategies = self.strategies

        if not strategies:
            raise ValueError("Aucune stratégie à comparer")

        # Tester chaque stratégie
        results = []
        for strategy in strategies:
            result = self.run(ticker, start_date, end_date, strategy)
            results.append(result)

        # Trouver la meilleure stratégie (basé sur Sharpe Ratio)
        best_strategy = max(results, key=lambda r: r.sharpe_ratio)

        # Calculer les métriques de comparaison
        comparison_metrics = {
            'best_total_return': max(r.total_return for r in results),
            'best_sharpe_ratio': max(r.sharpe_ratio for r in results),
            'lowest_drawdown': max(r.max_drawdown for r in results),  # Max car drawdown est négatif
            'highest_win_rate': max(r.win_rate for r in results),
            'ranking': sorted(
                [{'strategy': r.strategy_name, 'sharpe': r.sharpe_ratio, 'return': r.total_return}
                 for r in results],
                key=lambda x: x['sharpe'],
                reverse=True
            )
        }

        return ComparisonResult(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            strategies=results,
            best_strategy=best_strategy.strategy_name,
            comparison_metrics=comparison_metrics,
        )

    def optimize_parameters(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        strategy_class,
        param_grid: Dict[str, List]
    ) -> Dict:
        """
        Optimise les paramètres d'une stratégie via Grid Search

        Args:
            ticker: Symbole boursier
            start_date: Date de début
            end_date: Date de fin
            strategy_class: Classe de la stratégie (ex: MovingAverageCrossover)
            param_grid: Dict des paramètres à tester
                        Ex: {'fast_period': [20, 50], 'slow_period': [100, 200]}

        Returns:
            Dict avec les meilleurs paramètres et les résultats
        """
        from itertools import product

        # Générer toutes les combinaisons de paramètres
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))

        # Tester chaque combinaison
        best_result = None
        best_params = None
        best_sharpe = -np.inf

        all_results = []

        for params_tuple in param_combinations:
            # Créer un dict de paramètres
            params = dict(zip(param_names, params_tuple))

            # Créer une instance de la stratégie avec ces paramètres
            strategy = strategy_class(**params)

            # Tester
            try:
                result = self.run(ticker, start_date, end_date, strategy)

                # Stocker le résultat
                all_results.append({
                    'params': params,
                    'sharpe_ratio': result.sharpe_ratio,
                    'total_return': result.total_return,
                    'max_drawdown': result.max_drawdown,
                    'num_trades': result.num_trades,
                })

                # Vérifier si c'est le meilleur
                if result.sharpe_ratio > best_sharpe:
                    best_sharpe = result.sharpe_ratio
                    best_params = params
                    best_result = result

            except Exception as e:
                print(f"Erreur avec paramètres {params}: {e}")
                continue

        return {
            'best_params': best_params,
            'best_sharpe_ratio': best_sharpe,
            'best_result': best_result,
            'all_results': sorted(all_results, key=lambda x: x['sharpe_ratio'], reverse=True),
        }

    @staticmethod
    def get_available_strategies() -> List[str]:
        """
        Retourne la liste des stratégies disponibles

        Returns:
            Liste des noms de stratégies
        """
        return list(AVAILABLE_STRATEGIES.keys())

    @staticmethod
    def create_strategy(strategy_name: str, params: Optional[Dict] = None) -> Strategy:
        """
        Crée une instance de stratégie à partir du nom

        Args:
            strategy_name: Nom de la stratégie (ex: 'ma_crossover')
            params: Paramètres de la stratégie

        Returns:
            Instance de la stratégie
        """
        if strategy_name not in AVAILABLE_STRATEGIES:
            raise ValueError(f"Stratégie inconnue: {strategy_name}. Disponibles: {list(AVAILABLE_STRATEGIES.keys())}")

        strategy_class = AVAILABLE_STRATEGIES[strategy_name]

        # Créer l'instance avec ou sans paramètres
        if params:
            return strategy_class(**params)
        else:
            return strategy_class()
