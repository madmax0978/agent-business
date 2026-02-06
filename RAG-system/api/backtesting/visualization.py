"""
Génération de graphiques pour visualiser les résultats de backtesting
Utilise Plotly pour des visualisations interactives
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Optional
from .reports import BacktestResult
import numpy as np


class BacktestVisualizer:
    """
    Classe pour créer des visualisations des résultats de backtesting
    """

    @staticmethod
    def plot_equity_curve(
        result: BacktestResult,
        show_trades: bool = True,
        compare_with_buy_hold: bool = True
    ) -> go.Figure:
        """
        Crée un graphique de la courbe d'équité

        Args:
            result: Résultat du backtest
            show_trades: Afficher les markers des trades
            compare_with_buy_hold: Comparer avec Buy & Hold

        Returns:
            Figure Plotly
        """
        fig = go.Figure()

        # Courbe d'équité de la stratégie
        fig.add_trace(go.Scatter(
            x=result.dates,
            y=result.equity_curve,
            mode='lines',
            name=result.strategy_name,
            line=dict(color='blue', width=2)
        ))

        # Ajouter Buy & Hold pour comparaison
        if compare_with_buy_hold:
            # Simuler Buy & Hold
            initial_price = result.equity_curve[0]
            buy_hold_curve = []

            # On suppose que les données de prix sont disponibles dans les trades
            # Sinon on fait une approximation
            for i, equity in enumerate(result.equity_curve):
                # Approximation simple: projection linéaire du rendement total
                progress = i / (len(result.equity_curve) - 1) if len(result.equity_curve) > 1 else 0
                buy_hold_value = result.initial_capital * (1 + (result.total_return / 100) * progress)
                buy_hold_curve.append(buy_hold_value)

            fig.add_trace(go.Scatter(
                x=result.dates,
                y=buy_hold_curve,
                mode='lines',
                name='Buy & Hold',
                line=dict(color='gray', width=2, dash='dash')
            ))

        # Ajouter les markers des trades
        if show_trades:
            buy_dates = []
            buy_prices = []
            sell_dates = []
            sell_prices = []

            for trade in result.trades:
                # Trouver l'index de la date dans result.dates
                try:
                    idx = result.dates.index(trade.date)
                    if trade.type == 'BUY':
                        buy_dates.append(trade.date)
                        buy_prices.append(result.equity_curve[idx])
                    elif trade.type == 'SELL':
                        sell_dates.append(trade.date)
                        sell_prices.append(result.equity_curve[idx])
                except (ValueError, IndexError):
                    continue

            # Marker pour les achats
            if buy_dates:
                fig.add_trace(go.Scatter(
                    x=buy_dates,
                    y=buy_prices,
                    mode='markers',
                    name='Achats',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='green',
                        line=dict(width=1, color='darkgreen')
                    )
                ))

            # Marker pour les ventes
            if sell_dates:
                fig.add_trace(go.Scatter(
                    x=sell_dates,
                    y=sell_prices,
                    mode='markers',
                    name='Ventes',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='red',
                        line=dict(width=1, color='darkred')
                    )
                ))

        # Mise en forme
        fig.update_layout(
            title=f"Courbe d'équité - {result.strategy_name} sur {result.ticker}",
            xaxis_title="Date",
            yaxis_title="Valeur du Portfolio (€)",
            hovermode='x unified',
            template='plotly_white',
            height=600,
        )

        return fig

    @staticmethod
    def plot_drawdown(result: BacktestResult) -> go.Figure:
        """
        Crée un graphique du drawdown

        Args:
            result: Résultat du backtest

        Returns:
            Figure Plotly
        """
        # Calculer le drawdown
        equity = np.array(result.equity_curve)
        cummax = np.maximum.accumulate(equity)
        drawdown = (equity - cummax) / cummax * 100

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=result.dates,
            y=drawdown,
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='red', width=2),
            fillcolor='rgba(255, 0, 0, 0.2)'
        ))

        # Ajouter une ligne pour le max drawdown
        fig.add_hline(
            y=result.max_drawdown,
            line_dash="dash",
            line_color="darkred",
            annotation_text=f"Max Drawdown: {result.max_drawdown:.2f}%",
            annotation_position="left"
        )

        fig.update_layout(
            title=f"Drawdown - {result.strategy_name} sur {result.ticker}",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode='x unified',
            template='plotly_white',
            height=400,
        )

        return fig

    @staticmethod
    def plot_returns_distribution(result: BacktestResult) -> go.Figure:
        """
        Crée un histogramme de la distribution des rendements

        Args:
            result: Résultat du backtest

        Returns:
            Figure Plotly
        """
        # Calculer les rendements journaliers
        equity = np.array(result.equity_curve)
        returns = np.diff(equity) / equity[:-1] * 100

        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=returns,
            nbinsx=50,
            name='Distribution des rendements',
            marker=dict(
                color='blue',
                line=dict(color='darkblue', width=1)
            )
        ))

        # Ajouter une ligne verticale pour la moyenne
        mean_return = np.mean(returns)
        fig.add_vline(
            x=mean_return,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Moyenne: {mean_return:.2f}%",
            annotation_position="top right"
        )

        fig.update_layout(
            title=f"Distribution des Rendements - {result.strategy_name}",
            xaxis_title="Rendement Journalier (%)",
            yaxis_title="Fréquence",
            template='plotly_white',
            height=400,
        )

        return fig

    @staticmethod
    def plot_comparison(results: List[BacktestResult]) -> go.Figure:
        """
        Compare plusieurs stratégies sur un même graphique

        Args:
            results: Liste de résultats de backtest

        Returns:
            Figure Plotly
        """
        fig = go.Figure()

        # Ajouter chaque stratégie
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']

        for idx, result in enumerate(results):
            # Normaliser à 100 pour comparer les performances relatives
            normalized_curve = [
                (val / result.initial_capital) * 100
                for val in result.equity_curve
            ]

            fig.add_trace(go.Scatter(
                x=result.dates,
                y=normalized_curve,
                mode='lines',
                name=f"{result.strategy_name} ({result.total_return:+.1f}%)",
                line=dict(color=colors[idx % len(colors)], width=2)
            ))

        fig.update_layout(
            title="Comparaison des Stratégies (Normalized à 100)",
            xaxis_title="Date",
            yaxis_title="Valeur Normalisée",
            hovermode='x unified',
            template='plotly_white',
            height=600,
        )

        return fig

    @staticmethod
    def plot_metrics_comparison(results: List[BacktestResult]) -> go.Figure:
        """
        Compare les métriques de plusieurs stratégies

        Args:
            results: Liste de résultats de backtest

        Returns:
            Figure Plotly avec subplots
        """
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                'Rendement Total (%)',
                'Sharpe Ratio',
                'Max Drawdown (%)',
                'Win Rate (%)',
                'Profit Factor',
                'Nombre de Trades'
            )
        )

        strategy_names = [r.strategy_name for r in results]

        # Rendement Total
        fig.add_trace(
            go.Bar(
                x=strategy_names,
                y=[r.total_return for r in results],
                name='Rendement',
                marker_color='blue'
            ),
            row=1, col=1
        )

        # Sharpe Ratio
        fig.add_trace(
            go.Bar(
                x=strategy_names,
                y=[r.sharpe_ratio for r in results],
                name='Sharpe',
                marker_color='green'
            ),
            row=1, col=2
        )

        # Max Drawdown
        fig.add_trace(
            go.Bar(
                x=strategy_names,
                y=[r.max_drawdown for r in results],
                name='Drawdown',
                marker_color='red'
            ),
            row=1, col=3
        )

        # Win Rate
        fig.add_trace(
            go.Bar(
                x=strategy_names,
                y=[r.win_rate for r in results],
                name='Win Rate',
                marker_color='purple'
            ),
            row=2, col=1
        )

        # Profit Factor
        fig.add_trace(
            go.Bar(
                x=strategy_names,
                y=[min(r.profit_factor, 10) for r in results],  # Cap à 10 pour la lisibilité
                name='Profit Factor',
                marker_color='orange'
            ),
            row=2, col=2
        )

        # Nombre de Trades
        fig.add_trace(
            go.Bar(
                x=strategy_names,
                y=[r.num_trades for r in results],
                name='Trades',
                marker_color='brown'
            ),
            row=2, col=3
        )

        fig.update_layout(
            title_text="Comparaison des Métriques",
            showlegend=False,
            height=800,
            template='plotly_white'
        )

        return fig

    @staticmethod
    def save_figure(fig: go.Figure, filename: str, format: str = 'html'):
        """
        Sauvegarde une figure

        Args:
            fig: Figure Plotly
            filename: Nom du fichier
            format: Format ('html', 'png', 'jpg', 'pdf')
        """
        if format == 'html':
            fig.write_html(filename)
        else:
            fig.write_image(filename)
