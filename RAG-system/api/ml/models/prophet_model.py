"""
Modèle Prophet (Facebook) pour prédiction de prix

Prophet est robuste face aux données manquantes, gère automatiquement
les tendances et la saisonnalité. Idéal pour les séries temporelles financières.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict
import logging
from pathlib import Path
import joblib

# Prophet import avec gestion des warnings
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None

logger = logging.getLogger(__name__)


class ProphetModel:
    """
    Modèle Prophet pour prédiction de prix d'actions

    Utilise la bibliothèque Prophet de Facebook pour des prédictions
    robustes avec gestion automatique des tendances et saisonnalité.
    """

    def __init__(
        self,
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
        daily_seasonality: bool = False,
        weekly_seasonality: bool = True,
        yearly_seasonality: bool = True,
        changepoint_range: float = 0.9,
    ):
        """
        Initialise le modèle Prophet

        Args:
            changepoint_prior_scale: Flexibilité de la tendance (0.001-0.5)
                                     Plus élevé = plus flexible
            seasonality_prior_scale: Force de la saisonnalité (0.01-10)
            daily_seasonality: Activer saisonnalité quotidienne
            weekly_seasonality: Activer saisonnalité hebdomadaire
            yearly_seasonality: Activer saisonnalité annuelle
            changepoint_range: Proportion de l'historique pour détecter changements
        """
        if not PROPHET_AVAILABLE:
            raise ImportError(
                "Prophet n'est pas installé. Installez avec: pip install prophet"
            )

        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_prior_scale = seasonality_prior_scale
        self.daily_seasonality = daily_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.yearly_seasonality = yearly_seasonality
        self.changepoint_range = changepoint_range

        self.model = None
        self.trained = False

    def _create_model(self) -> Prophet:
        """
        Crée une instance du modèle Prophet

        Returns:
            Modèle Prophet configuré
        """
        model = Prophet(
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_prior_scale=self.seasonality_prior_scale,
            daily_seasonality=self.daily_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            yearly_seasonality=self.yearly_seasonality,
            changepoint_range=self.changepoint_range,
            interval_width=0.95,  # Intervalles de confiance à 95%
        )

        logger.info("Modèle Prophet créé")
        return model

    def _prepare_data(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        date_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Prépare les données au format Prophet (ds, y)

        Args:
            X: Features (doit contenir une colonne date ou avoir un index datetime)
            y: Target (prix)
            date_col: Nom de la colonne date ou None si index

        Returns:
            DataFrame au format Prophet
        """
        df = pd.DataFrame()

        # Récupérer les dates
        if date_col and date_col in X.columns:
            df['ds'] = pd.to_datetime(X[date_col])
        elif isinstance(X.index, pd.DatetimeIndex):
            df['ds'] = X.index
        else:
            # Générer des dates artificielles (1 jour par ligne)
            df['ds'] = pd.date_range(start='2020-01-01', periods=len(X), freq='D')
            logger.warning("Aucune colonne date trouvée, dates artificielles générées")

        # Target
        df['y'] = y.values

        # Ajouter les features comme regresseurs (optionnel)
        # Pour l'instant on utilise seulement le prix
        # Mais on pourrait ajouter: volume, indicateurs techniques, etc.

        return df

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        add_regressors: Optional[list] = None,
        verbose: int = 0
    ) -> Dict:
        """
        Entraîne le modèle Prophet

        Args:
            X_train: Features d'entraînement (avec dates)
            y_train: Target d'entraînement (prix)
            X_val: Features de validation (non utilisé par Prophet)
            y_val: Target de validation (non utilisé par Prophet)
            add_regressors: Liste de colonnes X à utiliser comme regresseurs
            verbose: Niveau de verbosité

        Returns:
            Dictionnaire avec métriques d'entraînement
        """
        logger.info("Début de l'entraînement Prophet...")

        # Créer le modèle
        self.model = self._create_model()

        # Ajouter des regresseurs si demandé
        if add_regressors:
            for reg in add_regressors:
                if reg in X_train.columns:
                    self.model.add_regressor(reg)
                    logger.info(f"Regresseur ajouté: {reg}")

        # Préparer les données
        df_train = self._prepare_data(X_train, y_train)

        # Ajouter les regresseurs aux données
        if add_regressors:
            for reg in add_regressors:
                if reg in X_train.columns:
                    df_train[reg] = X_train[reg].values

        # Entraîner (Prophet utilise Stan en arrière-plan)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(df_train)

        self.trained = True
        logger.info("Entraînement Prophet terminé")

        # Prophet n'a pas de métriques d'entraînement traditionnelles
        return {
            'trained': True,
            'n_samples': len(df_train),
            'changepoints': len(self.model.changepoints)
        }

    def predict(
        self,
        X: pd.DataFrame,
        return_components: bool = False
    ) -> np.ndarray:
        """
        Fait des prédictions avec le modèle entraîné

        Args:
            X: Features pour prédiction (avec dates)
            return_components: Si True, retourne aussi les composantes (trend, seasonality)

        Returns:
            Array de prédictions ou DataFrame si return_components=True
        """
        if not self.trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions")

        # Préparer les données (sans y)
        df = pd.DataFrame()
        if isinstance(X.index, pd.DatetimeIndex):
            df['ds'] = X.index
        else:
            df['ds'] = pd.date_range(start='2020-01-01', periods=len(X), freq='D')

        # Prédire
        forecast = self.model.predict(df)

        if return_components:
            return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper', 'trend']]
        else:
            return forecast['yhat'].values

    def predict_future(
        self,
        n_days: int = 30,
        include_history: bool = False
    ) -> pd.DataFrame:
        """
        Prédit les prix futurs

        Args:
            n_days: Nombre de jours à prédire
            include_history: Inclure l'historique dans les prédictions

        Returns:
            DataFrame avec colonnes: ds, yhat, yhat_lower, yhat_upper
        """
        if not self.trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions")

        # Créer le dataframe futur
        future = self.model.make_future_dataframe(periods=n_days, include_history=include_history)

        # Prédire
        forecast = self.model.predict(future)

        # Retourner seulement les colonnes utiles
        result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

        if not include_history:
            # Garder seulement les prédictions futures
            result = result.tail(n_days)

        logger.info(f"Prédictions futures générées: {len(result)} jours")
        return result

    def get_forecast_components(self) -> Dict:
        """
        Récupère les composantes de la prévision

        Returns:
            Dictionnaire avec trend, weekly, yearly, etc.
        """
        if not self.trained:
            raise ValueError("Le modèle doit être entraîné d'abord")

        # Faire une prédiction sur tout l'historique
        forecast = self.predict_future(n_days=30, include_history=True)

        components = {
            'trend': forecast['yhat'].values,
            'has_weekly': self.weekly_seasonality,
            'has_yearly': self.yearly_seasonality,
        }

        return components

    def save(self, path: str) -> None:
        """
        Sauvegarde le modèle Prophet

        Args:
            path: Chemin du dossier de sauvegarde
        """
        if not self.trained:
            raise ValueError("Aucun modèle à sauvegarder")

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Sauvegarder le modèle Prophet (sérialisé)
        model_path = path / "prophet_model.pkl"
        joblib.dump(self.model, str(model_path))

        # Sauvegarder la config
        config_path = path / "prophet_config.pkl"
        config = {
            'changepoint_prior_scale': self.changepoint_prior_scale,
            'seasonality_prior_scale': self.seasonality_prior_scale,
            'daily_seasonality': self.daily_seasonality,
            'weekly_seasonality': self.weekly_seasonality,
            'yearly_seasonality': self.yearly_seasonality,
            'changepoint_range': self.changepoint_range,
            'trained': self.trained,
        }
        joblib.dump(config, str(config_path))

        logger.info(f"Modèle Prophet sauvegardé dans {path}")

    def load(self, path: str) -> None:
        """
        Charge un modèle Prophet sauvegardé

        Args:
            path: Chemin du dossier contenant le modèle
        """
        path = Path(path)

        # Charger la config
        config_path = path / "prophet_config.pkl"
        config = joblib.load(str(config_path))
        self.changepoint_prior_scale = config['changepoint_prior_scale']
        self.seasonality_prior_scale = config['seasonality_prior_scale']
        self.daily_seasonality = config['daily_seasonality']
        self.weekly_seasonality = config['weekly_seasonality']
        self.yearly_seasonality = config['yearly_seasonality']
        self.changepoint_range = config['changepoint_range']
        self.trained = config['trained']

        # Charger le modèle
        model_path = path / "prophet_model.pkl"
        self.model = joblib.load(str(model_path))

        logger.info(f"Modèle Prophet chargé depuis {path}")
