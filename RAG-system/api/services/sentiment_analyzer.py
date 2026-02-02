"""
Analyse de sentiment des actualités avec Claude ou OpenAI
"""

import os
from typing import Dict, List
import re


class SentimentAnalyzer:
    """Analyseur de sentiment utilisant Claude ou GPT-4"""

    def __init__(self, provider: str = "claude"):
        """
        Args:
            provider: "claude" ou "openai"
        """
        self.provider = provider

        if provider == "claude":
            try:
                from anthropic import Anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    self.client = Anthropic(api_key=api_key)
                    self.model = "claude-3-5-sonnet-20241022"
                else:
                    print("⚠️ ANTHROPIC_API_KEY non configurée - Analyse de sentiment désactivée")
                    self.client = None
            except ImportError:
                print("⚠️ Package 'anthropic' non installé - Analyse de sentiment désactivée")
                self.client = None
        else:
            try:
                import openai
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    openai.api_key = api_key
                    self.model = "gpt-4-turbo-preview"
                    self.client = openai
                else:
                    print("⚠️ OPENAI_API_KEY non configurée - Analyse de sentiment désactivée")
                    self.client = None
            except ImportError:
                print("⚠️ Package 'openai' non installé - Analyse de sentiment désactivée")
                self.client = None

    def analyze_news_sentiment(
        self,
        company_name: str,
        news_articles: List[Dict]
    ) -> Dict:
        """
        Analyse le sentiment des actualités pour une entreprise

        Args:
            company_name: Nom de l'entreprise
            news_articles: Liste de dicts avec {title, description, url, published_at}

        Returns:
            Dict avec sentiment global et analyse détaillée
        """
        if not self.client:
            return self._fallback_analysis(company_name, news_articles)

        # Préparer le contexte
        news_text = f"Actualités récentes sur {company_name}:\n\n"
        for i, article in enumerate(news_articles[:10], 1):
            news_text += f"{i}. {article.get('title', '')}\n"
            news_text += f"   {article.get('description', '')}\n"
            news_text += f"   Source: {article.get('source', {}).get('name', 'Unknown')}\n\n"

        # Prompt pour l'analyse
        prompt = f"""Tu es un analyste financier expert. Analyse ces actualités sur {company_name} et donne:

{news_text}

Fournis une analyse structurée:

1. SENTIMENT GLOBAL: (Très Positif / Positif / Neutre / Négatif / Très Négatif)

2. SCORE D'IMPACT: (Note de 0 à 10 sur l'impact potentiel sur le cours à court/moyen terme)

3. POINTS CLÉS:
   - Points positifs (maximum 3)
   - Points négatifs (maximum 3)
   - Points neutres (maximum 2)

4. IMPACT ATTENDU SUR LE COURS:
   (Hausse forte / Hausse modérée / Stable / Baisse modérée / Baisse forte)

5. RECOMMANDATION:
   (Acheter / Renforcer / Conserver / Alléger / Vendre)

6. RÉSUMÉ EN 2-3 PHRASES:
   Synthèse claire de la situation

Sois factuel et basé uniquement sur les actualités fournies."""

        try:
            if self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                analysis_text = response.content[0].text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000
                )
                analysis_text = response.choices[0].message.content

            # Parser la réponse
            sentiment = self._extract_sentiment(analysis_text)
            impact_score = self._extract_impact_score(analysis_text)
            recommendation = self._extract_recommendation(analysis_text)

            return {
                "company": company_name,
                "sentiment": sentiment,
                "impact_score": impact_score,
                "recommendation": recommendation,
                "full_analysis": analysis_text,
                "news_count": len(news_articles),
                "provider": self.provider
            }
        except Exception as e:
            print(f"Erreur lors de l'analyse de sentiment: {e}")
            return self._fallback_analysis(company_name, news_articles)

    def _fallback_analysis(self, company_name: str, news_articles: List[Dict]) -> Dict:
        """Analyse simplifiée si pas d'API disponible"""
        # Analyse basique par mots-clés
        positive_keywords = ["croissance", "hausse", "record", "succès", "positif", "progression", "bénéfice", "gain"]
        negative_keywords = ["baisse", "chute", "perte", "difficultés", "crise", "négatif", "recul", "déficit"]

        positive_count = 0
        negative_count = 0

        for article in news_articles[:10]:
            text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
            positive_count += sum(1 for kw in positive_keywords if kw in text)
            negative_count += sum(1 for kw in negative_keywords if kw in text)

        if positive_count > negative_count * 1.5:
            sentiment = "POSITIF"
            impact_score = 6
            recommendation = "CONSERVER"
        elif negative_count > positive_count * 1.5:
            sentiment = "NÉGATIF"
            impact_score = 4
            recommendation = "SURVEILLER"
        else:
            sentiment = "NEUTRE"
            impact_score = 5
            recommendation = "CONSERVER"

        return {
            "company": company_name,
            "sentiment": sentiment,
            "impact_score": impact_score,
            "recommendation": recommendation,
            "full_analysis": f"Analyse basique: {positive_count} mentions positives, {negative_count} mentions négatives sur {len(news_articles)} articles.",
            "news_count": len(news_articles),
            "provider": "fallback"
        }

    def _extract_sentiment(self, text: str) -> str:
        """Extrait le sentiment du texte"""
        text_lower = text.lower()
        if "très positif" in text_lower:
            return "TRÈS POSITIF"
        elif "positif" in text_lower:
            return "POSITIF"
        elif "très négatif" in text_lower or "très negatif" in text_lower:
            return "TRÈS NÉGATIF"
        elif "négatif" in text_lower or "negatif" in text_lower:
            return "NÉGATIF"
        else:
            return "NEUTRE"

    def _extract_impact_score(self, text: str) -> int:
        """Extrait le score d'impact (0-10)"""
        match = re.search(r'SCORE D\'IMPACT.*?(\d+)', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 5  # Default

    def _extract_recommendation(self, text: str) -> str:
        """Extrait la recommandation"""
        text_lower = text.lower()
        if "acheter" in text_lower:
            return "ACHETER"
        elif "renforcer" in text_lower:
            return "RENFORCER"
        elif "vendre" in text_lower:
            return "VENDRE"
        elif "alléger" in text_lower or "alleger" in text_lower:
            return "ALLÉGER"
        else:
            return "CONSERVER"
