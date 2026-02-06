"""
Classe abstraite de base pour toutes les stratégies
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from enum import Enum
import pandas as pd


class Signal(Enum):
    """Signaux de trading"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy(ABC):
    """
    Classe abstraite de base pour toutes les stratégies de trading

    Toute stratégie doit hériter de cette classe et implémenter:
    - on_bar(): appelé à chaque nouvelle barre de prix
    - get_params(): retourne les paramètres de la stratégie
    """

    def __init__(self, name: str, params: Optional[Dict] = None):
        """
        Initialise la stratégie

        Args:
            name: Nom de la stratégie
            params: Paramètres de la stratégie
        """
        self.name = name
        self.params = params or {}
        self.data_cache = {}

    @abstractmethod
    def on_bar(self, data: pd.DataFrame, current_idx: int, holdings: int) -> Signal:
        """
        Appelé à chaque nouvelle barre de prix pour générer un signal

        Args:
            data: DataFrame avec colonnes OHLCV (Open, High, Low, Close, Volume)
            current_idx: Index de la barre courante
            holdings: Nombre d'actions actuellement détenues

        Returns:
            Signal: BUY, SELL ou HOLD
        """
        pass

    @abstractmethod
    def get_params(self) -> Dict:
        """
        Retourne les paramètres de la stratégie

        Returns:
            Dict avec les paramètres
        """
        pass

    def get_name(self) -> str:
        """Retourne le nom de la stratégie"""
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(params={self.params})"
