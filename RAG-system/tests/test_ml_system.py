"""
Tests unitaires pour le système ML de prédiction de prix

Execute avec: pytest tests/test_ml_system.py -v
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from ml.data_loader import DataLoader
from ml.feature_engineering import FeatureEngineer
from ml.evaluation import ModelEvaluator
from ml.price_predictor import PricePredictor


# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture
def sample_data():
    """Crée des données de test synthétiques"""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    np.random.seed(42)

    data = {
        'Date': dates,
        'Open': 100 + np.random.randn(100).cumsum(),
        'High': 102 + np.random.randn(100).cumsum(),
        'Low': 98 + np.random.randn(100).cumsum(),
        'Close': 100 + np.random.randn(100).cumsum(),
        'Volume': np.random.randint(1000000, 10000000, 100)
    }

    df = pd.DataFrame(data)
    # Assurer que High >= Low
    df['High'] = df[['High', 'Low', 'Close']].max(axis=1)
    df['Low'] = df[['Low', 'Close']].min(axis=1)

    return df


@pytest.fixture
def data_loader():
    """Fixture pour DataLoader"""
    return DataLoader()


@pytest.fixture
def feature_engineer():
    """Fixture pour FeatureEngineer"""
    return FeatureEngineer()


@pytest.fixture
def evaluator():
    """Fixture pour ModelEvaluator"""
    return ModelEvaluator()


# ==========================================
# TESTS DATA LOADER
# ==========================================

class TestDataLoader:
    """Tests pour le chargeur de données"""

    def test_load_data_valid_ticker(self, data_loader):
        """Test chargement d'un ticker valide"""
        # Test avec LVMH (MC.PA)
        df = data_loader.load_data("MC.PA", period="1mo")

        assert not df.empty
        assert 'Date' in df.columns
        assert 'Close' in df.columns
        assert len(df) > 10

    def test_load_data_invalid_ticker(self, data_loader):
        """Test chargement d'un ticker invalide"""
        with pytest.raises(ValueError):
            data_loader.load_data("INVALID_TICKER_XYZ", period="1mo")

    def test_split_train_test(self, data_loader, sample_data):
        """Test split train/test"""
        train, test = data_loader.split_train_test(sample_data, test_size=0.2)

        assert len(train) == 80
        assert len(test) == 20
        assert train.columns.equals(test.columns)

    def test_get_latest_price(self, data_loader):
        """Test récupération prix actuel"""
        price = data_loader.get_latest_price("MC.PA")

        assert price > 0
        assert isinstance(price, float)


# ==========================================
# TESTS FEATURE ENGINEERING
# ==========================================

class TestFeatureEngineer:
    """Tests pour l'ingénieur de features"""

    def test_calculate_all_features(self, feature_engineer, sample_data):
        """Test calcul de toutes les features"""
        df_features = feature_engineer.calculate_all_features(sample_data)

        # Vérifier que des features ont été ajoutées
        assert len(df_features.columns) > len(sample_data.columns)

        # Vérifier présence des features clés
        assert 'RSI' in df_features.columns
        assert 'MACD' in df_features.columns
        assert 'SMA_20' in df_features.columns
        assert 'BB_upper' in df_features.columns

    def test_rsi_bounds(self, feature_engineer, sample_data):
        """Test que RSI est entre 0 et 100"""
        df = feature_engineer.calculate_all_features(sample_data)

        assert df['RSI'].min() >= 0
        assert df['RSI'].max() <= 100

    def test_bollinger_bands_order(self, feature_engineer, sample_data):
        """Test que BB_upper > BB_middle > BB_lower"""
        df = feature_engineer.calculate_all_features(sample_data)

        assert (df['BB_upper'] >= df['BB_middle']).all()
        assert (df['BB_middle'] >= df['BB_lower']).all()

    def test_prepare_for_ml(self, feature_engineer, sample_data):
        """Test préparation pour ML"""
        df = feature_engineer.calculate_all_features(sample_data)
        X, y = feature_engineer.prepare_for_ml(df, target_col='Close')

        # Vérifier les dimensions
        assert len(X) == len(y)
        assert X.shape[1] > 5  # Au moins quelques features

        # Vérifier pas de NaN
        assert not X.isnull().any().any()
        assert not y.isnull().any()


# ==========================================
# TESTS EVALUATION
# ==========================================

class TestModelEvaluator:
    """Tests pour l'évaluateur de modèles"""

    def test_calculate_mae(self, evaluator):
        """Test calcul MAE"""
        y_true = np.array([100, 110, 105, 115])
        y_pred = np.array([98, 112, 107, 113])

        mae = evaluator.calculate_mae(y_true, y_pred)

        assert mae > 0
        assert mae == pytest.approx(2.0, rel=0.01)

    def test_calculate_rmse(self, evaluator):
        """Test calcul RMSE"""
        y_true = np.array([100, 110, 105, 115])
        y_pred = np.array([98, 112, 107, 113])

        rmse = evaluator.calculate_rmse(y_true, y_pred)

        assert rmse > 0
        assert rmse > evaluator.calculate_mae(y_true, y_pred)  # RMSE >= MAE

    def test_calculate_mape(self, evaluator):
        """Test calcul MAPE"""
        y_true = np.array([100, 110, 105, 115])
        y_pred = np.array([98, 112, 107, 113])

        mape = evaluator.calculate_mape(y_true, y_pred)

        assert mape > 0
        assert mape < 100  # Devrait être raisonnable

    def test_direction_accuracy(self, evaluator):
        """Test calcul direction accuracy"""
        # Séquence montante: [100, 110, 115, 120]
        y_true = np.array([100, 110, 115, 120])
        # Prédictions avec mêmes directions
        y_pred = np.array([98, 108, 113, 118])

        accuracy = evaluator.calculate_direction_accuracy(y_true, y_pred)

        assert 0 <= accuracy <= 1
        assert accuracy == 1.0  # Toutes les directions correctes

    def test_evaluate_model(self, evaluator):
        """Test évaluation complète"""
        y_true = np.random.rand(100) * 100 + 100
        y_pred = y_true + np.random.randn(100) * 2

        metrics = evaluator.evaluate_model(y_true, y_pred)

        # Vérifier présence des métriques
        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 'mape' in metrics
        assert 'direction_accuracy' in metrics


# ==========================================
# TESTS PRICE PREDICTOR
# ==========================================

class TestPricePredictor:
    """Tests pour le prédicteur principal"""

    @pytest.mark.slow
    def test_train_lstm(self):
        """Test entraînement LSTM (lent)"""
        predictor = PricePredictor(model_type='lstm')

        # Entraînement sur données réelles (rapide)
        result = predictor.train(
            ticker="MC.PA",
            period="6mo",
            test_size=0.2,
            epochs=5,  # Peu d'époques pour test rapide
            verbose=0
        )

        assert result['ticker'] == "MC.PA"
        assert 'evaluation' in result
        assert result['evaluation']['mae'] > 0

    def test_predictor_initialization(self):
        """Test initialisation du prédicteur"""
        predictor = PricePredictor(model_type='ensemble')

        assert predictor.model_type == 'ensemble'
        assert predictor.data_loader is not None
        assert predictor.feature_engineer is not None
        assert predictor.evaluator is not None

    def test_invalid_model_type(self):
        """Test type de modèle invalide"""
        predictor = PricePredictor(model_type='invalid')

        with pytest.raises(ValueError):
            predictor.train("MC.PA", period="1mo")


# ==========================================
# TESTS D'INTÉGRATION
# ==========================================

class TestIntegration:
    """Tests d'intégration du pipeline complet"""

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_pipeline(self):
        """Test du pipeline complet: train -> predict -> evaluate"""
        predictor = PricePredictor(model_type='ensemble')

        # 1. Entraînement
        train_result = predictor.train(
            ticker="MC.PA",
            period="1y",
            epochs=10,
            verbose=0
        )

        assert train_result['success'] or 'evaluation' in train_result

        # 2. Prédiction
        predictions = predictor.predict(
            ticker="MC.PA",
            horizon=7
        )

        assert 'predictions' in predictions
        assert len(predictions['predictions']) == 7
        assert 'recommendation' in predictions

        # 3. Évaluation
        eval_metrics = predictor.evaluate(
            ticker="MC.PA",
            test_size=0.2,
            generate_report=False
        )

        assert 'mae' in eval_metrics
        assert eval_metrics['mae'] > 0


# ==========================================
# TESTS DE ROBUSTESSE
# ==========================================

class TestRobustness:
    """Tests de robustesse et cas limites"""

    def test_empty_data(self, feature_engineer):
        """Test avec données vides"""
        df = pd.DataFrame()

        with pytest.raises((ValueError, KeyError)):
            feature_engineer.calculate_all_features(df)

    def test_insufficient_data(self, data_loader):
        """Test avec trop peu de données"""
        with pytest.raises(ValueError):
            # 1 jour de données seulement
            data_loader.load_data("MC.PA", start_date="2024-01-01", end_date="2024-01-01")

    def test_zero_prices(self, evaluator):
        """Test MAPE avec prix à zéro"""
        y_true = np.array([0, 10, 20])
        y_pred = np.array([5, 15, 25])

        mape = evaluator.calculate_mape(y_true, y_pred)

        # Devrait gérer le cas sans erreur
        assert not np.isnan(mape)


# ==========================================
# CONFIGURATION PYTEST
# ==========================================

def pytest_configure(config):
    """Configuration des markers pytest"""
    config.addinivalue_line(
        "markers", "slow: marque les tests lents (> 30s)"
    )
    config.addinivalue_line(
        "markers", "integration: marque les tests d'intégration"
    )


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v", "-m", "not slow"])
