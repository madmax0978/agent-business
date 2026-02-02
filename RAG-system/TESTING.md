# Guide de Tests - RAG-PEA System

**Version:** 1.0.0
**Dernière mise à jour:** Février 2026
**Coverage cible:** 80%+

---

## Table des Matières

- [Quick Start](#quick-start)
- [Structure des Tests](#structure-des-tests)
- [Types de Tests](#types-de-tests)
- [Suite de Tests Complète](#suite-de-tests-complète)
- [Commandes Utiles](#commandes-utiles)
- [Écrire de Nouveaux Tests](#écrire-de-nouveaux-tests)
- [Fixtures Pytest](#fixtures-pytest)
- [Mocking et Stubbing](#mocking-et-stubbing)
- [Coverage](#coverage)
- [CI/CD](#cicd)
- [Debugging Tests](#debugging-tests)
- [Best Practices](#best-practices)

---

## Quick Start

### Prérequis

```bash
# Installer dépendances de test
pip install pytest pytest-cov requests

# Démarrer l'API (dans un terminal séparé)
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api
python -m uvicorn main:app --reload

# Démarrer Ollama (optionnel, pour tests génération)
ollama serve
```

### Lancer tous les tests (2 minutes)

```bash
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system

# Méthode 1: Script dédié (recommandé)
./run_tests.sh

# Méthode 2: Pytest directement
pytest tests/ -v

# Méthode 3: Tests rapides uniquement (skip slow tests)
./run_tests.sh quick
```

### Résultat attendu

```
=================== RAG-PEA SYSTEM - SUITE DE TESTS COMPLÈTE ===================
Début des tests: 2026-02-01 14:30:00
================================================================================

tests/test_rag_workflow.py::TestRAGWorkflow::test_health_check PASSED        [ 5%]
tests/test_rag_workflow.py::TestRAGWorkflow::test_list_collections PASSED   [10%]
tests/test_portfolio.py::TestPortfolioManagement::test_add_position PASSED  [15%]
...
tests/test_integration.py::TestE2EWorkflow::test_complete_workflow PASSED   [100%]

===================== 38 passed, 0 failed in 125.34s ========================
✅ TOUS LES TESTS ONT RÉUSSI
```

---

## Structure des Tests

### Organisation des fichiers

```
RAG-system/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures globales
│   ├── pytest.ini                  # Configuration pytest
│   ├── README.md                   # Documentation tests
│   ├── test_rag_workflow.py        # Tests RAG (9 tests)
│   ├── test_portfolio.py           # Tests portfolio (12 tests)
│   ├── test_financial_analysis.py  # Tests analyses (8 tests)
│   └── test_integration.py         # Tests E2E (9 tests)
├── run_tests.sh                    # Script lanceur tests
└── pytest.ini                      # Config pytest (racine)
```

### Conventions de nommage

**Fichiers de test:**
- Pattern: `test_*.py`
- Exemple: `test_rag_workflow.py`, `test_portfolio.py`

**Classes de test:**
- Pattern: `TestNomDuModule`
- Exemple: `TestRAGWorkflow`, `TestPortfolioManagement`

**Fonctions de test:**
- Pattern: `test_ce_qui_est_teste`
- Exemple: `test_add_position`, `test_health_check`

**Fixtures:**
- Pattern: `nom_descriptif` (snake_case)
- Exemple: `api_base_url`, `test_tickers`, `sample_portfolio`

---

## Types de Tests

### 1. Tests Unitaires

**Objectif:** Tester une fonction/méthode isolée

**Caractéristiques:**
- Rapides (< 100ms)
- Aucune dépendance externe
- Mock toutes les I/O
- Test un seul comportement

**Exemple:**

```python
def test_calculate_portfolio_health_score():
    """Test unitaire: calcul score santé portefeuille"""

    # Arrange: Préparer les données
    positions = [
        {"ticker": "MC.PA", "quantity": 10, "gain_loss_percent": 15.5},
        {"ticker": "BNP.PA", "quantity": 20, "gain_loss_percent": -5.2},
    ]
    total_value = 15000

    # Act: Exécuter la fonction
    from api.services.portfolio_manager import calculate_health_score
    score = calculate_health_score(positions, total_value)

    # Assert: Vérifier le résultat
    assert 0 <= score <= 100, "Score doit être entre 0 et 100"
    assert score > 50, "Portfolio doit avoir un score décent"
```

### 2. Tests d'Intégration

**Objectif:** Tester l'interaction entre composants

**Caractéristiques:**
- Moyennement rapides (100ms - 5s)
- Dépendances contrôlées (DB test, API mocks)
- Test flux complet

**Exemple:**

```python
def test_add_position_integration(api_base_url):
    """Test intégration: ajouter position + récupérer portfolio"""

    # 1. Ajouter une position
    position_data = {
        "ticker": "MC.PA",
        "company_name": "LVMH",
        "quantity": 10,
        "price": 750.0
    }

    response = requests.post(
        f"{api_base_url}/portfolio/add",
        json=position_data
    )
    assert response.status_code == 200

    # 2. Vérifier que la position apparaît dans le portfolio
    response = requests.get(f"{api_base_url}/portfolio")
    portfolio = response.json()

    position = next(
        (p for p in portfolio['positions'] if p['ticker'] == "MC.PA"),
        None
    )

    assert position is not None, "Position doit être dans le portfolio"
    assert position['quantity'] == 10
    assert position['avg_price'] == 750.0
```

### 3. Tests End-to-End (E2E)

**Objectif:** Tester un workflow utilisateur complet

**Caractéristiques:**
- Lents (5s - 5min)
- Toutes dépendances réelles
- Simule comportement utilisateur réel

**Exemple:**

```python
def test_complete_portfolio_building_workflow(api_base_url):
    """Test E2E: workflow complet construction portfolio"""

    # 1. Vérifier santé API
    health = requests.get(f"{api_base_url}/health").json()
    assert health['status'] == 'healthy'

    # 2. Construire portfolio optimal
    build_request = {
        "budget": 10000,
        "risk_profile": "balanced",
        "sectors": ["luxury", "technology"],
        "min_companies": 5,
        "max_companies": 10
    }

    response = requests.post(
        f"{api_base_url}/build-portfolio",
        json=build_request,
        timeout=600  # 10 min max
    )

    assert response.status_code == 200
    result = response.json()

    # 3. Vérifier structure du résultat
    assert 'action_plan' in result
    assert 'budget' in result
    assert result['budget'] == 10000

    # 4. Ajouter chaque position au portfolio
    # (parsing action_plan pour extraire ordres d'achat)
    # ...

    # 5. Vérifier portfolio final
    portfolio = requests.get(f"{api_base_url}/portfolio").json()
    assert len(portfolio['positions']) >= 5
    assert portfolio['total_invested'] <= 10000
```

### 4. Tests de Performance

**Objectif:** Vérifier latence et throughput

**Exemple:**

```python
import time

def test_api_response_time(api_base_url):
    """Test performance: latence endpoints critiques"""

    endpoints = [
        "/health",
        "/portfolio",
        "/market/stock/MC.PA",
        "/collections",
    ]

    for endpoint in endpoints:
        start = time.time()
        response = requests.get(f"{api_base_url}{endpoint}")
        duration_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert duration_ms < 1000, f"{endpoint} trop lent: {duration_ms}ms"

        print(f"  {endpoint}: {duration_ms:.0f}ms ✓")
```

---

## Suite de Tests Complète

### test_rag_workflow.py (9 tests)

**Tests du système RAG (Retrieval-Augmented Generation)**

| Test | Description | Durée |
|------|-------------|-------|
| `test_health_check` | Vérifie API opérationnelle, Ollama accessible | < 1s |
| `test_list_collections` | Liste toutes collections ChromaDB | < 1s |
| `test_get_collection_info` | Info détaillée d'une collection | < 1s |
| `test_rag_search_semantic` | Recherche sémantique sans génération | 1-2s |
| `test_rag_search_with_generation` | Recherche + génération réponse Ollama | 5-10s |
| `test_rag_filter_tables` | Filtrage tableaux vs texte | 1-2s |
| `test_rag_quality_of_results` | Qualité scores similarité | 2-3s |
| `test_rag_error_handling` | Gestion erreurs (404, 422) | < 1s |
| `test_upload_document` | Upload et indexation PDF | 10-30s |

**Exécution:**

```bash
./run_tests.sh rag

# Ou
pytest tests/test_rag_workflow.py -v
```

**Exemple de sortie:**

```
tests/test_rag_workflow.py::TestRAGWorkflow::test_health_check PASSED

API Health Check: OK
  Status: healthy
  Version: 1.0.0
  Ollama disponible: True
  Collections existantes: 12

tests/test_rag_workflow.py::TestRAGWorkflow::test_rag_search_semantic PASSED

Recherche sémantique dans 'lvmh_2024':
  Question: Quel est le chiffre d'affaires de l'entreprise?
  Chunks trouvés: 5
  Meilleur score: 0.8542
  Temps de traitement: 0.47s

===================== 9 passed in 45.23s ======================
```

### test_portfolio.py (12 tests)

**Tests de gestion de portefeuille**

| Test | Description | Durée |
|------|-------------|-------|
| `test_add_position` | Ajout position au portfolio | < 1s |
| `test_add_position_duplicate` | Mise à jour position existante (recalcul PRU) | < 1s |
| `test_sell_position` | Vente partielle/totale position | < 1s |
| `test_sell_position_insufficient_qty` | Erreur vente quantité insuffisante | < 1s |
| `test_get_portfolio` | Récupération portfolio complet | 1-2s |
| `test_portfolio_summary` | Calcul total_value, gain/loss, etc. | 1-2s |
| `test_portfolio_health_score` | Score santé 0-100 + grade | < 1s |
| `test_portfolio_rebalance_recommendations` | Détection déséquilibres | < 1s |
| `test_portfolio_context_for_ai` | Génération contexte textuel pour LLM | < 1s |
| `test_position_details` | Détails position (portfolio + market data) | 1-2s |
| `test_update_current_prices` | Mise à jour prix via Yahoo Finance | 2-5s |
| `test_transaction_history` | Historique transactions par ticker | < 1s |

**Exécution:**

```bash
./run_tests.sh portfolio
```

**Key Tests Explained:**

#### `test_add_position_duplicate` - Calcul PRU

```python
def test_add_position_duplicate(api_base_url):
    """Test que l'ajout d'une position existante recalcule correctement le PRU"""

    # 1. Ajouter position initiale
    requests.post(f"{api_base_url}/portfolio/add", json={
        "ticker": "MC.PA",
        "company_name": "LVMH",
        "quantity": 10,
        "price": 700.0
    })

    # 2. Ajouter encore 5 actions à 800€
    requests.post(f"{api_base_url}/portfolio/add", json={
        "ticker": "MC.PA",
        "company_name": "LVMH",
        "quantity": 5,
        "price": 800.0
    })

    # 3. Vérifier PRU recalculé
    portfolio = requests.get(f"{api_base_url}/portfolio").json()
    position = next(p for p in portfolio['positions'] if p['ticker'] == "MC.PA")

    # PRU attendu: (10*700 + 5*800) / 15 = 733.33
    assert position['quantity'] == 15
    assert abs(position['avg_price'] - 733.33) < 0.1
```

#### `test_portfolio_health_score` - Scoring Algorithm

```python
def test_portfolio_health_score(api_base_url, sample_portfolio):
    """Test calcul score santé avec différents scénarios"""

    # Scenario 1: Portfolio bien diversifié (8 positions)
    # Score attendu: 85-95 (A)

    # Scenario 2: Portfolio concentré (2 positions)
    # Score attendu: 50-60 (D)

    # Scenario 3: Portfolio avec grosses pertes
    # Score attendu: 30-40 (F)

    response = requests.get(f"{api_base_url}/portfolio/health")
    health = response.json()

    assert 'score' in health
    assert 0 <= health['score'] <= 100
    assert 'grade' in health  # A+, A, B, C, D, F
    assert 'issues' in health
    assert 'recommendations' in health

    print(f"\nScore santé: {health['score']}/100 - Grade: {health['grade']}")
    print(f"Problèmes détectés: {len(health['issues'])}")
    for issue in health['issues']:
        print(f"  - {issue}")
```

### test_financial_analysis.py (8 tests)

**Tests d'analyse financière et market data**

| Test | Description | Durée |
|------|-------------|-------|
| `test_yahoo_finance_stock_info` | Récupération infos action (prix, P/E, etc.) | 1-2s |
| `test_yahoo_finance_historical_data` | Historique OHLCV | 2-3s |
| `test_yahoo_finance_cache` | Vérification cache LRU fonctionne | < 1s |
| `test_technical_analysis_indicators` | Calcul RSI, MACD, Bollinger | 2-3s |
| `test_technical_analysis_signals` | Détection signaux (golden cross, etc.) | 2-3s |
| `test_news_aggregation` | Récupération actualités | 2-5s |
| `test_sentiment_analysis` | Analyse sentiment avec Claude/GPT | 5-10s |
| `test_complete_analysis` | Analyse complète (market + news + tech) | 10-15s |

**Exécution:**

```bash
./run_tests.sh financial
```

**Key Tests Explained:**

#### `test_yahoo_finance_cache`

```python
def test_yahoo_finance_cache(api_base_url):
    """Test que le cache réduit la latence pour requêtes répétées"""

    ticker = "MC.PA"

    # 1. Premier appel (cache MISS)
    start = time.time()
    response1 = requests.get(f"{api_base_url}/market/stock/{ticker}")
    duration1_ms = (time.time() - start) * 1000

    # 2. Deuxième appel immédiat (cache HIT)
    start = time.time()
    response2 = requests.get(f"{api_base_url}/market/stock/{ticker}")
    duration2_ms = (time.time() - start) * 1000

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Cache HIT doit être beaucoup plus rapide
    assert duration2_ms < duration1_ms / 10, "Cache doit réduire latence 10x"

    print(f"\nCache performance:")
    print(f"  Premier appel (MISS): {duration1_ms:.0f}ms")
    print(f"  Second appel (HIT):   {duration2_ms:.0f}ms")
    print(f"  Speedup: {duration1_ms / duration2_ms:.1f}x")
```

#### `test_technical_analysis_signals`

```python
def test_technical_analysis_signals(api_base_url):
    """Test détection signaux techniques"""

    response = requests.get(
        f"{api_base_url}/analysis/technical/MC.PA",
        params={"period": "6mo"}
    )

    assert response.status_code == 200
    analysis = response.json()

    # Vérifier structure des signaux
    assert 'signals' in analysis
    signals = analysis['signals']

    # Signaux attendus
    expected_signals = [
        'golden_cross',
        'death_cross',
        'rsi_oversold',
        'rsi_overbought',
        'macd_bullish_cross',
        'macd_bearish_cross',
        'bb_breakout_up',
        'bb_breakout_down'
    ]

    for signal in expected_signals:
        assert signal in signals, f"Signal '{signal}' manquant"
        assert isinstance(signals[signal], bool)

    # Vérifier recommandation
    assert analysis['recommendation'] in ['BUY', 'HOLD', 'SELL']
    assert 0.0 <= analysis['confidence'] <= 1.0

    print(f"\nSignaux détectés pour MC.PA:")
    for signal, active in signals.items():
        if active:
            print(f"  ✓ {signal}")
```

### test_integration.py (9 tests)

**Tests end-to-end de workflows complets**

| Test | Description | Durée |
|------|-------------|-------|
| `test_complete_rag_workflow` | Upload PDF → Indexation → Query → Generation | 30-60s |
| `test_portfolio_building_workflow` | Build portfolio complet avec agents | 5-10min |
| `test_daily_portfolio_monitoring` | Workflow monitoring quotidien | 10-20s |
| `test_stock_analysis_workflow` | Analyse action complète avant achat | 15-30s |
| `test_rebalancing_workflow` | Détection + exécution rééquilibrage | 10-20s |
| `test_multiple_collections_query` | Query multi-collections | 5-10s |
| `test_error_recovery` | Récupération après erreurs (circuit breaker) | 5-10s |
| `test_concurrent_requests` | Requests concurrentes (thread-safe) | 5-10s |
| `test_data_consistency` | Cohérence données portfolio/market | 5-10s |

**Exécution:**

```bash
./run_tests.sh integration
```

**Key Test Explained:**

#### `test_complete_rag_workflow` - E2E RAG

```python
def test_complete_rag_workflow(api_base_url, test_document_path, cleanup_test_collections):
    """Test E2E complet du workflow RAG"""

    if not test_document_path:
        pytest.skip("Aucun document PDF de test disponible")

    collection_name = f"test_collection_{int(time.time())}"
    cleanup_test_collections.append(collection_name)

    # 1. Upload et indexation PDF
    print("\n1. Upload du document...")
    with open(test_document_path, 'rb') as f:
        files = {'file': f}
        data = {'collection_name': collection_name}
        response = requests.post(
            f"{api_base_url}/upload",
            files=files,
            data=data,
            timeout=300
        )

    assert response.status_code == 200
    index_result = response.json()
    assert index_result['success']
    print(f"   ✓ {index_result['total_chunks']} chunks indexés")

    # 2. Vérifier collection créée
    print("\n2. Vérification collection...")
    response = requests.get(f"{api_base_url}/collections/{collection_name}")
    assert response.status_code == 200
    print(f"   ✓ Collection '{collection_name}' créée")

    # 3. Query sémantique
    print("\n3. Recherche sémantique...")
    query = {
        "question": "Quels sont les principaux résultats?",
        "collection_name": collection_name,
        "n_results": 5,
        "generate_answer": False
    }
    response = requests.post(f"{api_base_url}/query", json=query)
    assert response.status_code == 200
    result = response.json()
    assert len(result['chunks']) > 0
    print(f"   ✓ {len(result['chunks'])} chunks pertinents trouvés")

    # 4. Génération réponse (si Ollama disponible)
    health = requests.get(f"{api_base_url}/health").json()
    if health.get('ollama_available'):
        print("\n4. Génération réponse...")
        query['generate_answer'] = True
        response = requests.post(f"{api_base_url}/query", json=query)
        result = response.json()
        assert result['answer'] is not None
        print(f"   ✓ Réponse générée ({len(result['answer'])} caractères)")

    # 5. Cleanup
    print("\n5. Nettoyage...")
    response = requests.delete(f"{api_base_url}/collections/{collection_name}")
    assert response.status_code == 200
    print(f"   ✓ Collection supprimée")

    print("\n✅ Workflow RAG complet réussi!")
```

---

## Commandes Utiles

### Script run_tests.sh

Le script `run_tests.sh` offre plusieurs modes d'exécution :

```bash
# Tous les tests
./run_tests.sh

# Tests rapides uniquement (skip @pytest.mark.slow)
./run_tests.sh quick

# Tests par catégorie
./run_tests.sh rag          # Tests RAG uniquement
./run_tests.sh financial    # Tests analyses financières
./run_tests.sh portfolio    # Tests portfolio
./run_tests.sh integration  # Tests E2E

# Tests avec coverage
./run_tests.sh coverage

# Aide
./run_tests.sh help
```

### Pytest directement

```bash
# Tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/test_rag_workflow.py -v
pytest tests/test_portfolio.py::TestPortfolioManagement::test_add_position -v

# Tests par marker
pytest -m "rag" -v          # Tests marqués @pytest.mark.rag
pytest -m "not slow" -v     # Skip tests lents

# Tests avec output détaillé
pytest tests/ -v -s         # -s : afficher print()

# Stopper au premier échec
pytest tests/ -x

# Relancer tests échoués
pytest tests/ --lf          # --last-failed

# Parallel execution (pytest-xdist)
pytest tests/ -n 4          # 4 workers

# Verbose logging
pytest tests/ -v --log-cli-level=DEBUG
```

### Coverage

```bash
# Coverage HTML report
pytest tests/ --cov=api --cov-report=html

# Ouvrir rapport dans navigateur
open htmlcov/index.html

# Coverage terminal
pytest tests/ --cov=api --cov-report=term-missing

# Coverage avec seuil minimum
pytest tests/ --cov=api --cov-fail-under=80
```

---

## Écrire de Nouveaux Tests

### Template Test Unitaire

```python
def test_function_name():
    """
    Description: Ce que le test vérifie

    Given: Contexte initial
    When: Action effectuée
    Then: Résultat attendu
    """
    # Arrange: Préparer données et mocks
    input_data = {"key": "value"}
    expected_output = {"result": "success"}

    # Act: Exécuter fonction testée
    from api.module import function_to_test
    result = function_to_test(input_data)

    # Assert: Vérifier résultat
    assert result == expected_output
    assert result["result"] == "success"
```

### Template Test API Endpoint

```python
def test_endpoint_name(api_base_url, check_api_running):
    """
    Test de l'endpoint POST /api/endpoint

    Vérifie:
    - Status code 200
    - Structure de la réponse
    - Validation des données
    """
    # Prepare request
    request_data = {
        "param1": "value1",
        "param2": 42
    }

    # Make request
    response = requests.post(
        f"{api_base_url}/api/endpoint",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )

    # Assertions
    assert response.status_code == 200, "Should return 200 OK"

    data = response.json()
    assert "result" in data, "Response must contain 'result' field"
    assert data["success"] is True

    # Print for debugging
    print(f"\nEndpoint response:")
    print(f"  Status: {response.status_code}")
    print(f"  Result: {data['result']}")
```

### Template Test avec Mock

```python
from unittest.mock import Mock, patch

def test_with_external_service_mocked():
    """Test avec mock d'un service externe (Yahoo Finance)"""

    # Mock Yahoo Finance response
    mock_response = {
        "ticker": "MC.PA",
        "current_price": 750.30,
        "pe_ratio": 24.5
    }

    # Patch the external call
    with patch('api.services.yahoo_finance_service.YahooFinanceService.get_stock_info') as mock_get:
        mock_get.return_value = mock_response

        # Test code that uses Yahoo Finance
        from api.services.portfolio_manager import PortfolioManager
        manager = PortfolioManager()
        result = manager.get_position_details("MC.PA")

        # Verify mock was called
        mock_get.assert_called_once_with("MC.PA")

        # Verify result uses mocked data
        assert result['market_data']['current_price'] == 750.30
```

### Template Test Paramétrisé

```python
import pytest

@pytest.mark.parametrize("ticker,expected_exchange", [
    ("MC.PA", "Paris"),
    ("BNP.PA", "Paris"),
    ("AAPL", "NASDAQ"),
    ("TSLA", "NASDAQ"),
])
def test_ticker_exchange_detection(ticker, expected_exchange):
    """Test détection de la bourse depuis le ticker"""
    from api.utils.ticker_utils import get_exchange

    exchange = get_exchange(ticker)
    assert exchange == expected_exchange
```

---

## Fixtures Pytest

### Fixtures Globales (conftest.py)

```python
# /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/tests/conftest.py

import pytest
import requests

@pytest.fixture(scope="session")
def api_base_url():
    """URL de base de l'API (session-scoped, créé une fois)"""
    return "http://localhost:8000"

@pytest.fixture(scope="session")
def check_api_running(api_base_url):
    """Vérifie que l'API est accessible avant de lancer les tests"""
    try:
        response = requests.get(f"{api_base_url}/health", timeout=5)
        if response.status_code != 200:
            pytest.skip("API non accessible")
    except requests.exceptions.RequestException:
        pytest.skip("API non accessible - démarrez avec 'uvicorn api.main:app'")
    return True

@pytest.fixture(scope="session")
def test_tickers():
    """Tickers pour tests (session-scoped)"""
    return {
        "lvmh": "MC.PA",
        "bnp": "BNP.PA",
        "total": "TTE.PA",
        "airbus": "AIR.PA",
        "loreal": "OR.PA",
    }

@pytest.fixture
def sample_portfolio():
    """Portfolio de test (function-scoped, recréé pour chaque test)"""
    return {
        "positions": [
            {"ticker": "MC.PA", "company_name": "LVMH", "quantity": 10, "avg_price": 700.0},
            {"ticker": "BNP.PA", "company_name": "BNP Paribas", "quantity": 50, "avg_price": 55.0},
        ],
        "total_invested": 9750.0,
    }

@pytest.fixture
def cleanup_test_collections(api_base_url):
    """Fixture cleanup: supprime collections de test après les tests"""
    test_collections = []

    yield test_collections  # Le test s'exécute ici

    # Cleanup après le test
    for collection_name in test_collections:
        try:
            requests.delete(f"{api_base_url}/collections/{collection_name}")
        except:
            pass
```

### Scopes de Fixtures

| Scope | Description | Quand utiliser |
|-------|-------------|----------------|
| `function` | Créée pour chaque test (défaut) | Données modifiables par le test |
| `class` | Créée une fois par classe de test | Données partagées dans une classe |
| `module` | Créée une fois par module de test | Setup coûteux partagé dans un fichier |
| `session` | Créée une seule fois pour toute la session | Setup très coûteux (DB, API connection) |

### Utilisation de Fixtures

```python
def test_with_fixtures(api_base_url, test_tickers, sample_portfolio):
    """Les fixtures sont injectées automatiquement par pytest"""

    # Utiliser api_base_url
    response = requests.get(f"{api_base_url}/health")

    # Utiliser test_tickers
    ticker = test_tickers['lvmh']

    # Utiliser sample_portfolio
    for position in sample_portfolio['positions']:
        print(position['ticker'])
```

---

## Mocking et Stubbing

### Quand utiliser des Mocks ?

**Mock les appels externes:**
- APIs externes (Yahoo Finance, NewsAPI, SerpAPI)
- Services tiers (Ollama, OpenAI)
- Opérations I/O coûteuses
- Services instables/lents

**Ne PAS mock:**
- Business logic (ce qu'on teste)
- Composants simples
- Database en test (utiliser DB test réelle)

### Mock Yahoo Finance

```python
from unittest.mock import patch, Mock

def test_portfolio_with_mocked_yahoo_finance():
    """Test avec Yahoo Finance mocké pour éviter appels réseau"""

    # Mock response structure
    mock_stock_info = {
        "ticker": "MC.PA",
        "current_price": 750.30,
        "previous_close": 745.20,
        "pe_ratio": 24.5,
        "dividend_yield": 2.1,
        "market_cap": 375000000000
    }

    # Patch YahooFinanceService.get_stock_info
    with patch('api.services.yahoo_finance_service.YahooFinanceService.get_stock_info') as mock_yf:
        mock_yf.return_value = mock_stock_info

        # Test code
        from api.services.portfolio_manager import PortfolioManager
        manager = PortfolioManager()
        manager.db.update_current_prices("test_user")

        # Verify mock was called
        assert mock_yf.called
        mock_yf.assert_called_with("MC.PA")
```

### Mock Ollama (LLM)

```python
def test_rag_generation_with_mocked_ollama():
    """Test génération RAG avec Ollama mocké"""

    mock_ollama_response = {
        "response": "Le chiffre d'affaires de LVMH en 2024 était de 86.2 milliards d'euros."
    }

    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_ollama_response
        mock_post.return_value.status_code = 200

        # Test RAG query avec génération
        response = requests.post(
            "http://localhost:8000/query",
            json={
                "question": "Quel est le CA de LVMH?",
                "collection_name": "lvmh_2024",
                "generate_answer": True
            }
        )

        data = response.json()
        assert "86.2" in data['answer']
```

### Mock Circuit Breaker

```python
def test_circuit_breaker_open():
    """Test comportement quand circuit breaker est ouvert"""

    from api.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

    breaker = CircuitBreaker(failure_threshold=3, timeout=60)

    # Simuler 3 échecs pour ouvrir le circuit
    for _ in range(3):
        try:
            breaker.call(lambda: 1/0)  # Division par zéro
        except ZeroDivisionError:
            pass

    # Circuit doit être ouvert maintenant
    assert breaker.is_open

    # Tentative d'appel doit lever CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        breaker.call(lambda: "ok")

    assert "Circuit breaker is OPEN" in str(exc_info.value)
```

### Stub Database

```python
def test_with_in_memory_db():
    """Test avec DB SQLite en mémoire"""

    from api.database.portfolio_db import PortfolioDatabase

    # Créer DB en mémoire (disparaît après le test)
    db = PortfolioDatabase(db_path=":memory:")

    # Ajouter données de test
    db.add_position("MC.PA", "LVMH", 10, 700.0, "test_user")

    # Tester
    portfolio = db.get_portfolio("test_user")
    assert len(portfolio) == 1
    assert portfolio[0]['ticker'] == "MC.PA"
```

---

## Coverage

### Mesurer la Coverage

```bash
# Coverage avec rapport HTML
pytest tests/ --cov=api --cov-report=html

# Ouvrir rapport
open htmlcov/index.html
```

### Interpréter les Résultats

```
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
api/__init__.py                        10      0   100%
api/config.py                         142     12    92%   245-250, 310-315
api/exceptions.py                     187     23    88%   423-430, 501-508
api/logging_config.py                 128      8    94%   387-392
api/main.py                           245     45    82%   156-162, 234-240, ...
api/middleware.py                     134     18    87%   245-250, 301-305
api/models.py                          89      3    97%   234-236
api/rag_manager.py                    156     28    82%   189-195, 267-272
api/services/portfolio_manager.py     187     34    82%   145-150, 223-230
api/services/yahoo_finance_service.py 234     42    82%   298-305, 367-372
api/utils/circuit_breaker.py          156     12    92%   389-395
-----------------------------------------------------------------
TOTAL                                1668    225    87%
```

**Objectifs:**
- **Minimum:** 70% coverage globale
- **Cible:** 80% coverage globale
- **Modules critiques:** 90%+ (config, exceptions, middleware)

**Fichiers à ignorer:**
- Scripts (ingestion.py, generator.py, etc.)
- Exemples (example_*.py)
- Tests eux-mêmes

### Identifier Code Non Testé

```bash
# Coverage avec liste des lignes manquantes
pytest tests/ --cov=api --cov-report=term-missing

# Output:
# api/main.py     245    45    82%   156-162, 234-240, 401-405
#                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                                     Lignes non testées
```

### Améliorer la Coverage

**1. Identifier fonctions non testées:**

```bash
# Coverage par fonction
pytest tests/ --cov=api --cov-report=term:skip-covered
```

**2. Écrire tests pour lignes manquantes:**

```python
# Si ligne 156-162 de main.py non testée:
def test_error_case_not_covered():
    """Test cas d'erreur manquant dans la coverage"""

    # Reproduire le cas qui trigger lignes 156-162
    response = requests.post(
        "http://localhost:8000/endpoint",
        json={"invalid": "data"}
    )

    assert response.status_code == 400  # Bad Request
```

**3. Vérifier branches conditionnelles:**

```python
# Code à tester:
def calculate_score(value):
    if value > 100:
        return "high"
    elif value > 50:
        return "medium"
    else:
        return "low"

# Tests pour 100% branch coverage:
def test_calculate_score_high():
    assert calculate_score(150) == "high"

def test_calculate_score_medium():
    assert calculate_score(75) == "medium"

def test_calculate_score_low():
    assert calculate_score(25) == "low"

# Sans ces 3 tests, branch coverage serait < 100%
```

---

## CI/CD

### GitHub Actions Template

Créer `.github/workflows/tests.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      # Optionnel: PostgreSQL pour tests
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Start API
      run: |
        cd api
        python -m uvicorn main:app &
        sleep 5  # Wait for API to start

    - name: Run tests
      run: |
        pytest tests/ -v --cov=api --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

### Pre-commit Hook

Créer `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Run tests before commit
echo "Running tests before commit..."

# Quick tests only
pytest tests/ -m "not slow" -v

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Commit aborted."
    exit 1
fi

echo "✅ Tests passed. Proceeding with commit."
exit 0
```

```bash
chmod +x .git/hooks/pre-commit
```

---

## Debugging Tests

### Techniques de Debugging

**1. Print debugging:**

```python
def test_with_prints(api_base_url):
    response = requests.get(f"{api_base_url}/portfolio")
    data = response.json()

    print(f"\n=== DEBUG ===")
    print(f"Status: {response.status_code}")
    print(f"Data: {data}")
    print(f"=============\n")

    assert response.status_code == 200
```

```bash
# Afficher prints
pytest tests/ -v -s  # -s = capture disabled
```

**2. Breakpoint debugging:**

```python
def test_with_breakpoint(api_base_url):
    response = requests.get(f"{api_base_url}/portfolio")

    # Pause ici
    import pdb; pdb.set_trace()

    # Ou avec breakpoint() (Python 3.7+)
    breakpoint()

    assert response.status_code == 200
```

**Commandes PDB:**
- `n` (next): ligne suivante
- `c` (continue): continuer jusqu'au prochain breakpoint
- `p variable`: afficher valeur variable
- `l` (list): afficher code autour du breakpoint
- `q` (quit): quitter debugger

**3. Verbose logging:**

```python
import logging

def test_with_logging(api_base_url):
    logging.basicConfig(level=logging.DEBUG)

    response = requests.get(f"{api_base_url}/portfolio")
    # Logs détaillés s'afficheront
```

**4. Pytest verbose output:**

```bash
# Maximum verbosity
pytest tests/ -vv

# Avec logs
pytest tests/ -v --log-cli-level=DEBUG
```

### Debugging Tests Échoués

**1. Relancer uniquement tests échoués:**

```bash
# Première exécution: certains tests échouent
pytest tests/

# Relancer uniquement les échecs
pytest tests/ --lf  # --last-failed
```

**2. Stopper au premier échec:**

```bash
pytest tests/ -x  # Stop at first failure
```

**3. Verbose traceback:**

```bash
pytest tests/ --tb=long  # Long traceback
pytest tests/ --tb=short # Short traceback
```

**4. Capturer screenshots (pour tests UI futurs):**

```python
def test_ui_with_screenshot(api_base_url):
    try:
        # Test code
        assert False, "Simulated failure"
    except AssertionError:
        # Capture state for debugging
        import json
        state = requests.get(f"{api_base_url}/portfolio").json()
        with open('/tmp/test_failure_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        raise
```

---

## Best Practices

### 1. Structure AAA (Arrange-Act-Assert)

```python
def test_good_structure():
    # Arrange: Setup test data
    ticker = "MC.PA"
    expected_fields = ["ticker", "current_price", "pe_ratio"]

    # Act: Execute function under test
    response = requests.get(f"http://localhost:8000/market/stock/{ticker}")
    data = response.json()

    # Assert: Verify results
    assert response.status_code == 200
    for field in expected_fields:
        assert field in data
```

### 2. Noms de Tests Descriptifs

```python
# ❌ Bad
def test_1():
    ...

# ✅ Good
def test_add_position_updates_portfolio_total_value():
    ...

# ✅ Good
def test_yahoo_finance_returns_404_for_invalid_ticker():
    ...
```

### 3. Un Concept par Test

```python
# ❌ Bad: teste trop de choses
def test_portfolio_everything():
    # Test add
    # Test sell
    # Test health
    # Test rebalance
    # ...

# ✅ Good: tests séparés
def test_add_position():
    ...

def test_sell_position():
    ...

def test_portfolio_health_score():
    ...
```

### 4. Tests Indépendants

```python
# ❌ Bad: tests dépendants
def test_step_1():
    global result
    result = create_something()

def test_step_2():
    # Dépend de test_step_1
    use_result(result)

# ✅ Good: tests indépendants
def test_step_1():
    result = create_something()
    assert result is not None

def test_step_2():
    result = create_something()  # Recréé dans chaque test
    use_result(result)
```

### 5. Cleanup Automatique

```python
# ✅ Good: cleanup avec fixture
@pytest.fixture
def temp_portfolio(api_base_url):
    user_id = f"test_user_{time.time()}"

    yield user_id  # Test s'exécute

    # Cleanup après le test
    requests.delete(f"{api_base_url}/portfolio/{user_id}")
```

### 6. Messages d'Erreur Clairs

```python
# ❌ Bad
assert portfolio['total_value'] > 0

# ✅ Good
assert portfolio['total_value'] > 0, \
    f"Total value should be positive, got {portfolio['total_value']}"
```

### 7. Éviter Magic Numbers

```python
# ❌ Bad
assert len(positions) == 5

# ✅ Good
EXPECTED_POSITION_COUNT = 5
assert len(positions) == EXPECTED_POSITION_COUNT, \
    f"Expected {EXPECTED_POSITION_COUNT} positions"
```

### 8. Documenter Tests Complexes

```python
def test_complex_portfolio_rebalancing():
    """
    Test algorithme de rééquilibrage complexe

    Scénario:
    1. Portfolio initial: 70% LVMH, 30% BNP (déséquilibré)
    2. Détection: position LVMH > 25% (seuil)
    3. Recommandation: vendre 20% LVMH, acheter autres positions
    4. Après rééquilibrage: distribution équilibrée

    Algorithme testé:
    - Détection concentration excessive
    - Calcul quantités à vendre/acheter
    - Vérification contraintes (min 5 positions, max 20% par position)
    """
    # Test implementation
    ...
```

### 9. Utiliser Markers

```python
# Marquer tests lents
@pytest.mark.slow
def test_full_portfolio_build():
    # 10 min test
    ...

# Marquer tests nécessitant API externe
@pytest.mark.requires_yahoo_finance
def test_stock_data():
    ...

# Skip si condition non remplie
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not available")
def test_rag_generation():
    ...
```

```bash
# Exécuter par marker
pytest -m "not slow"  # Skip tests lents
pytest -m "requires_yahoo_finance"  # Seulement tests Yahoo Finance
```

### 10. Coverage != Qualité

```python
# ❌ Bad: 100% coverage mais test inutile
def test_add(self):
    result = add(2, 2)
    # Pas d'assertion !

# ✅ Good: coverage + assertions utiles
def test_add(self):
    assert add(2, 2) == 4
    assert add(-1, 1) == 0
    assert add(0, 0) == 0
```

---

## Checklist Tests

Avant de soumettre une PR:

- [ ] Tous les tests passent (`./run_tests.sh`)
- [ ] Coverage >= 80% (`./run_tests.sh coverage`)
- [ ] Nouveaux tests ajoutés pour nouvelles features
- [ ] Tests suivent convention AAA
- [ ] Noms de tests descriptifs
- [ ] Pas de tests skip sans raison
- [ ] Cleanup fixtures approprié
- [ ] Documentation tests complexes
- [ ] Pas de magic numbers
- [ ] Messages d'erreur clairs

---

## Ressources

**Documentation Pytest:**
- https://docs.pytest.org/en/stable/

**Plugins utiles:**
- `pytest-cov`: Coverage
- `pytest-xdist`: Parallel execution
- `pytest-timeout`: Timeout tests
- `pytest-mock`: Better mocking

**Installation:**

```bash
pip install pytest pytest-cov pytest-xdist pytest-timeout pytest-mock
```

---

## Conclusion

Cette suite de tests couvre:
- **38 tests** au total
- **4 catégories** (RAG, Portfolio, Financial, Integration)
- **80%+ coverage** sur code critique
- **Tests E2E** pour workflows complets

**Pour contribuer:**
1. Écrire tests avant code (TDD)
2. Viser 80%+ coverage sur nouveaux modules
3. Documenter tests complexes
4. Utiliser fixtures pour code réutilisable
5. Mock services externes

**Questions?** Consultez:
- [ARCHITECTURE.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/ARCHITECTURE.md) - Comprendre le système
- [CONTRIBUTING.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/CONTRIBUTING.md) - Comment contribuer
- [TROUBLESHOOTING.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/TROUBLESHOOTING.md) - Résoudre problèmes

---

**Document version:** 1.0.0
**Dernière mise à jour:** Février 2026
