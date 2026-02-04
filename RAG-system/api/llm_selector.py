"""
Sélecteur automatique de LLM avec priorité à Claude (Anthropic)

Ce module choisit automatiquement le meilleur LLM disponible selon les clés API configurées,
en donnant la priorité à Claude.
"""

import os
from typing import Optional, Any

def get_llm_for_crewai(temperature: float = 0.7, max_tokens: int = 4000) -> Optional[Any]:
    """
    Retourne le LLM à utiliser pour CrewAI avec priorité à Claude.
    
    Ordre de priorité:
    1. Claude (Anthropic) si ANTHROPIC_API_KEY existe
    2. OpenAI si OPENAI_API_KEY existe
    3. None (utilise le défaut de CrewAI)
    
    Args:
        temperature: Température pour la génération (0-2)
        max_tokens: Nombre maximum de tokens
        
    Returns:
        Instance LLM ou None
    """
    
    # 1. Essayer Claude en priorité
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                anthropic_api_key=anthropic_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
            print("✅ Utilisation de Claude (Anthropic) pour l'IA")
            return llm
        except ImportError:
            print("⚠️ langchain-anthropic non installé, tentative avec OpenAI...")
        except Exception as e:
            print(f"⚠️ Erreur avec Claude: {e}, tentative avec OpenAI...")
    
    # 2. Fallback sur OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-4-turbo-preview",
                openai_api_key=openai_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
            print("✅ Utilisation d'OpenAI (GPT-4)")
            return llm
        except ImportError:
            print("⚠️ langchain-openai non installé")
        except Exception as e:
            print(f"⚠️ Erreur avec OpenAI: {e}")
    
    # 3. Aucun LLM disponible
    print("⚠️ Aucune clé API configurée (ANTHROPIC_API_KEY ou OPENAI_API_KEY)")
    return None


def get_ai_provider() -> str:
    """
    Retourne le nom du provider IA utilisé en priorité.
    
    Returns:
        "claude", "openai" ou "none"
    """
    if os.getenv("ANTHROPIC_API_KEY"):
        return "claude"
    elif os.getenv("OPENAI_API_KEY"):
        return "openai"
    else:
        return "none"
