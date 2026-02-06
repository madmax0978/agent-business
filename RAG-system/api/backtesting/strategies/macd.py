"""
Stratégie MACD Crossover
Signal d'achat quand la ligne MACD croise au-dessus de la ligne signal
Signal de vente quand la ligne MACD croise en-dessous de la ligne signal
"""

import pandas as pd
from typing import Dict
from .base import Strategy, Signal


class MACDCrossover(Strategy):
    """
    Stratégie basée sur le croisement MACD

    Paramètres:
    - fast_period: Période EMA rapide (défaut: 12)
    - slow_period: Période EMA lente (défaut: 26)
    - signal_period: Période de la ligne signal (défaut: 9)
    """

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__("MACD Crossover")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate_macd(self, prices: pd.Series) -> tuple:
        """
        Calcule le MACD et la ligne signal

        Args:
            prices: Series de prix de clôture

        Returns:
            Tuple (macd_line, signal_line, histogram)
        """
        # EMA rapide et lente
        ema_fast = prices.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow_period, adjust=False).mean()

        # Ligne MACD = EMA rapide - EMA lente
        macd_line = ema_fast - ema_slow

        # Ligne signal = EMA de la ligne MACD
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()

        # Histogramme = MACD - Signal
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    def on_bar(self, data: pd.DataFrame, current_idx: int, holdings: int) -> Signal:
        """
        Génère un signal basé sur le croisement MACD

        Args:
            data: DataFrame avec colonnes OHLCV
            current_idx: Index de la barre courante
            holdings: Nombre d'actions actuellement détenues

        Returns:
            Signal: BUY, SELL ou HOLD
        """
        # Besoin d'au moins slow_period + signal_period barres
        min_bars = self.slow_period + self.signal_period
        if current_idx < min_bars:
            return Signal.HOLD

        # Extraire les données jusqu'à l'index courant
        hist_data = data.iloc[:current_idx + 1]

        # Calculer le MACD
        macd_line, signal_line, histogram = self.calculate_macd(hist_data['Close'])

        # Valeurs actuelles et précédentes
        macd_current = macd_line.iloc[-1]
        macd_prev = macd_line.iloc[-2]
        signal_current = signal_line.iloc[-1]
        signal_prev = signal_line.iloc[-2]

        if pd.isna(macd_current) or pd.isna(signal_current):
            return Signal.HOLD

        # Signal d'achat: MACD croise au-dessus de la ligne signal
        if macd_prev <= signal_prev and macd_current > signal_current:
            if holdings == 0:
                return Signal.BUY

        # Signal de vente: MACD croise en-dessous de la ligne signal
        elif macd_prev >= signal_prev and macd_current < signal_current:
            if holdings > 0:
                return Signal.SELL

        return Signal.HOLD

    def get_params(self) -> Dict:
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "signal_period": self.signal_period,
        }
