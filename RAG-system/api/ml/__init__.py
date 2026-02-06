"""
Module de prédiction de prix d'actions avec Machine Learning

Ce module fournit des capacités avancées de prédiction de prix pour le système RAG-PEA,
incluant LSTM, Prophet, et des modèles ensemble pour des prédictions robustes.
"""

from .price_predictor import PricePredictor
from .data_loader import DataLoader
from .feature_engineering import FeatureEngineer

__version__ = "1.0.0"
__all__ = ["PricePredictor", "DataLoader", "FeatureEngineer"]
