"""
Modèle Ensemble pour combiner LSTM et Prophet

Combine les prédictions de plusieurs modèles avec pondération dynamique
basée sur la performance récente pour des prédictions plus robustes.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import joblib

from .lstm_model import LSTMModel
from .prophet_model import ProphetModel

logger = logging.getLogger(__name__)


class EnsembleModel:
    """
    Modèle ensemble combinant LSTM et Prophet

    Utilise une stratégie de voting pondéré où les poids sont ajustés
    dynamiquement selon la performance récente de chaque modèle.
    """

    def __init__(
        self,
        models: Optional[Dict[str, any]] = None,
        weights: Optional[Dict[str, float]] = None,
        voting_strategy: str = "weighted"
    ):
        """
        Initialise le modèle ensemble

        Args:
            models: Dictionnaire {nom: modèle} ou None pour créer LSTM + Prophet
            weights: Poids initiaux {nom: poids} ou None pour égaux
            voting_strategy: "weighted", "average", "best"
        """
        self.voting_strategy = voting_strategy
        self.performance_history = {}

        # Initialiser les modèles
        if models is None:
            self.models = {
                'lstm': LSTMModel(),
                'prophet': ProphetModel()
            }
        else:
            self.models = models

        # Initialiser les poids
        if weights is None:
            # Poids égaux au départ
            n_models = len(self.models)
            self.weights = {name: 1.0 / n_models for name in self.models.keys()}
        else:
            self.weights = weights
            # Normaliser
            total = sum(self.weights.values())
            self.weights = {k: v / total for k, v in self.weights.items()}

        logger.info(f"Ensemble créé avec {len(self.models)} modèles: {list(self.models.keys())}")
        logger.info(f"Poids initiaux: {self.weights}")

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        epochs: int = 100,
        verbose: int = 0
    ) -> Dict:
        """
        Entraîne tous les modèles de l'ensemble

        Args:
            X_train: Features d'entraînement
            y_train: Target d'entraînement
            X_val: Features de validation
            y_val: Target de validation
            epochs: Nombre d'époques (pour LSTM)
            verbose: Niveau de verbosité

        Returns:
            Dictionnaire avec résultats d'entraînement de chaque modèle
        """
        logger.info("Entraînement de l'ensemble...")
        results = {}

        for name, model in self.models.items():
            try:
                logger.info(f"Entraînement de {name}...")

                if name == 'lstm':
                    result = model.train(
                        X_train, y_train, X_val, y_val,
                        epochs=epochs, verbose=verbose
                    )
                elif name == 'prophet':
                    result = model.train(X_train, y_train, verbose=verbose)
                else:
                    # Modèle générique
                    result = model.train(X_train, y_train, X_val, y_val)

                results[name] = result
                logger.info(f"{name} entraîné avec succès")

            except Exception as e:
                logger.error(f"Erreur lors de l'entraînement de {name}: {str(e)}")
                results[name] = {'error': str(e)}

        return results

    def predict(
        self,
        X: pd.DataFrame,
        return_individual: bool = False
    ) -> np.ndarray:
        """
        Fait des prédictions avec l'ensemble

        Args:
            X: Features pour prédiction
            return_individual: Si True, retourne aussi les prédictions individuelles

        Returns:
            Array de prédictions combinées (et dict des individuelles si demandé)
        """
        predictions = {}
        valid_predictions = {}

        # Collecter les prédictions de chaque modèle
        for name, model in self.models.items():
            try:
                pred = model.predict(X)
                predictions[name] = pred

                # Vérifier que les prédictions sont valides
                if not np.isnan(pred).any() and len(pred) > 0:
                    valid_predictions[name] = pred
                else:
                    logger.warning(f"Prédictions invalides pour {name}")

            except Exception as e:
                logger.error(f"Erreur lors de la prédiction avec {name}: {str(e)}")

        if not valid_predictions:
            raise ValueError("Aucun modèle n'a pu faire de prédictions valides")

        # Combiner les prédictions selon la stratégie
        if self.voting_strategy == "weighted":
            ensemble_pred = self._weighted_average(valid_predictions)
        elif self.voting_strategy == "average":
            ensemble_pred = self._simple_average(valid_predictions)
        elif self.voting_strategy == "best":
            ensemble_pred = self._best_model(valid_predictions)
        else:
            raise ValueError(f"Stratégie inconnue: {self.voting_strategy}")

        if return_individual:
            return ensemble_pred, predictions
        else:
            return ensemble_pred

    def _weighted_average(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """
        Moyenne pondérée des prédictions

        Args:
            predictions: {nom_modèle: array_predictions}

        Returns:
            Array de prédictions combinées
        """
        # Normaliser les poids pour les modèles valides
        valid_weights = {k: self.weights.get(k, 1.0) for k in predictions.keys()}
        total_weight = sum(valid_weights.values())
        normalized_weights = {k: v / total_weight for k, v in valid_weights.items()}

        # Calculer la moyenne pondérée
        result = np.zeros_like(next(iter(predictions.values())))
        for name, pred in predictions.items():
            result += normalized_weights[name] * pred

        logger.info(f"Prédictions combinées avec poids: {normalized_weights}")
        return result

    def _simple_average(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Moyenne simple des prédictions"""
        result = np.mean([pred for pred in predictions.values()], axis=0)
        return result

    def _best_model(self, predictions: Dict[str, np.ndarray]) -> np.ndarray:
        """Utilise seulement le meilleur modèle"""
        # Trouver le modèle avec le plus haut poids
        best_name = max(self.weights.items(), key=lambda x: x[1])[0]

        if best_name in predictions:
            logger.info(f"Utilisation du meilleur modèle: {best_name}")
            return predictions[best_name]
        else:
            # Fallback sur le premier modèle disponible
            logger.warning(f"Meilleur modèle {best_name} indisponible, fallback")
            return next(iter(predictions.values()))

    def update_weights(
        self,
        performances: Dict[str, float],
        learning_rate: float = 0.1
    ) -> None:
        """
        Met à jour les poids selon les performances récentes

        Args:
            performances: {nom_modèle: score} (plus bas = meilleur, ex: MAE)
            learning_rate: Taux d'apprentissage pour mise à jour (0-1)
        """
        # Inverser les scores (on veut récompenser les bons modèles)
        # Utiliser softmax pour normaliser
        scores = {k: 1.0 / (v + 1e-10) for k, v in performances.items()}

        # Softmax
        exp_scores = {k: np.exp(v) for k, v in scores.items()}
        total = sum(exp_scores.values())
        new_weights = {k: v / total for k, v in exp_scores.items()}

        # Mise à jour progressive (learning rate)
        for name in self.weights.keys():
            if name in new_weights:
                old_weight = self.weights[name]
                new_weight = new_weights[name]
                self.weights[name] = (1 - learning_rate) * old_weight + learning_rate * new_weight

        # Normaliser
        total = sum(self.weights.values())
        self.weights = {k: v / total for k, v in self.weights.items()}

        logger.info(f"Poids mis à jour: {self.weights}")

    def evaluate_and_update(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        metric: str = "mae"
    ) -> Dict:
        """
        Évalue chaque modèle et met à jour les poids

        Args:
            X_test: Features de test
            y_test: Target de test
            metric: Métrique d'évaluation ("mae", "rmse", "mape")

        Returns:
            Dictionnaire avec performances de chaque modèle
        """
        from ..evaluation import ModelEvaluator
        evaluator = ModelEvaluator()

        performances = {}

        for name, model in self.models.items():
            try:
                pred = model.predict(X_test)

                if metric == "mae":
                    score = evaluator.calculate_mae(y_test.values, pred)
                elif metric == "rmse":
                    score = evaluator.calculate_rmse(y_test.values, pred)
                elif metric == "mape":
                    score = evaluator.calculate_mape(y_test.values, pred)
                else:
                    raise ValueError(f"Métrique inconnue: {metric}")

                performances[name] = score
                logger.info(f"{name} - {metric.upper()}: {score:.4f}")

            except Exception as e:
                logger.error(f"Erreur évaluation {name}: {str(e)}")
                performances[name] = float('inf')

        # Mettre à jour les poids
        self.update_weights(performances)

        return performances

    def predict_future(
        self,
        last_data: pd.DataFrame,
        n_days: int = 30
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Prédit les prix futurs avec l'ensemble

        Args:
            last_data: Dernières données connues
            n_days: Nombre de jours à prédire

        Returns:
            Tuple (prédictions_ensemble, prédictions_individuelles)
        """
        predictions = {}

        for name, model in self.models.items():
            try:
                if name == 'lstm':
                    pred = model.predict_future(last_data, n_days)
                elif name == 'prophet':
                    forecast = model.predict_future(n_days, include_history=False)
                    pred = forecast['yhat'].values
                else:
                    pred = model.predict_future(last_data, n_days)

                predictions[name] = pred

            except Exception as e:
                logger.error(f"Erreur prédiction future {name}: {str(e)}")

        # Combiner
        if predictions:
            ensemble_pred = self._weighted_average(predictions)
            return ensemble_pred, predictions
        else:
            raise ValueError("Aucun modèle n'a pu faire de prédictions")

    def save(self, path: str) -> None:
        """
        Sauvegarde l'ensemble complet

        Args:
            path: Chemin du dossier de sauvegarde
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Sauvegarder chaque modèle dans son sous-dossier
        for name, model in self.models.items():
            model_path = path / name
            model.save(str(model_path))

        # Sauvegarder la configuration de l'ensemble
        config_path = path / "ensemble_config.pkl"
        config = {
            'weights': self.weights,
            'voting_strategy': self.voting_strategy,
            'model_names': list(self.models.keys()),
            'performance_history': self.performance_history,
        }
        joblib.dump(config, str(config_path))

        logger.info(f"Ensemble sauvegardé dans {path}")

    def load(self, path: str) -> None:
        """
        Charge un ensemble sauvegardé

        Args:
            path: Chemin du dossier contenant l'ensemble
        """
        path = Path(path)

        # Charger la configuration
        config_path = path / "ensemble_config.pkl"
        config = joblib.load(str(config_path))

        self.weights = config['weights']
        self.voting_strategy = config['voting_strategy']
        self.performance_history = config.get('performance_history', {})

        # Charger chaque modèle
        self.models = {}
        for name in config['model_names']:
            model_path = path / name

            if name == 'lstm':
                model = LSTMModel()
            elif name == 'prophet':
                model = ProphetModel()
            else:
                logger.warning(f"Type de modèle inconnu: {name}, ignoré")
                continue

            model.load(str(model_path))
            self.models[name] = model

        logger.info(f"Ensemble chargé depuis {path}")
