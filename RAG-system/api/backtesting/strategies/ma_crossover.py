"""
Stratégie Moving Average Crossover
Signal d'achat quand MA rapide croise au-dessus de MA lente
Signal de vente quand MA rapide croise en-dessous de MA lente
"""

import pandas as pd
from typing import Dict
from .base import Strategy, Signal


class MovingAverageCrossover(Strategy):
    """
    Stratégie de croisement de moyennes mobiles

    Paramètres:
    - fast_period: Période de la MA rapide (défaut: 50)
    - slow_period: Période de la MA lente (défaut: 200)
    """

    def __init__(self, fast_period: int = 50, slow_period: int = 200):
        super().__init__("Moving Average Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period

    def on_bar(self, data: pd.DataFrame, current_idx: int, holdings: int) -> Signal:
        """
        Génère un signal basé sur le croisement des moyennes mobiles

        Args:
            data: DataFrame avec colonnes OHLCV
            current_idx: Index de la barre courante
            holdings: Nombre d'actions actuellement détenues

        Returns:
            Signal: BUY, SELL ou HOLD
        """
        # Besoin d'au moins slow_period + 1 barres pour calculer
        if current_idx < self.slow_period:
            return Signal.HOLD

        # Extraire les données jusqu'à l'index courant (éviter look-ahead bias)
        hist_data = data.iloc[:current_idx + 1]

        # Calculer les moyennes mobiles
        fast_ma = hist_data['Close'].rolling(window=self.fast_period).mean()
        slow_ma = hist_data['Close'].rolling(window=self.slow_period).mean()

        # Valeurs actuelles et précédentes
        fast_ma_current = fast_ma.iloc[-1]
        fast_ma_prev = fast_ma.iloc[-2]
        slow_ma_current = slow_ma.iloc[-1]
        slow_ma_prev = slow_ma.iloc[-2]

        # Détecter le croisement
        if pd.isna(fast_ma_current) or pd.isna(slow_ma_current):
            return Signal.HOLD

        # Golden Cross: MA rapide croise au-dessus de MA lente
        if fast_ma_prev <= slow_ma_prev and fast_ma_current > slow_ma_current:
            if holdings == 0:
                return Signal.BUY

        # Death Cross: MA rapide croise en-dessous de MA lente
        elif fast_ma_prev >= slow_ma_prev and fast_ma_current < slow_ma_current:
            if holdings > 0:
                return Signal.SELL

        return Signal.HOLD

    def get_params(self) -> Dict:
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
        }
