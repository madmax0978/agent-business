"""
Chargeur de données pour le système de prédiction ML

Récupère les données de marché depuis Yahoo Finance avec validation
et gestion des erreurs complètes.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Chargeur de données financières optimisé pour le ML

    Gère la récupération, validation et préparation des données
    depuis Yahoo Finance.
    """

    def __init__(self):
        """Initialise le chargeur de données"""
        self.cache = {}  # Cache simple pour éviter requêtes répétées

    def load_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "2y"
    ) -> pd.DataFrame:
        """
        Charge les données historiques pour un ticker

        Args:
            ticker: Symbole boursier (ex: "MC.PA" pour LVMH)
            start_date: Date de début (format YYYY-MM-DD) ou None
            end_date: Date de fin (format YYYY-MM-DD) ou None
            period: Période si pas de dates ("1y", "2y", "5y", "max")

        Returns:
            DataFrame avec colonnes: Date, Open, High, Low, Close, Volume

        Raises:
            ValueError: Si le ticker est invalide ou données vides
        """
        cache_key = f"{ticker}_{start_date}_{end_date}_{period}"

        # Vérifier le cache (valide 1 heure)
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(hours=1):
                logger.info(f"Données pour {ticker} récupérées depuis le cache")
                return cached_data.copy()

        try:
            logger.info(f"Chargement des données pour {ticker} depuis Yahoo Finance")

            # Télécharger les données
            if start_date and end_date:
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            else:
                df = yf.download(ticker, period=period, progress=False)

            # Validation
            if df.empty:
                raise ValueError(f"Aucune donnée disponible pour {ticker}")

            if len(df) < 30:
                raise ValueError(f"Données insuffisantes pour {ticker}: {len(df)} jours (minimum 30)")

            # Réinitialiser l'index pour avoir Date comme colonne
            df = df.reset_index()

            # Nettoyer les noms de colonnes (yfinance peut retourner MultiIndex)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Renommer pour cohérence
            column_mapping = {
                'Date': 'Date',
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Adj Close': 'Adj_Close',
                'Volume': 'Volume'
            }
            df = df.rename(columns=column_mapping)

            # Garder seulement les colonnes nécessaires
            required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = df[required_cols]

            # Gérer les valeurs manquantes
            df = self._handle_missing_values(df)

            # Valider les données
            self._validate_data(df, ticker)

            # Mettre en cache
            self.cache[cache_key] = (df.copy(), datetime.now())

            logger.info(f"Données chargées: {len(df)} jours pour {ticker}")
            return df

        except Exception as e:
            logger.error(f"Erreur lors du chargement de {ticker}: {str(e)}")
            raise ValueError(f"Impossible de charger les données pour {ticker}: {str(e)}")

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Gère les valeurs manquantes de manière intelligente

        Args:
            df: DataFrame avec données possiblement incomplètes

        Returns:
            DataFrame nettoyé
        """
        # Vérifier les valeurs manquantes
        missing_counts = df.isnull().sum()

        if missing_counts.sum() == 0:
            return df

        logger.warning(f"Valeurs manquantes détectées: {missing_counts[missing_counts > 0].to_dict()}")

        # Forward fill puis backward fill pour combler les trous
        df = df.fillna(method='ffill').fillna(method='bfill')

        # Si encore des NaN (début/fin de série), interpoler
        if df.isnull().sum().sum() > 0:
            df = df.interpolate(method='linear')

        # En dernier recours, supprimer les lignes restantes avec NaN
        df = df.dropna()

        return df

    def _validate_data(self, df: pd.DataFrame, ticker: str) -> None:
        """
        Valide la qualité des données

        Args:
            df: DataFrame à valider
            ticker: Symbole pour messages d'erreur

        Raises:
            ValueError: Si les données sont invalides
        """
        # Vérifier les valeurs négatives
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if (df[col] <= 0).any():
                logger.warning(f"Valeurs négatives ou nulles détectées dans {col} pour {ticker}")
                # Remplacer par la moyenne des valeurs adjacentes
                df[col] = df[col].replace(0, np.nan).fillna(method='ffill').fillna(method='bfill')

        # Vérifier la cohérence High >= Low
        if (df['High'] < df['Low']).any():
            raise ValueError(f"Données incohérentes pour {ticker}: High < Low détecté")

        # Vérifier que Close est entre Low et High
        invalid_close = (df['Close'] > df['High']) | (df['Close'] < df['Low'])
        if invalid_close.any():
            logger.warning(f"Close hors de la plage [Low, High] pour {ticker} ({invalid_close.sum()} occurrences)")
            # Clipper les valeurs
            df.loc[df['Close'] > df['High'], 'Close'] = df.loc[df['Close'] > df['High'], 'High']
            df.loc[df['Close'] < df['Low'], 'Close'] = df.loc[df['Close'] < df['Low'], 'Low']

        # Vérifier les sauts de prix anormaux (> 50% en 1 jour)
        price_changes = df['Close'].pct_change().abs()
        extreme_changes = price_changes > 0.5
        if extreme_changes.any():
            logger.warning(f"Changements de prix extrêmes détectés pour {ticker}: {extreme_changes.sum()} jours")

    def split_train_test(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Sépare les données en train/test de manière chronologique

        Args:
            df: DataFrame complet
            test_size: Proportion des données pour le test (0-1)

        Returns:
            Tuple (train_df, test_df)
        """
        split_idx = int(len(df) * (1 - test_size))
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        logger.info(f"Données divisées: {len(train_df)} train, {len(test_df)} test")
        return train_df, test_df

    def get_latest_price(self, ticker: str) -> float:
        """
        Récupère le prix actuel d'une action

        Args:
            ticker: Symbole boursier

        Returns:
            Prix actuel (close du dernier jour disponible)
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Essayer différentes clés pour le prix actuel
            price_keys = ['currentPrice', 'regularMarketPrice', 'previousClose']
            for key in price_keys:
                if key in info and info[key] is not None:
                    return float(info[key])

            # Fallback: dernier close de l'historique
            df = self.load_data(ticker, period="5d")
            return float(df['Close'].iloc[-1])

        except Exception as e:
            logger.error(f"Erreur récupération prix pour {ticker}: {e}")
            raise ValueError(f"Impossible de récupérer le prix pour {ticker}")

    def clear_cache(self) -> None:
        """Vide le cache des données"""
        self.cache = {}
        logger.info("Cache vidé")
