# Architecture du Système RAG-PEA

**Version:** 1.0.0
**Dernière mise à jour:** Février 2026
**Status:** Production Ready

---

## Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Architecture Globale](#architecture-globale)
- [Composants Détaillés](#composants-détaillés)
  - [API Layer](#api-layer-fastapi)
  - [Service Layer](#service-layer)
  - [Agents Layer](#agents-layer-crewai)
  - [Data Layer](#data-layer)
  - [Infrastructure Layer](#infrastructure-layer)
- [Design Patterns](#design-patterns)
- [Flux Critiques](#flux-critiques)
- [Décisions de Conception](#décisions-de-conception)
- [Sécurité](#sécurité)
- [Performance](#performance)
- [Scalabilité](#scalabilité)
- [Extensibilité](#extensibilité)

---

## Vue d'Ensemble

RAG-PEA est un système d'analyse financière et de gestion de portefeuille intelligent qui combine plusieurs technologies de pointe pour fournir une solution complète d'investissement automatisé.

### Objectifs du Système

1. **Portfolio Management** - Gérer un portefeuille PEA avec suivi en temps réel
2. **AI Analysis** - Analyser les entreprises avec des agents IA multi-spécialisés
3. **Document RAG** - Rechercher dans des rapports financiers avec embeddings vectoriels
4. **Market Intelligence** - Agréger données de marché, actualités et sentiment
5. **Automation** - Automatiser la collecte de données et les alertes

### Principes Architecturaux

- **Modularité** - Chaque service est indépendant et remplaçable
- **Résilience** - Circuit breakers, retry logic, graceful degradation
- **Observabilité** - Logging structuré JSON, métriques de performance
- **Configuration Centralisée** - Settings Pydantic avec validation
- **Type Safety** - Type hints complets, validation Pydantic
- **API-First** - Toutes les fonctionnalités exposées via REST API

---

## Architecture Globale

### Diagramme ASCII Art

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATIONS                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Browser UI  │  │  cURL/HTTP   │  │   Python     │  │  Telegram  │ │
│  │   (Future)   │  │   Clients    │  │   Scripts    │  │    Bot     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘ │
└─────────┼──────────────────┼──────────────────┼─────────────────┼───────┘
          │                  │                  │                 │
          └──────────────────┴──────────────────┴─────────────────┘
                                      │
                             ╔════════▼════════╗
                             ║   FASTAPI APP   ║
                             ║   (api/main.py) ║
                             ╚════════╤════════╝
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │              MIDDLEWARE LAYER (Sequential Processing)      │
        │  ┌──────────────────────────────────────────────────────┐ │
        │  │ 1. RequestIDMiddleware      - Generate UUID          │ │
        │  │ 2. RequestLoggingMiddleware - Log all requests       │ │
        │  │ 3. RateLimitMiddleware      - 60 req/min per IP      │ │
        │  │ 4. SecurityHeadersMiddleware- CORS, XSS protection   │ │
        │  └──────────────────────────────────────────────────────┘ │
        └────────────────────────────┬────────────────────────────────┘
                                     │
                      ┌──────────────┴──────────────┐
                      │   EXCEPTION HANDLING        │
                      │  - RAGSystemError           │
                      │  - ValidationError          │
                      │  - HTTPException            │
                      └──────────────┬──────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         │                    API ENDPOINTS (23 routes)          │
         │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
         │  │  Portfolio  │  │   Market    │  │   Analysis   │  │
         │  │  Management │  │    Data     │  │   & Agents   │  │
         │  │  (8 routes) │  │  (2 routes) │  │  (5 routes)  │  │
         │  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘  │
         │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │
         │  │     RAG     │  │   Health    │  │  Collections │  │
         │  │  Documents  │  │  & System   │  │  Management  │  │
         │  │  (3 routes) │  │  (2 routes) │  │  (3 routes)  │  │
         │  └──────┬──────┘  └─────────────┘  └──────┬───────┘  │
         └─────────┼──────────────────────────────────┼──────────┘
                   │                                  │
      ┌────────────┴────────────┐          ┌─────────┴──────────┐
      │                         │          │                    │
╔═════▼═════════╗  ╔═══════════▼═══════╗  ╔═══════▼═════════╗  ╔═══════════════╗
║   SERVICE     ║  ║     AGENTS        ║  ║  RAG MANAGER    ║  ║   DATABASE    ║
║    LAYER      ║  ║  LAYER (CrewAI)   ║  ║  (ChromaDB)     ║  ║     LAYER     ║
╚═════╤═════════╝  ╚═══════════╤═══════╝  ╚═══════╤═════════╝  ╚═══════╤═══════╝
      │                        │                  │                    │
┌─────┴─────────────┐   ┌──────┴────────┐   ┌────┴──────┐       ┌─────┴──────┐
│ • YahooFinance    │   │ 6 Agents:     │   │ Sentence  │       │ SQLite DB  │
│ • TechnicalAnalysis│   │  Portfolio    │   │ Transform │       │ ├─positions│
│ • SentimentAnalyzer│   │  Builder      │   │ Embeddings│       │ ├─trans... │
│ • NewsAggregator  │   │ 4 Agents:     │   │ Cosine    │       │ └─analyses │
│ • PortfolioManager│   │  Financial    │   │ Similarity│       │            │
│ • BacktestEngine  │   │  Analysis     │   │           │       │            │
│ • TelegramBot     │   │               │   │           │       │            │
│ • SmartDocProc... │   │               │   │           │       │            │
└───────────────────┘   └───────┬───────┘   └─────┬─────┘       └────────────┘
                                │                 │
                         ┌──────┴────────┐   ┌────┴──────┐
                         │ Tools:        │   │ ChromaDB  │
                         │ • RAG Search  │   │ Collections│
                         │ • Web Search  │   │ Persistent │
                         │ • Tech Anal.  │   │ Storage    │
                         └───────────────┘   └───────────┘
                                │
                    ╔═══════════▼════════════╗
                    ║  EXTERNAL SERVICES     ║
                    ╠════════════════════════╣
                    ║ • Ollama (Local LLM)  ║
                    ║ • OpenAI (Embeddings) ║
                    ║ • Claude (Analysis)   ║
                    ║ • Yahoo Finance (Free)║
                    ║ • NewsAPI (News)      ║
                    ║ • SerpAPI (Web Search)║
                    ╚════════════════════════╝
```

### Diagramme Mermaid - Architecture par Couches

```mermaid
graph TB
    subgraph "Client Layer"
        CLI[CLI Tools]
        HTTP[HTTP Clients]
        TELEGRAM[Telegram Bot]
    end

    subgraph "API Layer - FastAPI"
        MAIN[main.py<br/>23 Routes]
        MIDDLEWARE[Middleware Stack]
        EXCEPTIONS[Exception Handlers]
    end

    subgraph "Business Logic Layer"
        SERVICES[Services]
        AGENTS[CrewAI Agents]
        RAG[RAG Manager]
    end

    subgraph "Data Layer"
        SQLITE[(SQLite DB)]
        CHROMA[(ChromaDB)]
        CACHE[LRU Cache]
    end

    subgraph "External Services"
        OLLAMA[Ollama LLM]
        OPENAI[OpenAI API]
        YFINANCE[Yahoo Finance]
        NEWSAPI[NewsAPI]
    end

    CLI --> MAIN
    HTTP --> MAIN
    TELEGRAM --> MAIN

    MAIN --> MIDDLEWARE
    MIDDLEWARE --> EXCEPTIONS
    EXCEPTIONS --> SERVICES
    EXCEPTIONS --> AGENTS
    EXCEPTIONS --> RAG

    SERVICES --> SQLITE
    SERVICES --> CACHE
    SERVICES --> YFINANCE
    SERVICES --> NEWSAPI

    AGENTS --> SERVICES
    AGENTS --> RAG
    AGENTS --> OPENAI

    RAG --> CHROMA
    RAG --> OLLAMA

    style MAIN fill:#4CAF50
    style SERVICES fill:#2196F3
    style AGENTS fill:#FF9800
    style RAG fill:#9C27B0
```

---

## Composants Détaillés

### API Layer (FastAPI)

#### 1. Main Application (`api/main.py`)

**Responsabilités:**
- Point d'entrée de l'application
- Configuration FastAPI (CORS, middleware, exception handlers)
- Définition des 23 endpoints REST
- Validation des requêtes avec Pydantic
- Documentation automatique OpenAPI

**Endpoints par Catégorie:**

```python
# Portfolio Management (8 routes)
POST   /portfolio/add              # Ajouter position
POST   /portfolio/sell             # Vendre position
GET    /portfolio                  # Vue d'ensemble
GET    /portfolio/health           # Score de santé (0-100)
GET    /portfolio/rebalance        # Recommandations rééquilibrage
GET    /portfolio/position/{ticker}# Détails position
GET    /portfolio/context          # Contexte pour IA
GET    /portfolio/history          # Historique transactions

# Market Data (2 routes)
GET    /market/stock/{ticker}      # Infos stock (gratuit)
GET    /market/history/{ticker}    # Historique cours

# Analysis (5 routes)
GET    /analysis/technical/{ticker}    # Analyse technique
GET    /analysis/news/{company}        # Actualités
GET    /analysis/sentiment/{company}   # Analyse sentiment
GET    /analysis/complete/{ticker}     # Analyse complète
POST   /analyze/financial-report       # Rapport IA multi-agent

# RAG Documents (3 routes)
POST   /upload                     # Upload & indexation PDF
POST   /index                      # Indexer document existant
POST   /query                      # Requête RAG

# Collections (3 routes)
GET    /collections                # Liste collections
GET    /collections/{name}         # Info collection
DELETE /collections/{name}         # Supprimer collection

# AI Agents (1 route)
POST   /build-portfolio            # Construire portfolio optimal

# System (2 routes)
GET    /                          # Page d'accueil
GET    /health                    # Health check
```

#### 2. Configuration Centralisée (`api/config.py`)

**Implémentation:** Pydantic Settings avec validation automatique

**Structure:**

```python
class Settings(BaseSettings):
    # Métadonnées
    app_name: str = "RAG-PEA Financial Analysis System"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"]
    debug: bool = False

    # Serveur
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    reload: bool = True

    # Sous-configurations (nested)
    database: DatabaseSettings          # SQLite config
    ollama: OllamaSettings             # LLM config
    chromadb: ChromaDBSettings         # Vector DB config
    yahoo_finance: YahooFinanceSettings# Market data config
    api_keys: APISettings              # API keys (masked in logs)
    logging: LoggingSettings           # Logging config
    circuit_breaker: CircuitBreakerSettings
    cors: CORSSettings
    rate_limit: RateLimitSettings
```

**Avantages:**
- Validation automatique au démarrage
- Type hints complets (IDE autocomplete)
- Chargement depuis `.env` automatique
- Masquage des secrets dans les logs
- Validation des formats (clés API, URLs, etc.)

**Exemple d'utilisation:**

```python
from api.config import settings

# Accès type-safe
ollama_url = settings.ollama.url
db_url = settings.database.url

# Validation automatique
if settings.is_production:
    # Activer HTTPS, désactiver debug
    pass
```

#### 3. Logging Structuré (`api/logging_config.py`)

**Format:** JSON en production, texte coloré en développement

**Features:**
- Request ID tracking (UUID unique par requête)
- User ID et endpoint dans chaque log
- Rotation automatique des fichiers (10MB max, 5 backups)
- Contexte via ContextVars (thread-safe)
- Niveaux configurables par module

**Structure des logs JSON:**

```json
{
  "timestamp": "2026-02-01T14:23:45.123456Z",
  "level": "INFO",
  "logger": "api.services.portfolio_manager",
  "message": "Portfolio updated successfully",
  "module": "portfolio_manager",
  "function": "update_prices",
  "line": 142,
  "request_id": "abc123-def456-ghi789",
  "user_id": "default_user",
  "endpoint": "GET /portfolio",
  "duration_ms": 245.67,
  "status_code": 200
}
```

**Helpers fournis:**

```python
from api.logging_config import (
    get_logger,
    log_exception,      # Log exception avec stack trace
    log_performance,    # Log métriques de performance
    set_request_context,# Définir contexte requête
    LoggerMixin         # Mixin pour classes
)

logger = get_logger(__name__)

# Performance logging
start = time.time()
result = expensive_operation()
log_performance(logger, "expensive_op", (time.time()-start)*1000)

# Exception logging avec contexte
try:
    risky_operation()
except Exception as e:
    log_exception(logger, e, "Operation failed", user_id="user123")
```

#### 4. Exceptions Personnalisées (`api/exceptions.py`)

**Hiérarchie:**

```
RAGSystemError (Base)
├── DatabaseError
│   ├── CollectionNotFoundError
│   ├── CollectionAlreadyExistsError
│   ├── DocumentIndexingError
│   └── DocumentNotFoundError
├── OllamaError
│   ├── OllamaUnavailableError
│   ├── OllamaTimeoutError
│   └── CircuitBreakerOpenError
├── PortfolioError
│   ├── PositionNotFoundError
│   ├── InsufficientQuantityError
│   └── InvalidTransactionError
├── FinancialDataError
│   ├── TickerNotFoundError
│   └── MarketDataUnavailableError
├── CrewAIError
│   ├── AgentExecutionError
│   └── ToolExecutionError
└── ValidationError
    └── ConfigurationError
```

**Avantages:**
- Messages d'erreur exploitables
- Codes HTTP appropriés (404, 409, 503, etc.)
- Détails structurés pour debugging
- Logging automatique
- Réponses JSON cohérentes

**Exemple:**

```python
from api.exceptions import TickerNotFoundError, raise_for_status

def get_stock_data(ticker: str):
    data = fetch_data(ticker)

    raise_for_status(
        data is not None,
        TickerNotFoundError(ticker)
    )

    return data

# Réponse automatique:
# {
#   "error": {
#     "message": "Ticker 'INVALID' not found",
#     "code": "TICKER_NOT_FOUND",
#     "details": {
#       "ticker": "INVALID",
#       "suggestion": "Verify ticker symbol (e.g., MC.PA for LVMH)"
#     }
#   }
# }
```

#### 5. Middleware Stack (`api/middleware.py`)

**Ordre d'exécution (du premier au dernier):**

1. **RequestIDMiddleware** - Génère UUID unique
2. **RequestLoggingMiddleware** - Log toutes les requêtes/réponses
3. **RateLimitMiddleware** - Limite à 60 req/min par IP
4. **SecurityHeadersMiddleware** - Headers de sécurité (XSS, CSP, etc.)
5. **CORSMiddleware** - Configuration CORS

**RequestIDMiddleware:**
```python
# Génère ou récupère X-Request-ID
# Stocke dans request.state.request_id
# Configure le contexte de logging
# Ajoute X-Request-ID dans les headers de réponse
```

**RequestLoggingMiddleware:**
```python
# Log requête entrante avec:
# - Method, path, query params
# - Client IP, User-Agent
# - Request ID

# Mesure temps de traitement

# Log réponse avec:
# - Status code
# - Durée (ms)
# - Succès/échec
# Ajoute X-Response-Time header
```

**RateLimitMiddleware:**
```python
# Stratégie: Fenêtre glissante 1 minute par IP
# Limite: 60 requêtes/minute (configurable)
# Réponse 429 si dépassement
# Headers:
#   X-RateLimit-Limit: 60
#   X-RateLimit-Remaining: 23
#   X-RateLimit-Reset: 1234567890
#   Retry-After: 60
```

**SecurityHeadersMiddleware:**
```python
# Headers ajoutés:
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - X-XSS-Protection: 1; mode=block
# - Strict-Transport-Security (production uniquement)
```

#### 6. Modèles Pydantic (`api/models.py`)

**Modèles de requête/réponse:**

```python
# Portfolio
class PositionAddRequest(BaseModel):
    ticker: str
    company_name: str
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    user_id: str = "default_user"

# RAG
class QueryRequest(BaseModel):
    question: str = Field(min_length=3)
    collection_name: str
    n_results: int = Field(default=5, ge=1, le=20)
    filter_tables: bool = False
    generate_answer: bool = True

# Analysis
class FinancialAnalysisRequest(BaseModel):
    companies: List[str]
    collections: List[str]
    portfolio: Optional[Dict] = None

# Agents
class PortfolioBuildRequest(BaseModel):
    budget: float = Field(gt=0)
    risk_profile: Literal["conservative", "balanced", "aggressive"]
    sectors: Optional[List[str]] = None
    exclude_companies: Optional[List[str]] = None
    min_companies: int = Field(default=8, ge=3, le=20)
    max_companies: int = Field(default=15, ge=5, le=30)
```

**Validation automatique:**
- Types (int, float, str, List, Dict)
- Contraintes (min, max, regex, email, url)
- Valeurs par défaut
- Champs optionnels vs requis
- Enums et Literals
- Nested models

---

### Service Layer

#### 1. Yahoo Finance Service (`api/services/yahoo_finance_service.py`)

**Responsabilités:**
- Récupération données marché gratuites via yfinance
- Cache LRU avec TTL (5 min pour quotes, plus long pour historique)
- Thread-safe pour usage concurrent

**Méthodes:**

```python
class YahooFinanceService:
    def get_stock_info(ticker: str) -> Dict
        # Prix actuel, P/E, dividend yield, market cap
        # 52w high/low, beta, profit margin, ROE

    def get_historical_data(ticker: str, period: str, interval: str) -> pd.DataFrame
        # Historique OHLCV
        # Periods: 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max
        # Intervals: 1d, 1wk, 1mo

    def get_financials(ticker: str) -> Dict
        # Balance sheet, income statement, cash flow
        # Earnings (annual + quarterly)

    def get_recommendations(ticker: str) -> pd.DataFrame
        # Recommandations analystes (Buy/Hold/Sell)

    def get_realtime_quote(ticker: str) -> Dict
        # Prix temps réel (2 min cache)
        # Volume, open, high, low, change%

    def clear_cache(ticker: Optional[str] = None)
        # Invalider cache (global ou par ticker)
```

**Cache Strategy:**
```python
# Implémentation custom avec ContextVar pour thread-safety
# Structure: {key: (timestamp, value)}
# TTL: 5 minutes (300s) pour données générales
#      2 minutes (120s) pour quotes temps réel

def _get_from_cache(key: str) -> Optional[Any]:
    if key in cache:
        timestamp, value = cache[key]
        if time.time() - timestamp < TTL:
            return value  # Cache HIT
    return None  # Cache MISS
```

#### 2. Portfolio Manager (`api/services/portfolio_manager.py`)

**Responsabilités:**
- Business logic du portefeuille
- Calcul de métriques (santé, rééquilibrage)
- Génération de contexte pour IA

**Méthodes clés:**

```python
class PortfolioManager:
    def get_portfolio_context_for_ai(user_id: str) -> str
        # Génère texte formaté pour LLM:
        # - Valeur totale, gain/perte
        # - Détails chaque position
        # - Statistiques (meilleur/pire performer)

    def get_portfolio_health_score(user_id: str) -> Dict
        # Score 0-100 basé sur:
        # - Diversification (30 points)
        # - Concentration (25 points)
        # - Performance globale (25 points)
        # - Positions en perte (20 points)
        # Retourne: score, grade (A+ à F), issues, recommendations

    def should_rebalance(user_id: str) -> Dict
        # Détecte déséquilibres:
        # - Position > 25% → REDUCE
        # - Position < 5% (si < 15 positions) → INCREASE
        # - < 5 positions → DIVERSIFY
        # Retourne: needs_rebalance, recommendations avec urgency

    def get_position_details(ticker: str, user_id: str) -> Dict
        # Combine:
        # - Données portefeuille (quantity, avg_price, gain/loss)
        # - Données marché (current_price, P/E, dividend)
        # - Historique transactions
        # - Analyses passées
```

**Algorithme Health Score:**

```python
score = 100

# 1. Diversification (30 points)
if positions < 3:   score -= 30  # Très risqué
elif positions < 5: score -= 15  # Peu diversifié
elif positions > 20: score -= 10 # Trop à gérer

# 2. Concentration (25 points)
if any_position_weight > 30%: score -= 25  # Danger
elif any_position_weight > 25%: score -= 15

# 3. Performance (25 points)
if total_return < -20%: score -= 25  # Très mauvais
elif total_return < -10%: score -= 15
elif total_return < 0%: score -= 5

# 4. Positions perdantes (20 points)
if losing_positions >= 50%: score -= 20
elif losing_positions > 0: score -= 10

# Grade: A+ (90+), A (80+), B (70+), C (60+), D (50+), F (<50)
```

#### 3. Technical Analysis (`api/services/technical_analysis.py`)

**Responsabilités:**
- Calcul indicateurs techniques (RSI, MACD, Bollinger, SMA/EMA)
- Détection signaux (Golden Cross, Death Cross, oversold/overbought)
- Calcul support/résistance

**Indicateurs implémentés:**

```python
class TechnicalAnalyzer:
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame
        # Ajoute colonnes:
        # - SMA_20, SMA_50, SMA_200
        # - EMA_12, EMA_26
        # - RSI_14
        # - MACD, MACD_signal, MACD_hist
        # - BB_upper, BB_middle, BB_lower
        # - ATR_14 (Average True Range)

    def detect_signals(df: pd.DataFrame) -> Dict
        # Signaux détectés:
        # - Golden Cross (SMA50 croise SMA200 vers le haut)
        # - Death Cross (SMA50 croise SMA200 vers le bas)
        # - RSI Oversold (< 30)
        # - RSI Overbought (> 70)
        # - MACD Crossover (MACD croise signal)
        # - BB Breakout (prix sort des Bollinger)

    def calculate_support_resistance(df: pd.DataFrame) -> Dict
        # Détection niveaux clés:
        # - Support (pivots bas)
        # - Résistance (pivots hauts)
        # - Distance au support/résistance actuel

    def calculate_trend(df: pd.DataFrame) -> str
        # Détermine tendance: BULLISH, BEARISH, NEUTRAL
        # Basé sur: SMA, EMA, higher highs/lower lows
```

**Exemple de signaux:**

```json
{
  "signals": {
    "golden_cross": false,
    "death_cross": false,
    "rsi_oversold": true,
    "rsi_overbought": false,
    "macd_bullish_cross": true,
    "bb_breakout_up": false,
    "bb_breakout_down": false
  },
  "current_values": {
    "rsi": 28.5,
    "macd": 2.3,
    "price_vs_sma20": -3.2,
    "price_vs_sma50": -8.7
  },
  "recommendation": "BUY",
  "confidence": 0.75
}
```

#### 4. Sentiment Analyzer (`api/services/sentiment_analyzer.py`)

**Responsabilités:**
- Analyse sentiment des actualités avec Claude/GPT-4
- Scoring -1 (très négatif) à +1 (très positif)
- Agrégation multi-sources

**Workflow:**

```python
class SentimentAnalyzer:
    def analyze_news_sentiment(company: str, articles: List[Dict]) -> Dict
        # Pour chaque article:
        # 1. Extraire titre + description
        # 2. Envoyer à Claude/GPT-4
        # 3. Obtenir score sentiment + justification

        # Agrégation:
        # - Moyenne pondérée des scores
        # - Comptage positif/neutre/négatif
        # - Tendance générale
        # - Articles les plus influents

        return {
            "overall_sentiment": 0.65,  # -1 à +1
            "sentiment_label": "POSITIVE",
            "confidence": 0.82,
            "positive_count": 7,
            "neutral_count": 2,
            "negative_count": 1,
            "key_themes": ["expansion", "strong earnings", "innovation"],
            "risk_factors": ["regulatory concerns"]
        }
```

**Prompt Template:**

```python
SENTIMENT_PROMPT = """
Analyse le sentiment de cette actualité pour {company}:

Titre: {title}
Description: {description}
Source: {source}
Date: {date}

Fournis:
1. Score sentiment: -1 (très négatif) à +1 (très positif)
2. Justification en 1 phrase
3. Impact probable sur le cours: HIGH/MEDIUM/LOW

Format JSON:
{{"score": 0.7, "justification": "...", "impact": "MEDIUM"}}
"""
```

#### 5. News Aggregator (`api/services/news_aggregator.py`)

**Responsabilités:**
- Agrégation actualités multi-sources
- Filtrage et déduplication
- Tri par pertinence et date

**Sources:**

```python
class NewsAggregator:
    # Sources supportées:
    # 1. NewsAPI (100 req/jour gratuit)
    # 2. Google News RSS
    # 3. Fallback: web scraping (opt-in)

    def get_company_news(company: str, days_back: int = 7) -> List[Dict]
        # 1. Requête NewsAPI
        # 2. Filtrer par mots-clés (company, ticker, variants)
        # 3. Dédupliquer (titre similarity > 80%)
        # 4. Enrichir avec métadonnées
        # 5. Trier par:
        #    - Pertinence (keywords match)
        #    - Fraîcheur (date)
        #    - Source (fiabilité)

        return [
            {
                "title": "...",
                "description": "...",
                "url": "...",
                "source": "Reuters",
                "published_at": "2026-02-01T10:30:00Z",
                "relevance_score": 0.95,
                "sentiment_preview": "POSITIVE"
            },
            ...
        ]
```

#### 6. Backtesting Engine (`api/services/backtesting_engine.py`)

**Responsabilités:**
- Test stratégies sur données historiques
- Calcul métriques performance (Sharpe ratio, max drawdown, etc.)
- Visualisation résultats

**Stratégies implémentées:**

```python
class BacktestingEngine:
    def __init__(initial_capital: float = 10000):
        self.capital = initial_capital
        self.positions = []
        self.trades = []

    def run_simple_ma_strategy(ticker: str, historical_data: pd.DataFrame) -> Dict
        # Stratégie: SMA Crossover (20/50)
        # - Achat: SMA20 croise SMA50 vers le haut
        # - Vente: SMA20 croise SMA50 vers le bas

        # Métriques retournées:
        return {
            "initial_capital": 10000,
            "final_capital": 12345,
            "total_return": 23.45,       # %
            "annualized_return": 8.12,   # %
            "sharpe_ratio": 1.45,
            "max_drawdown": -15.3,       # %
            "win_rate": 0.62,            # 62% trades gagnants
            "total_trades": 24,
            "avg_trade_return": 1.8,     # %
            "best_trade": 12.5,          # %
            "worst_trade": -8.3,         # %
            "volatility": 18.5,          # % annualisé
            "trades": [...]              # Détails chaque trade
        }
```

**Métriques expliquées:**

- **Total Return:** (Final - Initial) / Initial * 100
- **Sharpe Ratio:** (Rendement - Risk-free rate) / Volatility
  - > 1.0 = bon, > 2.0 = excellent, > 3.0 = exceptionnel
- **Max Drawdown:** Plus grande perte pic-à-creux
- **Win Rate:** Nombre trades gagnants / Total trades

#### 7. Telegram Bot (`api/services/telegram_bot.py`)

**Responsabilités:**
- Notifications push trading
- Alertes personnalisées
- Commandes interactives

**Features:**

```python
class TelegramBot:
    def send_notification(message: str, parse_mode: str = "Markdown")
        # Envoie notification simple

    def send_trading_alert(ticker: str, signal: Dict, analysis: Dict)
        # Alerte formatée avec:
        # - Emoji selon signal (🟢 BUY, 🔴 SELL, 🟡 HOLD)
        # - Prix actuel et variation
        # - Raison du signal
        # - Niveau de confiance
        # - Lien vers analyse complète

    def send_portfolio_summary(summary: Dict)
        # Résumé quotidien:
        # - Performance jour/semaine/mois
        # - Top gainers/losers
        # - Alertes si seuils dépassés

    # Commandes interactives (si bot activé):
    # /portfolio - Vue d'ensemble
    # /analyze TICKER - Analyse rapide
    # /news COMPANY - Actualités récentes
    # /health - Score santé portefeuille
```

**Exemple de notification:**

```
🟢 SIGNAL D'ACHAT - LVMH (MC.PA)

Prix actuel: 752.30 EUR (+1.8%)

📊 Signaux détectés:
✓ RSI Oversold (28.5)
✓ MACD Bullish Cross
✓ Support rebondi

🎯 Confiance: 85%

📈 Analyse complète: https://app.rag-pea.com/analysis/MC.PA
```

#### 8. Smart Document Processor (`api/services/smart_document_processor.py`)

**Responsabilités:**
- Extraction intelligente de données financières depuis PDFs
- Compression 90% (500 pages → 50 pages de données clés)
- Détection automatique des sections importantes

**Workflow:**

```python
class SmartDocumentProcessor:
    def process_financial_report(pdf_path: str) -> Dict
        # 1. Extraction PDF (PyMuPDF/pdfplumber)
        # 2. Détection sections:
        #    - Executive Summary
        #    - Financial Highlights
        #    - Key Metrics
        #    - Tables (P&L, Balance Sheet, Cash Flow)
        # 3. Extraction données structurées:
        #    - Chiffres clés (revenue, profit, EPS)
        #    - Ratios (P/E, ROE, debt/equity)
        #    - Guidance future
        # 4. Résumé IA (Claude):
        #    - Top 5 insights
        #    - Risques identifiés
        #    - Opportunités

        return {
            "metadata": {...},
            "key_metrics": {...},
            "summary": "...",
            "sections": [...],
            "tables": [...],
            "compression_ratio": 0.92  # 92% réduction
        }
```

---

### Agents Layer (CrewAI)

#### Architecture Multi-Agent

Le système utilise CrewAI pour orchestrer des agents spécialisés qui collaborent sur des tâches complexes.

**Principes:**
- Chaque agent a un rôle, goal et backstory clairs
- Les agents utilisent des outils (RAG, web search, data analysis)
- Exécution séquentielle avec passage de contexte
- Résultat final agrégé par un agent Manager

#### 1. Portfolio Builder Crew (6 agents)

**Fichier:** `api/agents/portfolio_builder_crew.py`

**Objectif:** Construire un portefeuille PEA optimal de zéro

**Agents:**

```python
# 1. Data Collector Agent
Role: "Senior Financial Data Collector"
Goal: "Collecter automatiquement les données financières et rapports"
Tools: [web_search, yahoo_finance, news_search]
Tasks:
  - Identifier top 30 entreprises éligibles PEA
  - Télécharger rapports financiers (10-K, earnings)
  - Collecter données historiques 5-10 ans
  - Indexer dans ChromaDB

# 2. Fundamental Analyst Agent
Role: "Expert Financial Analyst - Fundamental Analysis"
Goal: "Analyser les fondamentaux de chaque entreprise"
Tools: [rag_search, financial_calculator]
Tasks:
  - Pour chaque entreprise:
    * Analyser P/E, P/B, ROE, debt/equity
    * Évaluer croissance revenue/profit
    * Identifier avantages compétitifs
  - Scoring: 0-100 par entreprise
  - Sélectionner top 15-20

# 3. Technical Analyst Agent
Role: "Senior Technical Analysis Specialist"
Goal: "Identifier points d'entrée optimaux"
Tools: [technical_analysis, chart_patterns]
Tasks:
  - Analyser tendances long terme
  - Identifier supports/résistances
  - Détecter signaux achat
  - Timing recommendations

# 4. Risk Manager Agent
Role: "Portfolio Risk Management Expert"
Goal: "Optimiser le risque du portefeuille"
Tools: [correlation_calculator, volatility_analyzer]
Tasks:
  - Calculer corrélations entre actifs
  - Analyser volatilité historique
  - Proposer allocation selon profil risque
  - Définir limites par position

# 5. Sector Diversification Agent
Role: "Sector Allocation Strategist"
Goal: "Assurer diversification sectorielle optimale"
Tools: [sector_analyzer]
Tasks:
  - Mapper entreprises par secteur
  - Définir allocation cible par secteur
  - Éviter concentration excessive
  - Équilibrer cycliques vs défensifs

# 6. Portfolio Construction Agent (Manager)
Role: "Chief Portfolio Manager"
Goal: "Construire le portefeuille final optimal"
Tools: [optimizer, backtester]
Tasks:
  - Agréger analyses de tous les agents
  - Optimiser allocation (Markowitz ou équipondéré)
  - Générer ordres d'achat précis
  - Fournir plan d'action complet
```

**Workflow:**

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Crew
    participant DataCollector
    participant FundamentalAnalyst
    participant TechnicalAnalyst
    participant RiskManager
    participant SectorAgent
    participant PortfolioManager

    User->>API: POST /build-portfolio {budget, risk_profile}
    API->>Crew: Kickoff crew

    Crew->>DataCollector: Collect data for top 30 PEA stocks
    DataCollector-->>Crew: Data + reports indexed

    Crew->>FundamentalAnalyst: Analyze fundamentals
    FundamentalAnalyst-->>Crew: Top 20 companies scored

    Crew->>TechnicalAnalyst: Analyze charts
    TechnicalAnalyst-->>Crew: Entry points identified

    Crew->>RiskManager: Optimize risk
    RiskManager-->>Crew: Correlation matrix + volatility

    Crew->>SectorAgent: Ensure diversification
    SectorAgent-->>Crew: Sector allocation plan

    Crew->>PortfolioManager: Build final portfolio
    PortfolioManager-->>Crew: Complete action plan

    Crew-->>API: Portfolio ready
    API-->>User: Action plan with buy orders
```

**Résultat final:**

```json
{
  "portfolio": {
    "total_budget": 10000,
    "allocated_budget": 9850,
    "cash_reserve": 150,
    "positions": [
      {
        "ticker": "MC.PA",
        "company": "LVMH",
        "sector": "Luxury",
        "allocation_percent": 12.5,
        "amount": 1231.25,
        "shares_to_buy": 1,
        "entry_price": 752.30,
        "rationale": "Strong fundamentals, RSI oversold, sector leader",
        "risk_score": 6.2,
        "expected_return": "8-12% annually"
      },
      // ... 9-14 autres positions
    ],
    "sector_allocation": {
      "Luxury": 25.0,
      "Technology": 20.0,
      "Healthcare": 15.0,
      "Finance": 15.0,
      "Industrial": 15.0,
      "Energy": 10.0
    },
    "risk_metrics": {
      "portfolio_volatility": 16.8,
      "expected_sharpe": 1.2,
      "max_correlation": 0.45
    }
  },
  "action_plan": "1. Acheter 1 action LVMH à 752.30€\n2. Acheter 3 actions ..."
}
```

#### 2. Financial Analysis Crew (4 agents)

**Fichier:** `api/agents/financial_crew.py`

**Objectif:** Analyser en profondeur une ou plusieurs entreprises

**Agents:**

```python
# 1. Document Analyst Agent
Role: "Financial Document Analysis Expert"
Goal: "Extraire insights des rapports financiers"
Tools: [rag_search_tool]
Tasks:
  - Rechercher dans rapports indexés
  - Extraire KPIs, trends, guidance
  - Identifier forces/faiblesses

# 2. Market Research Agent
Role: "Market Intelligence Specialist"
Goal: "Analyser contexte marché et compétition"
Tools: [web_search, news_aggregator]
Tasks:
  - Rechercher actualités récentes
  - Analyser communiqués de presse
  - Comparer vs compétiteurs
  - Identifier catalyseurs

# 3. Technical Expert Agent
Role: "Technical Analysis Expert"
Goal: "Évaluer aspects techniques"
Tools: [technical_analysis]
Tasks:
  - Analyser chart patterns
  - Calculer indicateurs
  - Déterminer timing

# 4. Investment Advisor Agent (Manager)
Role: "Senior Investment Advisor"
Goal: "Synthétiser et recommander"
Tools: [sentiment_analyzer]
Tasks:
  - Agréger toutes les analyses
  - Peser pour/contre
  - Recommandation: ACHETER/GARDER/VENDRE
  - Target price et stop loss
```

**Output:**

```markdown
# RAPPORT D'ANALYSE FINANCIÈRE - LVMH

## RECOMMANDATION: ACHETER 🟢
**Confiance:** 85%
**Target Price:** 820 EUR (+9%)
**Stop Loss:** 710 EUR (-6%)

## FONDAMENTAUX
- **Chiffre d'affaires:** 86.2B EUR (+14% YoY)
- **Marge opérationnelle:** 28.5% (excellent)
- **P/E Ratio:** 24.3 (raisonnable pour le secteur luxe)
- **ROE:** 22.1% (top quartile)
- **Dette/EBITDA:** 0.8x (très sain)

## FORCES
✓ Leader mondial du luxe avec portfolio unique
✓ Marques iconiques (Louis Vuitton, Dior, Tiffany)
✓ Exposition croissance Asie (+20% China recovery)
✓ Pricing power exceptionnel
✓ Management de classe mondiale (Bernard Arnault)

## RISQUES
⚠ Dépendance marché chinois (30% du CA)
⚠ Valorisation premium vs peers
⚠ Sensibilité cycle économique

## ANALYSE TECHNIQUE
- **Tendance:** BULLISH (SMA50 > SMA200)
- **RSI:** 42 (zone neutre, potentiel haussier)
- **Support:** 720 EUR
- **Résistance:** 780 EUR

## SENTIMENT ACTUALITÉS
**Score:** +0.72/1.0 (TRÈS POSITIF)
- Résultats Q4 dépassent attentes
- Expansion China post-COVID
- Innovation produits (métavers, NFT)

## CONCLUSION
LVMH présente un profil risque/rendement attractif pour investisseurs
long terme. Position de leader incontestée, fondamentaux solides,
et catalyseurs positifs à court terme (réouverture Chine).
Point d'entrée actuel intéressant après correction récente.

**Action recommandée:** ACHETER pour allocation 10-15% du portefeuille
```

#### 3. Tools pour Agents (`api/agents/tools.py` + `advanced_tools.py`)

**Tools disponibles:**

```python
# RAG Search Tool
@tool
def rag_search_tool(question: str, collection_name: str) -> str:
    """Recherche dans documents financiers indexés"""
    # Utilise RAGManager pour search vectoriel
    # Retourne top 5 chunks pertinents

# Web Search Tool
@tool
def web_search_tool(query: str) -> str:
    """Recherche Google via SerpAPI"""
    # Retourne top 10 résultats
    # Extrait snippets pertinents

# Technical Analysis Tool
@tool
def technical_analysis_tool(ticker: str) -> str:
    """Analyse technique complète"""
    # Utilise TechnicalAnalyzer
    # Retourne signaux + indicateurs

# Yahoo Finance Tool
@tool
def yahoo_finance_tool(ticker: str) -> str:
    """Données marché temps réel"""
    # Prix, volume, P/E, dividendes, etc.

# News Search Tool
@tool
def news_search_tool(company: str, days: int = 7) -> str:
    """Actualités récentes"""
    # Utilise NewsAggregator
    # Retourne articles triés par pertinence

# Sentiment Analysis Tool
@tool
def sentiment_analysis_tool(company: str, articles: List) -> str:
    """Analyse sentiment actualités"""
    # Utilise SentimentAnalyzer (Claude/GPT-4)
    # Retourne score + justification

# Portfolio Optimizer Tool
@tool
def portfolio_optimizer_tool(stocks: List, budget: float, risk: str) -> str:
    """Optimise allocation portefeuille"""
    # Markowitz Modern Portfolio Theory
    # Ou équipondération si données insuffisantes

# Backtesting Tool
@tool
def backtesting_tool(ticker: str, strategy: str, period: str) -> str:
    """Backtest stratégie sur historique"""
    # Utilise BacktestingEngine
    # Retourne métriques performance
```

---

### Data Layer

#### 1. SQLite Database (`api/database/portfolio_db.py`)

**Schéma:**

```sql
-- Table: positions
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    avg_price REAL NOT NULL,
    current_price REAL,
    last_updated TIMESTAMP,
    UNIQUE(user_id, ticker)
);

-- Table: transactions
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    transaction_type TEXT CHECK(transaction_type IN ('BUY', 'SELL')),
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    total_amount REAL NOT NULL,
    commission REAL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Table: analyses (cache analyses IA)
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    analysis_type TEXT,  -- 'fundamental', 'technical', 'sentiment'
    analysis_data TEXT,  -- JSON
    recommendation TEXT, -- 'BUY', 'HOLD', 'SELL'
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour performance
CREATE INDEX idx_positions_user ON positions(user_id);
CREATE INDEX idx_transactions_user_ticker ON transactions(user_id, ticker);
CREATE INDEX idx_analyses_user_ticker ON analyses(user_id, ticker, created_at);
```

**Méthodes PortfolioDatabase:**

```python
class PortfolioDatabase:
    def add_position(ticker, company, quantity, price, user_id) -> bool
        # INSERT ou UPDATE position
        # Recalcule avg_price si position existante
        # Enregistre transaction BUY

    def sell_position(ticker, quantity, price, user_id) -> bool
        # Vérifie quantité disponible
        # UPDATE position (quantity -= sell_quantity)
        # Si quantity == 0, DELETE position
        # Enregistre transaction SELL

    def get_portfolio(user_id) -> List[Dict]
        # SELECT toutes positions user
        # JOIN avec current_price (depuis cache)
        # Calcule gain/loss par position

    def update_current_prices(user_id) -> None
        # Pour chaque position:
        #   Fetch current price (YahooFinance)
        #   UPDATE positions SET current_price, last_updated

    def get_portfolio_summary(user_id) -> Dict
        # Agrège:
        # - total_value (sum(quantity * current_price))
        # - total_invested (sum(quantity * avg_price))
        # - total_gain_loss (total_value - total_invested)
        # - total_gain_loss_percent
        # - positions détaillées

    def get_transactions(ticker, user_id, limit) -> List[Dict]
        # SELECT transactions
        # ORDER BY timestamp DESC
        # LIMIT N

    def save_analysis(ticker, analysis_type, data, recommendation, confidence, user_id)
        # INSERT analyse dans cache
        # Évite de refaire analyses identiques

    def get_analysis_history(ticker, user_id, limit) -> List[Dict]
        # SELECT analyses passées
        # Permet tracking évolution recommandations
```

**Gestion transactions avec calcul PRU:**

```python
def add_position(ticker, company, quantity, price, user_id):
    existing = get_position(ticker, user_id)

    if existing:
        # Calcul nouveau PRU (Prix de Revient Unitaire)
        old_quantity = existing['quantity']
        old_avg_price = existing['avg_price']

        new_quantity = old_quantity + quantity
        new_avg_price = (
            (old_quantity * old_avg_price) + (quantity * price)
        ) / new_quantity

        UPDATE positions
        SET quantity = new_quantity,
            avg_price = new_avg_price
        WHERE ticker = ticker AND user_id = user_id
    else:
        # Nouvelle position
        INSERT INTO positions (ticker, company, quantity, avg_price, user_id)
        VALUES (ticker, company, quantity, price, user_id)

    # Enregistrer transaction
    INSERT INTO transactions (ticker, type, quantity, price, user_id)
    VALUES (ticker, 'BUY', quantity, price, user_id)
```

#### 2. ChromaDB Vector Store (`api/rag_manager.py`)

**Configuration:**

```python
# Embeddings: sentence-transformers/all-MiniLM-L6-v2
# Dimension: 384
# Distance: Cosine similarity
# Persistence: ./data/chroma_db/

client = chromadb.PersistentClient(
    path=settings.chromadb.persist_directory
)

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
```

**Structure Collection:**

```python
collection = client.get_or_create_collection(
    name="company_financials_2024",
    metadata={
        "hnsw:space": "cosine",
        "description": "Financial reports Q1-Q4 2024",
        "company": "LVMH",
        "year": 2024
    },
    embedding_function=embedding_function
)

# Documents stockés:
collection.add(
    documents=[chunk_text],           # Texte du chunk
    embeddings=[embedding_vector],     # Vector 384-dim
    metadatas=[{
        "chunk_id": "doc1_chunk_42",
        "content_type": "text|table",
        "num_tokens": 256,
        "page": 42,
        "section": "Financial Results",
        "source_file": "lvmh_q4_2024.pdf"
    }],
    ids=["unique_chunk_id"]
)
```

**Méthodes RAGManager:**

```python
class RAGManager:
    def index_document(file_path: str, collection_name: str) -> Dict
        # 1. Extraction PDF (PyMuPDF)
        # 2. Chunking intelligent:
        #    - Texte: 512 tokens avec overlap 50
        #    - Tables: détection automatique, extraction structurée
        # 3. Génération embeddings
        # 4. Stockage dans collection
        # Retourne: {chunks: 245, tables: 18, time: 5.2s}

    def search(question: str, collection_name: str, n_results: int = 5) -> Tuple
        # 1. Embed question (même modèle)
        # 2. Similarity search cosine
        # 3. Retourne: (chunks, metadatas, distances)

    def generate_answer(question: str, chunks: List, metadatas: List) -> str
        # 1. Construire contexte depuis chunks
        # 2. Appel Ollama avec circuit breaker
        # 3. Prompt: "Réponds à la question basé sur ces documents..."
        # 4. Retourne réponse générée

    def list_collections() -> List[str]
        # Liste toutes collections disponibles

    def get_collection_info(collection_name: str) -> Dict
        # Métadonnées collection:
        # - Nombre documents
        # - Date création
        # - Entreprise/année

    def delete_collection(collection_name: str) -> bool
        # Supprime collection et tous ses documents
```

**Chunking Strategy:**

```python
def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Chunking intelligent avec overlap pour contexte

    Stratégie:
    1. Découpe par paragraphes
    2. Si paragraphe > chunk_size, découpe par phrases
    3. Overlap de 50 tokens entre chunks
    4. Préserve cohérence sémantique
    """
    chunks = []
    sentences = split_into_sentences(text)

    current_chunk = []
    current_size = 0

    for sentence in sentences:
        tokens = count_tokens(sentence)

        if current_size + tokens > chunk_size:
            # Sauvegarder chunk actuel
            chunks.append(" ".join(current_chunk))

            # Nouveau chunk avec overlap
            overlap_sentences = current_chunk[-overlap:]
            current_chunk = overlap_sentences + [sentence]
            current_size = sum(count_tokens(s) for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_size += tokens

    # Dernier chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
```

**Table Detection:**

```python
def detect_and_extract_tables(pdf_path: str) -> List[Dict]:
    """
    Détection automatique des tables dans PDFs

    Utilise:
    1. pdfplumber pour détection layout
    2. Camelot pour extraction précise
    3. Pandas pour structuration
    """
    tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Détecter tables
            page_tables = page.extract_tables()

            for table in page_tables:
                # Convertir en DataFrame
                df = pd.DataFrame(table[1:], columns=table[0])

                # Structurer
                tables.append({
                    "page": page_num + 1,
                    "data": df.to_dict(),
                    "markdown": df.to_markdown(),
                    "row_count": len(df),
                    "col_count": len(df.columns)
                })

    return tables
```

#### 3. Cache Layer

**LRU Cache avec TTL (Yahoo Finance Service):**

```python
class CacheWithTTL:
    """
    Cache LRU avec expiration automatique

    Features:
    - Thread-safe (Lock)
    - TTL configurable par type de données
    - Invalidation manuelle possible
    - Métriques (hit rate, size)
    """

    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = Lock()
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            timestamp, value = self._cache[key]
            age = time.time() - timestamp
            ttl = ttl or self._default_ttl

            if age > ttl:
                # Expiré
                del self._cache[key]
                self._misses += 1
                return None

            # Hit
            self._hits += 1
            return value

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = (time.time(), value)

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """Invalide cache (tout ou pattern spécifique)"""
        with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                return count

            # Invalider par pattern
            keys_to_delete = [
                k for k in self._cache.keys()
                if pattern in k
            ]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def get_stats(self) -> Dict:
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate
        }
```

**Usage dans YahooFinanceService:**

```python
class YahooFinanceService:
    def __init__(self):
        # Cache général: 5 minutes
        self._cache = CacheWithTTL(default_ttl=300)

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        cache_key = f"info_{ticker}"

        # Check cache
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return cached

        # Fetch from Yahoo Finance
        logger.debug(f"Cache MISS: {cache_key}")
        data = self._fetch_from_yfinance(ticker)

        # Store in cache
        self._cache.set(cache_key, data)

        return data

    def get_realtime_quote(self, ticker: str) -> Optional[Dict]:
        # Cache plus court pour données temps réel: 2 minutes
        cache_key = f"quote_{ticker}"
        cached = self._cache.get(cache_key, ttl=120)

        if cached:
            return cached

        # Fetch fresh data
        data = self._fetch_realtime(ticker)
        self._cache.set(cache_key, data)
        return data
```

---

### Infrastructure Layer

#### 1. Circuit Breaker (`api/utils/circuit_breaker.py`)

**Pattern:** Circuit Breaker pour prévenir cascading failures

**États:**

```mermaid
stateDiagram-v2
    [*] --> CLOSED
    CLOSED --> OPEN: failures >= threshold
    OPEN --> HALF_OPEN: timeout elapsed
    HALF_OPEN --> CLOSED: success count >= max_calls
    HALF_OPEN --> OPEN: any failure
    OPEN --> OPEN: timeout not elapsed

    note right of CLOSED
        État normal
        Toutes requêtes passent
        Compteur échecs: 0
    end note

    note right of OPEN
        Trop d'échecs
        Requêtes bloquées
        Retry après timeout
    end note

    note right of HALF_OPEN
        Phase de test
        Limite N appels
        Décision: CLOSED ou OPEN
    end note
```

**Implémentation:**

```python
class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,      # Ouvrir après 5 échecs
        timeout: int = 60,                # Réessayer après 60s
        half_open_max_calls: int = 3,    # 3 appels de test
        name: str = "CircuitBreaker"
    ):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._lock = Lock()  # Thread-safe

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""

        # Check circuit state
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                retry_after = self.timeout - (time.time() - self._last_failure_time)
                raise CircuitBreakerOpenError(retry_after, self._failure_count)

        elif self._state == CircuitState.HALF_OPEN:
            if self._half_open_calls >= self.half_open_max_calls:
                self._transition_to_open()
                raise CircuitBreakerOpenError(self.timeout, self._failure_count)

        # Attempt call
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    def protect(self, func: Callable) -> Callable:
        """Decorator for protecting functions"""
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper

    def call_with_fallback(self, func: Callable, fallback: Callable, *args, **kwargs):
        """Call with automatic fallback if circuit open"""
        try:
            return self.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            logger.info(f"Circuit open, using fallback")
            return fallback(*args, **kwargs)
```

**Usage dans RAGManager:**

```python
class RAGManager:
    def __init__(self):
        # Circuit breaker pour Ollama
        self.ollama_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60,
            name="OllamaService"
        )

    def generate_answer(self, question: str, chunks: List) -> str:
        """Generate answer with circuit breaker protection"""

        def call_ollama():
            response = requests.post(
                f"{settings.ollama.url}/api/generate",
                json={"model": settings.ollama.model, "prompt": prompt},
                timeout=settings.ollama.timeout
            )
            return response.json()['response']

        def fallback():
            # Fallback: retourner chunks bruts sans génération
            logger.warning("Ollama unavailable, returning raw chunks")
            return "\n\n".join(chunks[:3])

        # Call avec fallback automatique
        return self.ollama_breaker.call_with_fallback(
            call_ollama,
            fallback
        )
```

**Métriques Circuit Breaker:**

```python
def get_stats(self) -> Dict:
    return {
        "name": self.name,
        "state": self._state.value,          # "closed", "open", "half_open"
        "failure_count": self._failure_count,
        "success_count": self._success_count,
        "failure_threshold": self.failure_threshold,
        "timeout": self.timeout,
        "last_failure": datetime.fromtimestamp(self._last_failure_time).isoformat()
            if self._last_failure_time else None,
        "time_until_retry": max(0, self.timeout - (time.time() - self._last_failure_time))
            if self._state == CircuitState.OPEN else 0
    }

# Endpoint pour monitoring
@app.get("/circuit-breaker/stats")
def get_circuit_breaker_stats():
    return {
        "ollama": rag_manager.ollama_breaker.get_stats(),
        "yahoo_finance": yf_service.circuit_breaker.get_stats()
    }
```

---

## Design Patterns

### 1. Repository Pattern

**Utilisation:** `PortfolioDatabase` pour abstraire l'accès données

```python
# Interface repository
class IPortfolioRepository(ABC):
    @abstractmethod
    def add_position(self, ticker, quantity, price, user_id) -> bool:
        pass

    @abstractmethod
    def get_portfolio(self, user_id) -> List[Dict]:
        pass

# Implémentation SQLite
class SQLitePortfolioRepository(IPortfolioRepository):
    def add_position(self, ticker, quantity, price, user_id) -> bool:
        # SQLite implementation
        pass

# Futur: PostgreSQL, MongoDB, etc.
class PostgresPortfolioRepository(IPortfolioRepository):
    def add_position(self, ticker, quantity, price, user_id) -> bool:
        # Postgres implementation
        pass
```

**Avantages:**
- Découplage business logic / persistence
- Facilite testing (mock repository)
- Changement de DB sans modifier business logic

### 2. Strategy Pattern

**Utilisation:** Backtesting avec stratégies interchangeables

```python
class TradingStrategy(ABC):
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        pass

class SMAStrategy(TradingStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # SMA 20/50 crossover logic
        pass

class RSIStrategy(TradingStrategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        # RSI oversold/overbought logic
        pass

class BacktestingEngine:
    def run(self, strategy: TradingStrategy, data: pd.DataFrame):
        signals = strategy.generate_signals(data)
        # Execute backtest
```

### 3. Circuit Breaker Pattern

**Utilisation:** Protection contre failures Ollama, Yahoo Finance, APIs externes

Voir section [Infrastructure Layer](#1-circuit-breaker-apiutilscircuit_breakerpy) ci-dessus.

### 4. Dependency Injection

**Utilisation:** FastAPI avec Pydantic Settings

```python
from fastapi import Depends

def get_portfolio_manager() -> PortfolioManager:
    """Dependency injection pour PortfolioManager"""
    return PortfolioManager()

def get_yahoo_finance() -> YahooFinanceService:
    """Dependency injection pour YahooFinanceService"""
    return YahooFinanceService()

@app.get("/portfolio")
def get_portfolio(
    user_id: str = "default_user",
    manager: PortfolioManager = Depends(get_portfolio_manager),
    yf: YahooFinanceService = Depends(get_yahoo_finance)
):
    manager.db.update_current_prices(user_id)
    return manager.db.get_portfolio_summary(user_id)
```

**Avantages:**
- Testabilité (mock dependencies)
- Lifecycle management (singleton, request-scoped)
- Découplage composants

### 5. Observer Pattern

**Utilisation:** Telegram notifications

```python
class PortfolioObserver(ABC):
    @abstractmethod
    def notify(self, event: str, data: Dict) -> None:
        pass

class TelegramNotifier(PortfolioObserver):
    def notify(self, event: str, data: Dict) -> None:
        if event == "SIGNAL_DETECTED":
            self.send_trading_alert(data)
        elif event == "THRESHOLD_CROSSED":
            self.send_threshold_alert(data)

class PortfolioManager:
    def __init__(self):
        self.observers: List[PortfolioObserver] = []

    def attach(self, observer: PortfolioObserver):
        self.observers.append(observer)

    def _notify_observers(self, event: str, data: Dict):
        for observer in self.observers:
            observer.notify(event, data)

    def check_signals(self):
        signals = self._detect_signals()
        if signals:
            self._notify_observers("SIGNAL_DETECTED", signals)
```

### 6. Factory Pattern

**Utilisation:** Création d'agents CrewAI

```python
class AgentFactory:
    @staticmethod
    def create_fundamental_analyst(tools: List) -> Agent:
        return Agent(
            role="Expert Financial Analyst",
            goal="Analyze company fundamentals",
            backstory="20 years experience in fundamental analysis...",
            tools=tools,
            verbose=True
        )

    @staticmethod
    def create_technical_analyst(tools: List) -> Agent:
        return Agent(
            role="Technical Analysis Specialist",
            goal="Identify optimal entry points",
            backstory="Expert in chart patterns and indicators...",
            tools=tools,
            verbose=True
        )

# Usage
tools = [rag_search_tool, yahoo_finance_tool]
fundamental_agent = AgentFactory.create_fundamental_analyst(tools)
technical_agent = AgentFactory.create_technical_analyst(tools)
```

---

## Flux Critiques

### 1. Workflow RAG Complet

```mermaid
sequenceDiagram
    participant User
    participant API
    participant RAGManager
    participant ChromaDB
    participant Ollama
    participant CircuitBreaker

    User->>API: POST /upload {file: pdf}
    API->>RAGManager: index_document(path, collection)

    Note over RAGManager: 1. Extract PDF
    RAGManager->>RAGManager: PyMuPDF extract text + tables

    Note over RAGManager: 2. Chunk intelligently
    RAGManager->>RAGManager: chunk_text(512 tokens, overlap 50)

    Note over RAGManager: 3. Generate embeddings
    RAGManager->>RAGManager: SentenceTransformer.encode()

    Note over RAGManager: 4. Store in ChromaDB
    RAGManager->>ChromaDB: collection.add(docs, embeddings, metadata)
    ChromaDB-->>RAGManager: Success

    RAGManager-->>API: {total_chunks: 245, time: 5.2s}
    API-->>User: 200 OK - Document indexed

    Note over User: Later: Query document

    User->>API: POST /query {question, collection}
    API->>RAGManager: search(question, collection, n=5)

    Note over RAGManager: 1. Embed question
    RAGManager->>RAGManager: SentenceTransformer.encode(question)

    Note over RAGManager: 2. Similarity search
    RAGManager->>ChromaDB: collection.query(embedding, n=5)
    ChromaDB-->>RAGManager: Top 5 chunks + metadata

    RAGManager-->>API: (chunks, metadatas, distances)

    Note over API: If generate_answer=true

    API->>RAGManager: generate_answer(question, chunks)
    RAGManager->>CircuitBreaker: call(ollama_generate)

    alt Circuit CLOSED
        CircuitBreaker->>Ollama: POST /api/generate
        Ollama-->>CircuitBreaker: Generated answer
        CircuitBreaker-->>RAGManager: Answer
    else Circuit OPEN
        CircuitBreaker-->>RAGManager: CircuitBreakerOpenError
        RAGManager->>RAGManager: Fallback: return raw chunks
    end

    RAGManager-->>API: Generated answer or chunks
    API-->>User: 200 OK {answer, chunks, time}
```

### 2. Workflow Portfolio Builder

```mermaid
flowchart TD
    Start([User: POST /build-portfolio]) --> Input{Validate Input}
    Input -->|Invalid| Error[400 Bad Request]
    Input -->|Valid| Crew[Kickoff CrewAI]

    Crew --> DataCollector[Agent 1: Data Collector]
    DataCollector --> CollectData[Collect Top 30 PEA Stocks]
    CollectData --> IndexReports[Index Financial Reports]
    IndexReports --> DataDone[Data Ready]

    DataDone --> Fundamental[Agent 2: Fundamental Analyst]
    Fundamental --> AnalyzeFundamentals[Analyze P/E, ROE, Growth]
    AnalyzeFundamentals --> Score[Score 0-100 Each Company]
    Score --> SelectTop[Select Top 20]

    SelectTop --> Technical[Agent 3: Technical Analyst]
    Technical --> AnalyzeCharts[Analyze Charts & Indicators]
    AnalyzeCharts --> EntryPoints[Identify Entry Points]

    EntryPoints --> Risk[Agent 4: Risk Manager]
    Risk --> CalcCorrelation[Calculate Correlation Matrix]
    CalcCorrelation --> CalcVolatility[Calculate Volatility]
    CalcVolatility --> RiskAllocation[Propose Allocation by Risk]

    RiskAllocation --> Sector[Agent 5: Sector Diversification]
    Sector --> MapSectors[Map Companies to Sectors]
    MapSectors --> DefineAllocation[Define Sector Allocation]
    DefineAllocation --> Balance[Balance Cyclical vs Defensive]

    Balance --> Portfolio[Agent 6: Portfolio Manager]
    Portfolio --> Aggregate[Aggregate All Analyses]
    Aggregate --> Optimize[Optimize Allocation]
    Optimize --> GenerateOrders[Generate Buy Orders]
    GenerateOrders --> ActionPlan[Complete Action Plan]

    ActionPlan --> Response[200 OK]
    Response --> End([User Receives Portfolio])

    style Start fill:#4CAF50
    style Crew fill:#2196F3
    style Portfolio fill:#FF9800
    style End fill:#4CAF50
```

### 3. Workflow Analyse Action Complète

```mermaid
sequenceDiagram
    participant User
    participant API
    participant YahooFinance
    participant NewsAggregator
    participant SentimentAnalyzer
    participant TechnicalAnalyzer
    participant Cache

    User->>API: GET /analysis/complete/MC.PA?company=LVMH

    par Parallel Data Fetching
        API->>YahooFinance: get_stock_info("MC.PA")
        YahooFinance->>Cache: Check cache
        alt Cache HIT
            Cache-->>YahooFinance: Cached data
        else Cache MISS
            YahooFinance->>YahooFinance: Fetch from Yahoo
            YahooFinance->>Cache: Store in cache (TTL 5min)
        end
        YahooFinance-->>API: Market data

    and
        API->>NewsAggregator: get_company_news("LVMH", days=7)
        NewsAggregator->>NewsAggregator: Query NewsAPI
        NewsAggregator->>NewsAggregator: Filter & deduplicate
        NewsAggregator-->>API: Recent articles

    and
        API->>YahooFinance: get_historical_data("MC.PA", "6mo")
        YahooFinance-->>API: OHLCV DataFrame
    end

    Note over API: All data fetched in parallel

    API->>SentimentAnalyzer: analyze_news_sentiment("LVMH", articles)
    SentimentAnalyzer->>SentimentAnalyzer: For each article: call Claude
    SentimentAnalyzer->>SentimentAnalyzer: Aggregate scores
    SentimentAnalyzer-->>API: Sentiment {score: 0.72, label: POSITIVE}

    API->>TechnicalAnalyzer: calculate_indicators(df)
    TechnicalAnalyzer->>TechnicalAnalyzer: Add RSI, MACD, Bollinger
    TechnicalAnalyzer-->>API: DataFrame with indicators

    API->>TechnicalAnalyzer: detect_signals(df)
    TechnicalAnalyzer->>TechnicalAnalyzer: Check crossovers, thresholds
    TechnicalAnalyzer-->>API: Signals detected

    API->>TechnicalAnalyzer: calculate_support_resistance(df)
    TechnicalAnalyzer-->>API: Support/resistance levels

    API->>TechnicalAnalyzer: calculate_trend(df)
    TechnicalAnalyzer-->>API: BULLISH/BEARISH/NEUTRAL

    Note over API: Aggregate all results

    API->>API: Build complete analysis response
    API-->>User: 200 OK {market_data, news_sentiment, technical_analysis}
```

### 4. États Circuit Breaker (Ollama)

```mermaid
stateDiagram-v2
    [*] --> Initialized: Application Start
    Initialized --> CLOSED: Circuit Initialized

    CLOSED --> CLOSED: Successful Calls\n(failure_count=0)
    CLOSED --> OPEN: 5 Consecutive Failures\n(threshold reached)

    OPEN --> OPEN: Timeout Not Elapsed\n(reject all calls)
    OPEN --> HALF_OPEN: 60s Timeout Elapsed\n(attempt reset)

    HALF_OPEN --> CLOSED: 3 Successful Calls\n(service recovered)
    HALF_OPEN --> OPEN: Any Failure\n(service still down)

    note right of CLOSED
        Normal Operation
        - All requests pass
        - failure_count tracked
        - Reset on success
    end note

    note right of OPEN
        Service Unavailable
        - All requests rejected
        - Return CircuitBreakerOpenError
        - Wait timeout period
    end note

    note right of HALF_OPEN
        Testing Phase
        - Limited calls (max 3)
        - Decide: recover or fail
        - One failure → back to OPEN
    end note
```

---

## Décisions de Conception

### 1. Pourquoi FastAPI ?

**Choix:** FastAPI pour l'API REST

**Alternatives considérées:**
- Flask
- Django REST Framework
- Express.js (Node)

**Raisons:**
1. **Performance** - Async/await natif, parmi les plus rapides (Starlette + Pydantic)
2. **Validation automatique** - Pydantic models = validation + documentation
3. **Documentation auto** - OpenAPI/Swagger généré automatiquement
4. **Type hints** - Support complet Python 3.9+ type hints
5. **Moderne** - Async first, WebSocket support, dependency injection
6. **Communauté** - Large adoption, nombreux packages

### 2. Pourquoi SQLite ?

**Choix:** SQLite pour la persistence portefeuille

**Alternatives considérées:**
- PostgreSQL
- MongoDB
- JSON files

**Raisons:**
1. **Zero-config** - Pas de serveur à installer/gérer
2. **Portable** - Fichier unique, facile backup/restore
3. **Suffisant pour scale actuel** - Mono-utilisateur, < 100k transactions
4. **ACID** - Transactions garanties
5. **Évolutif** - Migration vers Postgres facile si besoin (Repository pattern)

**Limitations connues:**
- Mono-utilisateur concurrent (write lock)
- Pas de partitioning/sharding
- Pas de réplication

**Migration future vers Postgres si:**
- Multi-users (> 10)
- Transactions/sec > 100
- Besoin haute disponibilité

### 3. Pourquoi ChromaDB ?

**Choix:** ChromaDB pour vector database RAG

**Alternatives considérées:**
- Pinecone
- Weaviate
- Milvus
- FAISS

**Raisons:**
1. **Open-source** - Pas de coûts, pas de lock-in
2. **Simplicité** - Installation pip, API intuitive
3. **Persistence** - Stockage local, pas de cloud requis
4. **Embeddings intégrés** - Sentence Transformers out-of-the-box
5. **Performance suffisante** - < 1M documents, < 500ms queries

**Limitations connues:**
- Pas de distributed mode (mono-machine)
- Moins de features avancées vs Pinecone

**Migration future vers Pinecone/Weaviate si:**
- Documents > 10M
- Multi-tenancy requis
- Besoin filtres complexes

### 4. Pourquoi Ollama (local LLM) ?

**Choix:** Ollama pour génération réponses RAG

**Alternatives considérées:**
- OpenAI GPT-4
- Claude API
- Hugging Face Inference

**Raisons:**
1. **Gratuit** - Pas de coûts API par requête
2. **Privacy** - Données restent locales
3. **Latence** - Pas de round-trip network
4. **Offline** - Fonctionne sans internet
5. **Flexibilité** - Plusieurs modèles (llama3.2, mistral, etc.)

**Trade-offs:**
- Qualité inférieure vs GPT-4
- Nécessite GPU (optionnel mais recommandé)
- Modèles volumineux (plusieurs GB)

**Fallback:** Si Ollama indisponible, retourner chunks bruts

### 5. Pourquoi Yahoo Finance (gratuit) ?

**Choix:** Yahoo Finance via yfinance pour market data

**Alternatives considérées:**
- Alpha Vantage API
- IEX Cloud
- Polygon.io
- Interactive Brokers API

**Raisons:**
1. **Gratuit** - Pas de limites API
2. **Pas de clé API** - Pas de setup requis
3. **Données complètes** - Prix, historique, fondamentaux
4. **Python library mature** - yfinance très stable
5. **Delay acceptable** - 15-20 min OK pour investissement long terme

**Limitations connues:**
- Délai 15-20 minutes (pas real-time)
- Pas de données intraday < 1 min
- Fiabilité non garantie (unofficial API)

**Migration future vers API payante si:**
- Besoin real-time (trading actif)
- Besoin level 2 data (order book)
- Besoin corporate actions détaillés

### 6. Pourquoi Pydantic Settings ?

**Choix:** Pydantic Settings pour configuration centralisée

**Alternatives considérées:**
- Python-decouple
- Dynaconf
- Environ config

**Raisons:**
1. **Validation automatique** - Types, contraintes, formats
2. **Type safety** - IDE autocomplete, mypy checking
3. **Hiérarchie** - Nested settings (database.url, ollama.model, etc.)
4. **Secrets masking** - Ne log jamais les API keys
5. **Multi-sources** - .env, env vars, defaults

**Exemple de validation:**

```python
class APISettings(BaseSettings):
    anthropic_api_key: Optional[str] = None

    @field_validator("anthropic_api_key")
    def validate_anthropic_key(cls, v):
        if v and not v.startswith("sk-ant-"):
            raise ValueError("Invalid Anthropic API key format")
        return v
```

### 7. Pourquoi Logging JSON Structuré ?

**Choix:** Logs JSON en production, texte coloré en dev

**Alternatives considérées:**
- Text logs uniquement
- Syslog
- Logstash format

**Raisons:**
1. **Parsable** - Facile indexation Elasticsearch/Loki
2. **Structuré** - Champs typés, pas de regex parsing
3. **Contexte riche** - request_id, user_id, endpoint dans chaque log
4. **Filtrable** - Requêtes complexes sur structured data
5. **Dev-friendly** - Texte coloré pour debugging local

**Exemple:**

```json
{
  "timestamp": "2026-02-01T14:23:45Z",
  "level": "ERROR",
  "message": "Failed to fetch stock data",
  "request_id": "abc123",
  "ticker": "MC.PA",
  "exception": "TimeoutError",
  "duration_ms": 30000
}
```

**Query Elasticsearch:**

```
GET /logs/_search
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"range": {"duration_ms": {"gte": 1000}}},
        {"exists": {"field": "exception"}}
      ]
    }
  }
}
```

---

## Sécurité

### 1. Authentification & Autorisation

**État actuel:** Aucune authentification (single-user)

**user_id:** Hardcodé à "default_user" partout

**Implémentation future (multi-user):**

```python
# JWT Authentication
from fastapi.security import OAuth2PasswordBearer
from jose import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    user_id = payload.get("sub")
    return get_user(user_id)

@app.get("/portfolio")
def get_portfolio(current_user: User = Depends(get_current_user)):
    return manager.get_portfolio(current_user.id)
```

### 2. Validation des Entrées

**Pydantic Models:** Validation automatique

```python
class PositionAddRequest(BaseModel):
    ticker: str = Field(regex=r"^[A-Z]+\.PA$")  # Format ticker Euronext
    quantity: float = Field(gt=0, le=10000)     # > 0, max 10k shares
    price: float = Field(gt=0, le=100000)       # > 0, max 100k EUR/share
    user_id: str = Field(default="default_user", min_length=3, max_length=50)

    @validator("ticker")
    def ticker_must_exist(cls, v):
        # Vérifier que le ticker existe sur Yahoo Finance
        if not YahooFinanceService().get_stock_info(v):
            raise ValueError(f"Ticker {v} not found")
        return v
```

### 3. Protection CSRF/XSS

**CORS:** Configuration stricte en production

```python
# Development
cors_origins = ["*"]

# Production
cors_origins = [
    "https://app.rag-pea.com",
    "https://admin.rag-pea.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

**Security Headers:**

```python
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Strict-Transport-Security"] = "max-age=31536000"
```

### 4. Rate Limiting

**Implementation:** IP-based rate limiting

```python
# Configuration
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_REQUESTS_PER_HOUR = 1000

# Middleware
class RateLimitMiddleware:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()

        # Clean old requests (> 1 minute)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > current_time - 60
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded"},
                headers={"Retry-After": "60"}
            )

        # Record request
        self.requests[client_ip].append(current_time)

        return await call_next(request)
```

### 5. Secrets Management

**Ne JAMAIS commit:**
- API keys (OpenAI, Anthropic, NewsAPI, etc.)
- Tokens (Telegram bot token)
- Database credentials (si Postgres)

**Utiliser .env:**

```bash
# .env (in .gitignore)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
NEWSAPI_KEY=...
TELEGRAM_BOT_TOKEN=...
```

**Validation au démarrage:**

```python
def validate_configuration():
    errors = []

    if not settings.api_keys.openai_api_key:
        errors.append("OPENAI_API_KEY is required")

    if settings.api_keys.anthropic_api_key:
        if not settings.api_keys.anthropic_api_key.startswith("sk-ant-"):
            errors.append("Invalid ANTHROPIC_API_KEY format")

    return errors

# At startup
errors = validate_configuration()
if errors:
    logger.error(f"Configuration errors: {errors}")
    sys.exit(1)
```

### 6. SQL Injection Prevention

**Utilisation:** Parameterized queries

```python
# NEVER do this (vulnerable):
cursor.execute(f"SELECT * FROM positions WHERE ticker = '{ticker}'")

# ALWAYS do this (safe):
cursor.execute(
    "SELECT * FROM positions WHERE ticker = ? AND user_id = ?",
    (ticker, user_id)
)
```

### 7. Logging Sécurisé

**Masquer secrets dans logs:**

```python
def model_dump_safe(self) -> dict:
    """Export config without secrets"""
    config = self.model_dump()

    # Mask API keys
    if config.get("api_keys"):
        for key in config["api_keys"]:
            if config["api_keys"][key]:
                config["api_keys"][key] = "***MASKED***"

    return config

# Log safe config at startup
logger.info(
    "Configuration loaded",
    extra={"config": settings.model_dump_safe()}
)
```

---

## Performance

### 1. Métriques Cibles

| Opération | Latence P50 | Latence P95 | Latence P99 |
|-----------|-------------|-------------|-------------|
| GET /health | < 10ms | < 20ms | < 50ms |
| GET /market/stock/{ticker} | < 100ms | < 300ms | < 500ms |
| GET /portfolio | < 200ms | < 500ms | < 1s |
| POST /query (RAG search) | < 500ms | < 1s | < 2s |
| POST /query (avec generation) | < 5s | < 10s | < 15s |
| GET /analysis/technical | < 1s | < 2s | < 3s |
| GET /analysis/complete | < 3s | < 5s | < 8s |
| POST /build-portfolio | 5-10 min | 12 min | 15 min |

### 2. Optimisations Implémentées

#### Cache LRU avec TTL

**Impact:** Réduction 80% latence requêtes répétées

```python
# Sans cache: 300ms par requête Yahoo Finance
# Avec cache: 2ms (cache hit)

# Example metrics
cache_stats = yf_service._cache.get_stats()
# {
#   "size": 124,
#   "hits": 1523,
#   "misses": 287,
#   "hit_rate": 0.84  # 84% cache hit rate
# }
```

#### Async Operations

**FastAPI async endpoints:**

```python
@app.get("/portfolio")
async def get_portfolio(user_id: str):
    # Non-blocking I/O
    portfolio = await async_get_portfolio(user_id)
    return portfolio
```

**Parallel data fetching:**

```python
async def complete_analysis(ticker: str, company: str):
    # Fetch all data in parallel
    market_data, news, historical = await asyncio.gather(
        fetch_market_data(ticker),
        fetch_news(company),
        fetch_historical_data(ticker)
    )
    # Total time = max(t1, t2, t3) instead of t1 + t2 + t3
```

#### Database Indexes

```sql
-- Improve query performance
CREATE INDEX idx_positions_user ON positions(user_id);
CREATE INDEX idx_transactions_user_ticker ON transactions(user_id, ticker);
CREATE INDEX idx_analyses_user_ticker_date ON analyses(user_id, ticker, created_at DESC);

-- Query improvement:
-- Without index: 245ms (full table scan)
-- With index: 3ms (index seek)
```

#### Batch Operations

**Batch update prices:**

```python
def update_all_current_prices(user_id: str):
    positions = get_portfolio(user_id)
    tickers = [p['ticker'] for p in positions]

    # Batch fetch (1 request instead of N)
    prices = yf.download(tickers, period="1d", group_by="ticker")

    # Batch update DB
    for ticker in tickers:
        current_price = prices[ticker]['Close'][-1]
        # Use executemany for batch insert
        cursor.executemany(
            "UPDATE positions SET current_price = ? WHERE ticker = ?",
            [(price, ticker) for ticker, price in prices.items()]
        )
```

### 3. Bottlenecks Identifiés

#### 1. PDF Indexing (500 pages = 5-10 min)

**Cause:** Extraction + embedding génération sequentiel

**Solution future:**

```python
# Parallel chunking + embedding
from concurrent.futures import ThreadPoolExecutor

def index_document_parallel(pdf_path: str):
    # Extract all pages
    pages = extract_pages(pdf_path)

    # Chunk in parallel
    with ThreadPoolExecutor(max_workers=8) as executor:
        chunks = list(executor.map(chunk_page, pages))

    # Batch embed (vectorize 100 chunks at once)
    embeddings = model.encode(chunks, batch_size=100, show_progress_bar=True)

    # Batch insert ChromaDB
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

# Performance:
# Before: 10 min (sequential)
# After: 2 min (parallel + batch)
```

#### 2. CrewAI Portfolio Builder (5-10 min)

**Cause:** 6 agents séquentiels + web searches

**Optimisations:**
- Cache analyses (éviter re-analyze mêmes stocks)
- Paralléliser agents indépendants (fundamental + technical)
- Limiter web searches (max 3 par agent)

**Impossible à réduire en dessous de 3-5 min:**
- LLM calls incompressibles
- Web searches network-bound
- Analyse qualité > vitesse

#### 3. Ollama Generation (2-5s par query)

**Cause:** CPU inference (pas de GPU)

**Solutions:**
- Utiliser GPU (CUDA): 10x speedup
- Modèles plus petits: llama3.2:1b au lieu de 3b
- Quantization: GGUF Q4 (2x speedup)

**Avec GPU RTX 3090:**
- llama3.2:3b: 500ms au lieu de 5s
- llama3.2:1b: 200ms au lieu de 2s

### 4. Monitoring Performance

**Endpoint metrics:**

```python
@app.middleware("http")
async def performance_monitoring(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000

    # Log slow requests (> 1s)
    if duration_ms > 1000:
        logger.warning(
            f"Slow request detected: {request.url.path}",
            extra={
                "duration_ms": duration_ms,
                "endpoint": request.url.path,
                "method": request.method
            }
        )

    # Add header
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

    return response
```

**Prometheus metrics (future):**

```python
from prometheus_client import Counter, Histogram

request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

---

## Scalabilité

### État Actuel (Single-User, Single-Machine)

**Limites:**
- 1 utilisateur concurrent (SQLite write lock)
- 1 CPU/GPU (Ollama local)
- 1 instance API
- Pas de load balancing
- Pas de réplication

**Capacité estimée:**
- Requêtes/sec: 10-50 (selon endpoint)
- Documents indexés: < 1M
- Utilisateurs: 1

### Scale Vertical (Upgrade Machine)

**Facile à implémenter:**

```
Hardware upgrade:
- CPU: 8 cores → 16 cores (2x throughput)
- RAM: 16GB → 64GB (plus cache, plus collections)
- GPU: None → RTX 4090 (10x LLM speed)
- SSD: 500GB → 2TB (plus documents)

Impact:
- Ollama: 5s → 500ms
- PDF indexing: 10 min → 2 min
- Concurrent users: 1 → 5-10 (si migration Postgres)
```

**Coût:** 1000-2000 EUR machine

### Scale Horizontal (Multi-Machines)

**Complexe, nécessite refactoring:**

#### Architecture Multi-Instance

```
         ┌─────────────────┐
         │  Load Balancer  │
         │   (Nginx/HAProxy)│
         └────────┬─────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
┌─────▼────┐ ┌────▼────┐ ┌───▼──────┐
│ API #1   │ │ API #2  │ │  API #3  │
│ FastAPI  │ │ FastAPI │ │  FastAPI │
└─────┬────┘ └────┬────┘ └───┬──────┘
      │           │           │
      └───────────┼───────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
┌─────▼────┐ ┌────▼────┐ ┌───▼──────┐
│PostgreSQL│ │  Redis  │ │ ChromaDB │
│  (RDS)   │ │ (Cache) │ │ (Weaviate)│
└──────────┘ └─────────┘ └──────────┘
```

**Changements requis:**

1. **Database:** SQLite → PostgreSQL

```python
# Before
DATABASE_URL = "sqlite:///./data/portfolio.db"

# After
DATABASE_URL = "postgresql://user:pass@db.example.com:5432/ragpea"

# Use SQLAlchemy for abstraction
from sqlalchemy import create_engine
engine = create_engine(DATABASE_URL, pool_size=20, max_overflow=40)
```

2. **Cache:** In-memory → Redis

```python
# Before
self._cache = {}  # In-process memory

# After
import redis
redis_client = redis.Redis(host='redis.example.com', port=6379)

def get_from_cache(key: str):
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None

def set_cache(key: str, value: Any, ttl: int = 300):
    redis_client.setex(key, ttl, json.dumps(value))
```

3. **Sessions:** Sticky sessions ou JWT stateless

```python
# JWT stateless (recommended)
from jose import jwt

def create_access_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# No session storage needed, JWT contains all info
```

4. **File Storage:** Local → S3

```python
# Before
UPLOAD_DIR = Path("./data/uploads")

# After
import boto3
s3 = boto3.client('s3')

def upload_file(file_path: str):
    with open(file_path, 'rb') as f:
        s3.upload_fileobj(f, 'ragpea-documents', file_name)
```

5. **Vector DB:** ChromaDB → Weaviate/Pinecone

```python
# ChromaDB limitations: single-machine
# Weaviate: distributed, multi-node

import weaviate

client = weaviate.Client("https://cluster.weaviate.network")

# Same API, distributed backend
```

### Projections Scaling

**Single Machine (optimized):**
- Users: 10
- Requests/sec: 100
- Documents: 1M
- Cost: 2000 EUR

**3-Instance Cluster:**
- Users: 100
- Requests/sec: 500
- Documents: 10M
- Cost: 500 EUR/month (AWS)

**10-Instance Cluster:**
- Users: 1000
- Requests/sec: 2000
- Documents: 100M
- Cost: 2000 EUR/month (AWS)

---

## Extensibilité

### Comment Ajouter...

#### 1. Un Nouveau Service

```python
# 1. Créer service dans api/services/
# api/services/crypto_data_service.py

from api.logging_config import get_logger, LoggerMixin
from api.config import settings
from typing import Dict, Optional

logger = get_logger(__name__)

class CryptoDataService(LoggerMixin):
    """Service pour données crypto (Bitcoin, Ethereum, etc.)"""

    def __init__(self):
        self.api_url = "https://api.coingecko.com/api/v3"
        self._cache = {}

    def get_crypto_price(self, symbol: str) -> Optional[Dict]:
        """Récupère prix crypto"""
        self.logger.info(f"Fetching crypto price for {symbol}")
        # Implementation
        pass

# 2. Ajouter endpoint dans api/main.py
from api.services.crypto_data_service import CryptoDataService

@app.get("/crypto/{symbol}", tags=["Crypto"])
def get_crypto_data(symbol: str):
    service = CryptoDataService()
    return service.get_crypto_price(symbol)

# 3. Ajouter config si nécessaire
# api/config.py
class CryptoSettings(BaseSettings):
    coingecko_api_key: Optional[str] = None

class Settings(BaseSettings):
    crypto: CryptoSettings = Field(default_factory=CryptoSettings)
```

#### 2. Un Nouvel Agent CrewAI

```python
# api/agents/portfolio_builder_crew.py

def create_esg_analyst() -> Agent:
    """Nouvel agent: Analyse ESG (Environmental, Social, Governance)"""
    return Agent(
        role="ESG Analysis Specialist",
        goal="Evaluate companies on ESG criteria",
        backstory="""You are an expert in sustainable investing.
        You analyze companies' environmental impact, social responsibility,
        and governance practices to ensure ethical investments.""",
        tools=[
            rag_search_tool,
            web_search_tool,
            esg_ratings_tool  # New tool
        ],
        verbose=True,
        allow_delegation=False
    )

# Add to crew
esg_agent = create_esg_analyst()
crew = Crew(
    agents=[
        data_collector,
        fundamental_analyst,
        technical_analyst,
        risk_manager,
        sector_agent,
        esg_agent,  # NEW
        portfolio_manager
    ],
    tasks=[...],
    verbose=True
)
```

#### 3. Un Nouvel Indicateur Technique

```python
# api/services/technical_analysis.py

def calculate_ichimoku(self, df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule l'Ichimoku Cloud (indicateur japonais)

    Components:
    - Tenkan-sen (Conversion Line): (9-period high + low) / 2
    - Kijun-sen (Base Line): (26-period high + low) / 2
    - Senkou Span A: (Tenkan + Kijun) / 2, shifted 26 ahead
    - Senkou Span B: (52-period high + low) / 2, shifted 26 ahead
    """
    high_9 = df['High'].rolling(window=9).max()
    low_9 = df['Low'].rolling(window=9).min()
    df['tenkan_sen'] = (high_9 + low_9) / 2

    high_26 = df['High'].rolling(window=26).max()
    low_26 = df['Low'].rolling(window=26).min()
    df['kijun_sen'] = (high_26 + low_26) / 2

    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)

    high_52 = df['High'].rolling(window=52).max()
    low_52 = df['Low'].rolling(window=52).min()
    df['senkou_span_b'] = ((high_52 + low_52) / 2).shift(26)

    return df

# Add to detect_signals
def detect_signals(self, df: pd.DataFrame) -> Dict:
    signals = {}

    # Existing signals...

    # NEW: Ichimoku signals
    if 'tenkan_sen' in df.columns:
        # Bullish: price above cloud
        current_price = df['Close'].iloc[-1]
        cloud_top = max(df['senkou_span_a'].iloc[-1], df['senkou_span_b'].iloc[-1])
        cloud_bottom = min(df['senkou_span_a'].iloc[-1], df['senkou_span_b'].iloc[-1])

        signals['ichimoku_above_cloud'] = current_price > cloud_top
        signals['ichimoku_below_cloud'] = current_price < cloud_bottom
        signals['ichimoku_in_cloud'] = cloud_bottom <= current_price <= cloud_top

        # TK Cross
        signals['ichimoku_tk_bullish_cross'] = (
            df['tenkan_sen'].iloc[-2] <= df['kijun_sen'].iloc[-2] and
            df['tenkan_sen'].iloc[-1] > df['kijun_sen'].iloc[-1]
        )

    return signals
```

#### 4. Une Nouvelle Stratégie de Backtesting

```python
# api/services/backtesting_engine.py

def run_bollinger_breakout_strategy(
    self,
    ticker: str,
    historical_data: pd.DataFrame
) -> Dict:
    """
    Stratégie: Bollinger Bands Breakout

    Rules:
    - Buy: Prix casse BB supérieure avec fort volume
    - Sell: Prix casse BB inférieure
    """
    # Calculate Bollinger Bands
    df = historical_data.copy()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['BB_std'] = df['Close'].rolling(window=20).std()
    df['BB_upper'] = df['SMA_20'] + (2 * df['BB_std'])
    df['BB_lower'] = df['SMA_20'] - (2 * df['BB_std'])

    # Volume threshold (1.5x average)
    df['Volume_avg'] = df['Volume'].rolling(window=20).mean()

    # Generate signals
    df['Signal'] = 0

    for i in range(1, len(df)):
        # Buy signal
        if (df['Close'].iloc[i] > df['BB_upper'].iloc[i] and
            df['Volume'].iloc[i] > 1.5 * df['Volume_avg'].iloc[i]):
            df.loc[df.index[i], 'Signal'] = 1

        # Sell signal
        elif df['Close'].iloc[i] < df['BB_lower'].iloc[i]:
            df.loc[df.index[i], 'Signal'] = -1

    # Execute backtest
    return self._execute_backtest(df, initial_capital=self.initial_capital)
```

#### 5. Un Nouveau Endpoint API

```python
# api/main.py

from api.models import NewFeatureRequest, NewFeatureResponse

@app.post(
    "/new-feature",
    response_model=NewFeatureResponse,
    tags=["New Features"],
    summary="Description courte",
    description="""
    Description longue markdown avec exemples:

    ## Usage
    ```bash
    curl -X POST http://localhost:8000/new-feature \\
      -H "Content-Type: application/json" \\
      -d '{"param": "value"}'
    ```

    ## Response
    - `field1`: Description
    - `field2`: Description
    """
)
async def new_feature_endpoint(
    request: NewFeatureRequest,
    background_tasks: BackgroundTasks,  # Si tâche longue
    current_user: User = Depends(get_current_user)  # Si auth
) -> NewFeatureResponse:
    """
    Docstring pour la doc auto
    """
    start_time = time.time()

    try:
        # Validate input
        if not request.param:
            raise ValidationError("param", "param is required")

        # Business logic
        result = process_feature(request)

        # Log performance
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"New feature executed successfully",
            extra={"duration_ms": duration_ms}
        )

        return NewFeatureResponse(
            success=True,
            result=result,
            processing_time=duration_ms
        )

    except Exception as e:
        log_exception(logger, e, "New feature failed")
        raise
```

#### 6. Un Nouveau Modèle Pydantic

```python
# api/models.py

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class NewFeatureRequest(BaseModel):
    """Request model for new feature"""

    param: str = Field(
        ...,  # Required
        min_length=3,
        max_length=100,
        description="Main parameter"
    )

    optional_param: Optional[int] = Field(
        default=None,
        ge=0,
        le=1000,
        description="Optional parameter (0-1000)"
    )

    items: List[str] = Field(
        default=[],
        max_items=10,
        description="List of items (max 10)"
    )

    @validator("param")
    def param_must_be_valid(cls, v):
        if v.lower() == "invalid":
            raise ValueError("param cannot be 'invalid'")
        return v

    class Config:
        schema_extra = {
            "example": {
                "param": "example_value",
                "optional_param": 42,
                "items": ["item1", "item2"]
            }
        }

class NewFeatureResponse(BaseModel):
    """Response model for new feature"""

    success: bool
    result: Dict
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)
```

---

## Diagrammes Complémentaires

### Diagramme Déploiement

```mermaid
graph TB
    subgraph "User Machine"
        BROWSER[Web Browser]
        CLI[CLI Tools]
    end

    subgraph "Server"
        NGINX[Nginx Reverse Proxy<br/>Port 80/443]

        subgraph "Application"
            API1[FastAPI Instance 1<br/>Port 8000]
            API2[FastAPI Instance 2<br/>Port 8001]
            OLLAMA[Ollama LLM Server<br/>Port 11434]
        end

        subgraph "Data"
            SQLITE[(SQLite DB<br/>./data/portfolio.db)]
            CHROMA[(ChromaDB<br/>./data/chroma_db)]
            FILES[File System<br/>./data/uploads]
        end
    end

    subgraph "External Services"
        YAHOO[Yahoo Finance API]
        NEWS[NewsAPI]
        OPENAI[OpenAI API]
        SERPAPI[SerpAPI]
    end

    BROWSER --> NGINX
    CLI --> NGINX

    NGINX --> API1
    NGINX --> API2

    API1 --> SQLITE
    API1 --> CHROMA
    API1 --> FILES
    API1 --> OLLAMA
    API1 --> YAHOO
    API1 --> NEWS
    API1 --> OPENAI
    API1 --> SERPAPI

    API2 --> SQLITE
    API2 --> CHROMA
    API2 --> FILES
    API2 --> OLLAMA

    style NGINX fill:#4CAF50
    style API1 fill:#2196F3
    style API2 fill:#2196F3
    style OLLAMA fill:#FF9800
```

### Diagramme Classes Principales

```mermaid
classDiagram
    class Settings {
        +str app_name
        +str environment
        +DatabaseSettings database
        +OllamaSettings ollama
        +ChromaDBSettings chromadb
        +create_directories()
        +model_dump_safe()
    }

    class RAGManager {
        -ChromaClient client
        -EmbeddingFunction embedding_fn
        -CircuitBreaker ollama_breaker
        +index_document(path, collection)
        +search(question, collection, n)
        +generate_answer(question, chunks)
        +list_collections()
    }

    class PortfolioDatabase {
        -Connection conn
        -Cursor cursor
        +add_position(ticker, qty, price)
        +sell_position(ticker, qty, price)
        +get_portfolio(user_id)
        +update_current_prices(user_id)
        +get_portfolio_summary(user_id)
    }

    class PortfolioManager {
        -PortfolioDatabase db
        -YahooFinanceService yf
        +get_portfolio_context_for_ai(user_id)
        +get_portfolio_health_score(user_id)
        +should_rebalance(user_id)
        +get_position_details(ticker, user_id)
    }

    class YahooFinanceService {
        -Dict cache
        -Lock cache_lock
        -int cache_ttl
        +get_stock_info(ticker)
        +get_historical_data(ticker, period)
        +get_financials(ticker)
        +clear_cache(ticker)
    }

    class TechnicalAnalyzer {
        +calculate_indicators(df)
        +detect_signals(df)
        +calculate_support_resistance(df)
        +calculate_trend(df)
    }

    class CircuitBreaker {
        -CircuitState state
        -int failure_count
        -float last_failure_time
        -Lock lock
        +call(func, args, kwargs)
        +protect(func)
        +call_with_fallback(func, fallback)
        +reset()
        +get_stats()
    }

    Settings --> RAGManager
    Settings --> PortfolioDatabase
    Settings --> YahooFinanceService

    PortfolioManager --> PortfolioDatabase
    PortfolioManager --> YahooFinanceService

    RAGManager --> CircuitBreaker
    TechnicalAnalyzer --> YahooFinanceService
```

---

## Conclusion

Cette architecture RAG-PEA a été conçue pour être:

1. **Modulaire** - Chaque composant est indépendant et testable
2. **Résiliente** - Circuit breakers, error handling, graceful degradation
3. **Observable** - Logging structuré, métriques, request tracking
4. **Performante** - Cache, async, optimisations DB
5. **Sécurisée** - Validation, rate limiting, secrets management
6. **Extensible** - Facile d'ajouter services, agents, endpoints

**Points forts:**
- Configuration centralisée avec validation
- Logging JSON structuré pour production
- Exceptions personnalisées avec codes HTTP appropriés
- Circuit breaker pour résilience
- Cache LRU avec TTL
- Architecture multi-agent CrewAI

**Limites actuelles:**
- Single-user (SQLite, pas d'auth)
- Single-machine (pas de distribution)
- Ollama local (nécessite GPU pour perf)

**Évolutions futures:**
- Multi-user avec PostgreSQL + JWT auth
- Scale horizontal avec load balancer
- Real-time data via WebSocket
- Machine learning pour prédictions
- Mobile app (React Native)

**Questions techniques?** Consultez:
- [TESTING.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/TESTING.md) - Guide tests
- [TROUBLESHOOTING.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/TROUBLESHOOTING.md) - Résolution problèmes
- [CONTRIBUTING.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/CONTRIBUTING.md) - Comment contribuer
- [API_REFERENCE.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/API_REFERENCE.md) - Référence API complète

---

**Document version:** 1.0.0
**Dernière mise à jour:** Février 2026
**Maintenu par:** Équipe RAG-PEA
