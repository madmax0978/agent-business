"""
Modèle LSTM (Long Short-Term Memory) pour prédiction de prix

Utilise TensorFlow/Keras pour créer un réseau de neurones récurrent
optimisé pour les séries temporelles financières.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Tuple
import logging
from pathlib import Path

# TensorFlow imports avec gestion des warnings
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Réduire les logs TF

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
import joblib

logger = logging.getLogger(__name__)


class LSTMModel:
    """
    Modèle LSTM pour prédiction de prix d'actions

    Architecture optimisée avec:
    - Couches LSTM empilées
    - Dropout pour régularisation
    - Batch Normalization
    - Early Stopping
    """

    def __init__(
        self,
        sequence_length: int = 60,
        n_features: int = 1,
        lstm_units: list = [128, 64, 32],
        dropout_rate: float = 0.2,
        learning_rate: float = 0.001,
    ):
        """
        Initialise le modèle LSTM

        Args:
            sequence_length: Nombre de jours utilisés pour prédire le futur
            n_features: Nombre de features (1 si univarié, plus si multivarié)
            lstm_units: Liste des unités LSTM par couche [128, 64, 32]
            dropout_rate: Taux de dropout pour régularisation (0.2 = 20%)
            learning_rate: Learning rate pour l'optimiseur Adam
        """
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate

        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.history = None

    def _build_model(self) -> Sequential:
        """
        Construit l'architecture du réseau LSTM

        Returns:
            Modèle Keras compilé
        """
        model = Sequential(name="LSTM_Price_Predictor")

        # Première couche LSTM
        model.add(LSTM(
            units=self.lstm_units[0],
            return_sequences=True,
            input_shape=(self.sequence_length, self.n_features),
            name="lstm_1"
        ))
        model.add(Dropout(self.dropout_rate, name="dropout_1"))
        model.add(BatchNormalization(name="batch_norm_1"))

        # Couches LSTM intermédiaires
        for i, units in enumerate(self.lstm_units[1:-1], start=2):
            model.add(LSTM(
                units=units,
                return_sequences=True,
                name=f"lstm_{i}"
            ))
            model.add(Dropout(self.dropout_rate, name=f"dropout_{i}"))
            model.add(BatchNormalization(name=f"batch_norm_{i}"))

        # Dernière couche LSTM (return_sequences=False)
        model.add(LSTM(
            units=self.lstm_units[-1],
            return_sequences=False,
            name=f"lstm_{len(self.lstm_units)}"
        ))
        model.add(Dropout(self.dropout_rate, name=f"dropout_{len(self.lstm_units)}"))
        model.add(BatchNormalization(name=f"batch_norm_{len(self.lstm_units)}"))

        # Couche de sortie
        model.add(Dense(units=1, name="output"))

        # Compilation
        optimizer = keras.optimizers.Adam(learning_rate=self.learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='mean_squared_error',
            metrics=['mae', 'mape']
        )

        logger.info(f"Modèle LSTM construit: {model.count_params()} paramètres")
        return model

    def _create_sequences(
        self,
        data: np.ndarray,
        target: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Crée des séquences pour l'entraînement LSTM

        Args:
            data: Données features (n_samples, n_features)
            target: Données cibles (n_samples,) ou None

        Returns:
            Tuple (X, y) où X est (n_sequences, sequence_length, n_features)
        """
        X = []
        y = [] if target is not None else None

        for i in range(self.sequence_length, len(data)):
            X.append(data[i - self.sequence_length:i])
            if target is not None:
                y.append(target[i])

        X = np.array(X)
        y = np.array(y) if target is not None else None

        logger.info(f"Séquences créées: {X.shape[0]} échantillons")
        return X, y

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None,
        epochs: int = 100,
        batch_size: int = 32,
        verbose: int = 0
    ) -> Dict:
        """
        Entraîne le modèle LSTM

        Args:
            X_train: Features d'entraînement
            y_train: Target d'entraînement
            X_val: Features de validation (optionnel)
            y_val: Target de validation (optionnel)
            epochs: Nombre d'époques maximum
            batch_size: Taille des batchs
            verbose: Niveau de verbosité (0=silencieux, 1=barre, 2=epoch)

        Returns:
            Dictionnaire avec historique d'entraînement
        """
        logger.info("Début de l'entraînement LSTM...")

        # Normaliser les données
        X_train_scaled = self.scaler.fit_transform(X_train)
        y_train_scaled = y_train.values.reshape(-1, 1)

        # Créer les séquences
        X_seq, y_seq = self._create_sequences(X_train_scaled, y_train_scaled)

        # Préparer la validation
        validation_data = None
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            y_val_scaled = y_val.values.reshape(-1, 1)
            X_val_seq, y_val_seq = self._create_sequences(X_val_scaled, y_val_scaled)
            validation_data = (X_val_seq, y_val_seq)

        # Construire le modèle
        if self.model is None:
            self.n_features = X_train_scaled.shape[1]
            self.model = self._build_model()

        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_loss' if validation_data else 'loss',
                patience=15,
                restore_best_weights=True,
                verbose=1 if verbose > 0 else 0
            ),
            ReduceLROnPlateau(
                monitor='val_loss' if validation_data else 'loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1 if verbose > 0 else 0
            )
        ]

        # Entraînement
        self.history = self.model.fit(
            X_seq, y_seq,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )

        logger.info(f"Entraînement terminé: {len(self.history.history['loss'])} époques")

        return {
            'epochs': len(self.history.history['loss']),
            'final_loss': float(self.history.history['loss'][-1]),
            'final_mae': float(self.history.history['mae'][-1]),
            'history': self.history.history
        }

    def predict(
        self,
        X: pd.DataFrame,
        last_sequence: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Fait des prédictions avec le modèle entraîné

        Args:
            X: Features pour prédiction
            last_sequence: Dernière séquence connue (pour prédictions futures)

        Returns:
            Array de prédictions
        """
        if self.model is None:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions")

        # Normaliser
        X_scaled = self.scaler.transform(X)

        # Créer les séquences
        X_seq, _ = self._create_sequences(X_scaled)

        # Prédire
        predictions_scaled = self.model.predict(X_seq, verbose=0)

        # Dénormaliser (uniquement la première colonne si multivarié)
        predictions = predictions_scaled.flatten()

        return predictions

    def predict_future(
        self,
        last_data: pd.DataFrame,
        n_days: int = 30
    ) -> np.ndarray:
        """
        Prédit les prix futurs de manière itérative

        Args:
            last_data: Dernières données connues (au moins sequence_length lignes)
            n_days: Nombre de jours à prédire

        Returns:
            Array de prédictions futures
        """
        if self.model is None:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions")

        if len(last_data) < self.sequence_length:
            raise ValueError(f"Besoin d'au moins {self.sequence_length} lignes de données")

        # Prendre les dernières données
        current_sequence = last_data.iloc[-self.sequence_length:].copy()
        predictions = []

        for _ in range(n_days):
            # Normaliser
            X_scaled = self.scaler.transform(current_sequence)

            # Reshape pour LSTM
            X_input = X_scaled.reshape(1, self.sequence_length, self.n_features)

            # Prédire
            pred_scaled = self.model.predict(X_input, verbose=0)[0, 0]

            # Stocker la prédiction
            predictions.append(pred_scaled)

            # Créer la nouvelle ligne avec la prédiction
            # (Simplification: on répète les dernières valeurs pour les autres features)
            new_row = current_sequence.iloc[-1].copy()
            # On met à jour seulement la première feature (prix)
            # En production, il faudrait mettre à jour toutes les features calculées

            # Shifter la séquence
            current_sequence = pd.concat([
                current_sequence.iloc[1:],
                pd.DataFrame([new_row], columns=current_sequence.columns)
            ], ignore_index=True)

        return np.array(predictions)

    def save(self, path: str) -> None:
        """
        Sauvegarde le modèle et le scaler

        Args:
            path: Chemin du dossier de sauvegarde
        """
        if self.model is None:
            raise ValueError("Aucun modèle à sauvegarder")

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Sauvegarder le modèle Keras
        model_path = path / "lstm_model.h5"
        self.model.save(str(model_path))

        # Sauvegarder le scaler
        scaler_path = path / "lstm_scaler.pkl"
        joblib.dump(self.scaler, str(scaler_path))

        # Sauvegarder les hyperparamètres
        config_path = path / "lstm_config.pkl"
        config = {
            'sequence_length': self.sequence_length,
            'n_features': self.n_features,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
        }
        joblib.dump(config, str(config_path))

        logger.info(f"Modèle LSTM sauvegardé dans {path}")

    def load(self, path: str) -> None:
        """
        Charge un modèle sauvegardé

        Args:
            path: Chemin du dossier contenant le modèle
        """
        path = Path(path)

        # Charger la config
        config_path = path / "lstm_config.pkl"
        config = joblib.load(str(config_path))
        self.sequence_length = config['sequence_length']
        self.n_features = config['n_features']
        self.lstm_units = config['lstm_units']
        self.dropout_rate = config['dropout_rate']
        self.learning_rate = config['learning_rate']

        # Charger le modèle
        model_path = path / "lstm_model.h5"
        self.model = keras.models.load_model(str(model_path))

        # Charger le scaler
        scaler_path = path / "lstm_scaler.pkl"
        self.scaler = joblib.load(str(scaler_path))

        logger.info(f"Modèle LSTM chargé depuis {path}")
