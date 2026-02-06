"""
Stratégie RSI Mean Reversion
Signal d'achat en zone de survente (RSI < 30)
Signal de vente en zone de surachat (RSI > 70)
"""

import pandas as pd
from typing import Dict
from .base import Strategy, Signal


class RSIMeanReversion(Strategy):
    """
    Stratégie de retour à la moyenne basée sur le RSI

    Paramètres:
    - rsi_period: Période du RSI (défaut: 14)
    - oversold: Seuil de survente (défaut: 30)
    - overbought: Seuil de surachat (défaut: 70)
    """

    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI Mean Reversion")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calcule le RSI (Relative Strength Index)

        Args:
            prices: Series de prix de clôture
            period: Période de calcul

        Returns:
            Series avec les valeurs RSI
        """
        # Calculer les variations
        delta = prices.diff()

        # Séparer gains et pertes
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Moyennes mobiles exponentielles
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        # RS = Average Gain / Average Loss
        rs = avg_gain / avg_loss

        # RSI = 100 - (100 / (1 + RS))
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def on_bar(self, data: pd.DataFrame, current_idx: int, holdings: int) -> Signal:
        """
        Génère un signal basé sur le RSI

        Args:
            data: DataFrame avec colonnes OHLCV
            current_idx: Index de la barre courante
            holdings: Nombre d'actions actuellement détenues

        Returns:
            Signal: BUY, SELL ou HOLD
        """
        # Besoin d'au moins rsi_period + 1 barres
        if current_idx < self.rsi_period + 1:
            return Signal.HOLD

        # Extraire les données jusqu'à l'index courant
        hist_data = data.iloc[:current_idx + 1]

        # Calculer le RSI
        rsi = self.calculate_rsi(hist_data['Close'], self.rsi_period)
        current_rsi = rsi.iloc[-1]

        if pd.isna(current_rsi):
            return Signal.HOLD

        # Signal d'achat en survente
        if current_rsi < self.oversold and holdings == 0:
            return Signal.BUY

        # Signal de vente en surachat
        elif current_rsi > self.overbought and holdings > 0:
            return Signal.SELL

        return Signal.HOLD

    def get_params(self) -> Dict:
        return {
            "rsi_period": self.rsi_period,
            "oversold": self.oversold,
            "overbought": self.overbought,
        }
