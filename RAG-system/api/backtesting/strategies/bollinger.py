"""
Stratégie Bollinger Bands Breakout
Signal d'achat quand le prix casse la bande inférieure (rebond)
Signal de vente quand le prix casse la bande supérieure (retournement)
"""

import pandas as pd
from typing import Dict
from .base import Strategy, Signal


class BollingerBandsBreakout(Strategy):
    """
    Stratégie basée sur les Bandes de Bollinger

    Paramètres:
    - period: Période de la moyenne mobile (défaut: 20)
    - std_dev: Nombre d'écarts-types (défaut: 2.0)
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__("Bollinger Bands Breakout")
        self.period = period
        self.std_dev = std_dev

    def on_bar(self, data: pd.DataFrame, current_idx: int, holdings: int) -> Signal:
        """
        Génère un signal basé sur les Bandes de Bollinger

        Args:
            data: DataFrame avec colonnes OHLCV
            current_idx: Index de la barre courante
            holdings: Nombre d'actions actuellement détenues

        Returns:
            Signal: BUY, SELL ou HOLD
        """
        # Besoin d'au moins period barres
        if current_idx < self.period:
            return Signal.HOLD

        # Extraire les données jusqu'à l'index courant
        hist_data = data.iloc[:current_idx + 1]

        # Calculer les bandes de Bollinger
        close = hist_data['Close']
        sma = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std()

        upper_band = sma + (self.std_dev * std)
        lower_band = sma - (self.std_dev * std)

        # Valeurs actuelles et précédentes
        price_current = close.iloc[-1]
        price_prev = close.iloc[-2]
        lower_current = lower_band.iloc[-1]
        lower_prev = lower_band.iloc[-2]
        upper_current = upper_band.iloc[-1]
        upper_prev = upper_band.iloc[-2]

        if pd.isna(lower_current) or pd.isna(upper_current):
            return Signal.HOLD

        # Signal d'achat: prix rebondit sur la bande inférieure
        if price_prev <= lower_prev and price_current > lower_current and holdings == 0:
            return Signal.BUY

        # Signal de vente: prix atteint la bande supérieure
        elif price_prev <= upper_prev and price_current > upper_current and holdings > 0:
            return Signal.SELL

        return Signal.HOLD

    def get_params(self) -> Dict:
        return {
            "period": self.period,
            "std_dev": self.std_dev,
        }
