"""
Évaluation des modèles de prédiction

Calcule les métriques standard (MAE, RMSE, MAPE, Direction Accuracy)
et fournit des rapports détaillés de performance.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Évaluateur de modèles de prédiction de prix

    Calcule diverses métriques pour évaluer la qualité des prédictions.
    """

    def __init__(self):
        """Initialise l'évaluateur"""
        pass

    def calculate_mae(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate Mean Absolute Error

        MAE = moyenne(|y_true - y_pred|)

        Args:
            y_true: Valeurs réelles
            y_pred: Valeurs prédites

        Returns:
            MAE (plus bas = meilleur)
        """
        return float(np.mean(np.abs(y_true - y_pred)))

    def calculate_rmse(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate Root Mean Squared Error

        RMSE = sqrt(moyenne((y_true - y_pred)^2))

        Args:
            y_true: Valeurs réelles
            y_pred: Valeurs prédites

        Returns:
            RMSE (plus bas = meilleur)
        """
        return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    def calculate_mape(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate Mean Absolute Percentage Error

        MAPE = 100 * moyenne(|y_true - y_pred| / |y_true|)

        Args:
            y_true: Valeurs réelles
            y_pred: Valeurs prédites

        Returns:
            MAPE en % (plus bas = meilleur)
        """
        # Éviter division par zéro
        mask = y_true != 0
        if not mask.any():
            return float('inf')

        return float(100 * np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))

    def calculate_direction_accuracy(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> float:
        """
        Calculate Direction Accuracy

        Mesure le % de fois où le modèle prédit correctement la direction
        (hausse ou baisse) par rapport au jour précédent.

        Args:
            y_true: Valeurs réelles
            y_pred: Valeurs prédites

        Returns:
            Direction accuracy entre 0 et 1 (plus haut = meilleur)
        """
        if len(y_true) < 2:
            return 0.0

        # Calculer les directions (1 = hausse, 0 = baisse)
        true_direction = np.diff(y_true) > 0
        pred_direction = np.diff(y_pred) > 0

        # Comparer
        correct = true_direction == pred_direction
        accuracy = float(np.mean(correct))

        return accuracy

    def calculate_sharpe_ratio(
        self,
        returns: np.ndarray,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe Ratio sur les prédictions

        Sharpe = (moyenne(returns) - risk_free_rate) / std(returns)

        Args:
            returns: Retours basés sur les prédictions
            risk_free_rate: Taux sans risque annuel (0.02 = 2%)

        Returns:
            Sharpe Ratio (plus haut = meilleur)
        """
        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        # Ajuster le risk-free rate pour la période (journalier)
        daily_rf = risk_free_rate / 252  # 252 jours de trading par an

        excess_returns = returns - daily_rf
        sharpe = float(excess_returns.mean() / returns.std())

        # Annualiser
        sharpe_annual = sharpe * np.sqrt(252)

        return sharpe_annual

    def calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """
        Calculate Maximum Drawdown

        Mesure la plus grande perte depuis un pic.

        Args:
            prices: Série de prix

        Returns:
            Max drawdown en % (négatif)
        """
        if len(prices) == 0:
            return 0.0

        # Calculer les peaks cumulés
        cummax = np.maximum.accumulate(prices)

        # Drawdown à chaque point
        drawdown = (prices - cummax) / cummax

        # Max drawdown
        max_dd = float(drawdown.min())

        return max_dd * 100  # En pourcentage

    def evaluate_model(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        prices: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Évaluation complète d'un modèle

        Args:
            y_true: Valeurs réelles
            y_pred: Valeurs prédites
            prices: Prix historiques (pour Sharpe et drawdown)

        Returns:
            Dictionnaire avec toutes les métriques
        """
        metrics = {
            'mae': self.calculate_mae(y_true, y_pred),
            'rmse': self.calculate_rmse(y_true, y_pred),
            'mape': self.calculate_mape(y_true, y_pred),
            'direction_accuracy': self.calculate_direction_accuracy(y_true, y_pred),
        }

        # Métriques additionnelles si prix disponibles
        if prices is not None and len(prices) > 1:
            returns = np.diff(prices) / prices[:-1]
            metrics['sharpe_ratio'] = self.calculate_sharpe_ratio(returns)
            metrics['max_drawdown'] = self.calculate_max_drawdown(prices)

        # Statistiques supplémentaires
        errors = y_true - y_pred
        metrics['mean_error'] = float(np.mean(errors))
        metrics['std_error'] = float(np.std(errors))
        metrics['median_error'] = float(np.median(errors))

        logger.info(f"Évaluation terminée - MAE: {metrics['mae']:.2f}, "
                   f"RMSE: {metrics['rmse']:.2f}, MAPE: {metrics['mape']:.2f}%")

        return metrics

    def compare_models(
        self,
        y_true: np.ndarray,
        predictions: Dict[str, np.ndarray]
    ) -> pd.DataFrame:
        """
        Compare plusieurs modèles

        Args:
            y_true: Valeurs réelles
            predictions: {nom_modèle: array_predictions}

        Returns:
            DataFrame avec comparaison des métriques
        """
        results = []

        for model_name, y_pred in predictions.items():
            metrics = self.evaluate_model(y_true, y_pred)
            metrics['model'] = model_name
            results.append(metrics)

        df = pd.DataFrame(results)
        df = df.set_index('model')

        # Trier par MAE (meilleur en premier)
        df = df.sort_values('mae')

        logger.info(f"Comparaison de {len(predictions)} modèles terminée")
        return df

    def get_confidence_intervals(
        self,
        y_pred: np.ndarray,
        confidence: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcule les intervalles de confiance autour des prédictions

        Méthode simple: suppose une distribution normale des erreurs

        Args:
            y_pred: Prédictions
            confidence: Niveau de confiance (0.95 = 95%)

        Returns:
            Tuple (lower_bound, upper_bound)
        """
        # Z-score pour le niveau de confiance
        from scipy import stats
        z_score = stats.norm.ppf((1 + confidence) / 2)

        # Estimer l'erreur standard (simplifié)
        # En production, utiliser l'historique des erreurs du modèle
        std_error = np.std(y_pred) * 0.1  # Assumer 10% de variation

        lower = y_pred - z_score * std_error
        upper = y_pred + z_score * std_error

        return lower, upper

    def calculate_trading_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        trading_cost: float = 0.001
    ) -> Dict:
        """
        Calcule des métriques de trading basées sur les prédictions

        Simule une stratégie: acheter si prédiction hausse, vendre sinon

        Args:
            y_true: Prix réels
            y_pred: Prix prédits
            trading_cost: Coût de transaction (0.001 = 0.1%)

        Returns:
            Dictionnaire avec métriques de trading
        """
        if len(y_true) < 2 or len(y_pred) < 2:
            return {}

        # Signaux de trading basés sur les prédictions
        pred_returns = np.diff(y_pred) / y_pred[:-1]
        signals = (pred_returns > 0).astype(int)  # 1 = long, 0 = cash

        # Retours réels
        true_returns = np.diff(y_true) / y_true[:-1]

        # Calculer les retours de la stratégie
        strategy_returns = signals * true_returns

        # Appliquer les coûts de transaction
        trades = np.diff(np.concatenate([[0], signals]))  # Détection des trades
        n_trades = np.sum(np.abs(trades))
        total_costs = n_trades * trading_cost

        # Performance
        cumulative_return = float(np.sum(strategy_returns) - total_costs)
        annualized_return = cumulative_return * 252 / len(strategy_returns)

        # Win rate
        winning_trades = strategy_returns > 0
        win_rate = float(np.mean(winning_trades)) if len(winning_trades) > 0 else 0.0

        return {
            'cumulative_return': cumulative_return,
            'annualized_return': annualized_return,
            'n_trades': int(n_trades),
            'win_rate': win_rate,
            'sharpe_ratio': self.calculate_sharpe_ratio(strategy_returns),
            'total_trading_costs': total_costs,
        }

    def generate_evaluation_report(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str = "Model",
        save_path: Optional[str] = None
    ) -> str:
        """
        Génère un rapport d'évaluation détaillé

        Args:
            y_true: Valeurs réelles
            y_pred: Valeurs prédites
            model_name: Nom du modèle
            save_path: Chemin pour sauvegarder le rapport (optionnel)

        Returns:
            Rapport en format texte
        """
        metrics = self.evaluate_model(y_true, y_pred, y_true)
        trading_metrics = self.calculate_trading_metrics(y_true, y_pred)

        report = f"""
========================================
RAPPORT D'ÉVALUATION - {model_name}
========================================

MÉTRIQUES DE PRÉDICTION
------------------------
MAE (Mean Absolute Error):        {metrics['mae']:.4f}
RMSE (Root Mean Squared Error):   {metrics['rmse']:.4f}
MAPE (Mean Abs. Pct Error):       {metrics['mape']:.2f}%
Direction Accuracy:                {metrics['direction_accuracy']:.2%}

STATISTIQUES D'ERREUR
---------------------
Erreur moyenne:                    {metrics['mean_error']:.4f}
Écart-type erreur:                 {metrics['std_error']:.4f}
Erreur médiane:                    {metrics['median_error']:.4f}

MÉTRIQUES DE RISQUE
-------------------
Sharpe Ratio:                      {metrics.get('sharpe_ratio', 0):.4f}
Max Drawdown:                      {metrics.get('max_drawdown', 0):.2f}%

MÉTRIQUES DE TRADING
--------------------
Retour cumulé:                     {trading_metrics.get('cumulative_return', 0):.2%}
Retour annualisé:                  {trading_metrics.get('annualized_return', 0):.2%}
Nombre de trades:                  {trading_metrics.get('n_trades', 0)}
Win rate:                          {trading_metrics.get('win_rate', 0):.2%}
Coûts de transaction:              {trading_metrics.get('total_trading_costs', 0):.4f}

INTERPRÉTATION
--------------
Direction Accuracy > 60%:          {"✓ Excellent" if metrics['direction_accuracy'] > 0.6 else "✗ À améliorer"}
MAPE < 5%:                         {"✓ Excellent" if metrics['mape'] < 5 else "✗ À améliorer"}
Sharpe Ratio > 1:                  {"✓ Bon" if metrics.get('sharpe_ratio', 0) > 1 else "✗ Faible"}

========================================
"""

        if save_path:
            with open(save_path, 'w') as f:
                f.write(report)
            logger.info(f"Rapport sauvegardé dans {save_path}")

        return report
