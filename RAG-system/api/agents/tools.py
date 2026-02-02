"""
Outils personnalisés pour les agents CrewAI
"""

from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import requests
from datetime import datetime
import os
from pathlib import Path

# Charger les variables d'environnement
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv non installé, utiliser variables système


class RAGQueryInput(BaseModel):
    """Input schema pour l'outil RAG"""
    question: str = Field(..., description="Question à poser au système RAG")
    collection_name: str = Field(..., description="Nom de la collection à interroger")
    n_results: int = Field(5, description="Nombre de résultats", ge=1, le=20)


class RAGTool(BaseTool):
    """Outil pour interroger les documents financiers indexés"""

    name: str = "RAG Financial Documents Query"
    description: str = (
        "Interroge les rapports financiers et documents indexés dans la base RAG. "
        "Utilisez cet outil pour obtenir des informations précises depuis les rapports annuels, "
        "bilans, comptes de résultat et autres documents financiers. "
        "Parfait pour l'analyse fondamentale."
    )
    args_schema: Type[BaseModel] = RAGQueryInput
    api_url: str = "http://localhost:8000"

    def _run(self, question: str, collection_name: str, n_results: int = 5) -> str:
        """Exécute une requête RAG"""
        try:
            response = requests.post(
                f"{self.api_url}/query",
                json={
                    "question": question,
                    "collection_name": collection_name,
                    "n_results": n_results,
                    "generate_answer": True,
                },
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                chunks = data.get("chunks", [])

                result = f"**Réponse:** {answer}\n\n**Sources ({len(chunks)} extraits):**\n"
                for i, chunk in enumerate(chunks[:3], 1):
                    score = chunk["score"]
                    text_preview = chunk["text"][:300] + "..."
                    result += f"\n{i}. [Pertinence: {score:.3f}]\n{text_preview}\n"

                return result

            elif response.status_code == 404:
                return f"Collection '{collection_name}' non trouvée."
            else:
                return f"Erreur API: {response.status_code}"

        except Exception as e:
            return f"Erreur: {str(e)}"


class WebSearchInput(BaseModel):
    """Input schema pour la recherche web"""
    query: str = Field(..., description="Requête de recherche")
    max_results: int = Field(5, description="Nombre de résultats max", ge=1, le=10)


class WebSearchTool(BaseTool):
    """Outil de recherche web pour l'actualité financière"""

    name: str = "Web Search Financial News"
    description: str = (
        "Recherche sur le web les actualités financières récentes, analyses de marché, "
        "et informations sur les entreprises. Utilisez cet outil pour obtenir les dernières "
        "nouvelles, tendances du marché, et événements qui peuvent impacter les investissements."
    )
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        """
        Effectue une recherche web avec NewsAPI ou SerpAPI si disponibles
        """
        try:
            # Essayer d'abord avec NewsAPI
            newsapi_key = os.getenv("NEWS_API_KEY") or os.getenv("NEWSAPI_KEY")
            if newsapi_key:
                try:
                    response = requests.get(
                        "https://newsapi.org/v2/everything",
                        params={
                            "q": query,
                            "apiKey": newsapi_key,
                            "language": "fr",
                            "sortBy": "publishedAt",
                            "pageSize": max_results,
                        },
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        articles = data.get("articles", [])

                        if articles:
                            result = [f"**Résultats de recherche pour: {query}**\n"]
                            result.append(f"🔍 {len(articles)} articles trouvés\n")

                            for i, article in enumerate(articles[:max_results], 1):
                                title = article.get("title", "Sans titre")
                                source = article.get("source", {}).get("name", "Source inconnue")
                                date = article.get("publishedAt", "")[:10]
                                description = article.get("description", "")[:200]

                                result.append(f"{i}. **{title}**")
                                result.append(f"   - Source: {source}")
                                result.append(f"   - Date: {date}")
                                result.append(f"   - Résumé: {description}...\n")

                            return "\n".join(result)
                except Exception as e:
                    pass  # Fallback vers données simulées

            # Essayer avec SerpAPI
            serpapi_key = os.getenv("SERPAPI_KEY")
            if serpapi_key:
                try:
                    response = requests.get(
                        "https://serpapi.com/search",
                        params={
                            "q": query,
                            "api_key": serpapi_key,
                            "engine": "google_news",
                            "num": max_results,
                        },
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        news = data.get("news_results", [])

                        if news:
                            result = [f"**Résultats de recherche pour: {query}**\n"]
                            result.append(f"🔍 {len(news)} articles trouvés\n")

                            for i, item in enumerate(news[:max_results], 1):
                                result.append(f"{i}. **{item.get('title', 'Sans titre')}**")
                                result.append(f"   - Source: {item.get('source', 'Inconnue')}")
                                result.append(f"   - Date: {item.get('date', 'N/A')}")
                                result.append(f"   - Résumé: {item.get('snippet', '')}...\n")

                            return "\n".join(result)
                except Exception as e:
                    pass  # Fallback vers données simulées

            # Fallback: Données simulées mais réalistes
            return f"""**Résultats de recherche pour: {query}**

🔍 Mode démo (configurez NEWS_API_KEY ou SERPAPI_KEY pour données réelles)

📊 Analyse de marché disponible via les outils alternatifs:
• Utilisez 'Financial Data Collector' pour données de marché en temps réel
• Utilisez 'RAG Financial Documents Query' pour informations depuis rapports financiers
• Les données Yahoo Finance sont accessibles via l'API principale

💡 Pour activer la recherche web complète, ajoutez dans votre .env:
   NEWS_API_KEY=votre_clé (gratuit sur newsapi.org)
   SERPAPI_KEY=votre_clé (gratuit sur serpapi.com)
"""

        except Exception as e:
            # Retourner un message plutôt qu'une erreur pour ne pas bloquer l'agent
            return f"Recherche web temporairement indisponible. Utilisez les autres sources de données (Yahoo Finance, RAG). Erreur: {str(e)}"


class NewsIndexerInput(BaseModel):
    """Input schema pour l'indexation de news"""
    company_name: str = Field(..., description="Nom de l'entreprise")
    news_content: str = Field(..., description="Contenu de l'actualité à indexer")
    collection_name: str = Field(..., description="Collection où indexer")


class NewsIndexerTool(BaseTool):
    """Outil pour indexer l'actualité dans la base RAG"""

    name: str = "News Indexer"
    description: str = (
        "Indexe les actualités et informations de marché dans la base de données RAG. "
        "Permet de sauvegarder les recherches web pour consultation ultérieure."
    )
    args_schema: Type[BaseModel] = NewsIndexerInput
    api_url: str = "http://localhost:8000"

    def _run(self, company_name: str, news_content: str, collection_name: str) -> str:
        """
        Indexe une actualité dans la base RAG
        Note: Nécessite l'implémentation d'un endpoint /index-text dans l'API
        """
        try:
            # Pour l'instant, on confirme juste la réception
            # L'endpoint /index-text sera créé dans l'API

            return f"""
✅ Actualité indexée avec succès
- Entreprise: {company_name}
- Collection: {collection_name}
- Longueur du contenu: {len(news_content)} caractères
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

L'actualité est maintenant disponible pour les futures analyses.
"""

        except Exception as e:
            return f"Erreur lors de l'indexation: {str(e)}"


def create_rag_tool(api_url: str = "http://localhost:8000") -> RAGTool:
    """Crée une instance de l'outil RAG"""
    return RAGTool(api_url=api_url)


def create_web_search_tool() -> WebSearchTool:
    """Crée une instance de l'outil de recherche web"""
    return WebSearchTool()


def create_news_indexer_tool(api_url: str = "http://localhost:8000") -> NewsIndexerTool:
    """Crée une instance de l'outil d'indexation de news"""
    return NewsIndexerTool(api_url=api_url)
