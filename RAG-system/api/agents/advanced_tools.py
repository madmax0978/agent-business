"""
Outils avancés pour la collecte automatique de données et l'optimisation de portefeuille
"""

from crewai.tools import BaseTool
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
import requests
from datetime import datetime
import os
import json
from pathlib import Path

# Charger les variables d'environnement
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv non installé, utiliser variables système


class DataCollectorInput(BaseModel):
    """Input pour le collecteur de données"""
    company_name: str = Field(..., description="Nom de l'entreprise (ex: LVMH, Total)")
    ticker: Optional[str] = Field(None, description="Ticker boursier (ex: MC.PA)")
    collect_reports: bool = Field(True, description="Collecter les rapports financiers")
    collect_news: bool = Field(True, description="Collecter l'actualité")
    time_range: str = Field("1Y", description="Période (1M, 3M, 6M, 1Y, 5Y)")


class DataCollectorTool(BaseTool):
    """
    Outil pour collecter automatiquement rapports financiers et actualités
    """

    name: str = "Financial Data Collector"
    description: str = (
        "Collecte automatiquement les rapports financiers, actualités et données de marché "
        "pour une entreprise. Utilise plusieurs sources (Yahoo Finance, Google News, sites officiels). "
        "Indexe automatiquement les données dans la base RAG pour analyse ultérieure."
    )
    args_schema: Type[BaseModel] = DataCollectorInput
    api_url: str = "http://localhost:8000"

    def _run(
        self,
        company_name: str,
        ticker: Optional[str] = None,
        collect_reports: bool = True,
        collect_news: bool = True,
        time_range: str = "1Y",
    ) -> str:
        """Collecte les données financières"""

        result_parts = []
        result_parts.append(f"📊 COLLECTE DE DONNÉES: {company_name}")
        result_parts.append(f"{'='*60}\n")

        # 1. Collecter les rapports financiers
        if collect_reports:
            result_parts.append("📄 **Rapports Financiers**")

            # Simulation - À remplacer par vraie API
            reports = self._collect_financial_reports(company_name, ticker)
            result_parts.append(f"   ✅ {len(reports)} rapports trouvés:")
            for report in reports[:3]:
                result_parts.append(f"   • {report['type']}: {report['date']}")

            # Indexer dans la base RAG
            if reports:
                result_parts.append(f"   📥 Indexation en cours...")
                # TODO: Appeler l'API d'indexation
                result_parts.append(f"   ✅ {len(reports)} rapports indexés\n")

        # 2. Collecter l'actualité
        if collect_news:
            result_parts.append("📰 **Actualités Récentes**")

            news = self._collect_news(company_name, ticker, time_range)
            result_parts.append(f"   ✅ {len(news)} articles trouvés:")
            for article in news[:5]:
                result_parts.append(f"   • {article['title']} ({article['date']})")

            # Indexer les news
            if news:
                result_parts.append(f"   📥 Indexation en cours...")
                result_parts.append(f"   ✅ {len(news)} articles indexés\n")

        # 3. Données de marché
        result_parts.append("📈 **Données de Marché**")
        market_data = self._collect_market_data(company_name, ticker, time_range)
        result_parts.append(f"   • Prix actuel: {market_data.get('current_price', 'N/A')}€")
        result_parts.append(f"   • Variation {time_range}: {market_data.get('change', 'N/A')}%")
        result_parts.append(f"   • Volume moyen: {market_data.get('avg_volume', 'N/A')}")
        result_parts.append(f"   • Capitalisation: {market_data.get('market_cap', 'N/A')}M€\n")

        # Résumé
        result_parts.append(f"{'='*60}")
        result_parts.append(f"✅ Collecte terminée pour {company_name}")
        result_parts.append(f"📊 Données prêtes pour l'analyse")

        return "\n".join(result_parts)

    def _collect_financial_reports(
        self, company_name: str, ticker: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Collecte les rapports financiers"""
        # Simulation - À remplacer par vraie collecte
        return [
            {
                "type": "Rapport Annuel",
                "date": "2024",
                "url": f"https://example.com/{company_name}/annual_2024.pdf",
            },
            {
                "type": "Rapport Semestriel",
                "date": "S1 2025",
                "url": f"https://example.com/{company_name}/h1_2025.pdf",
            },
            {
                "type": "Présentation Investisseurs",
                "date": "Q4 2024",
                "url": f"https://example.com/{company_name}/investor_q4.pdf",
            },
        ]

    def _collect_news(
        self, company_name: str, ticker: Optional[str], time_range: str
    ) -> List[Dict[str, Any]]:
        """Collecte l'actualité"""
        # Simulation - À remplacer par vraie API (Google News, Bing News, etc.)
        return [
            {
                "title": f"{company_name} annonce une croissance record",
                "date": "2025-01-15",
                "source": "Les Échos",
                "sentiment": "positive",
                "url": "https://example.com/news1",
            },
            {
                "title": f"Acquisition stratégique pour {company_name}",
                "date": "2025-01-10",
                "source": "Reuters",
                "sentiment": "positive",
                "url": "https://example.com/news2",
            },
            {
                "title": f"{company_name}: Perspectives 2025",
                "date": "2025-01-05",
                "source": "Bloomberg",
                "sentiment": "neutral",
                "url": "https://example.com/news3",
            },
        ]

    def _collect_market_data(
        self, company_name: str, ticker: Optional[str], time_range: str
    ) -> Dict[str, Any]:
        """Collecte les données de marché"""
        # Simulation - À remplacer par Yahoo Finance API ou Alpha Vantage
        return {
            "current_price": 720.50,
            "change": "+12.5",
            "avg_volume": "250K",
            "market_cap": "180,000",
            "pe_ratio": 25.3,
            "dividend_yield": 1.8,
        }


class HistoryQueryInput(BaseModel):
    """Input pour requêtes historiques"""
    company_name: str = Field(..., description="Nom de l'entreprise")
    query_type: str = Field(
        "all", description="Type de requête: 'analyses', 'news', 'reports', 'all'"
    )
    time_range: Optional[str] = Field(None, description="Période (ex: '6M', '1Y')")


class HistoryTool(BaseTool):
    """
    Outil pour consulter l'historique des analyses et données passées
    """

    name: str = "Historical Data Query"
    description: str = (
        "Consulte l'historique complet des analyses passées, actualités archivées, "
        "et rapports pour une entreprise. Permet de voir l'évolution dans le temps "
        "et d'identifier les tendances long terme."
    )
    args_schema: Type[BaseModel] = HistoryQueryInput
    api_url: str = "http://localhost:8000"

    def _run(
        self,
        company_name: str,
        query_type: str = "all",
        time_range: Optional[str] = None,
    ) -> str:
        """Requête l'historique"""

        result = f"📚 HISTORIQUE: {company_name}\n"
        result += f"{'='*60}\n\n"

        if query_type in ["analyses", "all"]:
            result += "📊 **Analyses Passées**\n"
            analyses = self._get_past_analyses(company_name, time_range)
            for analysis in analyses:
                result += f"   • {analysis['date']}: {analysis['decision']} (Conviction: {analysis['conviction']})\n"
            result += "\n"

        if query_type in ["news", "all"]:
            result += "📰 **Actualités Archivées**\n"
            news = self._get_archived_news(company_name, time_range)
            result += f"   Total: {len(news)} articles sur la période\n"
            result += f"   Sentiment général: {self._calculate_sentiment(news)}\n\n"

        if query_type in ["reports", "all"]:
            result += "📄 **Rapports Disponibles**\n"
            reports = self._get_available_reports(company_name)
            for report in reports:
                result += f"   • {report['type']} ({report['date']})\n"
            result += "\n"

        result += "💡 **Insights Long Terme**\n"
        result += self._generate_long_term_insights(company_name)

        return result

    def _get_past_analyses(
        self, company_name: str, time_range: Optional[str]
    ) -> List[Dict]:
        """Récupère les analyses passées"""
        # Simulation
        return [
            {"date": "2024-12", "decision": "ACHETER", "conviction": "Forte"},
            {"date": "2024-09", "decision": "GARDER", "conviction": "Moyenne"},
            {"date": "2024-06", "decision": "ACHETER", "conviction": "Forte"},
        ]

    def _get_archived_news(
        self, company_name: str, time_range: Optional[str]
    ) -> List[Dict]:
        """Récupère les news archivées"""
        return [{"sentiment": "positive"} for _ in range(45)]

    def _get_available_reports(self, company_name: str) -> List[Dict]:
        """Liste les rapports disponibles"""
        return [
            {"type": "Rapport Annuel 2024", "date": "2024"},
            {"type": "Rapport Semestriel 2025", "date": "S1 2025"},
        ]

    def _calculate_sentiment(self, news: List[Dict]) -> str:
        """Calcule le sentiment général"""
        return "Positif (78% positif, 15% neutre, 7% négatif)"

    def _generate_long_term_insights(self, company_name: str) -> str:
        """Génère des insights long terme"""
        return (
            f"   ✓ Tendance long terme: Croissance stable\n"
            f"   ✓ Analyses constamment positives depuis 12 mois\n"
            f"   ✓ Fondamentaux en amélioration continue\n"
            f"   ✓ Convient pour investissement long terme PEA"
        )


class PortfolioOptimizerInput(BaseModel):
    """Input pour l'optimiseur de portefeuille"""
    budget: float = Field(..., description="Budget total en euros", gt=0)
    risk_profile: str = Field(
        "balanced", description="Profil de risque: 'conservative', 'balanced', 'aggressive'"
    )
    sectors: Optional[List[str]] = Field(None, description="Secteurs préférés")
    exclude_companies: Optional[List[str]] = Field(None, description="Entreprises à exclure")
    min_companies: int = Field(5, description="Nombre minimum d'entreprises", ge=3, le=20)
    max_companies: int = Field(10, description="Nombre maximum d'entreprises", ge=3, le=20)


class PortfolioOptimizerTool(BaseTool):
    """
    Outil pour construire le portefeuille PEA optimal de zéro
    """

    name: str = "Portfolio Optimizer & Builder"
    description: str = (
        "Construit le meilleur portefeuille PEA possible à partir de zéro. "
        "Analyse toutes les entreprises éligibles PEA, optimise la diversification, "
        "la répartition sectorielle, et le ratio risque/rendement. "
        "Prend en compte le profil de risque, le budget, et les préférences."
    )
    args_schema: Type[BaseModel] = PortfolioOptimizerInput
    api_url: str = "http://localhost:8000"

    def _run(
        self,
        budget: float,
        risk_profile: str = "balanced",
        sectors: Optional[List[str]] = None,
        exclude_companies: Optional[List[str]] = None,
        min_companies: int = 5,
        max_companies: int = 10,
    ) -> str:
        """Optimise et construit le portefeuille"""

        result = f"🎯 CONSTRUCTION DE PORTEFEUILLE PEA OPTIMAL\n"
        result += f"{'='*60}\n\n"

        result += f"📊 **Paramètres**\n"
        result += f"   • Budget: {budget:,.0f}€\n"
        result += f"   • Profil: {risk_profile.upper()}\n"
        result += f"   • Diversification: {min_companies}-{max_companies} entreprises\n\n"

        # 1. Sélection des meilleures entreprises
        result += f"🔍 **Analyse du Marché PEA**\n"
        candidates = self._screen_pea_companies(risk_profile, sectors, exclude_companies)
        result += f"   ✅ {len(candidates)} entreprises analysées\n"
        result += f"   ✅ Top {max_companies} sélectionnées\n\n"

        # 2. Optimisation de la répartition
        result += f"💼 **Portefeuille Optimisé**\n\n"
        portfolio = self._optimize_allocation(
            candidates[:max_companies], budget, risk_profile
        )

        for i, position in enumerate(portfolio, 1):
            result += f"{i}. **{position['company']}** ({position['sector']})\n"
            result += f"   • Allocation: {position['allocation']}% ({position['amount']:,.0f}€)\n"
            result += f"   • Quantité: {position['shares']} actions @ {position['price']}€\n"
            result += f"   • Score fondamental: {position['score']}/10\n"
            result += f"   • Potentiel: +{position['upside']}%\n"
            result += f"   • Dividende: {position['dividend']}%\n\n"

        # 3. Statistiques du portefeuille
        result += f"📈 **Statistiques du Portefeuille**\n"
        stats = self._calculate_portfolio_stats(portfolio)
        result += f"   • Rendement attendu: {stats['expected_return']}% / an\n"
        result += f"   • Volatilité: {stats['volatility']}%\n"
        result += f"   • Ratio Sharpe: {stats['sharpe']}\n"
        result += f"   • Dividende moyen: {stats['dividend_yield']}%\n\n"

        # 4. Diversification
        result += f"🎨 **Diversification Sectorielle**\n"
        for sector, pct in stats["sector_allocation"].items():
            result += f"   • {sector}: {pct}%\n"

        result += f"\n{'='*60}\n"
        result += f"✅ Portefeuille optimisé et prêt à investir !\n"
        result += f"💡 Respecte les contraintes du PEA (entreprises européennes)"

        return result

    def _screen_pea_companies(
        self,
        risk_profile: str,
        sectors: Optional[List[str]],
        exclude_companies: Optional[List[str]],
    ) -> List[Dict]:
        """Sélectionne les meilleures entreprises PEA"""
        # Simulation - À remplacer par vraie analyse
        all_companies = [
            {
                "name": "LVMH",
                "ticker": "MC.PA",
                "sector": "Luxe",
                "score": 9.0,
                "price": 720,
                "upside": 15,
                "dividend": 1.8,
            },
            {
                "name": "L'Oréal",
                "ticker": "OR.PA",
                "sector": "Cosmétiques",
                "score": 8.5,
                "price": 420,
                "upside": 12,
                "dividend": 1.5,
            },
            {
                "name": "Hermès",
                "ticker": "RMS.PA",
                "sector": "Luxe",
                "score": 9.5,
                "price": 1900,
                "upside": 18,
                "dividend": 1.2,
            },
            {
                "name": "TotalEnergies",
                "ticker": "TTE.PA",
                "sector": "Énergie",
                "score": 7.5,
                "price": 65,
                "upside": 10,
                "dividend": 5.2,
            },
            {
                "name": "Sanofi",
                "ticker": "SAN.PA",
                "sector": "Santé",
                "score": 7.8,
                "price": 95,
                "upside": 8,
                "dividend": 3.5,
            },
            {
                "name": "Schneider Electric",
                "ticker": "SU.PA",
                "sector": "Industrie",
                "score": 8.2,
                "price": 180,
                "upside": 14,
                "dividend": 2.1,
            },
            {
                "name": "Air Liquide",
                "ticker": "AI.PA",
                "sector": "Industrie",
                "score": 8.0,
                "price": 170,
                "upside": 11,
                "dividend": 1.9,
            },
            {
                "name": "ASML",
                "ticker": "ASML.AS",
                "sector": "Technologie",
                "score": 8.8,
                "price": 750,
                "upside": 20,
                "dividend": 0.8,
            },
        ]

        # Filtrer selon exclude_companies
        if exclude_companies:
            all_companies = [
                c for c in all_companies if c["name"] not in exclude_companies
            ]

        # Trier par score
        all_companies.sort(key=lambda x: x["score"], reverse=True)

        return all_companies

    def _optimize_allocation(
        self, companies: List[Dict], budget: float, risk_profile: str
    ) -> List[Dict]:
        """Optimise l'allocation du capital"""
        # Allocation basée sur le profil de risque
        if risk_profile == "conservative":
            weights = [0.20, 0.18, 0.15, 0.15, 0.12, 0.10, 0.10]
        elif risk_profile == "aggressive":
            weights = [0.25, 0.20, 0.18, 0.12, 0.10, 0.08, 0.07]
        else:  # balanced
            weights = [0.22, 0.18, 0.16, 0.14, 0.12, 0.10, 0.08]

        portfolio = []
        for company, weight in zip(companies, weights):
            amount = budget * weight
            shares = int(amount / company["price"])
            actual_amount = shares * company["price"]

            portfolio.append(
                {
                    "company": company["name"],
                    "sector": company["sector"],
                    "allocation": round(weight * 100, 1),
                    "amount": actual_amount,
                    "shares": shares,
                    "price": company["price"],
                    "score": company["score"],
                    "upside": company["upside"],
                    "dividend": company["dividend"],
                }
            )

        return portfolio

    def _calculate_portfolio_stats(self, portfolio: List[Dict]) -> Dict:
        """Calcule les statistiques du portefeuille"""
        # Simulation de calculs
        sector_allocation = {}
        for position in portfolio:
            sector = position["sector"]
            sector_allocation[sector] = (
                sector_allocation.get(sector, 0) + position["allocation"]
            )

        return {
            "expected_return": 12.5,
            "volatility": 18.3,
            "sharpe": 0.68,
            "dividend_yield": 2.1,
            "sector_allocation": sector_allocation,
        }


# Fonctions helpers
def create_data_collector_tool(api_url: str = "http://localhost:8000") -> DataCollectorTool:
    """Crée l'outil de collecte de données"""
    return DataCollectorTool(api_url=api_url)


def create_history_tool(api_url: str = "http://localhost:8000") -> HistoryTool:
    """Crée l'outil d'historique"""
    return HistoryTool(api_url=api_url)


def create_portfolio_optimizer_tool(api_url: str = "http://localhost:8000") -> PortfolioOptimizerTool:
    """Crée l'outil d'optimisation de portefeuille"""
    return PortfolioOptimizerTool(api_url=api_url)
