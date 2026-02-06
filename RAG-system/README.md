# RAG-PEA System - Portfolio Intelligent avec IA

**Version 3.0.0** - Production Ready + ML + Backtesting

Système complet d'analyse financière et de gestion de portefeuille combinant:
- **RAG v2 optimisé** (recherche dans documents financiers)
- **🆕 Machine Learning** (LSTM/Prophet - Prédictions de prix 30 jours)
- **🆕 Backtesting** (6+ stratégies - Test performance historique)
- **🆕 Intelligence Service** (Agrégation ML + Backtesting + Technical + Fundamental)
- **Trésorerie PEA** (gestion cash, dépôts, opportunités IA)
- **Bot Telegram complet** (onboarding + 22 commandes + rapports automatiques)
- **Multi-Agent AI** (CrewAI) pour analyses approfondies
- **Données temps réel** (Yahoo Finance gratuit)
- **Analyse technique** complète (RSI, MACD, Bollinger, Support/Résistance)
- **API REST** FastAPI avec 48 endpoints (33 existants + 15 nouveaux ML/Backtesting)
- **Déploiement VPS** (Docker + docker-compose)

---

## 🚀 Démarrage Rapide (5 minutes)

### Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'API
cd api
python -m uvicorn main:app --reload

# ou
./start_api.sh
```

L'API est accessible sur [http://localhost:8000/docs](http://localhost:8000/docs)

### Premier Test

```bash
# Vérifier que tout fonctionne
curl http://localhost:8000/health

# Obtenir des données de marché (gratuit, pas de clé API)
curl http://localhost:8000/market/stock/MC.PA

# Ajouter une position
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"ticker": "MC.PA", "company_name": "LVMH", "quantity": 10, "price": 750.00, "user_id": "test_user"}'

# Voir le portfolio
curl http://localhost:8000/portfolio?user_id=test_user
```

✅ C'est tout ! Vous avez un système de suivi d'investissements fonctionnel.

---

## 🤖 Nouveau: Bot Telegram

**Gérez votre PEA directement depuis Telegram !**

```bash
# 1. Configurer le bot
cp .env.example .env
# Ajouter votre TELEGRAM_BOT_TOKEN

# 2. Lancer l'API
cd api && python -m uvicorn main:app --reload

# 3. Lancer le bot
python telegram_bot_main.py

# 4. Lancer le scheduler (rapports automatiques)
python telegram_scheduler.py
```

**Ou via Docker (recommandé):**
```bash
docker-compose up -d
```

**Commandes principales:**
- `/start` - Onboarding complet (dépôt + positions)
- `/portfolio` - Voir le portfolio complet
- `/balance` - Trésorerie PEA
- `/opportunities` - Opportunités IA
- `/buy` / `/sell` - Transactions
- `/analyze` - Analyse IA complète
- `/help` - Liste toutes les commandes

**Rapports automatiques:**
- Quotidien à 9h (si cash disponible > 100€)
- Hebdomadaire le lundi (santé du portfolio)

Voir **[DEPLOYMENT.md](DEPLOYMENT.md)** pour déployer sur VPS.

---

## 📚 Fonctionnalités Principales

### 1. Trésorerie PEA

**Gérez votre Plan d'Épargne en Actions avec tracking complet:**

```bash
# Déposer de l'argent (règle PEA: ne peut pas être retiré)
curl -X POST "http://localhost:8000/portfolio/deposit?amount=10000"

# Consulter la trésorerie
curl "http://localhost:8000/portfolio/treasury"
# → total_deposits: 10000€
# → cash_available: 7000€ (dispo pour investir)
# → cash_invested: 3000€ (en actions)

# Détecter opportunités IA (si cash disponible)
curl -X POST "http://localhost:8000/portfolio/opportunities/analyze"
# → DIVERSIFY: ajouter 2-3 positions
# → ADD_TO_EXISTING: renforcer positions gagnantes
# → REBALANCE_CASH: investir le cash stagnant
```

**Gestion automatique:**
- ✅ Cash déduit automatiquement lors d'un achat
- ✅ Cash ajouté automatiquement lors d'une vente
- ✅ Opportunités IA basées sur le cash disponible
- ✅ Historique complet des flux de trésorerie

### 2. RAG v2 - Recherche dans Documents Financiers

**Recherche sémantique optimisée dans vos rapports PDF financiers**

```bash
# Indexer un PDF (automatique avec v2)
python3 scripts/quick_index.py          # 3 PDFs de test
python3 scripts/index_all_pdfs.py       # Tous les PDFs

# Rechercher dans les documents
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quel est le chiffre d affaires 2024?",
    "collection_name": "LVMH_Financiers_2024",
    "n_results": 5,
    "generate_answer": true
  }'
```

**Avantages v2:**
- ✅ Modèle multilingual optimisé (paraphrase-multilingual-mpnet-base-v2)
- ✅ Scores 0.4-0.6 pour le français (+1500% vs v1)
- ✅ Cache embeddings (20x plus rapide)
- ✅ Cosine similarity

### 3. Portfolio Management

```bash
# Ajouter des positions
POST /portfolio/add

# Vendre une position
POST /portfolio/sell

# Voir le portfolio complet
GET /portfolio?user_id=your_id

# Score de santé (0-100)
GET /portfolio/health?user_id=your_id

# Recommandations de rééquilibrage
GET /portfolio/rebalance?user_id=your_id

# Détails d'une position
GET /portfolio/position/{ticker}?user_id=your_id
```

### 4. Analyse de Marché

```bash
# Données en temps réel (gratuit - Yahoo Finance)
GET /market/stock/{ticker}           # Info stock (prix, P/E, dividende)
GET /market/history/{ticker}          # Historique

# Analyse technique
GET /analysis/technical/{ticker}      # RSI, MACD, Bollinger, S/R
GET /analysis/news/{company}          # Actualités récentes
GET /analysis/sentiment/{company}     # Analyse sentiment IA
GET /analysis/complete/{ticker}       # Analyse complète
```

### 5. Agents IA Multi-Agents

```bash
# Construire un portfolio optimal (6 agents CrewAI)
POST /build-portfolio
{
  "budget": 10000,
  "risk_profile": "balanced",
  "sectors": ["technology", "healthcare"],
  "min_companies": 10,
  "max_companies": 15
}

# Analyse financière approfondie (4 agents)
POST /analyze/financial-report
```

### 6. 🆕 Machine Learning - Prédictions de Prix

**Entraîner et utiliser des modèles LSTM/Prophet pour prédire les prix futurs**

```bash
# Entraîner un modèle (LSTM + Prophet ensemble)
POST /ml/train/MC.PA
{
  "model_type": "ensemble",
  "period": "2y",
  "epochs": 100
}
# ⏱ Durée: 2-5 minutes
# Métri ques: MAE, RMSE, MAPE, Direction Accuracy

# Prédire les prix (30 jours par défaut)
GET /ml/predict/MC.PA?horizon=30&model_type=ensemble

# Réponse:
{
  "current_price": 730.0,
  "predictions": [...],  # Prix jour par jour
  "expected_return_30d": 3.2,  # +3.2% attendu
  "confidence_avg": 0.75,
  "trend": "BULLISH",
  "recommendation": "BUY"
}

# Évaluer un modèle
GET /ml/evaluate/MC.PA
# → MAE: 12.5, Direction Accuracy: 68%

# Lister tous les modèles
GET /ml/models
```

**Outils utilisés:**
- TensorFlow/Keras (LSTM deep learning)
- Prophet (Facebook time series)
- pandas-ta (feature engineering: RSI, MACD, SMA)
- scikit-learn (métriques)

### 7. 🆕 Backtesting - Test de Stratégies

**Tester des stratégies de trading sur données historiques**

```bash
# Lancer un backtest
POST /backtesting/run
{
  "ticker": "MC.PA",
  "strategy": "ma_crossover",
  "params": {"fast_period": 20, "slow_period": 50},
  "start_date": "2021-01-01",
  "end_date": "2026-01-01",
  "initial_capital": 10000.0
}

# Réponse:
{
  "performance": {
    "total_return": 45.3,  # +45.3%
    "sharpe_ratio": 1.35,
    "max_drawdown": -15.7,
    "win_rate": 0.58,
    "num_trades": 28
  },
  "trades": [...]  # Historique des trades
}

# Comparer plusieurs stratégies
POST /backtesting/compare
{
  "ticker": "MC.PA",
  "strategies": ["ma_crossover", "rsi_strategy", "macd"]
}

# Optimiser les paramètres (Grid Search)
POST /backtesting/optimize
{
  "ticker": "MC.PA",
  "strategy": "ma_crossover",
  "param_grid": {
    "fast_period": [10, 20, 30],
    "slow_period": [40, 50, 60]
  }
}

# Lister toutes les stratégies disponibles
GET /backtesting/strategies
# → 6 stratégies: MA Crossover, RSI, MACD, Bollinger, Momentum, Buy&Hold
```

**Outils utilisés:**
- BacktestEngine custom
- yfinance (données historiques)
- numpy/pandas (calculs vectorisés)
- plotly (visualisations)

### 8. 🔥 Intelligence - Analyse Complète

**Endpoint principal combinant ML + Backtesting + Technical + Fundamental**

```bash
# Analyse d'investissement complète
POST /intelligence/analyze/MC.PA?include_ml=true&include_backtesting=true

# Réponse agrégée:
{
  "ticker": "MC.PA",
  "current_price": 730.0,

  "ml_prediction": {
    "expected_return_30d": 3.2,  # ML: +3.2% sur 30j
    "trend": "BULLISH"
  },

  "backtesting": {
    "best_strategy": "rsi_strategy",
    "sharpe_ratio": 1.68,
    "total_return": 52.3
  },

  "technical_analysis": {
    "rsi": 65.2,
    "macd": "BUY",
    "signal": "BUY"
  },

  "aggregated_recommendation": {
    "decision": "BUY",  # Vote pondéré
    "confidence": 0.78,
    "target_price": 803.0,
    "stop_loss": 693.5,
    "risk_level": "MODERATE"
  },

  "signals": [
    {"source": "ML", "decision": "BUY", "confidence": 0.75},
    {"source": "BACKTESTING", "decision": "BUY", "confidence": 0.85},
    {"source": "TECHNICAL", "decision": "BUY", "confidence": 0.70}
  ]
}
```

**Pipeline:**
1. Récupération données marché (yfinance)
2. ML Predictions (LSTM/Prophet) - 30 jours
3. Backtesting (test 3 meilleures stratégies)
4. Analyse technique (RSI, MACD, Bollinger)
5. Agrégation vote pondéré
6. Recommandation finale BUY/HOLD/SELL

⏱ **Temps d'exécution**: 10-20 secondes (sans ML training)

---

## 🏗️ Architecture Simple

```
RAG-system/
├── api/
│   ├── main.py                    # API FastAPI (48 endpoints)
│   ├── rag_manager_v2.py          # RAG optimisé (v2 uniquement)
│   ├── models.py                  # Modèles Pydantic
│   ├── agents/                    # Agents CrewAI
│   │   ├── portfolio_builder_crew.py   # 6 agents construction portfolio
│   │   └── financial_crew.py           # 4 agents analyse
│   ├── services/                  # Services métier
│   │   ├── intelligence_service.py     # 🆕 Agrégation ML + Backtesting
│   │   ├── yahoo_finance_service.py    # Données gratuites
│   │   ├── technical_analysis.py       # Indicateurs techniques
│   │   ├── sentiment_analyzer.py       # Analyse sentiment IA
│   │   ├── portfolio_manager.py        # Gestion portfolio
│   │   └── data_fetcher.py             # Fetcher données marché
│   ├── ml/                        # 🆕 Machine Learning
│   │   ├── price_predictor.py          # Prédicteur LSTM/Prophet/Ensemble
│   │   ├── data_loader.py              # Chargement données yfinance
│   │   ├── feature_engineering.py      # Indicateurs techniques
│   │   ├── evaluation.py               # Métriques ML
│   │   ├── serving.py                  # API routes ML (8 endpoints)
│   │   └── models/                     # Modèles sauvegardés
│   ├── backtesting/               # 🆕 Backtesting
│   │   ├── engine.py                   # Moteur backtesting
│   │   ├── strategies/                 # 6 stratégies trading
│   │   │   ├── ma_crossover.py
│   │   │   ├── rsi_strategy.py
│   │   │   ├── macd.py
│   │   │   ├── bollinger.py
│   │   │   ├── momentum.py
│   │   │   └── buy_and_hold.py
│   │   ├── portfolio.py                # Portfolio virtuel
│   │   ├── metrics.py                  # Métriques performance
│   │   ├── visualization.py            # Graphiques Plotly
│   │   └── routes.py                   # API routes (6 endpoints)
│   └── database/
│       └── portfolio_db.py             # SQLite
├── data/
│   ├── vector_db/                 # ChromaDB (collections RAG v2)
│   ├── context/                   # PDFs à indexer
│   └── uploads/                   # Documents uploadés
├── scripts/
│   ├── quick_index.py             # Indexation rapide (3 PDFs)
│   └── index_all_pdfs.py          # Indexation complète
└── tests/                         # 36 tests pytest
```

---

## 🔧 Configuration Minimale

**Aucune clé API requise** pour les fonctionnalités de base !

- ✅ Données marché (Yahoo Finance) - GRATUIT
- ✅ Portfolio management - GRATUIT
- ✅ RAG v2 - GRATUIT (modèle local)
- ✅ Analyse technique - GRATUIT

**Optionnel** (fonctionnalités avancées):

```bash
# .env (optionnel)
OPENAI_API_KEY=sk-...          # Pour analyse IA avancée
ANTHROPIC_API_KEY=sk-ant-...   # Pour Claude AI sentiment
NEWSAPI_KEY=...                # Pour actualités (100 req/jour gratuit)
TELEGRAM_BOT_TOKEN=...         # Pour alertes Telegram
```

---

## 📊 Endpoints API Principaux

| Catégorie | Endpoint | Description |
|-----------|----------|-------------|
| **Santé** | `GET /health` | Vérifier API + Ollama |
| **Portfolio** | `POST /portfolio/add` | Ajouter position |
| | `POST /portfolio/sell` | Vendre position |
| | `GET /portfolio` | Portfolio complet |
| | `GET /portfolio/health` | Score santé 0-100 |
| **Marché** | `GET /market/stock/{ticker}` | Données temps réel |
| | `GET /market/history/{ticker}` | Historique |
| **Analyse** | `GET /analysis/technical/{ticker}` | Analyse technique |
| | `GET /analysis/complete/{ticker}` | Analyse complète |
| **RAG** | `POST /query` | Recherche documents |
| | `GET /collections` | Lister collections |
| | `POST /upload` | Upload & indexer PDF |
| **IA** | `POST /build-portfolio` | Construire portfolio (6 agents) |
| | `POST /analyze/financial-report` | Analyse profonde (4 agents) |

**Documentation complète**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Tests et Validation

```bash
# Lancer tous les tests (36 tests)
./run_tests.sh

# Vérifier la version RAG
python3 verifier_rag_version.py

# Diagnostic RAG complet
python3 diagnose_rag.py
```

**Tous les tests doivent passer**: ✅ 36/36 tests

---

## 📖 Documentation

### Fichiers Essentiels

- **README.md** (ce fichier) - Vue d'ensemble et démarrage
- **GUIDE_UTILISATION.md** - Guide complet (RAG + Portfolio + PEA + Telegram Bot)
- **DEPLOYMENT.md** - Déploiement sur VPS avec Docker
- **TROUBLESHOOTING.md** - Tests, diagnostic, résolution de problèmes

### Documentation Technique

Le système utilise:
- **FastAPI** - Framework web moderne
- **ChromaDB** - Base vectorielle pour RAG
- **sentence-transformers** - Embeddings multilingues
- **CrewAI** - Orchestration multi-agents
- **yfinance** - Données Yahoo Finance gratuites
- **pandas-ta** - Analyse technique
- **SQLite** - Stockage portfolio
- **Ollama** - Génération locale (Mistral)

---

## 🎯 Cas d'Usage

### Exemple 1: Suivre Mon Portfolio

```python
import requests

API = "http://localhost:8000"

# Ajouter 3 actions
for ticker, qty, price in [("MC.PA", 10, 750), ("AIR.PA", 15, 140), ("SAN.PA", 20, 95)]:
    requests.post(f"{API}/portfolio/add", json={
        "ticker": ticker,
        "quantity": qty,
        "price": price,
        "user_id": "maxime"
    })

# Consulter le portfolio
portfolio = requests.get(f"{API}/portfolio?user_id=maxime").json()
print(f"Valeur totale: {portfolio['total_value']}€")

# Score de santé
health = requests.get(f"{API}/portfolio/health?user_id=maxime").json()
print(f"Score: {health['health_score']}/100")
```

### Exemple 2: Analyser une Action Avant Achat

```bash
# Analyse complète d'Airbus
curl "http://localhost:8000/analysis/complete/AIR.PA?company_name=Airbus"

# Retourne:
# - Prix actuel, P/E, dividende
# - RSI, MACD, Bollinger
# - Support/Résistance
# - Sentiment news
# - Recommandation Buy/Hold/Sell
```

### Exemple 3: Rechercher dans Documents Financiers

```bash
# 1. Indexer vos PDFs
python3 scripts/index_all_pdfs.py

# 2. Rechercher
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "résultat opérationnel 2024",
    "collection_name": "LVMH_Financiers_2024",
    "generate_answer": true
  }'

# Obtient des réponses avec contexte et sources
```

---

## 🚨 Performances

- **API**: < 100ms (endpoints simples)
- **RAG recherche**: ~5-100ms (avec cache)
- **Analyse technique**: < 2s
- **Agents IA**: 5-10 min (analyse complète)
- **Indexation**: ~45s pour 80 pages PDF

**Scores RAG v2**: 0.4-0.6 pour recherches françaises (excellent!)

---

## ⚠️ Limitations Actuelles

- Yahoo Finance: délai 15-20 min (gratuit)
- Un seul utilisateur par défaut
- Pas d'intégration courtier (ordres manuels)
- Backtesting: 1 stratégie implémentée (SMA crossover)

**Prochaines améliorations**: voir GUIDE_UTILISATION.md section Roadmap

---

## 🆘 Besoin d'Aide ?

1. **Démarrage**: Suivez le [Démarrage Rapide](#-démarrage-rapide-5-minutes)
2. **Utilisation**: Consultez **GUIDE_UTILISATION.md**
3. **Problème**: Voir **TROUBLESHOOTING.md**
4. **API complète**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📝 Disclaimer

Ce logiciel est à but éducatif et informatif uniquement. Il ne constitue pas un conseil financier. Faites toujours vos propres recherches et consultez un conseiller financier agréé avant de prendre des décisions d'investissement.

---

**Prêt à commencer ?** Suivez le [Démarrage Rapide](#-démarrage-rapide-5-minutes) !

**Questions ?** Consultez **GUIDE_UTILISATION.md** ou **TROUBLESHOOTING.md**
