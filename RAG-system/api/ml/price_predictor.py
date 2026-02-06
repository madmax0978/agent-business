"""
Classe principale PricePredictor

Interface unifiée pour la prédiction de prix d'actions.
Gère l'entraînement, la prédiction, l'évaluation et la sauvegarde des modèles.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
import json

from .data_loader import DataLoader
from .feature_engineering import FeatureEngineer
from .models.lstm_model import LSTMModel
from .models.prophet_model import ProphetModel
from .models.ensemble import EnsembleModel
from .evaluation import ModelEvaluator

logger = logging.getLogger(__name__)


class PricePredictor:
    """
    Interface principale pour la prédiction de prix d'actions

    Cette classe orchestre tout le pipeline ML:
    1. Chargement des données
    2. Feature engineering
    3. Entraînement des modèles
    4. Prédictions
    5. Évaluation
    6. Sauvegarde/Chargement

    Usage:
        predictor = PricePredictor(model_type="ensemble")
        predictor.train("MC.PA", start_date="2020-01-01", end_date="2024-12-31")
        predictions = predictor.predict("MC.PA", horizon=30)
    """

    def __init__(
        self,
        model_type: str = "ensemble",
        model_dir: str = "/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/data/ml_models"
    ):
        """
        Initialise le prédicteur

        Args:
            model_type: Type de modèle ("lstm", "prophet", "ensemble")
            model_dir: Répertoire pour sauvegarder les modèles
        """
        self.model_type = model_type
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Composants
        self.data_loader = DataLoader()
        self.feature_engineer = FeatureEngineer()
        self.evaluator = ModelEvaluator()

        # Modèle (initialisé lors de l'entraînement)
        self.model = None
        self.ticker = None
        self.trained_at = None
        self.training_metrics = {}

        logger.info(f"PricePredictor initialisé avec modèle: {model_type}")

    def train(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        period: str = "2y",
        test_size: float = 0.2,
        epochs: int = 100,
        verbose: int = 0
    ) -> Dict:
        """
        Entraîne le modèle sur les données historiques

        Args:
            ticker: Symbole boursier (ex: "MC.PA")
            start_date: Date de début (YYYY-MM-DD) ou None
            end_date: Date de fin (YYYY-MM-DD) ou None
            period: Période si pas de dates ("1y", "2y", "5y")
            test_size: Proportion des données pour test (0-1)
            epochs: Nombre d'époques d'entraînement (pour LSTM)
            verbose: Niveau de verbosité

        Returns:
            Dictionnaire avec résultats d'entraînement
        """
        logger.info(f"Début entraînement pour {ticker}...")
        self.ticker = ticker

        try:
            # 1. Charger les données
            logger.info("Chargement des données...")
            df = self.data_loader.load_data(ticker, start_date, end_date, period)

            # 2. Feature engineering
            logger.info("Calcul des features techniques...")
            df = self.feature_engineer.calculate_all_features(df)

            # 3. Préparer pour ML
            X, y = self.feature_engineer.prepare_for_ml(df, target_col='Close')

            # 4. Split train/test
            split_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

            logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")

            # 5. Créer et entraîner le modèle
            if self.model_type == "lstm":
                self.model = LSTMModel(n_features=X_train.shape[1])
                train_results = self.model.train(
                    X_train, y_train, X_test, y_test,
                    epochs=epochs, verbose=verbose
                )

            elif self.model_type == "prophet":
                self.model = ProphetModel()
                # Prophet n'utilise que la colonne Close + Date
                X_train_prophet = df.iloc[:split_idx][['Date']].copy()
                train_results = self.model.train(
                    X_train_prophet, y_train, verbose=verbose
                )

            elif self.model_type == "ensemble":
                self.model = EnsembleModel()
                train_results = self.model.train(
                    X_train, y_train, X_test, y_test,
                    epochs=epochs, verbose=verbose
                )

            else:
                raise ValueError(f"Type de modèle inconnu: {self.model_type}")

            # 6. Évaluer sur le test set
            logger.info("Évaluation sur test set...")
            if self.model_type == "prophet":
                X_test_prophet = df.iloc[split_idx:][['Date']].copy()
                y_pred = self.model.predict(X_test_prophet)
            else:
                y_pred = self.model.predict(X_test)

            # Ajuster les tailles si nécessaire (LSTM crée des séquences)
            min_len = min(len(y_test), len(y_pred))
            y_test_aligned = y_test.iloc[-min_len:].values
            y_pred_aligned = y_pred[-min_len:]

            eval_metrics = self.evaluator.evaluate_model(y_test_aligned, y_pred_aligned)

            # 7. Sauvegarder les métriques
            self.trained_at = datetime.now().isoformat()
            self.training_metrics = {
                'ticker': ticker,
                'model_type': self.model_type,
                'trained_at': self.trained_at,
                'train_size': len(X_train),
                'test_size': len(X_test),
                'train_results': train_results,
                'evaluation': eval_metrics,
                'data_range': {
                    'start': df['Date'].min().strftime('%Y-%m-%d') if 'Date' in df.columns else None,
                    'end': df['Date'].max().strftime('%Y-%m-%d') if 'Date' in df.columns else None,
                }
            }

            logger.info(f"Entraînement terminé - MAE: {eval_metrics['mae']:.2f}, "
                       f"MAPE: {eval_metrics['mape']:.2f}%")

            return self.training_metrics

        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement: {str(e)}")
            raise

    def predict(
        self,
        ticker: str,
        horizon: int = 30,
        return_confidence: bool = True
    ) -> Dict:
        """
        Prédit les prix futurs

        Args:
            ticker: Symbole boursier
            horizon: Nombre de jours à prédire
            return_confidence: Inclure intervalles de confiance

        Returns:
            Dictionnaire avec prédictions détaillées
        """
        if self.model is None:
            # Essayer de charger le modèle
            logger.info(f"Aucun modèle en mémoire, tentative de chargement pour {ticker}")
            self.load_model(ticker)

        if self.model is None:
            raise ValueError(f"Aucun modèle disponible pour {ticker}. Entraînez d'abord.")

        logger.info(f"Prédiction pour {ticker} sur {horizon} jours...")

        try:
            # Charger les données récentes
            df = self.data_loader.load_data(ticker, period="6mo")
            df = self.feature_engineer.calculate_all_features(df)

            # Prix actuel
            current_price = float(df['Close'].iloc[-1])
            current_date = df['Date'].iloc[-1] if 'Date' in df.columns else datetime.now()

            # Faire les prédictions
            if self.model_type == "prophet":
                forecast = self.model.predict_future(n_days=horizon, include_history=False)
                predictions_values = forecast['yhat'].values
                lower_bound = forecast['yhat_lower'].values
                upper_bound = forecast['yhat_upper'].values

            elif self.model_type == "ensemble":
                X, _ = self.feature_engineer.prepare_for_ml(df)
                predictions_values, individual = self.model.predict_future(X, horizon)
                # Calculer intervalles de confiance approximatifs
                lower_bound, upper_bound = self.evaluator.get_confidence_intervals(predictions_values)

            else:  # LSTM
                X, _ = self.feature_engineer.prepare_for_ml(df)
                predictions_values = self.model.predict_future(X, horizon)
                lower_bound, upper_bound = self.evaluator.get_confidence_intervals(predictions_values)

            # Générer les dates futures
            future_dates = [
                (current_date + timedelta(days=i+1)).strftime('%Y-%m-%d')
                for i in range(horizon)
            ]

            # Formater les prédictions
            predictions_list = []
            for i, (date, pred, lower, upper) in enumerate(zip(
                future_dates, predictions_values, lower_bound, upper_bound
            )):
                # Confidence décroit avec l'horizon
                confidence = max(0.5, 0.95 - (i * 0.01))

                predictions_list.append({
                    'date': date,
                    'predicted_price': float(pred),
                    'confidence': float(confidence),
                    'lower_bound': float(lower) if return_confidence else None,
                    'upper_bound': float(upper) if return_confidence else None,
                })

            # Déterminer la tendance
            price_change_pct = ((predictions_values[-1] - current_price) / current_price) * 100
            if price_change_pct > 5:
                trend = "BULLISH"
            elif price_change_pct < -5:
                trend = "BEARISH"
            else:
                trend = "NEUTRAL"

            # Recommandation
            if trend == "BULLISH" and price_change_pct > 10:
                recommendation = "STRONG_BUY"
            elif trend == "BULLISH":
                recommendation = "BUY"
            elif trend == "BEARISH" and price_change_pct < -10:
                recommendation = "STRONG_SELL"
            elif trend == "BEARISH":
                recommendation = "SELL"
            else:
                recommendation = "HOLD"

            result = {
                'ticker': ticker,
                'current_price': current_price,
                'predictions': predictions_list,
                'trend': trend,
                'price_change_pct': float(price_change_pct),
                'confidence_avg': float(np.mean([p['confidence'] for p in predictions_list])),
                'recommendation': recommendation,
                'model_used': self.model_type.upper(),
                'trained_on': self.training_metrics.get('data_range', {}),
                'metrics': {
                    'mae': self.training_metrics.get('evaluation', {}).get('mae'),
                    'rmse': self.training_metrics.get('evaluation', {}).get('rmse'),
                    'mape': self.training_metrics.get('evaluation', {}).get('mape'),
                    'direction_accuracy': self.training_metrics.get('evaluation', {}).get('direction_accuracy'),
                }
            }

            logger.info(f"Prédictions générées: {trend} ({price_change_pct:.2f}%)")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la prédiction: {str(e)}")
            raise

    def evaluate(
        self,
        ticker: str,
        test_size: float = 0.2,
        generate_report: bool = True
    ) -> Dict:
        """
        Évalue le modèle sur des données récentes

        Args:
            ticker: Symbole boursier
            test_size: Proportion pour le test
            generate_report: Générer un rapport texte

        Returns:
            Dictionnaire avec métriques d'évaluation
        """
        if self.model is None:
            self.load_model(ticker)

        if self.model is None:
            raise ValueError(f"Aucun modèle disponible pour {ticker}")

        logger.info(f"Évaluation du modèle pour {ticker}...")

        try:
            # Charger les données
            df = self.data_loader.load_data(ticker, period="1y")
            df = self.feature_engineer.calculate_all_features(df)
            X, y = self.feature_engineer.prepare_for_ml(df)

            # Split
            split_idx = int(len(X) * (1 - test_size))
            X_test = X.iloc[split_idx:]
            y_test = y.iloc[split_idx:]

            # Prédire
            y_pred = self.model.predict(X_test)

            # Aligner
            min_len = min(len(y_test), len(y_pred))
            y_test_aligned = y_test.iloc[-min_len:].values
            y_pred_aligned = y_pred[-min_len:]

            # Évaluer
            metrics = self.evaluator.evaluate_model(y_test_aligned, y_pred_aligned)

            # Rapport
            if generate_report:
                report = self.evaluator.generate_evaluation_report(
                    y_test_aligned, y_pred_aligned,
                    model_name=f"{self.model_type.upper()} - {ticker}"
                )
                metrics['report'] = report

            return metrics

        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation: {str(e)}")
            raise

    def save_model(self, ticker: str, version: str = "v1") -> None:
        """
        Sauvegarde le modèle entraîné

        Args:
            ticker: Symbole boursier
            version: Version du modèle (v1, v2, etc.)
        """
        if self.model is None:
            raise ValueError("Aucun modèle à sauvegarder")

        # Créer le chemin
        model_path = self.model_dir / ticker / version / self.model_type
        model_path.mkdir(parents=True, exist_ok=True)

        # Sauvegarder le modèle
        self.model.save(str(model_path))

        # Sauvegarder les métadonnées
        metadata = {
            'ticker': ticker,
            'model_type': self.model_type,
            'version': version,
            'trained_at': self.trained_at,
            'training_metrics': self.training_metrics,
        }

        metadata_path = model_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Modèle sauvegardé: {model_path}")

    def load_model(self, ticker: str, version: str = "v1") -> None:
        """
        Charge un modèle sauvegardé

        Args:
            ticker: Symbole boursier
            version: Version du modèle
        """
        model_path = self.model_dir / ticker / version / self.model_type

        if not model_path.exists():
            raise FileNotFoundError(f"Aucun modèle trouvé: {model_path}")

        # Charger les métadonnées
        metadata_path = model_path / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.training_metrics = metadata.get('training_metrics', {})
                self.trained_at = metadata.get('trained_at')

        # Créer et charger le modèle
        if self.model_type == "lstm":
            self.model = LSTMModel()
        elif self.model_type == "prophet":
            self.model = ProphetModel()
        elif self.model_type == "ensemble":
            self.model = EnsembleModel()

        self.model.load(str(model_path))
        self.ticker = ticker

        logger.info(f"Modèle chargé: {model_path}")

    def list_available_models(self) -> List[Dict]:
        """
        Liste tous les modèles disponibles

        Returns:
            Liste de dictionnaires avec infos des modèles
        """
        models = []

        if not self.model_dir.exists():
            return models

        for ticker_dir in self.model_dir.iterdir():
            if not ticker_dir.is_dir():
                continue

            ticker = ticker_dir.name

            for version_dir in ticker_dir.iterdir():
                if not version_dir.is_dir():
                    continue

                version = version_dir.name

                for model_type_dir in version_dir.iterdir():
                    if not model_type_dir.is_dir():
                        continue

                    model_type = model_type_dir.name
                    metadata_path = model_type_dir / "metadata.json"

                    metadata = {}
                    if metadata_path.exists():
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)

                    models.append({
                        'ticker': ticker,
                        'version': version,
                        'model_type': model_type,
                        'trained_at': metadata.get('trained_at'),
                        'path': str(model_type_dir),
                        'metrics': metadata.get('training_metrics', {}).get('evaluation', {}),
                    })

        return models

    def delete_model(self, ticker: str, version: str = "v1") -> bool:
        """
        Supprime un modèle sauvegardé

        Args:
            ticker: Symbole boursier
            version: Version du modèle

        Returns:
            True si supprimé avec succès
        """
        model_path = self.model_dir / ticker / version

        if not model_path.exists():
            logger.warning(f"Modèle non trouvé: {model_path}")
            return False

        import shutil
        shutil.rmtree(model_path)
        logger.info(f"Modèle supprimé: {model_path}")
        return True
