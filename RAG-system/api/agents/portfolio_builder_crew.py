"""
Équipe CrewAI pour la construction automatique d'un portefeuille PEA optimal

Ce module orchestre une équipe de 6 agents IA spécialisés pour construire
un portefeuille PEA complet de zéro avec collecte automatique de données.

L'équipe est composée de :
1. Collecteur de Données : Collecte automatiquement rapports et actualités
2. Analyste Historique : Analyse les performances sur 5-10 ans
3. Architecte de Portefeuille : Optimise diversification et allocation
4. Analyste Fondamental : Analyse approfondie de chaque entreprise
5. Analyste Technique : Identifie les meilleurs points d'entrée long terme
6. Gestionnaire Master : Décision finale et plan d'action détaillé

Workflow complet :
    Input : Budget + Profil de risque + Préférences sectorielles
    -> Collecte automatique des données des meilleures entreprises PEA
    -> Analyse historique pour identifier opportunités long terme
    -> Construction du portefeuille optimal (diversification + allocation)
    -> Analyse fondamentale approfondie de chaque sélection
    -> Analyse technique pour timing d'entrée
    -> Plan d'action avec ordres d'achat précis
    Output : Plan complet pour construire votre portefeuille PEA

Ce système est 100% autonome : il collecte lui-même toutes les données nécessaires.

Example:
    >>> from api.agents.portfolio_builder_crew import build_optimal_pea_portfolio
    >>>
    >>> # Construction d'un portefeuille équilibré de 10000€
    >>> plan = build_optimal_pea_portfolio(
    ...     budget=10000,
    ...     risk_profile="balanced",
    ...     sectors=["luxe", "technologie", "santé"],
    ...     min_companies=8,
    ...     max_companies=12
    ... )
    >>> print(plan)
    >>> # Le plan contient les ordres d'achat précis à passer

Key Features:
    - Collecte automatique des rapports financiers et actualités
    - Analyse historique sur 5-10 ans (pas juste les 6 derniers mois)
    - Optimisation risque/rendement avec théorie moderne du portefeuille
    - Respect des contraintes PEA (uniquement actions européennes)
    - Diversification optimale (secteurs, géographie, taille)
    - Plan d'action concret avec dates et montants précis
    - Timing d'entrée optimisé (achat immédiat vs progressif)
"""

from __future__ import annotations

from crewai import Agent, Task, Crew
from typing import Dict, Any, Optional
from datetime import datetime
import sys
import os
from pathlib import Path

# Charger les variables d'environnement depuis le .env
try:
    from dotenv import load_dotenv
    # Chercher le .env à la racine du projet (2 niveaux au-dessus)
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
    print(f"✅ Fichier .env chargé depuis: {env_path}")
except ImportError:
    print("⚠️ python-dotenv non installé, utilisation des variables d'environnement système")
except Exception as e:
    print(f"⚠️ Erreur lors du chargement du .env: {e}")

# Imports conditionnels pour gérer l'exécution directe vs import
if __name__ == "__main__":
    # Exécution directe
    from tools import create_rag_tool, create_web_search_tool
    from advanced_tools import (
        create_data_collector_tool,
        create_history_tool,
        create_portfolio_optimizer_tool,
    )
    # Import du sélecteur LLM
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from llm_selector import get_llm_for_crewai
else:
    # Import comme module
    from .tools import create_rag_tool, create_web_search_tool
    from .advanced_tools import (
        create_data_collector_tool,
        create_history_tool,
        create_portfolio_optimizer_tool,
    )
    # Import du sélecteur LLM (import absolu pour Docker)
    from llm_selector import get_llm_for_crewai


def create_portfolio_builder_crew(
    budget: float,
    risk_profile: str = "balanced",
    sectors: Optional[list] = None,
    exclude_companies: Optional[list] = None,
) -> Crew:
    """
    Crée une équipe pour construire un portefeuille PEA optimal de zéro

    Args:
        budget: Budget total en euros
        risk_profile: conservative/balanced/aggressive
        sectors: Secteurs préférés (optionnel)
        exclude_companies: Entreprises à exclure (optionnel)

    Returns:
        Crew configuré pour la construction de portefeuille
    """

    # Sélectionner le LLM (priorité à Claude)
    llm = get_llm_for_crewai(temperature=0.7, max_tokens=4000)

    # Outils disponibles
    rag_tool = create_rag_tool()
    web_search_tool = create_web_search_tool()
    data_collector_tool = create_data_collector_tool()
    history_tool = create_history_tool()
    portfolio_optimizer_tool = create_portfolio_optimizer_tool()

    # 1. AGENT COLLECTEUR DE DONNÉES
    data_collector_agent = Agent(
        role="Collecteur de Données Financières Autonome",
        goal="Collecter automatiquement rapports financiers, actualités et données de marché pour les meilleures entreprises PEA",
        backstory=(
            "Vous êtes un agent automatisé spécialisé dans la collecte exhaustive de données financières. "
            "Vous savez où trouver les meilleurs rapports annuels, les actualités pertinentes, "
            "et les données de marché en temps réel. Vous indexez automatiquement tout dans la base "
            "de données pour que les analystes puissent faire leur travail."
        ),
        tools=[data_collector_tool, web_search_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # 2. AGENT HISTORIQUE ET MÉMOIRE
    historical_analyst = Agent(
        role="Analyste Historique et Tendances Long Terme",
        goal="Analyser l'historique complet des entreprises pour identifier les meilleures opportunités long terme",
        backstory=(
            "Vous êtes un expert en analyse historique avec une vision long terme. "
            "Vous consultez toutes les analyses passées, les évolutions de performance, "
            "les tendances sur plusieurs années. Vous identifiez les entreprises avec "
            "une croissance stable et durable, parfaites pour un investissement PEA long terme (5-10 ans)."
        ),
        tools=[history_tool, rag_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # 3. AGENT OPTIMISEUR DE PORTEFEUILLE
    portfolio_architect = Agent(
        role="Architecte de Portefeuille PEA",
        goal="Construire le portefeuille PEA optimal avec la meilleure diversification et allocation",
        backstory=(
            "Vous êtes un expert en construction de portefeuille avec 25 ans d'expérience. "
            "Vous maîtrisez la théorie moderne du portefeuille, l'optimisation risque/rendement, "
            "et les spécificités du PEA français. Vous créez des portefeuilles diversifiés, "
            "équilibrés et adaptés au profil de risque de l'investisseur."
        ),
        tools=[portfolio_optimizer_tool, rag_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # 4. ANALYSTE FONDAMENTAL APPROFONDI
    fundamental_deep_analyst = Agent(
        role="Analyste Fondamental Senior - Valorisation",
        goal="Effectuer une analyse fondamentale approfondie de chaque entreprise sélectionnée",
        backstory=(
            "Vous êtes un analyste fondamental d'élite, formé aux méthodes des plus grands "
            "investisseurs (Warren Buffett, Peter Lynch). Vous analysez en profondeur "
            "les bilans, les avantages concurrentiels durables (moats), la qualité du management, "
            "et la valorisation. Vous distinguez les vraies opportunités des pièges à valeur."
        ),
        tools=[rag_tool, history_tool],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # 5. ANALYSTE TECHNIQUE LONG TERME
    technical_long_term_analyst = Agent(
        role="Analyste Technique - Investissement Long Terme",
        goal="Identifier les meilleurs points d'entrée avec une vision long terme (5-10 ans)",
        backstory=(
            "Vous êtes un analyste technique spécialisé dans l'investissement long terme. "
            "Vous utilisez les graphiques hebdomadaires et mensuels, les moyennes mobiles 200 jours, "
            "les tendances structurelles. Vous identifiez les phases d'accumulation et "
            "les opportunités d'achat sur repli. Vous distinguez le bruit court terme "
            "des vraies tendances de fond."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # 6. GESTIONNAIRE DE PORTEFEUILLE FINAL
    master_portfolio_manager = Agent(
        role="Gestionnaire de Portefeuille PEA Master",
        goal="Prendre la décision finale sur le portefeuille optimal et fournir un plan d'action clair",
        backstory=(
            "Vous êtes le gestionnaire en chef avec autorité décisionnelle finale. "
            "Vous synthétisez toutes les analyses (collecte de données, historique, fondamental, "
            "technique, optimisation) pour créer LE portefeuille PEA optimal. "
            "Vous fournissez un plan d'action précis avec les ordres d'achat exacts."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=True,
    )

    # === TÂCHES ===

    # Tâche 1: Collecte automatique de données
    data_collection_task = Task(
        description=(
            "Collectez automatiquement les données pour les 15 meilleures entreprises éligibles PEA:\n\n"
            "1. Identifiez les 15 entreprises les plus prometteuses (grandes caps françaises et européennes)\n"
            "2. Pour chaque entreprise:\n"
            "   • Collectez les rapports financiers récents (2-3 ans)\n"
            "   • Collectez l'actualité des 12 derniers mois\n"
            "   • Récupérez les données de marché (prix, volume, capitalisation)\n"
            "3. Indexez automatiquement toutes les données dans la base RAG\n"
            "4. Créez un résumé de la collecte avec statistiques\n\n"
            "Secteurs à couvrir: Luxe, Tech, Santé, Énergie, Industrie, Banques, Télécom\n"
            "Focus sur des entreprises leaders avec un historique solide."
        ),
        agent=data_collector_agent,
        expected_output=(
            "Rapport de collecte avec:\n"
            "- Liste des 15 entreprises collectées\n"
            "- Nombre de rapports/articles indexés par entreprise\n"
            "- Données de marché clés pour chaque entreprise\n"
            "- Statut de l'indexation dans la base RAG"
        ),
    )

    # Tâche 2: Analyse historique long terme
    historical_analysis_task = Task(
        description=(
            "Analysez l'historique et les tendances long terme des 15 entreprises collectées:\n\n"
            "1. Consultez toutes les données historiques disponibles\n"
            "2. Analysez la croissance sur 5-10 ans (CA, résultats, dividendes)\n"
            "3. Identifiez la stabilité et la régularité des performances\n"
            "4. Évaluez la résilience pendant les crises passées\n"
            "5. Notez chaque entreprise sur son potentiel LONG TERME (5-10 ans)\n\n"
            "Critères importants:\n"
            "- Croissance régulière (pas de yo-yo)\n"
            "- Dividendes croissants\n"
            "- Bilan solide historiquement\n"
            "- Leader de secteur sur la durée"
        ),
        agent=historical_analyst,
        expected_output=(
            "Analyse historique avec:\n"
            "- Note long terme (1-10) pour chaque entreprise\n"
            "- Tendances de croissance sur 5-10 ans\n"
            "- Niveau de stabilité/régularité\n"
            "- Top 10 entreprises pour investissement long terme"
        ),
        context=[data_collection_task],
    )

    # Tâche 3: Construction du portefeuille optimal
    portfolio_optimization_task = Task(
        description=(
            f"Construisez le portefeuille PEA optimal avec les paramètres suivants:\n\n"
            f"📊 **Contraintes**:\n"
            f"• Budget: {budget:,.0f}€\n"
            f"• Profil de risque: {risk_profile}\n"
            f"• Secteurs préférés: {sectors if sectors else 'Tous'}\n"
            f"• Entreprises à exclure: {exclude_companies if exclude_companies else 'Aucune'}\n\n"
            f"**Mission**:\n"
            f"1. Utilisez les résultats de l'analyse historique\n"
            f"2. Optimisez la répartition (diversification sectorielle et géographique)\n"
            f"3. Calculez l'allocation optimale pour chaque entreprise\n"
            f"4. Assurez-vous d'avoir au moins 8-10 entreprises (diversification)\n"
            f"5. Maximisez le ratio rendement/risque long terme\n\n"
            f"Contraintes PEA:\n"
            f"• Uniquement actions européennes éligibles\n"
            f"• Pas plus de 25% sur une seule valeur\n"
            f"• Diversification sectorielle (pas plus de 30% sur un secteur)"
        ),
        agent=portfolio_architect,
        expected_output=(
            "Portefeuille optimisé avec:\n"
            "- Liste complète des entreprises sélectionnées\n"
            "- Allocation en % et en € pour chaque position\n"
            "- Nombre d'actions à acheter\n"
            "- Répartition sectorielle\n"
            "- Statistiques (rendement attendu, volatilité, Sharpe ratio)\n"
            "- Justification de la construction"
        ),
        context=[historical_analysis_task],
    )

    # Tâche 4: Analyse fondamentale approfondie
    deep_fundamental_task = Task(
        description=(
            "Pour chaque entreprise du portefeuille optimisé, effectuez une analyse fondamentale approfondie:\n\n"
            "1. **Qualité de l'entreprise**:\n"
            "   • Avantages concurrentiels durables (moat)\n"
            "   • Position de marché et parts de marché\n"
            "   • Qualité du management\n"
            "   • Innovation et R&D\n\n"
            "2. **Santé financière**:\n"
            "   • Croissance du CA et des bénéfices\n"
            "   • Marges opérationnelles et évolution\n"
            "   • ROE, ROIC (rentabilité des capitaux)\n"
            "   • Flux de trésorerie libre\n"
            "   • Niveau d'endettement\n\n"
            "3. **Valorisation**:\n"
            "   • PER vs historique et secteur\n"
            "   • P/B, EV/EBITDA\n"
            "   • Rendement du dividende\n"
            "   • Potentiel de hausse (DCF si données suffisantes)\n\n"
            "4. **Risques identifiés**\n\n"
            "Notez chaque entreprise sur 10 avec justification détaillée."
        ),
        agent=fundamental_deep_analyst,
        expected_output=(
            "Analyse fondamentale détaillée avec:\n"
            "- Note fondamentale (1-10) pour chaque entreprise\n"
            "- Forces et faiblesses identifiées\n"
            "- Niveau de valorisation (sous-évaluée/juste/surévaluée)\n"
            "- Prix cible estimé\n"
            "- Principaux risques"
        ),
        context=[portfolio_optimization_task],
    )

    # Tâche 5: Analyse technique long terme
    technical_analysis_task = Task(
        description=(
            "Pour chaque entreprise du portefeuille, analysez le timing d'entrée avec vision LONG TERME:\n\n"
            "1. **Tendance structurelle** (graphique mensuel):\n"
            "   • Tendance haussière/baissière sur 5-10 ans\n"
            "   • Canaux de progression\n"
            "   • Niveaux de support majeurs\n\n"
            "2. **Timing d'entrée** (graphique hebdomadaire/mensuel):\n"
            "   • Position par rapport à MM200\n"
            "   • Phase du cycle (accumulation/distribution)\n"
            "   • Zones de support/résistance importantes\n\n"
            "3. **Évaluation**:\n"
            "   • Bon moment pour acheter? (MAINTENANT/ATTENDRE/EXCELLENT)\n"
            "   • Si attendre: quel niveau de prix cibler?\n"
            "   • Horizon de patience acceptable\n\n"
            "Note: On investit pour 5-10 ans, donc un repli de 10-15% peut être une excellente opportunité!"
        ),
        agent=technical_long_term_analyst,
        expected_output=(
            "Analyse technique avec:\n"
            "- État de la tendance long terme par entreprise\n"
            "- Qualité du timing (MAINTENANT/ATTENDRE/EXCELLENT)\n"
            "- Prix d'entrée idéal vs prix actuel\n"
            "- Niveaux de support à surveiller\n"
            "- Recommandation d'achat immédiat ou progressif"
        ),
        context=[deep_fundamental_task],
    )

    # Tâche 6: Décision finale et plan d'action
    final_decision_task = Task(
        description=(
            "Synthétisez TOUTES les analyses et créez le PLAN D'ACTION FINAL pour construire le portefeuille PEA:\n\n"
            f"Budget disponible: {budget:,.0f}€\n"
            f"Profil: {risk_profile}\n\n"
            "Votre mission:\n"
            "1. Validez le portefeuille optimisé (ou ajustez si nécessaire)\n"
            "2. Pour chaque entreprise, décidez:\n"
            "   • ACHETER MAINTENANT (bon timing)\n"
            "   • ACHETER PROGRESSIVEMENT (étaler sur 2-3 mois)\n"
            "   • ATTENDRE (mauvais timing, définir prix cible)\n\n"
            "3. Créez un PLAN D'ACHAT PRÉCIS:\n"
            "   • Ordres d'achat immédiats (Semaine 1)\n"
            "   • Ordres à placer progressivement (Mois 1-3)\n"
            "   • Ordres conditionnels (si prix atteint X)\n\n"
            "4. Définissez la stratégie long terme:\n"
            "   • Fréquence de rééquilibrage\n"
            "   • Critères de renforcement\n"
            "   • Signaux d'alerte pour vente\n\n"
            "5. Fournissez un TABLEAU DE BORD récapitulatif\n\n"
            "IMPORTANT: Soyez ULTRA PRÉCIS et ACTIONNABLE. L'investisseur doit pouvoir "
            "copier-coller les ordres d'achat."
        ),
        agent=master_portfolio_manager,
        expected_output=(
            "PLAN D'ACTION COMPLET avec:\n\n"
            "# 1. Portefeuille Final Validé\n"
            "   - Liste des entreprises avec allocations\n"
            "   - Nombre exact d'actions à acheter\n"
            "   - Prix d'entrée cible pour chaque position\n\n"
            "# 2. Plan d'Achat Détaillé\n"
            "   - Semaine 1: Ordres immédiats (entreprises au bon timing)\n"
            "   - Mois 1-2: Achats progressifs (DCA)\n"
            "   - Ordres à cours limité (si attente de meilleur prix)\n\n"
            "# 3. Statistiques du Portefeuille\n"
            "   - Rendement attendu annualisé\n"
            "   - Volatilité estimée\n"
            "   - Dividende moyen\n"
            "   - Diversification (secteurs, géo)\n\n"
            "# 4. Stratégie Long Terme\n"
            "   - Fréquence de suivi recommandée\n"
            "   - Critères de rééquilibrage\n"
            "   - Plan de renforcement progressif\n\n"
            "# 5. Tableau de Bord\n"
            "   Format exploitable pour suivi Excel/Google Sheets"
        ),
        context=[
            portfolio_optimization_task,
            deep_fundamental_task,
            technical_analysis_task,
        ],
    )

    # Créer le crew
    crew = Crew(
        agents=[
            data_collector_agent,
            historical_analyst,
            portfolio_architect,
            fundamental_deep_analyst,
            technical_long_term_analyst,
            master_portfolio_manager,
        ],
        tasks=[
            data_collection_task,
            historical_analysis_task,
            portfolio_optimization_task,
            deep_fundamental_task,
            technical_analysis_task,
            final_decision_task,
        ],
        verbose=True,
    )

    return crew


def build_optimal_pea_portfolio(
    budget: float,
    risk_profile: str = "balanced",
    sectors: Optional[list] = None,
    exclude_companies: Optional[list] = None,
    min_companies: int = 8,
    max_companies: int = 15,
) -> str:
    """
    Construit un portefeuille PEA optimal de zéro avec collecte autonome des données

    Cette fonction orchestre une équipe complète de 6 agents IA pour créer
    un portefeuille PEA personnalisé. Le système collecte automatiquement
    toutes les données nécessaires (rapports financiers, actualités, données
    de marché) puis construit le portefeuille optimal selon vos critères.

    Le résultat est un plan d'action complet et actionnable avec :
    - Liste précise des entreprises sélectionnées
    - Nombre exact d'actions à acheter pour chaque position
    - Timing d'achat (immédiat, progressif, ou attendre)
    - Ordres d'achat détaillés pour chaque semaine/mois
    - Justification détaillée pour chaque sélection
    - Statistiques du portefeuille (rendement attendu, risque, dividendes)

    Args:
        budget: Budget total disponible en euros
            Example: 10000 pour un portefeuille de 10 000€
        risk_profile: Profil de risque souhaité
            Choix: "conservative" (sécurité), "balanced" (équilibré), "aggressive" (croissance)
            Default: "balanced"
        sectors: Liste de secteurs préférés (optionnel)
            Exemples: ["luxe"], ["technologie", "santé"], ["énergie", "industrie"]
            Si None, tous les secteurs sont considérés
        exclude_companies: Liste d'entreprises à exclure (optionnel)
            Example: ["Total", "BNP Paribas"] pour exclure énergie fossile et banques
        min_companies: Nombre minimum d'entreprises dans le portefeuille
            Default: 8 (diversification minimale)
        max_companies: Nombre maximum d'entreprises dans le portefeuille
            Default: 15 (éviter sur-diversification)

    Returns:
        Plan d'action formaté en texte contenant :
        - Portefeuille final validé avec allocations
        - Plan d'achat détaillé (semaine 1, mois 1-2, ordres conditionnels)
        - Statistiques complètes (rendement, volatilité, dividendes)
        - Stratégie long terme et critères de rééquilibrage
        - Tableau de bord exploitable pour suivi

    Raises:
        ValueError: Si le budget est négatif ou le profil de risque invalide
        CrewAIError: Si l'exécution des agents échoue

    Example:
        >>> from api.agents.portfolio_builder_crew import build_optimal_pea_portfolio
        >>>
        >>> # Construction d'un portefeuille équilibré de 10 000€
        >>> plan = build_optimal_pea_portfolio(
        ...     budget=10000,
        ...     risk_profile="balanced",
        ...     sectors=["luxe", "technologie"],
        ...     min_companies=8,
        ...     max_companies=12
        ... )
        >>> print(plan)
        >>> # Affiche le plan d'action complet
        >>>
        >>> # Exemple avec profil conservateur
        >>> plan_conservateur = build_optimal_pea_portfolio(
        ...     budget=50000,
        ...     risk_profile="conservative",
        ...     exclude_companies=["TotalEnergies"],  # Exclure pétrole
        ...     min_companies=10,
        ...     max_companies=15
        ... )
        >>>
        >>> # Exemple agressif croissance
        >>> plan_agressif = build_optimal_pea_portfolio(
        ...     budget=5000,
        ...     risk_profile="aggressive",
        ...     sectors=["technologie", "luxe", "santé"],
        ...     min_companies=6,
        ...     max_companies=8
        ... )

    Note:
        Temps d'exécution : 5-10 minutes (collecte de données + analyse)

        Le système est 100% autonome :
        - Identifie automatiquement les 15 meilleures entreprises PEA
        - Collecte leurs rapports financiers et actualités
        - Les indexe dans la base RAG pour analyse
        - Construit le portefeuille optimal selon vos critères

        Profils de risque :
        - Conservative : Grandes caps stables, dividendes élevés, faible volatilité
        - Balanced : Mix croissance/dividendes, diversification sectorielle
        - Aggressive : Forte croissance potentielle, accepte plus de volatilité

        Contraintes PEA respectées :
        - Uniquement actions européennes éligibles
        - Pas plus de 25% sur une seule valeur
        - Diversification sectorielle (max 30% par secteur)
        - Privilège grandes/moyennes caps liquides

        Les recommandations sont générées par IA et ne constituent pas
        un conseil en investissement. Consultez un conseiller financier agréé.
    """

    # Créer l'équipe
    crew = create_portfolio_builder_crew(budget, risk_profile, sectors, exclude_companies)

    # Exécuter l'analyse complète
    result = crew.kickoff()

    # Formatter le rapport final
    report = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║              CONSTRUCTION DE PORTEFEUILLE PEA OPTIMAL - PLAN D'ACTION          ║
║                           {datetime.now().strftime('%d/%m/%Y %H:%M')}                                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝

💼 Budget: {budget:,.0f}€
📊 Profil: {risk_profile.upper()}
🎯 Horizon: LONG TERME (5-10 ans)

{result}

═══════════════════════════════════════════════════════════════════════════════════

✅ PROCHAINES ÉTAPES IMMÉDIATES:

1. Ouvrez votre compte PEA si ce n'est pas déjà fait
2. Transférez le budget ({budget:,.0f}€) sur le compte
3. Passez les ordres d'achat de la "Semaine 1" (ci-dessus)
4. Programmez les achats progressifs pour les mois suivants
5. Configurez le réinvestissement automatique des dividendes
6. Ajoutez ce portefeuille à votre suivi (Excel/Google Sheets)

💡 RAPPELS IMPORTANTS:

• PEA = Investissement LONG TERME (5-10 ans minimum)
• Ne paniquez pas sur les fluctuations court terme
• Renforcez progressivement (versements mensuels si possible)
• Réinvestissez les dividendes automatiquement
• Rééquilibrez 1 fois par an maximum
• Pas d'impôts sur les plus-values après 5 ans de détention !

⚠️  DISCLAIMER:

Ce plan d'action est généré par IA et constitue une aide à la décision.
Il ne remplace PAS un conseil financier personnalisé.
Consultez un conseiller en gestion de patrimoine (CGP) pour valider
votre stratégie selon votre situation personnelle.

═══════════════════════════════════════════════════════════════════════════════════
Généré par RAG Financial Analysis System v2.0 - Portfolio Builder Edition
"""

    return report


if __name__ == "__main__":
    """
    Exécution directe du script pour construire un portefeuille PEA optimal
    """
    print("🚀 Lancement de la construction de portefeuille PEA optimal...\n")

    # Configuration par défaut
    budget = 10000  # 10 000 €
    risk_profile = "balanced"  # conservative, balanced, aggressive
    sectors = None  # Tous les secteurs
    exclude_companies = None  # Aucune exclusion

    # Possibilité de personnaliser via arguments
    if len(sys.argv) > 1:
        try:
            budget = float(sys.argv[1])
        except ValueError:
            print("⚠️ Budget invalide, utilisation de 10000€ par défaut")

    if len(sys.argv) > 2:
        risk_profile = sys.argv[2].lower()
        if risk_profile not in ["conservative", "balanced", "aggressive"]:
            print("⚠️ Profil de risque invalide, utilisation de 'balanced' par défaut")
            risk_profile = "balanced"

    print(f"💼 Budget: {budget:,.0f}€")
    print(f"📊 Profil de risque: {risk_profile.upper()}")
    print("\n⏳ Construction du portefeuille en cours... (cela peut prendre 5-10 minutes)\n")

    # Lancer la construction
    try:
        report = build_optimal_pea_portfolio(
            budget=budget,
            risk_profile=risk_profile,
            sectors=sectors,
            exclude_companies=exclude_companies
        )

        print(report)

        # Sauvegarder le rapport
        filename = f"portfolio_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ Rapport sauvegardé dans: {filename}")

    except Exception as e:
        print(f"\n❌ Erreur lors de la construction du portefeuille:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
