# 📊 RAG SYSTEM - Documentation Complète

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture du Système](#architecture-du-système)
3. [Fonctionnalités Implémentées](#fonctionnalités-implémentées)
4. [Configuration Complète](#configuration-complète)
5. [Guide de Test](#guide-de-test)
6. [Utilisation Quotidienne](#utilisation-quotidienne)
7. [Référence API](#référence-api)
8. [Dépannage](#dépannage)

---

## 🎯 Vue d'ensemble

Ce système RAG (Retrieval-Augmented Generation) est une plateforme complète d'analyse financière utilisant l'IA pour la gestion de portefeuille, l'analyse technique, la veille news, et le backtesting de stratégies d'investissement.

### 🌟 Points Clés

- **Intelligence Artificielle Multi-Agents** (CrewAI) pour l'analyse financière
- **Base de Données Vectorielle** (ChromaDB) pour la recherche de documents
- **Portfolio Manager Intelligent** avec scoring et recommandations
- **Analyse Technique Complète** (RSI, MACD, Bollinger, Support/Résistance)
- **Sentiment Analysis** des actualités avec Claude/GPT-4
- **Alertes Telegram** en temps réel
- **Backtesting** de stratégies
- **Extraction Intelligente** de documents financiers
- **API REST** complète avec FastAPI

### 🎓 Cas d'Usage Principal

**Investisseur PEA (Plan d'Épargne en Actions)** cherchant à :
- Construire un portefeuille optimal pour du long terme (5-10 ans)
- Suivre automatiquement les performances
- Recevoir des alertes sur les opportunités d'achat/vente
- Analyser les rapports financiers et actualités
- Backtester des stratégies avant investissement

---

## 🏗️ Architecture du Système

```
RAG-system/
├── api/
│   ├── main.py                          # FastAPI - Point d'entrée API
│   ├── database/
│   │   ├── portfolio_db.py              # Base SQLite pour le portefeuille
│   │   └── portfolio_manager.py         # Gestion intelligente du portefeuille
│   ├── services/
│   │   ├── yahoo_finance_service.py     # Données de marché (GRATUIT)
│   │   ├── sentiment_analyzer.py        # Analyse sentiment avec IA
│   │   ├── news_aggregator.py           # Agrégation d'actualités
│   │   ├── technical_analysis.py        # Indicateurs techniques
│   │   ├── telegram_bot.py              # Alertes Telegram
│   │   ├── smart_document_processor.py  # Extraction IA de documents
│   │   └── backtesting_engine.py        # Moteur de backtesting
│   └── agents/
│       ├── portfolio_builder_crew.py    # Crew pour construire portfolio
│       └── market_analyzer_crew.py      # Crew pour analyser le marché
├── scripts/
│   ├── document_indexer.py              # Indexation de documents dans ChromaDB
│   └── analyze_financial_reports.py     # Analyse de rapports
├── data/
│   ├── documents/                       # Documents PDF à indexer
│   └── chroma_db/                       # Base vectorielle ChromaDB
└── portfolio.db                         # Base de données SQLite (auto-créée)
```

### 🧠 Composants Clés

#### 1. **CrewAI Multi-Agents**
- **Portfolio Builder Crew** (6 agents) : Construction de portefeuille optimal
  - Data Collector Agent
  - Fundamental Analyst Agent
  - Technical Analyst Agent
  - Risk Manager Agent
  - Portfolio Optimizer Agent
  - Report Writer Agent

- **Market Analyzer Crew** (4 agents) : Analyse de marché complète
  - Market Researcher
  - Financial Analyst
  - Technical Analyst
  - Investment Advisor

#### 2. **Services Backend**
- **Yahoo Finance Service** : Données de marché gratuites (pas d'API key)
- **Portfolio Manager** : Gestion des positions, calcul de performance
- **Technical Analyzer** : Calcul d'indicateurs et signaux
- **Sentiment Analyzer** : Analyse IA des actualités
- **News Aggregator** : Collecte d'actualités multi-sources
- **Telegram Bot** : Notifications push
- **Document Processor** : Extraction IA de données financières
- **Backtesting Engine** : Validation de stratégies

#### 3. **Base de Données**
- **ChromaDB** (vectorielle) : Documents financiers indexés
- **SQLite** : Portfolio, transactions, historique d'analyses

---

## ✨ Fonctionnalités Implémentées

### 📊 1. Gestion de Portefeuille

#### Caractéristiques
- ✅ **Ajout/Vente de positions** avec calcul automatique de PRU (Prix de Revient Unitaire)
- ✅ **Calcul de plus-values** en temps réel
- ✅ **Historique des transactions** complet
- ✅ **Score de santé du portefeuille** (0-100) basé sur :
  - Diversification
  - Concentration des positions
  - Performance globale
- ✅ **Contexte IA** généré automatiquement pour les agents CrewAI
- ✅ **Recommandations de rééquilibrage**

#### Base de Données SQLite
Tables :
- `positions` : Positions actuelles (ticker, quantité, PRU, valeur actuelle)
- `transactions` : Historique (type, ticker, quantité, prix, date)
- `analysis_history` : Historique des analyses IA

#### Endpoints API
```
POST   /portfolio/add              # Ajouter une position
POST   /portfolio/sell             # Vendre une position
GET    /portfolio                  # Récupérer le portefeuille complet
GET    /portfolio/context          # Contexte formaté pour IA
GET    /portfolio/health           # Score de santé (0-100)
GET    /portfolio/rebalance        # Recommandations de rééquilibrage
GET    /portfolio/position/{ticker} # Détails d'une position
```

---

### 📈 2. Données de Marché (Yahoo Finance)

#### Caractéristiques
- ✅ **GRATUIT** - Pas besoin d'API key
- ✅ **25+ actions françaises** pré-configurées pour PEA
- ✅ **Données en temps réel** : Prix, P/E ratio, dividendes, capitalisation
- ✅ **Historique jusqu'à 10 ans**
- ✅ **Conversion automatique** EUR/USD

#### Tickers Supportés
```python
# Actions françaises
MC.PA (LVMH), OR.PA (L'Oréal), SU.PA (Schneider Electric),
AIR.PA (Airbus), BN.PA (Danone), SAF.PA (Safran),
TTE.PA (TotalEnergies), SAN.PA (Sanofi), CS.PA (AXA), etc.

# Indices
^FCHI (CAC 40)
```

#### Endpoints API
```
GET /market/stock/{ticker}          # Infos complètes sur une action
GET /market/history/{ticker}        # Historique (paramètres: period, interval)
```

---

### 🔍 3. Analyse Technique

#### Indicateurs Calculés
- ✅ **Moyennes Mobiles** : SMA 50, SMA 200, EMA 20
- ✅ **RSI** (Relative Strength Index)
- ✅ **MACD** (Moving Average Convergence Divergence)
- ✅ **Bandes de Bollinger**
- ✅ **Volume Analysis**
- ✅ **Support & Résistance** (3 niveaux les plus proches)
- ✅ **Tendance** (HAUSSIER / BAISSIER / NEUTRE)

#### Signaux de Trading
Le système détecte automatiquement :
- 🌟 **Golden Cross** (MA50 croise MA200 à la hausse) → TRÈS HAUSSIER
- 💀 **Death Cross** (MA50 croise MA200 à la baisse) → TRÈS BAISSIER
- 🔵 **RSI < 30** → Zone de survente (opportunité d'achat)
- 🔴 **RSI > 70** → Zone de surachat (risque de correction)
- 💎 **Prix proche bande basse Bollinger** → Opportunité
- ⚡ **Prix proche bande haute Bollinger** → Prudence
- 🔊 **Volume élevé** → Confirmation du mouvement

#### Score et Recommandation
- **Score** : de -100 (très baissier) à +100 (très haussier)
- **Recommandations** :
  - `ACHETER FORT` (score ≥ 50)
  - `ACHETER` (score ≥ 25)
  - `ACCUMULER` (score ≥ 10)
  - `CONSERVER` (score ≥ -10)
  - `ALLÉGER` (score ≥ -25)
  - `VENDRE` (score < -25)

#### Endpoint API
```
GET /analysis/technical/{ticker}
```

---

### 📰 4. Agrégation d'Actualités

#### Sources Supportées
- ✅ **NewsAPI** (100 requêtes/jour gratuites)
- ✅ **SerpAPI** (Google News) - optionnel
- ✅ **Fallback démo** si pas d'API configurée

#### Fonctionnalités
- Recherche par nom d'entreprise
- Filtrage par période (7 jours par défaut)
- Limitation du nombre de résultats
- Tri par date (plus récents en premier)

#### Endpoint API
```
GET /analysis/news/{company_name}?days_back=7&max_results=20
```

---

### 🧠 5. Analyse de Sentiment (IA)

#### Providers Supportés
- ✅ **Claude 3.5 Sonnet** (Anthropic) - recommandé
- ✅ **GPT-4 Turbo** (OpenAI) - alternative
- ✅ **Fallback par mots-clés** si pas d'IA

#### Analyse Fournie
- **Sentiment** : TRÈS POSITIF / POSITIF / NEUTRE / NÉGATIF / TRÈS NÉGATIF
- **Score d'impact** : 0-10 (impact sur le cours)
- **Recommandation** : ACHETER / RENFORCER / CONSERVER / ALLÉGER / VENDRE
- **Analyse complète** : Texte détaillé de l'analyse

#### Endpoint API
```
GET /analysis/sentiment/{company_name}
```

---

### 📱 6. Alertes Telegram

#### Types d'Alertes
- 🚨 **PRICE_DROP** : Baisse importante détectée
- 🚀 **PRICE_RISE** : Hausse importante détectée
- 💎 **BUY_OPPORTUNITY** : Opportunité d'achat (analyse technique favorable)
- ⚠️ **SELL_RECOMMENDATION** : Recommandation de vente
- 📰 **NEWS** : Actualité importante
- 📊 **TECHNICAL_SIGNAL** : Signal technique détecté

#### Messages Formatés
- Emojis selon le type d'alerte
- Prix actuel et variation %
- Analyse contextuelle
- Support du Markdown

#### Configuration
Nécessite 2 variables d'environnement :
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

---

### 📄 7. Extraction Intelligente de Documents

#### Fonctionnalités
- ✅ **Extraction IA** avec Claude ou GPT-4
- ✅ **Compression 90%+** du texte original
- ✅ **Extraction structurée** de données financières clés :
  - Chiffre d'affaires (CA) et évolution YoY
  - Résultat opérationnel et marge
  - Résultat net et marge nette
  - Dette nette et ratio d'endettement
  - Free cash flow
  - Dividendes et rendement
  - Guidance (prévisions)
  - Événements importants

#### Avantages
- **Réduction de coûts** : Pas besoin de stocker les documents complets
- **Recherche plus rapide** : Données structurées
- **Focus sur l'essentiel** : Ignore les disclaimers et détails non pertinents

#### Utilisation
```python
from services.smart_document_processor import SmartDocumentProcessor

processor = SmartDocumentProcessor(provider="claude")
result = processor.extract_key_financial_data(document_text, "LVMH")

print(f"Compression: {result['compression_ratio']:.1f}%")
print(result['extracted_data'])
```

---

### 📊 8. Backtesting de Stratégies

#### Stratégie Implémentée
**Simple Moving Average (SMA) Crossover** :
- **Achat** : Quand SMA courte (50j) croise SMA longue (200j) à la hausse (Golden Cross)
- **Vente** : Quand SMA courte croise SMA longue à la baisse (Death Cross)

#### Métriques Calculées
- ✅ **Total Return** : Rendement total de la stratégie
- ✅ **Annual Return** : Rendement annualisé
- ✅ **Volatility** : Volatilité annualisée (risque)
- ✅ **Sharpe Ratio** : Ratio rendement/risque (taux sans risque = 2%)
- ✅ **Maximum Drawdown** : Perte maximale depuis le plus haut
- ✅ **Win Rate** : % de trades gagnants
- ✅ **Number of Trades** : Nombre total de trades

#### Utilisation
```python
from services.backtesting_engine import BacktestingEngine

engine = BacktestingEngine(initial_capital=10000)
results = engine.run_simple_ma_strategy(
    ticker="MC.PA",
    historical_data=df,
    short_window=50,
    long_window=200
)

print(f"Total Return: {results['total_return']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
```

---

### 🤖 9. Agents CrewAI

#### Portfolio Builder Crew
**Objectif** : Construire un portefeuille optimal à partir de zéro

**6 Agents spécialisés** :
1. **Data Collector** : Collecte données de marché et rapports
2. **Fundamental Analyst** : Analyse fondamentale (P/E, dividendes, croissance)
3. **Technical Analyst** : Analyse technique (tendances, signaux)
4. **Risk Manager** : Évaluation des risques
5. **Portfolio Optimizer** : Allocation optimale selon Markowitz
6. **Report Writer** : Rédaction du rapport final

**Livrable** : Rapport complet avec allocations précises et ordres d'achat

#### Market Analyzer Crew
**Objectif** : Analyser une action spécifique en profondeur

**4 Agents spécialisés** :
1. **Market Researcher** : Recherche de documents et actualités
2. **Financial Analyst** : Analyse des données financières
3. **Technical Analyst** : Analyse des graphiques et indicateurs
4. **Investment Advisor** : Recommandation finale

**Livrable** : Analyse complète avec recommandation ACHETER/VENDRE/CONSERVER

---

### 🔍 10. Recherche Vectorielle (ChromaDB)

#### Fonctionnalités
- ✅ **Indexation de documents** PDF
- ✅ **Chunking intelligent** par page
- ✅ **Recherche sémantique** avec embeddings OpenAI
- ✅ **Métadonnées** : source, page, date

#### Utilisation
```bash
# Indexer des documents
cd scripts
python document_indexer.py

# Analyser avec RAG
python analyze_financial_reports.py
```

---

## ⚙️ Configuration Complète

### 1. Installation Rapide

```bash
# Cloner le repo
cd RAG-system

# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier .env
cp .env.example .env
```

### 2. Variables d'Environnement (.env)

```bash
# ============================================
# 1. OPENAI (REQUIS pour ChromaDB)
# ============================================
OPENAI_API_KEY=sk-...

# ============================================
# 2. DONNÉES DE MARCHÉ (OPTIONNEL)
# ============================================
# Yahoo Finance = GRATUIT (pas besoin d'API key)
# Alpha Vantage (optionnel, pour données US)
ALPHA_VANTAGE_API_KEY=votre_key

# ============================================
# 3. ACTUALITÉS (OPTIONNEL)
# ============================================
# NewsAPI : 100 requêtes/jour gratuit
# Récupérer sur : https://newsapi.org/
NEWSAPI_KEY=votre_newsapi_key

# SerpAPI (optionnel, Google News)
# Récupérer sur : https://serpapi.com/
SERPAPI_KEY=votre_serpapi_key

# ============================================
# 4. ANALYSE IA AVANCÉE (OPTIONNEL)
# ============================================
# Anthropic Claude (recommandé pour analyse de sentiment)
# Récupérer sur : https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-...

# Alternative : OpenAI GPT-4
# (Utilisez la même clé que ci-dessus)

# ============================================
# 5. ALERTES TELEGRAM (OPTIONNEL)
# ============================================
# Créer un bot : https://t.me/BotFather
TELEGRAM_BOT_TOKEN=123456789:ABC...
# Récupérer votre chat_id : https://t.me/userinfobot
TELEGRAM_CHAT_ID=123456789

# ============================================
# 6. ENVIRONNEMENT
# ============================================
ENV=development
```

### 3. Configuration Minimale (Démarrage Rapide)

**Pour commencer immédiatement, vous avez seulement besoin de** :
```bash
OPENAI_API_KEY=sk-...
```

Tout le reste fonctionne avec des fallbacks :
- ✅ Yahoo Finance = GRATUIT (pas d'API)
- ✅ Portfolio = SQLite local (auto-créé)
- ✅ News = Mode démo si pas de NewsAPI
- ✅ Sentiment = Analyse par mots-clés si pas d'IA
- ✅ Telegram = Logs console si pas configuré

### 4. Obtenir les Clés API

#### OpenAI (REQUIS)
1. Aller sur https://platform.openai.com/api-keys
2. Créer un nouveau projet
3. Générer une clé API
4. Ajouter du crédit (minimum 5$)

#### NewsAPI (100 req/jour GRATUIT)
1. Aller sur https://newsapi.org/register
2. Créer un compte gratuit
3. Copier votre API key

#### Anthropic Claude (OPTIONNEL)
1. Aller sur https://console.anthropic.com/
2. Créer un compte
3. Ajouter du crédit (minimum 5$)
4. Générer une API key

#### Telegram Bot (OPTIONNEL)
1. Ouvrir Telegram et chercher `@BotFather`
2. Taper `/newbot` et suivre les instructions
3. Copier le token fourni
4. Chercher `@userinfobot` et taper `/start` pour obtenir votre chat_id

---

## 🧪 Guide de Test

### Test 1 : Vérifier l'Installation

```bash
cd api
python -m uvicorn main:app --reload
```

Ouvrir : http://localhost:8000/docs

✅ Vous devriez voir la documentation Swagger avec tous les endpoints

### Test 2 : Données de Marché (Yahoo Finance)

```bash
curl http://localhost:8000/market/stock/MC.PA
```

**Résultat attendu** :
```json
{
  "ticker": "MC.PA",
  "name": "LVMH Moët Hennessy Louis Vuitton SE",
  "current_price": 750.50,
  "pe_ratio": 25.3,
  "dividend_yield": 2.1,
  "market_cap": 375000000000,
  "sector": "Consumer Cyclical"
}
```

### Test 3 : Ajouter une Position au Portfolio

```bash
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "price": 750.00
  }'
```

**Résultat attendu** :
```json
{
  "message": "Position ajoutée/mise à jour",
  "position": {
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "average_price": 750.00,
    "total_invested": 7500.00
  }
}
```

### Test 4 : Récupérer le Portfolio

```bash
curl http://localhost:8000/portfolio
```

**Résultat attendu** :
```json
{
  "total_value": 7505.00,
  "total_invested": 7500.00,
  "total_gain_loss": 5.00,
  "total_gain_loss_percent": 0.07,
  "positions": [
    {
      "ticker": "MC.PA",
      "company_name": "LVMH",
      "quantity": 10,
      "average_price": 750.00,
      "current_price": 750.50,
      "total_value": 7505.00,
      "gain_loss": 5.00,
      "gain_loss_percent": 0.07
    }
  ]
}
```

### Test 5 : Score de Santé du Portfolio

```bash
curl http://localhost:8000/portfolio/health
```

**Résultat attendu** :
```json
{
  "health_score": 45,
  "grade": "C",
  "issues": [
    "Portfolio très peu diversifié (1 positions)"
  ],
  "recommendations": [
    "Diversifier avec au moins 10-15 actions différentes",
    "Équilibrer les secteurs pour réduire le risque"
  ]
}
```

### Test 6 : Analyse Technique

```bash
curl http://localhost:8000/analysis/technical/MC.PA
```

**Résultat attendu** :
```json
{
  "ticker": "MC.PA",
  "score": 35,
  "recommendation": "ACHETER",
  "signals": [
    "✅ Prix au-dessus des MA 50 et 200 (haussier)",
    "⚪ RSI à 55.2 - Zone neutre",
    "📈 MACD au-dessus du signal (momentum haussier)"
  ],
  "current_price": 750.50,
  "sma_50": 730.25,
  "sma_200": 710.80,
  "rsi": 55.2,
  "support_resistance": {
    "supports": [740.00, 720.00, 700.00],
    "resistances": [765.00, 780.00, 800.00]
  }
}
```

### Test 7 : Actualités

```bash
curl http://localhost:8000/analysis/news/LVMH
```

**Résultat attendu** :
```json
{
  "company": "LVMH",
  "total_articles": 15,
  "articles": [
    {
      "title": "LVMH reports strong Q4 results",
      "description": "Luxury giant beats expectations...",
      "url": "https://...",
      "published_at": "2024-01-15T10:30:00Z",
      "source": "Reuters"
    }
  ]
}
```

### Test 8 : Sentiment Analysis

```bash
curl http://localhost:8000/analysis/sentiment/LVMH
```

**Résultat attendu** (avec API Claude/OpenAI) :
```json
{
  "company": "LVMH",
  "sentiment": "POSITIF",
  "impact_score": 7,
  "recommendation": "RENFORCER",
  "full_analysis": "Les actualités récentes sur LVMH sont majoritairement positives..."
}
```

### Test 9 : Analyse Complète

```bash
curl http://localhost:8000/analysis/complete/MC.PA?company_name=LVMH
```

**Résultat attendu** :
```json
{
  "ticker": "MC.PA",
  "company_name": "LVMH",
  "market_data": { ... },
  "technical_analysis": { ... },
  "news": { ... },
  "sentiment": { ... },
  "overall_recommendation": "ACHETER",
  "confidence": 75
}
```

### Test 10 : CrewAI Portfolio Builder

```bash
cd api/agents
python portfolio_builder_crew.py
```

**Résultat attendu** :
- Exécution de 6 agents séquentiels
- Génération d'un rapport complet
- Allocations optimales pour 10-15 actions
- Liste précise d'ordres d'achat

⏱️ Durée : 5-10 minutes

### Test 11 : Indexation de Documents

```bash
# Placer des PDFs dans data/documents/
cp rapport_LVMH.pdf data/documents/

# Indexer
cd scripts
python document_indexer.py

# Vérifier
python analyze_financial_reports.py
```

**Résultat attendu** :
- Documents détectés et indexés dans ChromaDB
- Analyse générée avec citations des documents

---

## 📅 Utilisation Quotidienne

### Workflow Recommandé pour Investisseur PEA

#### 🌅 **Matin (10 minutes)**

**1. Vérifier le portfolio**
```bash
curl http://localhost:8000/portfolio
```
- Voir la performance globale
- Identifier les plus/moins values

**2. Vérifier les actualités importantes**
```bash
# Pour chaque position du portfolio
curl http://localhost:8000/analysis/news/LVMH
curl http://localhost:8000/analysis/news/Airbus
# etc.
```

**3. Consulter le score de santé**
```bash
curl http://localhost:8000/portfolio/health
```
- Score < 50 → Rééquilibrage nécessaire
- Suivre les recommandations

#### 🔍 **Recherche d'Opportunités (hebdomadaire)**

**1. Analyser une nouvelle action**
```bash
curl http://localhost:8000/analysis/complete/AIR.PA?company_name=Airbus
```

**2. Vérifier l'analyse technique**
```bash
curl http://localhost:8000/analysis/technical/AIR.PA
```
- Score > 25 → Potentiel d'achat
- RSI < 30 → Zone de survente (opportunité)

**3. Lire le sentiment des news**
```bash
curl http://localhost:8000/analysis/sentiment/Airbus
```
- Sentiment POSITIF + Score > 7 → Bonne période
- Sentiment NÉGATIF → Attendre ou approfondir

**4. Demander un portfolio optimal**
```bash
cd api/agents
python portfolio_builder_crew.py
```
⏱️ 5-10 minutes
📊 Résultat : Liste précise d'ordres d'achat

#### 💼 **Gestion de Positions**

**Acheter une nouvelle position**
```bash
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AIR.PA",
    "company_name": "Airbus",
    "quantity": 5,
    "price": 145.50
  }'
```

**Renforcer une position existante**
```bash
# Le système calcule automatiquement le nouveau PRU
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 2,
    "price": 735.00
  }'
```

**Vendre une position**
```bash
curl -X POST http://localhost:8000/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "quantity": 5,
    "price": 760.00
  }'
```

#### 📊 **Backtesting (avant achat)**

```python
# Tester la stratégie SMA sur LVMH des 5 dernières années
from services.backtesting_engine import BacktestingEngine
from services.yahoo_finance_service import YahooFinanceService

# Récupérer les données
yf = YahooFinanceService()
history = yf.get_historical_data("MC.PA", period="5y")

# Backtest
engine = BacktestingEngine(initial_capital=10000)
results = engine.run_simple_ma_strategy(
    ticker="MC.PA",
    historical_data=history,
    short_window=50,
    long_window=200
)

print(f"Rendement annuel: {results['annual_return']:.2f}%")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
print(f"Win Rate: {results['win_rate']:.2f}%")

# Si Sharpe > 1 et Max Drawdown < 20% → Bonne stratégie
```

#### 🔔 **Configuration des Alertes Telegram**

**1. Créer un monitoring script**

```python
# monitor.py
import time
import requests
from services.telegram_bot import TelegramBot
from services.yahoo_finance_service import YahooFinanceService

bot = TelegramBot()
yf = YahooFinanceService()

# Liste des tickers à surveiller
WATCHLIST = ["MC.PA", "AIR.PA", "OR.PA", "SU.PA"]

while True:
    for ticker in WATCHLIST:
        # Récupérer prix actuel
        stock = yf.get_stock_info(ticker)

        # Analyse technique
        response = requests.get(f"http://localhost:8000/analysis/technical/{ticker}")
        analysis = response.json()

        # Alertes
        if analysis['recommendation'] == "ACHETER FORT":
            bot.send_alert(
                ticker=ticker,
                company_name=stock['name'],
                alert_type="BUY_OPPORTUNITY",
                current_price=stock['current_price'],
                change_percent=stock['change_percent']
            )

        # Vérifier les news
        response = requests.get(f"http://localhost:8000/analysis/sentiment/{stock['name']}")
        sentiment = response.json()

        if sentiment['impact_score'] >= 8:
            bot.send_message(f"📰 Actualité importante pour {stock['name']}\n{sentiment['full_analysis']}")

    # Attendre 1 heure
    time.sleep(3600)
```

**2. Lancer le monitoring**
```bash
python monitor.py
```

#### 📄 **Analyser un Nouveau Rapport Financier**

```bash
# 1. Télécharger le PDF (ex: rapport LVMH)
# 2. Le placer dans data/documents/
cp ~/Downloads/rapport_LVMH_2024.pdf data/documents/

# 3. Indexer dans ChromaDB
cd scripts
python document_indexer.py

# 4. Extraire les données clés avec IA
cd ../api
python -c "
from services.smart_document_processor import SmartDocumentProcessor

with open('../data/documents/rapport_LVMH_2024.pdf', 'rb') as f:
    # Convertir PDF en texte (utiliser PyPDF2 ou similaire)
    text = extract_text_from_pdf(f)

processor = SmartDocumentProcessor(provider='claude')
result = processor.extract_key_financial_data(text, 'LVMH')

print(result['extracted_data'])
"
```

#### 🎯 **Stratégie Long Terme Recommandée**

**Profil : Investisseur PEA long terme (5-10 ans)**

**1. Construction du Portfolio (une fois)**
```bash
cd api/agents
python portfolio_builder_crew.py
```
→ Suivre les allocations recommandées

**2. Suivi Mensuel**
- Vérifier le score de santé
- Rééquilibrer si score < 50
- Ajouter du capital progressivement (DCA - Dollar Cost Averaging)

**3. Alertes à Configurer**
- Baisse > 10% → Opportunité de renforcement ?
- Hausse > 15% → Prendre des bénéfices partiels ?
- RSI < 30 sur une position du portefeuille → Renforcer
- Actualité négative (impact > 7) → Analyser en profondeur

**4. Critères de Sélection**
Utiliser l'analyse complète pour valider :
- ✅ Entreprise profitable (P/E < 30)
- ✅ Dividendes stables (rendement 2-4%)
- ✅ Tendance long terme haussière (SMA200)
- ✅ Actualités positives (sentiment > NEUTRE)
- ✅ Secteur en croissance

---

## 📡 Référence API

### Base URL
```
http://localhost:8000
```

### Endpoints Disponibles

#### Portfolio Management

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/portfolio/add` | Ajouter/Renforcer une position |
| POST | `/portfolio/sell` | Vendre une position |
| GET | `/portfolio` | Récupérer le portfolio complet |
| GET | `/portfolio/context` | Contexte formaté pour IA |
| GET | `/portfolio/health` | Score de santé (0-100) |
| GET | `/portfolio/rebalance` | Recommandations de rééquilibrage |
| GET | `/portfolio/position/{ticker}` | Détails d'une position |

#### Market Data

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/market/stock/{ticker}` | Infos complètes sur une action |
| GET | `/market/history/{ticker}` | Historique (params: period, interval) |

#### Analysis

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/analysis/news/{company_name}` | Actualités récentes |
| GET | `/analysis/sentiment/{company_name}` | Analyse de sentiment IA |
| GET | `/analysis/technical/{ticker}` | Analyse technique complète |
| GET | `/analysis/complete/{ticker}` | Analyse globale (market + news + sentiment + technical) |

#### Documents

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/analyze` | Analyser avec RAG (CrewAI) |
| POST | `/query` | Recherche vectorielle simple |

### Exemples de Requêtes

#### Ajouter une Position
```bash
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "price": 750.00
  }'
```

#### Vendre une Position
```bash
curl -X POST http://localhost:8000/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "quantity": 5,
    "price": 760.00
  }'
```

#### Récupérer le Portfolio
```bash
curl http://localhost:8000/portfolio
```

#### Infos sur une Action
```bash
curl http://localhost:8000/market/stock/MC.PA
```

#### Historique 1 An
```bash
curl "http://localhost:8000/market/history/MC.PA?period=1y&interval=1d"
```

#### Analyse Technique
```bash
curl http://localhost:8000/analysis/technical/MC.PA
```

#### Actualités
```bash
curl "http://localhost:8000/analysis/news/LVMH?days_back=7&max_results=20"
```

#### Sentiment Analysis
```bash
curl http://localhost:8000/analysis/sentiment/LVMH
```

#### Analyse Complète
```bash
curl "http://localhost:8000/analysis/complete/MC.PA?company_name=LVMH"
```

---

## 🔧 Dépannage

### Problème : API ne démarre pas

**Erreur** : `ModuleNotFoundError: No module named 'fastapi'`

**Solution** :
```bash
pip install -r requirements.txt
```

---

### Problème : ChromaDB ne fonctionne pas

**Erreur** : `chromadb.errors.InvalidDimensionException`

**Solution** :
```bash
# Supprimer la base existante
rm -rf data/chroma_db

# Réindexer
cd scripts
python document_indexer.py
```

---

### Problème : Yahoo Finance rate limit

**Erreur** : `Too Many Requests`

**Solution** :
Attendre quelques minutes entre les requêtes. Yahoo Finance limite à ~2000 req/heure.

---

### Problème : NewsAPI limite dépassée

**Erreur** : `rateLimited`

**Solution** :
Le plan gratuit NewsAPI est limité à 100 requêtes/jour. Le système bascule automatiquement en mode démo.

Pour augmenter :
- Passer au plan payant NewsAPI
- Utiliser SerpAPI (configurer `SERPAPI_KEY`)

---

### Problème : Telegram ne reçoit pas les messages

**Solution** :
```bash
# Vérifier la configuration
python -c "
from services.telegram_bot import TelegramBot
bot = TelegramBot()
print('Configured:', bot.is_configured())
bot.send_message('Test message')
"
```

Si échec :
1. Vérifier `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` dans `.env`
2. Tester le bot manuellement sur Telegram
3. S'assurer que le bot a été démarré (`/start`)

---

### Problème : IA (Claude/OpenAI) ne fonctionne pas

**Erreur** : `AuthenticationError` ou `Invalid API key`

**Solution** :
```bash
# Vérifier les clés
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Tester directement
python -c "
from anthropic import Anthropic
client = Anthropic()
response = client.messages.create(
    model='claude-3-5-sonnet-20241022',
    max_tokens=100,
    messages=[{'role': 'user', 'content': 'Test'}]
)
print(response.content[0].text)
"
```

Le système bascule automatiquement en mode fallback (analyse par mots-clés) si pas d'IA configurée.

---

### Problème : Portfolio vide après redémarrage

**Cause** : Base SQLite supprimée ou corrompue

**Solution** :
```bash
# Vérifier si la base existe
ls -lh portfolio.db

# Si corrompue, recréer
rm portfolio.db
# Relancer l'API, la base sera recréée automatiquement
```

---

### Problème : CrewAI prend trop de temps

**Cause** : Les agents font beaucoup de recherches

**Solutions** :
1. Réduire le nombre d'actions à analyser (modifier `ACTIONS_TO_ANALYZE` dans `portfolio_builder_crew.py`)
2. Utiliser un modèle plus rapide (modifier `llm` dans les agents)
3. Augmenter le `max_iter` si les agents échouent

---

### Problème : Erreur lors de l'indexation PDF

**Erreur** : `PyPDF2.errors.PdfReadError`

**Solution** :
Certains PDFs sont protégés ou corrompus. Essayer :
```bash
# Convertir le PDF avec un outil externe
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -o output.pdf input.pdf

# Puis indexer
python document_indexer.py
```

---

## 📊 Limites et Améliorations Futures

### Limites Actuelles

1. **Yahoo Finance** : Données légèrement différées (15-20 min), pas de données intraday
2. **NewsAPI gratuit** : 100 requêtes/jour max
3. **Backtesting** : Une seule stratégie implémentée (SMA crossover)
4. **Portfolio** : Pas de gestion multi-utilisateurs (user_id par défaut)
5. **Telegram** : Monitoring manuel (pas d'alertes automatiques configurées)

### Améliorations Prévues

- [ ] **WebSocket** pour données en temps réel
- [ ] **Plus de stratégies de backtesting** (RSI, Bollinger, MACD)
- [ ] **Optimisation de paramètres** de stratégies (grid search)
- [ ] **Walk-forward analysis** pour backtesting robuste
- [ ] **Screener d'actions** automatique
- [ ] **Alertes automatiques** configurables via API
- [ ] **Dashboard web** (React + Charts)
- [ ] **Export Excel** des analyses
- [ ] **Intégration brokers** (passage d'ordres automatique)
- [ ] **Machine Learning** pour prédictions de prix
- [ ] **OCR** pour extraire données de screenshots

---

## 📚 Ressources et Support

### Documentation
- FastAPI : https://fastapi.tiangolo.com/
- CrewAI : https://docs.crewai.com/
- ChromaDB : https://docs.trychroma.com/
- yfinance : https://pypi.org/project/yfinance/
- pandas-ta : https://github.com/twopirllc/pandas-ta

### APIs
- Yahoo Finance : https://finance.yahoo.com/
- NewsAPI : https://newsapi.org/docs
- Anthropic Claude : https://docs.anthropic.com/
- OpenAI : https://platform.openai.com/docs

### Support
- Issues GitHub : [Créer une issue]
- Email : votre@email.com
- Telegram Community : [Lien vers groupe]

---

## 📄 Licence

MIT License - Libre d'utilisation et de modification

---

## 🎉 Conclusion

Vous disposez maintenant d'un système complet d'analyse financière et de gestion de portefeuille, propulsé par l'IA.

**Ce que vous pouvez faire** :
- ✅ Construire un portefeuille optimal pour le PEA
- ✅ Suivre vos performances en temps réel
- ✅ Recevoir des alertes sur opportunités d'achat/vente
- ✅ Analyser des rapports financiers automatiquement
- ✅ Backtester des stratégies avant investissement
- ✅ Prendre des décisions basées sur des données et l'IA

**Configuration minimale** :
- 1 clé API OpenAI
- 5 minutes de setup

**Configuration complète** :
- OpenAI + Claude + NewsAPI + Telegram
- Alertes automatiques et analyse avancée

---

**Bon investissement ! 📈**
