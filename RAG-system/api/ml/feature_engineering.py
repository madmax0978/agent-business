"""
Feature Engineering pour prédiction de prix

Calcule les indicateurs techniques et features avancées pour l'entraînement
des modèles ML (RSI, MACD, Bollinger Bands, moyennes mobiles, etc.)
"""

import pandas as pd
import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Ingénieur de features pour données financières

    Calcule des indicateurs techniques et transforme les données brutes
    en features exploitables pour les modèles ML.
    """

    def __init__(self):
        """Initialise l'ingénieur de features"""
        pass

    def calculate_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule tous les indicateurs techniques

        Args:
            df: DataFrame avec colonnes: Date, Open, High, Low, Close, Volume

        Returns:
            DataFrame enrichi avec tous les indicateurs
        """
        df = df.copy()

        logger.info("Calcul des features techniques...")

        # Moyennes mobiles
        df = self._calculate_moving_averages(df)

        # RSI (Relative Strength Index)
        df = self._calculate_rsi(df)

        # MACD (Moving Average Convergence Divergence)
        df = self._calculate_macd(df)

        # Bollinger Bands
        df = self._calculate_bollinger_bands(df)

        # Momentum et volatilité
        df = self._calculate_momentum_features(df)

        # Volume features
        df = self._calculate_volume_features(df)

        # Features de prix relatifs
        df = self._calculate_price_features(df)

        # Supprimer les NaN créés par les calculs de moyennes
        df = df.dropna()

        logger.info(f"Features calculées: {len(df.columns)} colonnes, {len(df)} lignes")
        return df

    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les moyennes mobiles simples et exponentielles"""
        periods = [5, 10, 20, 50, 200]

        for period in periods:
            # SMA - Simple Moving Average
            df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()

            # EMA - Exponential Moving Average
            df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()

        # Signaux de croisement
        df['SMA_5_20_cross'] = (df['SMA_5'] > df['SMA_20']).astype(int)
        df['SMA_50_200_cross'] = (df['SMA_50'] > df['SMA_200']).astype(int)

        return df

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calcule le RSI (Relative Strength Index)

        RSI = 100 - (100 / (1 + RS))
        où RS = moyenne des gains / moyenne des pertes
        """
        delta = df['Close'].diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Signaux RSI
        df['RSI_oversold'] = (df['RSI'] < 30).astype(int)  # Survendu
        df['RSI_overbought'] = (df['RSI'] > 70).astype(int)  # Suracheté

        return df

    def _calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> pd.DataFrame:
        """
        Calcule le MACD (Moving Average Convergence Divergence)

        MACD = EMA(12) - EMA(26)
        Signal = EMA(9) du MACD
        Histogram = MACD - Signal
        """
        ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()

        df['MACD'] = ema_fast - ema_slow
        df['MACD_signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']

        # Signal de croisement
        df['MACD_bullish'] = (df['MACD'] > df['MACD_signal']).astype(int)

        return df

    def _calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        num_std: float = 2.0
    ) -> pd.DataFrame:
        """
        Calcule les Bollinger Bands

        Middle Band = SMA(20)
        Upper Band = Middle Band + (2 * std)
        Lower Band = Middle Band - (2 * std)
        """
        df['BB_middle'] = df['Close'].rolling(window=period).mean()
        rolling_std = df['Close'].rolling(window=period).std()

        df['BB_upper'] = df['BB_middle'] + (num_std * rolling_std)
        df['BB_lower'] = df['BB_middle'] - (num_std * rolling_std)

        # Bandwidth (volatilité)
        df['BB_bandwidth'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']

        # Position du prix par rapport aux bandes
        df['BB_position'] = (df['Close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])

        return df

    def _calculate_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les features de momentum et volatilité"""

        # Retours journaliers
        df['returns'] = df['Close'].pct_change()

        # Retours sur différentes périodes
        for period in [5, 10, 20]:
            df[f'returns_{period}d'] = df['Close'].pct_change(periods=period)

        # Volatilité (écart-type des retours)
        for period in [5, 10, 20]:
            df[f'volatility_{period}d'] = df['returns'].rolling(window=period).std()

        # Momentum (Rate of Change)
        for period in [5, 10, 20]:
            df[f'momentum_{period}d'] = df['Close'] - df['Close'].shift(period)

        # ATR (Average True Range) - mesure de volatilité
        df['TR'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                abs(df['High'] - df['Close'].shift(1)),
                abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()

        return df

    def _calculate_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les features liées au volume"""

        # Moyenne mobile du volume
        for period in [5, 10, 20]:
            df[f'volume_SMA_{period}'] = df['Volume'].rolling(window=period).mean()

        # Ratio volume actuel / moyenne
        df['volume_ratio'] = df['Volume'] / df['volume_SMA_20']

        # OBV (On-Balance Volume)
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

        # VWAP (Volume Weighted Average Price)
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

        return df

    def _calculate_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les features de prix relatifs"""

        # Range du jour
        df['daily_range'] = df['High'] - df['Low']
        df['daily_range_pct'] = df['daily_range'] / df['Close']

        # Position du close dans le range
        df['close_position'] = (df['Close'] - df['Low']) / df['daily_range']

        # Gap par rapport au jour précédent
        df['gap'] = df['Open'] - df['Close'].shift(1)
        df['gap_pct'] = df['gap'] / df['Close'].shift(1)

        # Prix par rapport aux moyennes mobiles
        df['price_to_SMA_20'] = df['Close'] / df['SMA_20']
        df['price_to_SMA_50'] = df['Close'] / df['SMA_50']

        return df

    def get_feature_list(self) -> List[str]:
        """
        Retourne la liste des features calculées

        Returns:
            Liste des noms de colonnes features (sans Date, Open, High, Low, Close, Volume)
        """
        # Toutes les features créées par calculate_all_features
        base_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        return [
            # Moving Averages
            'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50', 'SMA_200',
            'EMA_5', 'EMA_10', 'EMA_20', 'EMA_50', 'EMA_200',
            'SMA_5_20_cross', 'SMA_50_200_cross',
            # RSI
            'RSI', 'RSI_oversold', 'RSI_overbought',
            # MACD
            'MACD', 'MACD_signal', 'MACD_histogram', 'MACD_bullish',
            # Bollinger Bands
            'BB_middle', 'BB_upper', 'BB_lower', 'BB_bandwidth', 'BB_position',
            # Momentum & Volatility
            'returns', 'returns_5d', 'returns_10d', 'returns_20d',
            'volatility_5d', 'volatility_10d', 'volatility_20d',
            'momentum_5d', 'momentum_10d', 'momentum_20d',
            'TR', 'ATR',
            # Volume
            'volume_SMA_5', 'volume_SMA_10', 'volume_SMA_20',
            'volume_ratio', 'OBV', 'VWAP',
            # Price Features
            'daily_range', 'daily_range_pct', 'close_position',
            'gap', 'gap_pct', 'price_to_SMA_20', 'price_to_SMA_50',
        ]

    def prepare_for_ml(
        self,
        df: pd.DataFrame,
        target_col: str = 'Close',
        feature_cols: Optional[List[str]] = None
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Prépare les données pour l'entraînement ML

        Args:
            df: DataFrame avec toutes les features
            target_col: Colonne cible (par défaut 'Close')
            feature_cols: Liste des colonnes features ou None pour toutes

        Returns:
            Tuple (X, y) où X sont les features et y la cible
        """
        if feature_cols is None:
            # Exclure Date et les colonnes de prix de base
            exclude_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj_Close']
            feature_cols = [col for col in df.columns if col not in exclude_cols]

        X = df[feature_cols].copy()
        y = df[target_col].copy()

        # Vérifier les NaN
        if X.isnull().sum().sum() > 0:
            logger.warning(f"NaN détectés dans les features: {X.isnull().sum().sum()}")
            X = X.fillna(method='ffill').fillna(method='bfill')

        logger.info(f"Données préparées: {X.shape[0]} échantillons, {X.shape[1]} features")
        return X, y
