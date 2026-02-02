"""
Extraction intelligente de documents avec IA
"""

import os
from typing import Dict, Optional


class SmartDocumentProcessor:
    """Processeur intelligent de documents utilisant Claude/GPT-4"""

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
                    print("⚠️ ANTHROPIC_API_KEY non configurée - Extraction intelligente désactivée")
                    self.client = None
            except ImportError:
                print("⚠️ Package 'anthropic' non installé - Extraction intelligente désactivée")
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
                    print("⚠️ OPENAI_API_KEY non configurée - Extraction intelligente désactivée")
                    self.client = None
            except ImportError:
                print("⚠️ Package 'openai' non installé - Extraction intelligente désactivée")
                self.client = None

    def extract_key_financial_data(
        self,
        document_text: str,
        company_name: str
    ) -> Dict:
        """
        Extrait uniquement les données financières clés d'un rapport

        Args:
            document_text: Texte complet du document
            company_name: Nom de l'entreprise

        Returns:
            Dict avec les données extraites
        """
        if not self.client:
            return self._fallback_extraction(document_text, company_name)

        # Limiter le texte si trop long (max 100k caractères)
        if len(document_text) > 100000:
            document_text = document_text[:100000] + "...[TRONQUÉ]"

        prompt = f"""Extrait uniquement les informations financières CLÉS de ce rapport pour {company_name}.

Document:
{document_text}

Extrait et structure les données suivantes (indique "Non trouvé" si absent):

1. CHIFFRE D'AFFAIRES:
   - Dernier trimestre/semestre
   - Évolution YoY (%)
   - Par zone géographique si disponible

2. RÉSULTAT OPÉRATIONNEL:
   - Montant
   - Marge opérationnelle (%)
   - Évolution YoY

3. RÉSULTAT NET:
   - Montant
   - Marge nette (%)
   - Évolution YoY

4. DETTE ET TRÉSORERIE:
   - Dette nette
   - Ratio d'endettement
   - Trésorerie disponible

5. FLUX DE TRÉSORERIE:
   - Free cash flow
   - Capacité d'autofinancement

6. DIVIDENDES:
   - Montant par action
   - Rendement (%)
   - Politique de distribution

7. GUIDANCE (Prévisions):
   - Objectifs de CA
   - Objectifs de marge
   - Outlook général

8. ÉVÉNEMENTS IMPORTANTS:
   - Acquisitions/cessions
   - Lancements de produits
   - Changements stratégiques

IMPORTANT:
- Sois concis et précis
- Indique les montants en millions ou milliards €
- Indique les périodes exactes
- Ignore les disclaimers, détails comptables complexes, et informations non essentielles"""

        try:
            if self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                extracted_data = response.content[0].text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4000
                )
                extracted_data = response.choices[0].message.content

            return {
                "company": company_name,
                "extracted_data": extracted_data,
                "original_length": len(document_text),
                "compressed_length": len(extracted_data),
                "compression_ratio": (1 - len(extracted_data) / len(document_text)) * 100,
                "provider": self.provider
            }

        except Exception as e:
            print(f"Erreur lors de l'extraction intelligente: {e}")
            return self._fallback_extraction(document_text, company_name)

    def _fallback_extraction(self, document_text: str, company_name: str) -> Dict:
        """Extraction basique si pas d'IA disponible"""
        # Extraction très basique par mots-clés
        keywords = {
            "chiffre d'affaires": ["chiffre d'affaires", "ca", "revenus", "ventes"],
            "résultat opérationnel": ["résultat opérationnel", "ebit"],
            "résultat net": ["résultat net", "bénéfice net"],
            "dette": ["dette nette", "endettement"],
            "dividende": ["dividende", "distribution"]
        }

        extracted_sections = []

        for section, terms in keywords.items():
            for term in terms:
                # Chercher le terme dans le document
                index = document_text.lower().find(term)
                if index != -1:
                    # Extraire 500 caractères autour
                    start = max(0, index - 250)
                    end = min(len(document_text), index + 250)
                    snippet = document_text[start:end]
                    extracted_sections.append(f"{section.upper()}:\n{snippet}\n")
                    break

        extracted_data = "\n".join(extracted_sections) if extracted_sections else "Extraction basique limitée - Configurez une clé API pour extraction complète"

        return {
            "company": company_name,
            "extracted_data": extracted_data,
            "original_length": len(document_text),
            "compressed_length": len(extracted_data),
            "compression_ratio": (1 - len(extracted_data) / len(document_text)) * 100,
            "provider": "fallback"
        }

    def summarize_document(
        self,
        document_text: str,
        max_length: int = 500
    ) -> str:
        """
        Résume un document en quelques phrases

        Args:
            document_text: Texte à résumer
            max_length: Longueur maximale du résumé

        Returns:
            Résumé du document
        """
        if not self.client:
            # Résumé basique: prendre les premières phrases
            sentences = document_text.split('.')
            summary = '. '.join(sentences[:5]) + '.'
            return summary[:max_length]

        prompt = f"""Résume ce document financier en {max_length} caractères maximum.
Concentre-toi sur les points clés et les chiffres importants.

Document:
{document_text[:50000]}

Résumé concis:"""

        try:
            if self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                return response.choices[0].message.content

        except Exception as e:
            print(f"Erreur lors du résumé: {e}")
            sentences = document_text.split('.')
            summary = '. '.join(sentences[:5]) + '.'
            return summary[:max_length]
