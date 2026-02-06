"""
Stratégie Buy and Hold (Baseline)
Achète au début et garde jusqu'à la fin
Utilisée comme référence pour comparer les autres stratégies
"""

import pandas as pd
from typing import Dict
from .base import Strategy, Signal


class BuyAndHold(Strategy):
    """
    Stratégie Buy and Hold (baseline)

    Achète dès que possible et conserve jusqu'à la fin.
    Pas de paramètres à configurer.
    """

    def __init__(self):
        super().__init__("Buy and Hold")
        self.has_bought = False

    def on_bar(self, data: pd.DataFrame, current_idx: int, holdings: int) -> Signal:
        """
        Achète au premier appel, puis garde

        Args:
            data: DataFrame avec colonnes OHLCV
            current_idx: Index de la barre courante
            holdings: Nombre d'actions actuellement détenues

        Returns:
            Signal: BUY au début, HOLD ensuite
        """
        # Acheter au premier appel si on n'a rien
        if holdings == 0 and not self.has_bought:
            self.has_bought = True
            return Signal.BUY

        # Sinon, toujours garder
        return Signal.HOLD

    def get_params(self) -> Dict:
        return {}
