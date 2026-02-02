"""
Service de gestion de portefeuille avec intégration IA
"""

from database.portfolio_db import PortfolioDatabase
from services.yahoo_finance_service import YahooFinanceService
from typing import Dict, List


class PortfolioManager:
    """Gestionnaire de portefeuille intelligent"""

    def __init__(self):
        self.db = PortfolioDatabase()
        self.yf = YahooFinanceService()

    def get_portfolio_context_for_ai(self, user_id: str = "default_user") -> str:
        """
        Génère un contexte textuel du portefeuille pour l'IA

        Returns:
            String formaté avec toutes les infos du portefeuille
        """
        # Mise à jour des prix
        self.db.update_current_prices(user_id)

        summary = self.db.get_portfolio_summary(user_id)

        context = f"""
PORTEFEUILLE ACTUEL DE L'UTILISATEUR:

💰 Valeur totale: {summary['total_value']:,.2f} €
📊 Montant investi: {summary['total_invested']:,.2f} €
{"📈" if summary['total_gain_loss'] >= 0 else "📉"} Plus/Moins-value: {summary['total_gain_loss']:,.2f} € ({summary['total_gain_loss_percent']:+.2f}%)

📍 POSITIONS ({summary['total_positions']} entreprises):
"""

        for pos in summary['positions']:
            context += f"""
🏢 {pos['company_name']} ({pos['ticker']}):
   • Quantité: {pos['quantity']} actions
   • PRU (Prix de Revient Unitaire): {pos['avg_price']:.2f} €
   • Prix actuel: {pos['current_price']:.2f} €
   • Valeur: {pos['current_value']:,.2f} €
   • Performance: {"🟢" if pos['gain_loss_percent'] >= 0 else "🔴"} {pos['gain_loss_percent']:+.2f}%
   • Poids: {(pos['current_value'] / summary['total_value'] * 100):.1f}% du portefeuille
"""

        # Ajouter les statistiques
        if summary['positions']:
            best_performer = max(summary['positions'], key=lambda x: x['gain_loss_percent'] or 0)
            worst_performer = min(summary['positions'], key=lambda x: x['gain_loss_percent'] or 0)

            context += f"""

📊 STATISTIQUES:
   🥇 Meilleure performance: {best_performer['company_name']} ({best_performer['gain_loss_percent']:+.2f}%)
   🥉 Moins bonne performance: {worst_performer['company_name']} ({worst_performer['gain_loss_percent']:+.2f}%)
   🎯 Performance moyenne du portefeuille: {summary['total_gain_loss_percent']:+.2f}%
"""

        return context

    def should_rebalance(self, user_id: str = "default_user") -> Dict:
        """
        Analyse si le portefeuille nécessite un rééquilibrage

        Returns:
            Dict avec recommandations de rebalancing
        """
        self.db.update_current_prices(user_id)
        summary = self.db.get_portfolio_summary(user_id)
        positions = summary['positions']
        total_value = summary['total_value']

        # Calculer les poids actuels
        for pos in positions:
            pos['weight'] = (pos['current_value'] / total_value * 100) if total_value > 0 else 0

        # Détecter les déséquilibres
        recommendations = []

        for pos in positions:
            if pos['weight'] > 25:  # > 25% sur une position
                recommendations.append({
                    "action": "REDUCE",
                    "ticker": pos['ticker'],
                    "company": pos['company_name'],
                    "current_weight": pos['weight'],
                    "target_weight": 20,  # Ramener à 20%
                    "reason": "Concentration excessive (>25%)",
                    "urgency": "HIGH" if pos['weight'] > 30 else "MEDIUM"
                })
            elif pos['weight'] < 5 and len(positions) < 15:  # < 5% et peu de positions
                recommendations.append({
                    "action": "INCREASE",
                    "ticker": pos['ticker'],
                    "company": pos['company_name'],
                    "current_weight": pos['weight'],
                    "target_weight": 8,  # Ramener à 8%
                    "reason": "Position trop faible, peut être renforcée",
                    "urgency": "LOW"
                })

        # Détecter si trop peu de diversification
        if len(positions) < 5:
            recommendations.append({
                "action": "DIVERSIFY",
                "reason": f"Portefeuille peu diversifié ({len(positions)} positions). Recommandation: 6-10 positions minimum",
                "urgency": "HIGH"
            })

        return {
            "needs_rebalance": len(recommendations) > 0,
            "portfolio_size": len(positions),
            "total_value": total_value,
            "recommendations": recommendations
        }

    def get_portfolio_health_score(self, user_id: str = "default_user") -> Dict:
        """
        Calcule un score de santé du portefeuille (0-100)

        Returns:
            Dict avec le score et les détails
        """
        self.db.update_current_prices(user_id)
        summary = self.db.get_portfolio_summary(user_id)
        positions = summary['positions']

        if not positions:
            return {
                "score": 0,
                "grade": "N/A",
                "details": "Aucune position dans le portefeuille"
            }

        score = 100
        issues = []

        # 1. Diversification (30 points max)
        num_positions = len(positions)
        if num_positions < 3:
            score -= 30
            issues.append("Diversification insuffisante (< 3 positions)")
        elif num_positions < 5:
            score -= 15
            issues.append("Diversification faible (< 5 positions)")
        elif num_positions > 20:
            score -= 10
            issues.append("Trop de positions (> 20), difficile à gérer")

        # 2. Concentration (25 points max)
        for pos in positions:
            weight = (pos['current_value'] / summary['total_value'] * 100)
            if weight > 30:
                score -= 25
                issues.append(f"Concentration excessive sur {pos['company_name']} ({weight:.1f}%)")
                break
            elif weight > 25:
                score -= 15
                issues.append(f"Forte concentration sur {pos['company_name']} ({weight:.1f}%)")

        # 3. Performance globale (25 points max)
        perf = summary['total_gain_loss_percent']
        if perf < -20:
            score -= 25
            issues.append(f"Performance très négative ({perf:.1f}%)")
        elif perf < -10:
            score -= 15
            issues.append(f"Performance négative ({perf:.1f}%)")
        elif perf < 0:
            score -= 5

        # 4. Positions en perte (20 points max)
        losing_positions = [p for p in positions if (p['gain_loss_percent'] or 0) < -15]
        if len(losing_positions) >= len(positions) / 2:
            score -= 20
            issues.append(f"Majorité des positions en perte ({len(losing_positions)}/{len(positions)})")
        elif losing_positions:
            score -= 10

        # Déterminer le grade
        if score >= 90:
            grade = "A+ (Excellent)"
        elif score >= 80:
            grade = "A (Très Bien)"
        elif score >= 70:
            grade = "B (Bien)"
        elif score >= 60:
            grade = "C (Moyen)"
        elif score >= 50:
            grade = "D (Faible)"
        else:
            grade = "F (Mauvais)"

        return {
            "score": score,
            "grade": grade,
            "total_positions": num_positions,
            "total_value": summary['total_value'],
            "performance": summary['total_gain_loss_percent'],
            "issues": issues if issues else ["Aucun problème majeur détecté"],
            "recommendations": self._get_health_recommendations(score, issues)
        }

    def _get_health_recommendations(self, score: int, issues: List[str]) -> List[str]:
        """Génère des recommandations basées sur le score de santé"""
        recommendations = []

        if score < 70:
            if any("Diversification" in issue for issue in issues):
                recommendations.append("➕ Ajouter 2-3 nouvelles positions de qualité pour diversifier")

            if any("Concentration" in issue for issue in issues):
                recommendations.append("⚖️ Réduire les positions > 25% et redistribuer sur d'autres valeurs")

            if any("Performance" in issue for issue in issues):
                recommendations.append("🔍 Analyser les positions en forte perte et décider: renforcer ou couper?")

            if any("perte" in issue for issue in issues):
                recommendations.append("📉 Définir des stop-loss stricts sur les positions les plus faibles")

        if not recommendations:
            recommendations.append("✅ Portefeuille en bonne santé, continuer le suivi régulier")

        return recommendations

    def get_position_details(self, ticker: str, user_id: str = "default_user") -> Dict:
        """
        Récupère tous les détails d'une position (portfolio + Yahoo Finance)

        Returns:
            Dict complet avec données du portefeuille + marché
        """
        # Données du portefeuille
        positions = self.db.get_portfolio(user_id)
        position = next((p for p in positions if p['ticker'] == ticker), None)

        if not position:
            return {"error": f"Position {ticker} non trouvée"}

        # Données de marché
        market_data = self.yf.get_stock_info(ticker)

        # Historique des transactions
        transactions = self.db.get_transactions(ticker, user_id, limit=10)

        # Analyses passées
        analyses = self.db.get_analysis_history(ticker, user_id, limit=5)

        return {
            "position": position,
            "market_data": market_data,
            "transactions": transactions,
            "past_analyses": analyses
        }
