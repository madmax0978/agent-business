"""
Agrégateur d'actualités depuis plusieurs sources
"""

import os
import requests
from typing import List, Dict
from datetime import datetime, timedelta


class NewsAggregator:
    """Agrège les actualités depuis NewsAPI et autres sources"""

    def __init__(self):
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.serpapi_key = os.getenv("SERPAPI_KEY")

    def get_company_news(
        self,
        company_name: str,
        days_back: int = 7,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Récupère les actualités récentes d'une entreprise

        Args:
            company_name: Nom de l'entreprise
            days_back: Nombre de jours à remonter
            max_results: Nombre max d'articles

        Returns:
            Liste d'articles avec {title, description, url, published_at, source}
        """
        articles = []

        # NewsAPI
        if self.news_api_key:
            articles.extend(self._fetch_newsapi(company_name, days_back, max_results))
        else:
            # Fallback: simulation pour démo
            articles.extend(self._fallback_news(company_name, days_back, max_results))

        # Google News via SerpAPI (optionnel)
        if self.serpapi_key and len(articles) < max_results:
            articles.extend(self._fetch_google_news(company_name, max_results - len(articles)))

        # Trier par date (plus récent d'abord)
        articles.sort(key=lambda x: x.get('published_at', ''), reverse=True)

        return articles[:max_results]

    def _fetch_newsapi(
        self,
        company_name: str,
        days_back: int,
        max_results: int
    ) -> List[Dict]:
        """Récupère depuis NewsAPI"""
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

            url = "https://newsapi.org/v2/everything"
            params = {
                "q": company_name,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "fr",
                "pageSize": max_results,
                "apiKey": self.news_api_key
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get("articles", [])
            else:
                print(f"Erreur NewsAPI: {response.status_code}")
                return []
        except Exception as e:
            print(f"Erreur _fetch_newsapi: {e}")
            return []

    def _fetch_google_news(self, company_name: str, max_results: int) -> List[Dict]:
        """Récupère depuis Google News via SerpAPI"""
        try:
            url = "https://serpapi.com/search.json"
            params = {
                "engine": "google_news",
                "q": company_name,
                "gl": "fr",
                "hl": "fr",
                "num": max_results,
                "api_key": self.serpapi_key
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                news_results = data.get("news_results", [])

                # Formater pour correspondre au format NewsAPI
                formatted = []
                for item in news_results:
                    formatted.append({
                        "title": item.get("title", ""),
                        "description": item.get("snippet", ""),
                        "url": item.get("link", ""),
                        "published_at": item.get("date", ""),
                        "source": {"name": item.get("source", {}).get("name", "Google News")}
                    })

                return formatted
            else:
                return []
        except Exception as e:
            print(f"Erreur _fetch_google_news: {e}")
            return []

    def _fallback_news(self, company_name: str, days_back: int, max_results: int) -> List[Dict]:
        """Génère des actualités de démonstration si pas d'API"""
        today = datetime.now()

        demo_news = [
            {
                "title": f"{company_name} annonce ses résultats trimestriels",
                "description": f"La société {company_name} a publié ses résultats financiers du dernier trimestre, montrant une croissance continue.",
                "url": f"https://example.com/news/{company_name.lower()}/1",
                "published_at": (today - timedelta(days=1)).isoformat(),
                "source": {"name": "Les Échos (Démo)"}
            },
            {
                "title": f"Analyse: Les perspectives de {company_name} pour 2024",
                "description": f"Les analystes sont optimistes concernant {company_name} avec des prévisions de croissance solide.",
                "url": f"https://example.com/news/{company_name.lower()}/2",
                "published_at": (today - timedelta(days=2)).isoformat(),
                "source": {"name": "Reuters (Démo)"}
            },
            {
                "title": f"{company_name}: Nouvelle stratégie internationale",
                "description": f"Le groupe {company_name} dévoile sa nouvelle stratégie d'expansion sur les marchés émergents.",
                "url": f"https://example.com/news/{company_name.lower()}/3",
                "published_at": (today - timedelta(days=3)).isoformat(),
                "source": {"name": "Le Figaro (Démo)"}
            },
            {
                "title": f"Innovation: {company_name} lance un nouveau produit",
                "description": f"{company_name} présente son dernier produit innovant qui pourrait révolutionner le marché.",
                "url": f"https://example.com/news/{company_name.lower()}/4",
                "published_at": (today - timedelta(days=5)).isoformat(),
                "source": {"name": "BFM Business (Démo)"}
            },
            {
                "title": f"Cours de bourse: {company_name} en hausse",
                "description": f"L'action {company_name} progresse suite aux annonces positives de la direction.",
                "url": f"https://example.com/news/{company_name.lower()}/5",
                "published_at": (today - timedelta(days=6)).isoformat(),
                "source": {"name": "Boursorama (Démo)"}
            }
        ]

        print(f"⚠️ Utilisation de news de démonstration pour {company_name}")
        print(f"   Pour des vraies actualités, configurez NEWS_API_KEY dans .env")

        return demo_news[:max_results]
