"""
Équipe CrewAI pour l'analyse financière et l'investissement PEA

Ce module orchestre une équipe d'agents IA spécialisés pour analyser
des actions et fournir des recommandations d'investissement PEA.

L'équipe est composée de 4 agents :
1. Analyste Fondamental : Analyse bilans, comptes de résultat, valorisation
2. Analyste Actualités : Recherche et analyse les news récentes
3. Analyste Technique : Évalue tendances, momentum, timing d'entrée
4. Gestionnaire de Portefeuille : Synthèse et décisions ACHETER/GARDER/VENDRE

Workflow :
    Input : Liste d'entreprises + collections RAG + portefeuille actuel
    -> Analyse fondamentale des états financiers
    -> Recherche d'actualités et sentiment de marché
    -> Analyse technique des cours
    -> Décision finale avec allocation recommandée
    Output : Rapport complet avec recommandations claires

Example:
    >>> from api.agents.financial_crew import generate_financial_report
    >>>
    >>> report = generate_financial_report(
    ...     companies=["LVMH", "Hermès", "L'Oréal"],
    ...     collections=["lvmh_2023", "hermes_2023", "loreal_2023"],
    ...     portfolio={"LVMH": {"quantity": 10, "avg_price": 650}}
    ... )
    >>> print(report)
"""

from __future__ import annotations

from crewai import Agent, Task, Crew
from .tools import create_rag_tool, create_web_search_tool, create_news_indexer_tool
from typing import Dict, Any
from datetime import datetime


def create_financial_analysis_crew(
    companies: list[str],
    collections: list[str],
    portfolio: Dict[str, Any] = None,
) -> Crew:
    """
    Crée une équipe d'agents pour l'analyse financière

    Args:
        companies: Liste des entreprises à analyser
        collections: Collections RAG correspondantes
        portfolio: Portefeuille actuel (optionnel)

    Returns:
        Crew configuré
    """

    # Outils disponibles
    rag_tool = create_rag_tool()
    web_search_tool = create_web_search_tool()
    news_indexer_tool = create_news_indexer_tool()

    # 1. ANALYSTE FONDAMENTAL
    fundamental_analyst = Agent(
        role="Analyste Fondamental Senior",
        goal="Analyser en profondeur les états financiers et la santé économique des entreprises",
        backstory=(
            "Vous êtes un analyste financier chevronné avec 20 ans d'expérience dans l'analyse "
            "fondamentale. Vous excellez dans l'interprétation des bilans, comptes de résultat, "
            "et tableaux de flux de trésorerie. Vous identifiez les forces et faiblesses "
            "financières avec une précision remarquable."
        ),
        tools=[rag_tool],
        verbose=True,
        allow_delegation=False,
    )

    # 2. ANALYSTE ACTUALITÉS ET MARCHÉ
    market_news_analyst = Agent(
        role="Analyste Actualités et Tendances de Marché",
        goal="Identifier les actualités importantes et tendances de marché impactant les investissements",
        backstory=(
            "Vous êtes un expert en veille économique et analyse de marché avec une capacité "
            "exceptionnelle à détecter les signaux faibles et les tendances émergentes. "
            "Vous suivez l'actualité financière mondiale et savez distinguer le bruit "
            "des informations réellement impactantes pour les investissements."
        ),
        tools=[web_search_tool, news_indexer_tool],
        verbose=True,
        allow_delegation=False,
    )

    # 3. ANALYSTE TECHNIQUE
    technical_analyst = Agent(
        role="Analyste Technique",
        goal="Évaluer les tendances de prix, momentum et signaux techniques",
        backstory=(
            "Vous êtes un analyste technique expérimenté spécialisé dans l'identification "
            "des points d'entrée et de sortie optimaux. Vous maîtrisez les indicateurs techniques, "
            "les figures chartistes et l'analyse du sentiment de marché. Vous savez quand "
            "les conditions techniques sont favorables ou défavorables."
        ),
        tools=[],
        verbose=True,
        allow_delegation=False,
    )

    # 4. GESTIONNAIRE DE PORTEFEUILLE PEA
    portfolio_manager = Agent(
        role="Gestionnaire de Portefeuille PEA",
        goal="Prendre des décisions d'investissement optimales pour maximiser le rendement du PEA",
        backstory=(
            "Vous êtes un gestionnaire de portefeuille expérimenté spécialisé dans les PEA. "
            "Vous comprenez les contraintes réglementaires du PEA (actions européennes), "
            "et vous excellez dans la construction de portefeuilles équilibrés. Vous prenez "
            "des décisions claires (ACHETER/GARDER/VENDRE) basées sur une analyse complète "
            "combinant fondamentaux, technique et actualités."
        ),
        tools=[],
        verbose=True,
        allow_delegation=True,
    )

    # TÂCHES

    # Tâche 1: Analyse fondamentale
    fundamental_analysis_task = Task(
        description=(
            f"Analysez en profondeur les fondamentaux des entreprises suivantes : {', '.join(companies)}.\n\n"
            f"Pour chaque entreprise, utilisez la collection RAG correspondante : {', '.join(collections)}.\n\n"
            "Analysez les points suivants:\n"
            "1. Résultat opérationnel et tendances\n"
            "2. Chiffre d'affaires et croissance\n"
            "3. Rentabilité (marges, ROE, etc.)\n"
            "4. Endettement et structure financière\n"
            "5. Flux de trésorerie\n"
            "6. Valorisation (PE, PB, etc. si disponible)\n\n"
            "Fournissez une note de 1 à 10 pour la solidité fondamentale de chaque entreprise."
        ),
        agent=fundamental_analyst,
        expected_output=(
            "Rapport d'analyse fondamentale détaillé avec:\n"
            "- Métriques financières clés\n"
            "- Forces et faiblesses identifiées\n"
            "- Note fondamentale sur 10\n"
            "- Recommandation préliminaire par entreprise"
        ),
    )

    # Tâche 2: Recherche d'actualités
    news_research_task = Task(
        description=(
            f"Recherchez les actualités récentes et tendances de marché pour : {', '.join(companies)}.\n\n"
            "Pour chaque entreprise:\n"
            "1. Recherchez les actualités des 3 derniers mois\n"
            "2. Identifiez les événements importants (résultats, acquisitions, contrats, etc.)\n"
            "3. Analysez le sentiment général (positif/neutre/négatif)\n"
            "4. Indexez les actualités importantes dans la base RAG pour référence future\n\n"
            "Évaluez l'impact potentiel de ces actualités sur le cours de l'action."
        ),
        agent=market_news_analyst,
        expected_output=(
            "Rapport d'actualités avec:\n"
            "- Résumé des actualités clés par entreprise\n"
            "- Sentiment de marché (positif/neutre/négatif)\n"
            "- Événements à venir susceptibles d'impacter le cours\n"
            "- Risques et opportunités identifiés"
        ),
    )

    # Tâche 3: Analyse technique
    technical_analysis_task = Task(
        description=(
            f"Évaluez les conditions techniques pour : {', '.join(companies)}.\n\n"
            "Pour chaque entreprise, analysez:\n"
            "1. Tendance générale (haussière/baissière/neutre)\n"
            "2. Momentum actuel\n"
            "3. Niveaux de support et résistance importants\n"
            "4. Timing d'entrée (bon/mauvais moment pour acheter)\n"
            "5. Signaux techniques (surachat/survente)\n\n"
            "Fournissez une note technique de 1 à 10 pour chaque action."
        ),
        agent=technical_analyst,
        expected_output=(
            "Analyse technique avec:\n"
            "- État de la tendance par entreprise\n"
            "- Qualité du timing d'achat actuel\n"
            "- Note technique sur 10\n"
            "- Points d'entrée et de sortie suggérés"
        ),
        context=[fundamental_analysis_task, news_research_task],
    )

    # Tâche 4: Décision finale
    portfolio_decision_task = Task(
        description=(
            "En tant que gestionnaire de portefeuille PEA, synthétisez toutes les analyses et "
            "prenez une décision d'investissement claire pour chaque entreprise.\n\n"
            f"Entreprises à analyser: {', '.join(companies)}\n"
            f"Portefeuille actuel: {portfolio if portfolio else 'Nouveau portefeuille'}\n\n"
            "Pour chaque entreprise, fournissez:\n"
            "1. **DÉCISION**: ACHETER / GARDER / VENDRE (en gras et clair)\n"
            "2. **Conviction**: Faible / Moyenne / Forte\n"
            "3. **Allocation suggérée**: Pourcentage du portefeuille\n"
            "4. **Prix cible**: Si applicable\n"
            "5. **Stop-loss**: Niveau de protection\n"
            "6. **Horizon**: Court terme / Moyen terme / Long terme\n"
            "7. **Justification**: Résumé en 3-4 points clés\n\n"
            "Créez également une vue d'ensemble du portefeuille recommandé avec répartition sectorielle."
        ),
        agent=portfolio_manager,
        expected_output=(
            "RAPPORT D'INVESTISSEMENT FINAL avec:\n\n"
            "# Décisions par entreprise\n"
            "Pour chaque entreprise:\n"
            "- Décision claire (ACHETER/GARDER/VENDRE)\n"
            "- Niveau de conviction\n"
            "- Allocation recommandée\n"
            "- Prix cible et stop-loss\n"
            "- Justification synthétique\n\n"
            "# Recommandations de portefeuille\n"
            "- Répartition optimale\n"
            "- Niveau de risque global\n"
            "- Diversification sectorielle\n"
            "- Actions immédiates à prendre"
        ),
        context=[fundamental_analysis_task, news_research_task, technical_analysis_task],
    )

    # Créer et retourner le crew
    crew = Crew(
        agents=[
            fundamental_analyst,
            market_news_analyst,
            technical_analyst,
            portfolio_manager,
        ],
        tasks=[
            fundamental_analysis_task,
            news_research_task,
            technical_analysis_task,
            portfolio_decision_task,
        ],
        verbose=True,
    )

    return crew


def generate_financial_report(
    companies: list[str],
    collections: list[str],
    portfolio: Dict[str, Any] = None,
) -> str:
    """
    Génère un rapport financier complet avec recommandations d'investissement

    Cette fonction orchestre l'équipe complète d'agents pour produire
    un rapport d'analyse détaillé. Le rapport inclut :
    - Analyse fondamentale de chaque entreprise
    - Actualités récentes et sentiment de marché
    - Analyse technique et timing d'entrée
    - Décisions claires (ACHETER/GARDER/VENDRE)
    - Allocations recommandées par entreprise
    - Vue d'ensemble du portefeuille optimal

    Args:
        companies: Liste des noms d'entreprises à analyser
            Example: ["LVMH", "Hermès", "L'Oréal"]
        collections: Collections RAG correspondant à chaque entreprise
            Doit avoir la même longueur que companies
            Example: ["lvmh_2023", "hermes_2023", "loreal_2023"]
        portfolio: Portefeuille actuel (optionnel)
            Format: {"TICKER": {"quantity": X, "avg_price": Y}}
            Example: {"MC.PA": {"quantity": 10, "avg_price": 650.50}}

    Returns:
        Rapport d'analyse financière formaté en texte avec recommandations

    Raises:
        ValueError: Si le nombre d'entreprises ne correspond pas au nombre de collections
        CrewAIError: Si l'exécution des agents échoue

    Example:
        >>> from api.agents.financial_crew import generate_financial_report
        >>>
        >>> # Analyse de 3 entreprises du luxe
        >>> report = generate_financial_report(
        ...     companies=["LVMH", "Hermès", "Kering"],
        ...     collections=["lvmh_annual_2023", "hermes_annual_2023", "kering_annual_2023"],
        ...     portfolio={
        ...         "MC.PA": {"quantity": 5, "avg_price": 700.00},
        ...         "RMS.PA": {"quantity": 2, "avg_price": 1850.00}
        ...     }
        ... )
        >>>
        >>> # Le rapport contient les décisions pour chaque action
        >>> print(report)

    Note:
        L'exécution peut prendre plusieurs minutes (5-10 min) car les agents
        effectuent des recherches web, des analyses RAG et des calculs complexes.

        Pour un portefeuille existant, l'analyse prendra en compte vos positions
        actuelles pour suggérer des ajustements (renforcer, alléger, ou garder).

        Les recommandations sont générées par IA et ne constituent pas un conseil
        en investissement. Consultez toujours un professionnel agréé.
    """

    # Créer l'équipe
    crew = create_financial_analysis_crew(companies, collections, portfolio)

    # Exécuter l'analyse
    result = crew.kickoff()

    # Formatter le rapport
    report = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      RAPPORT D'ANALYSE FINANCIÈRE PEA                          ║
║                         {datetime.now().strftime('%d/%m/%Y %H:%M')}                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

📊 ENTREPRISES ANALYSÉES: {', '.join(companies)}
🗂️  COLLECTIONS UTILISÉES: {', '.join(collections)}
💼 PORTEFEUILLE: {'Existant' if portfolio else 'Nouveau'}

{result}

═══════════════════════════════════════════════════════════════════════════════

⚠️  AVERTISSEMENT:
Ce rapport est généré par une IA et ne constitue pas un conseil en investissement.
Les décisions d'investissement doivent être prises en tenant compte de votre profil
de risque, horizon d'investissement et situation financière personnelle.

Consulter un conseiller financier agréé pour des conseils personnalisés.

═══════════════════════════════════════════════════════════════════════════════
Généré par RAG Financial Analysis System v1.0
"""

    return report
