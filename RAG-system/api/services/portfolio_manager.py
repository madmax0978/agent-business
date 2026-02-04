"""
Service de gestion de portefeuille avec intégration IA
"""

from database.portfolio_db import PortfolioDatabase
from services.yahoo_finance_service import YahooFinanceService
from typing import Dict, List, Optional
from datetime import datetime


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
        treasury = summary.get('pea_treasury', {})

        # Calculer les ratios
        cash_ratio = summary.get('cash_ratio', 0)
        investment_ratio = summary.get('investment_ratio', 0)
        pea_total_value = treasury.get('pea_total_value', 0)
        cash_available = treasury.get('cash_available', 0)

        context = f"""
PORTEFEUILLE PEA DE L'UTILISATEUR:

💰 TRÉSORERIE PEA:
   • Valeur totale PEA: {pea_total_value:,.2f} €
   • Total déposé: {treasury.get('total_deposits', 0):,.2f} €
   • Cash disponible: {cash_available:,.2f} € ({cash_ratio:.1f}%)
   • Cash investi: {treasury.get('cash_invested', 0):,.2f} € ({investment_ratio:.1f}%)
   • Performance globale PEA: {"📈" if treasury.get('pea_gain_loss', 0) >= 0 else "📉"} {treasury.get('pea_gain_loss', 0):,.2f} € ({treasury.get('pea_gain_loss_percent', 0):+.2f}%)
   • Date d'ouverture: {treasury.get('pea_opening_date', 'N/A')}
   • Dernier dépôt: {treasury.get('last_deposit_date', 'N/A')}

📊 POSITIONS EN PORTEFEUILLE:
   • Valeur positions: {summary['total_value']:,.2f} €
   • Montant investi: {summary['total_invested']:,.2f} €
   • Plus/Moins-value positions: {"📈" if summary['total_gain_loss'] >= 0 else "📉"} {summary['total_gain_loss']:,.2f} € ({summary['total_gain_loss_percent']:+.2f}%)
   • Nombre de positions: {summary['total_positions']} entreprises

📍 DÉTAIL DES POSITIONS:
"""

        for pos in summary['positions']:
            # Gérer les valeurs None
            avg_price = pos['avg_price'] or 0
            current_price = pos['current_price'] or 0
            current_value = pos['current_value'] or 0
            gain_loss_percent = pos['gain_loss_percent'] or 0
            weight = (current_value / summary['total_value'] * 100) if summary['total_value'] > 0 else 0

            context += f"""
🏢 {pos['company_name']} ({pos['ticker']}):
   • Quantité: {pos['quantity']} actions
   • PRU (Prix de Revient Unitaire): {avg_price:.2f} €
   • Prix actuel: {current_price:.2f} €
   • Valeur: {current_value:,.2f} €
   • Performance: {"🟢" if gain_loss_percent >= 0 else "🔴"} {gain_loss_percent:+.2f}%
   • Poids: {weight:.1f}% du portefeuille
"""

        # Ajouter les statistiques
        if summary['positions']:
            best_performer = max(summary['positions'], key=lambda x: x['gain_loss_percent'] or 0)
            worst_performer = min(summary['positions'], key=lambda x: x['gain_loss_percent'] or 0)

            # Gérer les valeurs None
            best_perf_pct = best_performer['gain_loss_percent'] or 0
            worst_perf_pct = worst_performer['gain_loss_percent'] or 0

            context += f"""

📊 STATISTIQUES:
   🥇 Meilleure performance: {best_performer['company_name']} ({best_perf_pct:+.2f}%)
   🥉 Moins bonne performance: {worst_performer['company_name']} ({worst_perf_pct:+.2f}%)
   🎯 Performance moyenne du portefeuille: {summary['total_gain_loss_percent']:+.2f}%
"""

        # Ajouter les opportunités d'investissement si cash disponible
        if cash_available > 100:
            opportunities = self.analyze_cash_opportunities(user_id)
            if opportunities.get('has_opportunities'):
                context += f"""

💡 OPPORTUNITÉS D'INVESTISSEMENT DÉTECTÉES:
   • Cash disponible pour investir: {cash_available:,.2f} €
"""
                for opp in opportunities.get('opportunities', []):
                    context += f"""
   • {opp['type']}: {opp['description']}
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

    def analyze_cash_opportunities(self, user_id: str = "default_user") -> Dict:
        """
        Analyse les opportunités d'investissement basées sur le cash disponible

        Returns:
            Dict avec has_opportunities, cash_available, opportunities[]
        """
        treasury = self.db.get_treasury_status(user_id)
        summary = self.db.get_portfolio_summary(user_id)

        cash_available = treasury.get('cash_available', 0)
        positions = summary.get('positions', [])
        total_value = summary.get('total_value', 0)
        pea_total_value = summary.get('pea_treasury', {}).get('pea_total_value', 0)
        cash_ratio = summary.get('cash_ratio', 0)

        # Seuil minimum pour déclencher des opportunités
        MIN_CASH_THRESHOLD = 100

        if cash_available < MIN_CASH_THRESHOLD:
            return {
                "has_opportunities": False,
                "cash_available": cash_available,
                "reason": f"Cash disponible ({cash_available:.2f}€) inférieur au seuil minimum ({MIN_CASH_THRESHOLD}€)",
                "opportunities": []
            }

        opportunities = []

        # 1. Vérifier la diversification (< 5 positions)
        if len(positions) < 5:
            opportunities.append({
                "type": "DIVERSIFY",
                "priority": "HIGH",
                "description": f"Portefeuille peu diversifié ({len(positions)} positions). Recommandation: ajouter 2-3 nouvelles positions de qualité.",
                "suggested_amount": min(cash_available * 0.3, 1000),  # Max 30% du cash ou 1000€
                "reasoning": "Diversification insuffisante augmente le risque du portefeuille"
            })

        # 2. Renforcer les positions gagnantes (< 20% poids et performance > 5%)
        for pos in positions:
            current_value = pos.get('current_value', 0) or 0
            gain_loss_percent = pos.get('gain_loss_percent', 0) or 0
            weight = (current_value / total_value * 100) if total_value > 0 else 0

            # Position performante et pas trop concentrée
            if gain_loss_percent > 5 and weight < 20:
                current_price = pos.get('current_price', 0) or 0
                if current_price > 0:
                    # Calculer combien on peut ajouter pour atteindre ~15% max
                    target_weight = min(15, weight + 5)
                    target_value = (target_weight / 100) * pea_total_value if pea_total_value > 0 else 0
                    suggested_amount = max(0, target_value - current_value)
                    suggested_amount = min(suggested_amount, cash_available * 0.4)  # Max 40% du cash

                    if suggested_amount >= 100:  # Minimum 100€ pour que ça vaille le coup
                        opportunities.append({
                            "type": "ADD_TO_EXISTING",
                            "ticker": pos['ticker'],
                            "company_name": pos['company_name'],
                            "priority": "MEDIUM",
                            "description": f"Renforcer {pos['company_name']} (performance: +{gain_loss_percent:.1f}%, poids actuel: {weight:.1f}%)",
                            "suggested_amount": suggested_amount,
                            "suggested_quantity": int(suggested_amount / current_price),
                            "current_price": current_price,
                            "current_weight": weight,
                            "target_weight": target_weight,
                            "reasoning": f"Position performante avec potentiel de renforcement sans surconcentration"
                        })

        # 3. Rééquilibrage du cash (> 30% en cash)
        if cash_ratio > 30 and total_value > 0:
            opportunities.append({
                "type": "REBALANCE_CASH",
                "priority": "MEDIUM",
                "description": f"Trop de cash dormant ({cash_ratio:.1f}%). Recommandation: investir progressivement pour optimiser le rendement.",
                "suggested_amount": cash_available * 0.5,  # Investir 50% du cash
                "reasoning": f"Ratio cash/investissement déséquilibré: {cash_ratio:.1f}% en cash vs {summary.get('investment_ratio', 0):.1f}% investi"
            })

        return {
            "has_opportunities": len(opportunities) > 0,
            "cash_available": cash_available,
            "cash_ratio": cash_ratio,
            "portfolio_size": len(positions),
            "total_value": pea_total_value,
            "opportunities": sorted(opportunities, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(x['priority'], 3))
        }

    def save_opportunity_to_db(
        self,
        ticker: str,
        company_name: str,
        recommendation_type: str,
        suggested_amount: float,
        reasoning: str,
        user_id: str = "default_user",
        suggested_quantity: Optional[int] = None,
        target_price: Optional[float] = None,
        confidence_score: float = 0.7,
        risk_level: str = "MEDIUM",
        expires_in_days: int = 7
    ) -> bool:
        """
        Sauvegarde une opportunité d'investissement en base de données

        Args:
            ticker: Symbole de l'action
            company_name: Nom de l'entreprise
            recommendation_type: Type de recommandation (DIVERSIFY, ADD_TO_EXISTING, etc.)
            suggested_amount: Montant suggéré en euros
            reasoning: Raisonnement de la recommandation
            suggested_quantity: Nombre d'actions suggéré (optionnel)
            target_price: Prix cible (optionnel)
            confidence_score: Score de confiance (0-1)
            risk_level: Niveau de risque (LOW, MEDIUM, HIGH)
            expires_in_days: Validité de l'opportunité en jours

        Returns:
            True si succès, False sinon
        """
        try:
            import sqlite3
            from datetime import timedelta

            treasury = self.db.get_treasury_status(user_id)
            summary = self.db.get_portfolio_summary(user_id)

            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()

            expires_at = (datetime.now() + timedelta(days=expires_in_days)).strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO investment_opportunities
                (user_id, ticker, company_name, recommendation_type, suggested_amount,
                 suggested_quantity, target_price, reasoning, confidence_score, risk_level,
                 cash_available_at_time, portfolio_value_at_time, status, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
            """, (
                user_id, ticker, company_name, recommendation_type, suggested_amount,
                suggested_quantity, target_price, reasoning, confidence_score, risk_level,
                treasury.get('cash_available', 0),
                summary.get('pea_treasury', {}).get('pea_total_value', 0),
                expires_at
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Erreur save_opportunity_to_db: {e}")
            if 'conn' in locals():
                conn.close()
            return False

    def get_pending_opportunities(
        self,
        user_id: str = "default_user",
        include_expired: bool = False
    ) -> List[Dict]:
        """
        Récupère les opportunités d'investissement en attente

        Args:
            user_id: Identifiant utilisateur
            include_expired: Inclure les opportunités expirées

        Returns:
            Liste des opportunités en attente
        """
        try:
            import sqlite3

            conn = sqlite3.connect(self.db.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if include_expired:
                cursor.execute("""
                    SELECT * FROM investment_opportunities
                    WHERE user_id = ? AND status = 'PENDING'
                    ORDER BY created_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT * FROM investment_opportunities
                    WHERE user_id = ? AND status = 'PENDING'
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                    ORDER BY created_at DESC
                """, (user_id,))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            print(f"Erreur get_pending_opportunities: {e}")
            return []

    def accept_opportunity(
        self,
        opportunity_id: int,
        user_id: str = "default_user",
        actual_quantity: Optional[int] = None,
        actual_price: Optional[float] = None
    ) -> Dict:
        """
        Accepte une opportunité d'investissement et exécute la transaction

        Args:
            opportunity_id: ID de l'opportunité
            user_id: Identifiant utilisateur
            actual_quantity: Quantité réelle achetée (si différent de suggéré)
            actual_price: Prix réel d'achat (si différent du marché)

        Returns:
            Dict avec le résultat de la transaction
        """
        try:
            import sqlite3

            # Récupérer l'opportunité
            conn = sqlite3.connect(self.db.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM investment_opportunities
                WHERE id = ? AND user_id = ? AND status = 'PENDING'
            """, (opportunity_id, user_id))

            opportunity = cursor.fetchone()
            conn.close()

            if not opportunity:
                return {
                    "success": False,
                    "error": "Opportunité non trouvée ou déjà traitée"
                }

            # Vérifier si expirée
            if opportunity['expires_at']:
                expires_at = datetime.strptime(opportunity['expires_at'], "%Y-%m-%d %H:%M:%S")
                if datetime.now() > expires_at:
                    return {
                        "success": False,
                        "error": "Opportunité expirée"
                    }

            # Déterminer la quantité et le prix
            ticker = opportunity['ticker']
            company_name = opportunity['company_name']

            if actual_price is None:
                # Récupérer le prix du marché
                market_info = self.yf.get_stock_info(ticker)
                actual_price = market_info.get('currentPrice', 0)

                if actual_price <= 0:
                    return {
                        "success": False,
                        "error": "Impossible de récupérer le prix actuel du marché"
                    }

            if actual_quantity is None:
                # Utiliser la quantité suggérée ou calculer à partir du montant
                actual_quantity = opportunity['suggested_quantity']
                if not actual_quantity:
                    actual_quantity = int(opportunity['suggested_amount'] / actual_price)

            if actual_quantity <= 0:
                return {
                    "success": False,
                    "error": "Quantité invalide"
                }

            # Exécuter la transaction
            success = self.db.add_position(
                ticker=ticker,
                company_name=company_name,
                quantity=actual_quantity,
                price=actual_price,
                user_id=user_id
            )

            if success:
                # Marquer l'opportunité comme acceptée
                conn = sqlite3.connect(self.db.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE investment_opportunities
                    SET status = 'ACCEPTED',
                        actioned_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (opportunity_id,))

                conn.commit()
                conn.close()

                return {
                    "success": True,
                    "ticker": ticker,
                    "company_name": company_name,
                    "quantity": actual_quantity,
                    "price": actual_price,
                    "total_amount": actual_quantity * actual_price,
                    "message": f"Transaction exécutée: {actual_quantity} actions de {company_name} à {actual_price:.2f}€"
                }
            else:
                return {
                    "success": False,
                    "error": "Échec de la transaction (probablement cash insuffisant)"
                }

        except Exception as e:
            print(f"Erreur accept_opportunity: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def reject_opportunity(
        self,
        opportunity_id: int,
        user_id: str = "default_user",
        reason: Optional[str] = None
    ) -> bool:
        """
        Rejette une opportunité d'investissement

        Args:
            opportunity_id: ID de l'opportunité
            user_id: Identifiant utilisateur
            reason: Raison du rejet (optionnel)

        Returns:
            True si succès, False sinon
        """
        try:
            import sqlite3

            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()

            # Vérifier que l'opportunité existe et appartient à l'utilisateur
            cursor.execute("""
                SELECT id FROM investment_opportunities
                WHERE id = ? AND user_id = ? AND status = 'PENDING'
            """, (opportunity_id, user_id))

            if not cursor.fetchone():
                conn.close()
                return False

            # Marquer comme rejetée
            cursor.execute("""
                UPDATE investment_opportunities
                SET status = 'REJECTED',
                    actioned_at = CURRENT_TIMESTAMP,
                    reasoning = CASE
                        WHEN ? IS NOT NULL THEN reasoning || ' | Rejet: ' || ?
                        ELSE reasoning
                    END
                WHERE id = ?
            """, (reason, reason, opportunity_id))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Erreur reject_opportunity: {e}")
            if 'conn' in locals():
                conn.close()
            return False
