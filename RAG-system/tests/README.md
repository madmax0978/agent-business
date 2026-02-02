# Suite de Tests RAG-PEA System

Suite de tests complète pour vérifier toutes les fonctionnalités du système RAG-PEA.

## Structure des Tests

```
tests/
├── conftest.py                    # Configuration pytest et fixtures
├── pytest.ini                     # Configuration pytest
├── test_rag_workflow.py          # Tests RAG (indexation, recherche, génération)
├── test_financial_analysis.py   # Tests analyses financières
├── test_portfolio.py             # Tests gestion portefeuille
└── test_integration.py           # Tests end-to-end
```

## Prérequis

1. **API en cours d'exécution**:
```bash
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system
uvicorn api.main:app --reload
```

2. **Ollama en cours d'exécution** (pour tests de génération):
```bash
ollama serve
```

3. **Dépendances installées**:
```bash
pip install pytest requests
```

## Exécution des Tests

### Tous les tests
```bash
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system
pytest tests/ -v
```

### Par catégorie

**Tests RAG uniquement**:
```bash
pytest tests/test_rag_workflow.py -v
```

**Tests analyses financières**:
```bash
pytest tests/test_financial_analysis.py -v
```

**Tests portefeuille**:
```bash
pytest tests/test_portfolio.py -v
```

**Tests intégration end-to-end**:
```bash
pytest tests/test_integration.py -v
```

### Par marker

**Tests rapides (sans les tests lents)**:
```bash
pytest tests/ -v -m "not slow"
```

**Uniquement tests d'intégration**:
```bash
pytest tests/ -v -m integration
```

**Uniquement tests RAG**:
```bash
pytest tests/ -v -m rag
```

**Uniquement tests financiers**:
```bash
pytest tests/ -v -m financial
```

**Uniquement tests portefeuille**:
```bash
pytest tests/ -v -m portfolio
```

## Détails des Tests

### test_rag_workflow.py (8 tests)

Tests du système RAG complet:
- ✓ Health check API
- ✓ Liste des collections
- ✓ Informations collection
- ✓ Recherche sémantique
- ✓ Recherche avec génération (Ollama)
- ✓ Filtrage tableaux vs texte
- ✓ Qualité des résultats
- ✓ Gestion d'erreurs

### test_financial_analysis.py (10 tests)

Tests des analyses financières:
- ✓ Récupération infos marché (Yahoo Finance)
- ✓ Historique des cours
- ✓ Actualités d'entreprise
- ✓ Analyse de sentiment
- ✓ Analyse technique (RSI, MACD, MM)
- ✓ Analyse complète multi-sources
- ✓ Analyse multi-actions
- ✓ Qualité indicateurs techniques
- ✓ Gestion d'erreurs
- ✓ Fraîcheur des données

### test_portfolio.py (12 tests)

Tests de gestion de portefeuille:
- ✓ Ajout position
- ✓ Ajout positions multiples
- ✓ Calcul PRU (Prix de Revient Unitaire)
- ✓ Vente position (partielle/totale)
- ✓ Résumé portefeuille
- ✓ Score de santé (0-100)
- ✓ Recommandations rééquilibrage
- ✓ Détails position
- ✓ Contexte pour IA
- ✓ Gestion d'erreurs
- ✓ Calculs plus-values
- ✓ Persistance données

### test_integration.py (8 tests)

Tests d'intégration end-to-end:
- ✓ Workflow complet (données → RAG → agents → portefeuille)
- ✓ Intégration RAG → Agents CrewAI
- ✓ Boucle de feedback (portefeuille ↔ analyse)
- ✓ Intégration multi-sources (Yahoo + RAG + News + Technique)
- ✓ Mise à jour temps réel des prix
- ✓ Récupération après erreurs
- ✓ Performances sous charge
- ✓ Cohérence des données

## Rapport de Couverture

Pour générer un rapport de couverture:

```bash
pip install pytest-cov
pytest tests/ --cov=api --cov-report=html
```

Le rapport sera dans `htmlcov/index.html`

## Résultats Attendus

**Total**: ~38 tests

**Catégories**:
- RAG Workflow: 8 tests
- Financial Analysis: 10 tests
- Portfolio Management: 12 tests
- Integration E2E: 8 tests

**Temps d'exécution estimé**: 2-5 minutes (selon disponibilité API/Ollama)

## Dépannage

### API non accessible
```
FAILED - API non accessible - démarrez l'API avec 'uvicorn api.main:app'
```
→ Lancez l'API: `cd api && uvicorn main:app --reload`

### Ollama non disponible
```
SKIPPED - Ollama n'est pas disponible
```
→ Lancez Ollama: `ollama serve`

### Aucune collection RAG
```
SKIPPED - Aucune collection disponible
```
→ Indexez des documents: `python batch_index_documents.py`

### Tests échouent avec timeout
→ Augmentez le timeout dans conftest.py ou vérifiez la connexion réseau

## Notes Importantes

- Les tests utilisent des **données réelles** (LVMH, BNP, TotalEnergies, etc.)
- Les tests de portefeuille créent des utilisateurs de test temporaires
- Les tests n'affectent pas les données de production
- Certains tests peuvent être lents (marqués `@pytest.mark.slow`)
- Les tests d'intégration nécessitent que tous les services soient opérationnels
