"""
Endpoints API FastAPI pour le système ML de prédiction de prix

Fournit les routes REST pour entraîner, prédire et gérer les modèles.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import logging

from .price_predictor import PricePredictor

logger = logging.getLogger(__name__)

# Créer le router
ml_router = APIRouter(prefix="/ml", tags=["Machine Learning"])

# Cache des prédicteurs (un par type de modèle)
_predictors = {
    'lstm': PricePredictor(model_type='lstm'),
    'prophet': PricePredictor(model_type='prophet'),
    'ensemble': PricePredictor(model_type='ensemble'),
}


# ==========================================
# MODELS PYDANTIC
# ==========================================

class TrainRequest(BaseModel):
    """Requête d'entraînement"""
    ticker: str = Field(..., description="Symbole boursier (ex: MC.PA)")
    start_date: Optional[str] = Field(None, description="Date début YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="Date fin YYYY-MM-DD")
    period: str = Field("2y", description="Période (1y, 2y, 5y, max)")
    test_size: float = Field(0.2, ge=0.1, le=0.4, description="Taille du test set")
    epochs: int = Field(100, ge=10, le=500, description="Nombre d'époques (LSTM)")
    model_type: str = Field("ensemble", description="Type: lstm, prophet, ensemble")
    save_model: bool = Field(True, description="Sauvegarder après entraînement")


class TrainResponse(BaseModel):
    """Réponse d'entraînement"""
    success: bool
    ticker: str
    model_type: str
    trained_at: str
    training_metrics: Dict
    message: str


class PredictRequest(BaseModel):
    """Requête de prédiction"""
    ticker: str = Field(..., description="Symbole boursier")
    horizon: int = Field(30, ge=1, le=90, description="Jours à prédire")
    model_type: str = Field("ensemble", description="Type de modèle")
    return_confidence: bool = Field(True, description="Inclure intervalles")


class PredictionResponse(BaseModel):
    """Réponse de prédiction"""
    ticker: str
    current_price: float
    predictions: List[Dict]
    trend: str
    price_change_pct: float
    confidence_avg: float
    recommendation: str
    model_used: str
    trained_on: Dict
    metrics: Dict


class EvaluateRequest(BaseModel):
    """Requête d'évaluation"""
    ticker: str
    model_type: str = Field("ensemble", description="Type de modèle")
    test_size: float = Field(0.2, ge=0.1, le=0.5)
    generate_report: bool = Field(True)


class ModelInfo(BaseModel):
    """Informations sur un modèle"""
    ticker: str
    version: str
    model_type: str
    trained_at: Optional[str]
    path: str
    metrics: Dict


# ==========================================
# ENDPOINTS
# ==========================================

@ml_router.post("/train/{ticker}", response_model=TrainResponse)
async def train_model(
    ticker: str,
    request: TrainRequest,
    background_tasks: BackgroundTasks
):
    """
    Entraîne un modèle de prédiction de prix

    **Processus**:
    1. Charge les données historiques depuis Yahoo Finance
    2. Calcule les indicateurs techniques (RSI, MACD, etc.)
    3. Entraîne le modèle sélectionné (LSTM/Prophet/Ensemble)
    4. Évalue sur test set
    5. Sauvegarde le modèle

    **Temps d'exécution**: 2-5 minutes selon le modèle

    **Exemple**:
    ```json
    {
      "ticker": "MC.PA",
      "model_type": "ensemble",
      "period": "2y",
      "epochs": 50
    }
    ```
    """
    try:
        logger.info(f"Début entraînement {request.model_type} pour {ticker}")

        # Récupérer le prédicteur
        if request.model_type not in _predictors:
            raise HTTPException(
                status_code=400,
                detail=f"Type de modèle invalide. Utilisez: {list(_predictors.keys())}"
            )

        predictor = _predictors[request.model_type]

        # Entraîner
        training_metrics = predictor.train(
            ticker=ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            period=request.period,
            test_size=request.test_size,
            epochs=request.epochs,
            verbose=0
        )

        # Sauvegarder si demandé
        if request.save_model:
            predictor.save_model(ticker, version="v1")

        return TrainResponse(
            success=True,
            ticker=ticker,
            model_type=request.model_type,
            trained_at=training_metrics['trained_at'],
            training_metrics=training_metrics,
            message=f"Modèle {request.model_type} entraîné avec succès pour {ticker}"
        )

    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/predict/{ticker}", response_model=PredictionResponse)
async def predict_price(
    ticker: str,
    horizon: int = 30,
    model_type: str = "ensemble",
    return_confidence: bool = True
):
    """
    Prédit les prix futurs d'une action

    **Sorties**:
    - Prédictions jour par jour
    - Tendance (BULLISH/BEARISH/NEUTRAL)
    - Recommandation (BUY/SELL/HOLD)
    - Intervalles de confiance
    - Métriques de qualité du modèle

    **Performance**: < 2 secondes

    **Exemple**:
    ```
    GET /ml/predict/MC.PA?horizon=30&model_type=ensemble
    ```
    """
    try:
        logger.info(f"Prédiction {model_type} pour {ticker} ({horizon} jours)")

        # Récupérer le prédicteur
        if model_type not in _predictors:
            raise HTTPException(
                status_code=400,
                detail=f"Type de modèle invalide. Utilisez: {list(_predictors.keys())}"
            )

        predictor = _predictors[model_type]

        # Prédire
        result = predictor.predict(
            ticker=ticker,
            horizon=horizon,
            return_confidence=return_confidence
        )

        return PredictionResponse(**result)

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Modèle non trouvé pour {ticker}. Entraînez d'abord avec POST /ml/train/{ticker}"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/evaluate/{ticker}")
async def evaluate_model(
    ticker: str,
    model_type: str = "ensemble",
    test_size: float = 0.2,
    generate_report: bool = True
):
    """
    Évalue la performance d'un modèle

    **Métriques**:
    - MAE (Mean Absolute Error)
    - RMSE (Root Mean Squared Error)
    - MAPE (Mean Absolute Percentage Error)
    - Direction Accuracy
    - Sharpe Ratio

    **Retourne** un rapport détaillé avec interprétation
    """
    try:
        predictor = _predictors.get(model_type)
        if not predictor:
            raise HTTPException(status_code=400, detail="Type de modèle invalide")

        metrics = predictor.evaluate(
            ticker=ticker,
            test_size=test_size,
            generate_report=generate_report
        )

        return {
            "ticker": ticker,
            "model_type": model_type,
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/models", response_model=List[ModelInfo])
async def list_models():
    """
    Liste tous les modèles entraînés disponibles

    **Retourne** une liste de tous les modèles sauvegardés avec:
    - Ticker
    - Type de modèle
    - Date d'entraînement
    - Métriques de performance
    """
    try:
        # Utiliser n'importe quel prédicteur pour lister (ils partagent le même model_dir)
        predictor = _predictors['ensemble']
        models = predictor.list_available_models()

        return [ModelInfo(**m) for m in models]

    except Exception as e:
        logger.error(f"Erreur lors du listage des modèles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.delete("/models/{ticker}")
async def delete_model(
    ticker: str,
    version: str = "v1",
    model_type: str = "ensemble"
):
    """
    Supprime un modèle sauvegardé

    **Attention**: Cette action est irréversible
    """
    try:
        predictor = _predictors.get(model_type)
        if not predictor:
            raise HTTPException(status_code=400, detail="Type de modèle invalide")

        success = predictor.delete_model(ticker, version)

        if success:
            return {
                "message": f"Modèle {ticker} ({model_type} {version}) supprimé avec succès"
            }
        else:
            raise HTTPException(status_code=404, detail="Modèle non trouvé")

    except Exception as e:
        logger.error(f"Erreur lors de la suppression: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/models/{ticker}/info")
async def get_model_info(
    ticker: str,
    model_type: str = "ensemble"
):
    """
    Récupère les informations détaillées d'un modèle

    **Inclut**:
    - Métriques d'entraînement
    - Date d'entraînement
    - Configuration du modèle
    - Performance historique
    """
    try:
        predictor = _predictors.get(model_type)
        if not predictor:
            raise HTTPException(status_code=400, detail="Type de modèle invalide")

        # Charger le modèle
        predictor.load_model(ticker, version="v1")

        return {
            "ticker": ticker,
            "model_type": model_type,
            "trained_at": predictor.trained_at,
            "training_metrics": predictor.training_metrics
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Modèle non trouvé pour {ticker}")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.post("/retrain/{ticker}")
async def retrain_model(
    ticker: str,
    model_type: str = "ensemble",
    background_tasks: BackgroundTasks = None
):
    """
    Re-entraîne un modèle existant avec les données les plus récentes

    **Usage**: À exécuter hebdomadairement pour maintenir la performance

    **Process**: Entraînement en arrière-plan (non-bloquant)
    """
    try:
        predictor = _predictors.get(model_type)
        if not predictor:
            raise HTTPException(status_code=400, detail="Type de modèle invalide")

        # Lancer en background
        def retrain_task():
            try:
                logger.info(f"Re-entraînement en arrière-plan: {ticker}")
                predictor.train(ticker, period="2y", epochs=50, verbose=0)
                predictor.save_model(ticker, version="v1")
                logger.info(f"Re-entraînement terminé: {ticker}")
            except Exception as e:
                logger.error(f"Erreur re-entraînement: {e}")

        if background_tasks:
            background_tasks.add_task(retrain_task)

        return {
            "message": f"Re-entraînement de {ticker} lancé en arrière-plan",
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Erreur lors du lancement du re-entraînement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@ml_router.get("/status")
async def get_ml_status():
    """
    Vérifie le statut du système ML

    **Retourne**:
    - Modèles disponibles
    - Mémoire utilisée
    - Version TensorFlow
    """
    import tensorflow as tf

    return {
        "status": "operational",
        "models_loaded": list(_predictors.keys()),
        "tensorflow_version": tf.__version__,
        "gpu_available": len(tf.config.list_physical_devices('GPU')) > 0
    }


# Fonction pour intégrer dans main.py
def setup_ml_routes(app):
    """
    Intègre les routes ML dans l'application FastAPI

    Usage dans main.py:
        from ml.serving import setup_ml_routes
        setup_ml_routes(app)
    """
    app.include_router(ml_router)
    logger.info("Routes ML configurées")
