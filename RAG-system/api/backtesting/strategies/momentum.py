"""
Stratégie Momentum
Signal d'achat sur forte tendance haussière (momentum positif)
Signal de vente sur retournement de tendance (momentum négatif)
"""

import pandas as pd
from typing import Dict
from .base import Strategy, Signal


class MomentumStrategy(Strategy):
    """
    Stratégie basée sur le momentum

    Paramètres:
    - lookback_period: Période de calcul du momentum (défaut: 10)
    - threshold: Seuil de momentum pour signal (défaut: 0.02 = 2%)
    """

    def __init__(self, lookback_period: int = 10, threshold: float = 0.02):
        super().__init__("Momentum Strategy")
        self.lookback_period = lookback_period
        self.threshold = threshold

    def calculate_momentum(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calcule le momentum (rate of change)

        Args:
            prices: Series de prix de clôture
            period: Période de lookback

        Returns:
            Series avec les valeurs de momentum
        """
        # Momentum = (Prix actuel - Prix il y a N jours) / Prix il y a N jours
        momentum = prices.pct_change(periods=period)
        return momentum

    def on_bar(self, data: pd.DataFrame, current_idx: int, holdings: int) -> Signal:
        """
        Génère un signal basé sur le momentum

        Args:
            data: DataFrame avec colonnes OHLCV
            current_idx: Index de la barre courante
            holdings: Nombre d'actions actuellement détenues

        Returns:
            Signal: BUY, SELL ou HOLD
        """
        # Besoin d'au moins lookback_period + 1 barres
        if current_idx < self.lookback_period + 1:
            return Signal.HOLD

        # Extraire les données jusqu'à l'index courant
        hist_data = data.iloc[:current_idx + 1]

        # Calculer le momentum
        momentum = self.calculate_momentum(hist_data['Close'], self.lookback_period)
        current_momentum = momentum.iloc[-1]

        if pd.isna(current_momentum):
            return Signal.HOLD

        # Signal d'achat: momentum positif et fort
        if current_momentum > self.threshold and holdings == 0:
            return Signal.BUY

        # Signal de vente: momentum négatif
        elif current_momentum < -self.threshold and holdings > 0:
            return Signal.SELL

        return Signal.HOLD

    def get_params(self) -> Dict:
        return {
            "lookback_period": self.lookback_period,
            "threshold": self.threshold,
        }
