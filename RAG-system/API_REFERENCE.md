# API Reference - RAG-PEA System

**Base URL:** `http://localhost:8000`
**Version:** 1.0.0
**Format:** JSON

Documentation interactive complète: http://localhost:8000/docs

---

## Table des Matières

- [Authentification](#authentification)
- [Codes de Réponse](#codes-de-réponse)
- [Rate Limiting](#rate-limiting)
- [System](#system)
- [Portfolio Management](#portfolio-management)
- [Market Data](#market-data)
- [Analysis](#analysis)
- [RAG Documents](#rag-documents)
- [Collections](#collections)
- [AI Agents](#ai-agents)

---

## Authentification

**État actuel:** Aucune authentification requise (single-user mode)

**Future:** JWT tokens pour multi-user

---

## Codes de Réponse

| Code | Signification | Description |
|------|---------------|-------------|
| 200 | OK | Requête réussie |
| 400 | Bad Request | Paramètres invalides |
| 404 | Not Found | Ressource non trouvée |
| 422 | Unprocessable Entity | Validation échouée |
| 429 | Too Many Requests | Rate limit dépassé |
| 500 | Internal Server Error | Erreur serveur |
| 503 | Service Unavailable | Service externe indisponible |

**Format erreur:**

```json
{
  "error": {
    "message": "Description erreur",
    "code": "ERROR_CODE",
    "details": {
      "field": "valeur"
    }
  }
}
```

---

## Rate Limiting

**Limites:**
- 60 requêtes/minute par IP
- 1000 requêtes/heure par IP

**Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1234567890
```

**Dépassement:**
```json
{
  "error": {
    "message": "Rate limit exceeded",
    "code": "RATE_LIMIT_EXCEEDED",
    "details": {
      "retry_after": 60
    }
  }
}
```

---

## System

### GET / - Page d'accueil

**Description:** Informations sur l'API

**Exemple:**

```bash
curl http://localhost:8000/
```

**Réponse:**

```json
{
  "message": "API RAG Multi-Documents",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

### GET /health - Health Check

**Description:** Vérifie état de l'API et services

**Exemple:**

```bash
curl http://localhost:8000/health
```

**Réponse:**

```json
{
  "status": "healthy",
  "ollama_available": true,
  "collections": ["lvmh_2024", "bnp_2024"],
  "version": "1.0.0"
}
```

---

## Portfolio Management

### POST /portfolio/add - Ajouter Position

**Description:** Ajoute ou met à jour une position

**Body:**

```json
{
  "ticker": "MC.PA",
  "company_name": "LVMH",
  "quantity": 10,
  "price": 750.0,
  "user_id": "default_user"
}
```

**Validation:**
- `ticker`: Format ticker Euronext (ex: MC.PA)
- `quantity`: > 0
- `price`: > 0

**Exemple:**

```bash
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "price": 750.0
  }'
```

**Réponse:**

```json
{
  "message": "Position LVMH ajoutée avec succès",
  "ticker": "MC.PA"
}
```

---

### POST /portfolio/sell - Vendre Position

**Description:** Vend partiellement ou totalement une position

**Body:**

```json
{
  "ticker": "MC.PA",
  "quantity": 5,
  "price": 780.0,
  "user_id": "default_user"
}
```

**Exemple:**

```bash
curl -X POST http://localhost:8000/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "quantity": 5,
    "price": 780.0
  }'
```

**Réponse:**

```json
{
  "message": "Vente de 5 actions MC.PA enregistrée"
}
```

**Erreurs:**
- 404: Position non trouvée
- 400: Quantité insuffisante

---

### GET /portfolio - Vue d'Ensemble

**Description:** Récupère portefeuille complet avec prix à jour

**Paramètres query:**
- `user_id` (optionnel): ID utilisateur (défaut: "default_user")

**Exemple:**

```bash
curl "http://localhost:8000/portfolio?user_id=default_user"
```

**Réponse:**

```json
{
  "total_positions": 3,
  "total_value": 25430.50,
  "total_invested": 22150.00,
  "total_gain_loss": 3280.50,
  "total_gain_loss_percent": 14.81,
  "positions": [
    {
      "ticker": "MC.PA",
      "company_name": "LVMH",
      "quantity": 10,
      "avg_price": 700.0,
      "current_price": 752.30,
      "current_value": 7523.00,
      "invested_value": 7000.00,
      "gain_loss": 523.00,
      "gain_loss_percent": 7.47,
      "last_updated": "2026-02-01T14:23:45Z"
    }
  ]
}
```

---

### GET /portfolio/health - Score Santé

**Description:** Calcule score de santé 0-100

**Exemple:**

```bash
curl http://localhost:8000/portfolio/health
```

**Réponse:**

```json
{
  "score": 85,
  "grade": "A (Très Bien)",
  "total_positions": 8,
  "total_value": 25430.50,
  "performance": 14.81,
  "issues": [],
  "recommendations": [
    "Portfolio en bonne santé, continuer le suivi régulier"
  ]
}
```

**Grades:**
- A+ (90-100): Excellent
- A (80-89): Très bien
- B (70-79): Bien
- C (60-69): Moyen
- D (50-59): Faible
- F (0-49): Mauvais

---

### GET /portfolio/rebalance - Recommandations Rééquilibrage

**Description:** Analyse besoins de rééquilibrage

**Exemple:**

```bash
curl http://localhost:8000/portfolio/rebalance
```

**Réponse:**

```json
{
  "needs_rebalance": true,
  "portfolio_size": 8,
  "total_value": 25430.50,
  "recommendations": [
    {
      "action": "REDUCE",
      "ticker": "MC.PA",
      "company": "LVMH",
      "current_weight": 29.6,
      "target_weight": 20.0,
      "reason": "Concentration excessive (>25%)",
      "urgency": "MEDIUM"
    },
    {
      "action": "INCREASE",
      "ticker": "AIR.PA",
      "company": "Airbus",
      "current_weight": 4.2,
      "target_weight": 8.0,
      "reason": "Position trop faible, peut être renforcée",
      "urgency": "LOW"
    }
  ]
}
```

---

### GET /portfolio/position/{ticker} - Détails Position

**Description:** Détails complets d'une position

**Exemple:**

```bash
curl http://localhost:8000/portfolio/position/MC.PA
```

**Réponse:**

```json
{
  "position": {
    "ticker": "MC.PA",
    "quantity": 10,
    "avg_price": 700.0,
    "current_price": 752.30,
    "gain_loss_percent": 7.47
  },
  "market_data": {
    "current_price": 752.30,
    "pe_ratio": 24.5,
    "dividend_yield": 2.1,
    "52w_high": 820.0,
    "52w_low": 650.0
  },
  "transactions": [
    {
      "type": "BUY",
      "quantity": 10,
      "price": 700.0,
      "date": "2025-12-15T10:30:00Z"
    }
  ],
  "past_analyses": []
}
```

---

### GET /portfolio/context - Contexte IA

**Description:** Contexte formaté pour LLM

**Exemple:**

```bash
curl http://localhost:8000/portfolio/context
```

**Réponse:**

```json
{
  "context": "PORTEFEUILLE ACTUEL DE L'UTILISATEUR:\n\n💰 Valeur totale: 25,430.50 €\n📊 Montant investi: 22,150.00 €\n📈 Plus/Moins-value: 3,280.50 € (+14.81%)\n\n📍 POSITIONS (3 entreprises):\n..."
}
```

---

## Market Data

### GET /market/stock/{ticker} - Infos Action

**Description:** Données marché Yahoo Finance (gratuit)

**Exemple:**

```bash
curl http://localhost:8000/market/stock/MC.PA
```

**Réponse:**

```json
{
  "ticker": "MC.PA",
  "name": "LVMH Moet Hennessy Louis Vuitton SE",
  "sector": "Consumer Cyclical",
  "industry": "Luxury Goods",
  "current_price": 752.30,
  "previous_close": 745.20,
  "day_change_percent": 0.95,
  "market_cap": 375000000000,
  "pe_ratio": 24.5,
  "forward_pe": 22.1,
  "dividend_yield": 2.1,
  "payout_ratio": 45.2,
  "52w_high": 820.0,
  "52w_low": 650.0,
  "avg_volume": 1250000,
  "beta": 1.15,
  "profit_margin": 28.5,
  "debt_to_equity": 0.42,
  "return_on_equity": 22.3
}
```

**Erreurs:**
- 404: Ticker non trouvé

---

### GET /market/history/{ticker} - Historique Cours

**Description:** Historique OHLCV

**Paramètres query:**
- `period`: 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, max (défaut: 1y)
- `interval`: 1d, 1wk, 1mo (défaut: 1d)

**Exemple:**

```bash
curl "http://localhost:8000/market/history/MC.PA?period=6mo&interval=1d"
```

**Réponse:**

```json
{
  "ticker": "MC.PA",
  "period": "6mo",
  "interval": "1d",
  "data_points": 126,
  "data": [
    {
      "Date": "2025-08-01",
      "Open": 710.50,
      "High": 720.30,
      "Low": 708.10,
      "Close": 715.20,
      "Volume": 1234567
    }
  ]
}
```

---

## Analysis

### GET /analysis/technical/{ticker} - Analyse Technique

**Description:** Indicateurs techniques complets

**Paramètres query:**
- `period`: Période historique (défaut: 6mo)

**Exemple:**

```bash
curl "http://localhost:8000/analysis/technical/MC.PA?period=6mo"
```

**Réponse:**

```json
{
  "ticker": "MC.PA",
  "signals": {
    "golden_cross": false,
    "death_cross": false,
    "rsi_oversold": true,
    "rsi_overbought": false,
    "macd_bullish_cross": true,
    "bb_breakout_up": false
  },
  "current_values": {
    "rsi": 28.5,
    "macd": 2.3,
    "price_vs_sma20": -3.2,
    "price_vs_sma50": -8.7
  },
  "levels": {
    "support": 720.0,
    "resistance": 780.0,
    "distance_to_support": -4.3,
    "distance_to_resistance": 3.7
  },
  "trend": "BULLISH",
  "recommendation": "BUY",
  "confidence": 0.75
}
```

**Signaux détectés:**
- **Golden Cross:** SMA50 croise SMA200 vers le haut
- **Death Cross:** SMA50 croise SMA200 vers le bas
- **RSI Oversold:** RSI < 30
- **RSI Overbought:** RSI > 70
- **MACD Cross:** MACD croise signal line

---

### GET /analysis/news/{company_name} - Actualités

**Description:** Actualités récentes

**Paramètres query:**
- `days_back`: Nombre jours (défaut: 7)

**Exemple:**

```bash
curl "http://localhost:8000/analysis/news/LVMH?days_back=7"
```

**Réponse:**

```json
{
  "company": "LVMH",
  "news_count": 12,
  "articles": [
    {
      "title": "LVMH dépasse les attentes au Q4 2025",
      "description": "Le géant du luxe annonce...",
      "url": "https://...",
      "source": "Reuters",
      "published_at": "2026-02-01T10:30:00Z",
      "relevance_score": 0.95,
      "sentiment_preview": "POSITIVE"
    }
  ]
}
```

---

### GET /analysis/sentiment/{company_name} - Analyse Sentiment

**Description:** Sentiment actualités avec IA

**Exemple:**

```bash
curl "http://localhost:8000/analysis/sentiment/LVMH?days_back=7"
```

**Réponse:**

```json
{
  "overall_sentiment": 0.72,
  "sentiment_label": "POSITIVE",
  "confidence": 0.85,
  "positive_count": 9,
  "neutral_count": 2,
  "negative_count": 1,
  "key_themes": [
    "strong earnings",
    "China recovery",
    "innovation"
  ],
  "risk_factors": [
    "regulatory concerns"
  ]
}
```

**Score sentiment:**
- 0.7 à 1.0: Très positif
- 0.3 à 0.7: Positif
- -0.3 à 0.3: Neutre
- -0.7 à -0.3: Négatif
- -1.0 à -0.7: Très négatif

---

### GET /analysis/complete/{ticker} - Analyse Complète

**Description:** Analyse all-in-one (market + news + technical + sentiment)

**Paramètres query:**
- `company_name`: Nom entreprise (requis)

**Exemple:**

```bash
curl "http://localhost:8000/analysis/complete/MC.PA?company_name=LVMH"
```

**Réponse:**

```json
{
  "ticker": "MC.PA",
  "company": "LVMH",
  "market_data": {
    "current_price": 752.30,
    "pe_ratio": 24.5,
    "dividend_yield": 2.1
  },
  "news_sentiment": {
    "overall_sentiment": 0.72,
    "sentiment_label": "POSITIVE"
  },
  "technical_analysis": {
    "signals": {
      "rsi_oversold": true,
      "macd_bullish_cross": true
    },
    "levels": {
      "support": 720.0,
      "resistance": 780.0
    },
    "trend": "BULLISH",
    "recommendation": "BUY",
    "confidence": 0.75
  }
}
```

---

## RAG Documents

### POST /upload - Upload PDF

**Description:** Upload et indexe un document PDF

**Form Data:**
- `file`: Fichier PDF
- `collection_name` (optionnel): Nom collection

**Exemple:**

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/lvmh_rapport_2024.pdf" \
  -F "collection_name=lvmh_2024"
```

**Réponse:**

```json
{
  "success": true,
  "collection_name": "lvmh_2024",
  "total_chunks": 245,
  "table_chunks": 18,
  "text_chunks": 227,
  "message": "Document indexé avec succès en 5.23s"
}
```

---

### POST /index - Indexer Document Existant

**Description:** Indexe un document depuis un chemin

**Body:**

```json
{
  "file_path": "/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/data/documents/lvmh_rapport_2024.pdf",
  "document_name": "LVMH Rapport Annuel 2024",
  "collection_name": "lvmh_2024"
}
```

**Exemple:**

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.pdf",
    "collection_name": "lvmh_2024"
  }'
```

**Réponse:** Identique à /upload

---

### POST /query - Requête RAG

**Description:** Recherche sémantique + génération optionnelle

**Body:**

```json
{
  "question": "Quel est le chiffre d'affaires 2024?",
  "collection_name": "lvmh_2024",
  "n_results": 5,
  "filter_tables": false,
  "generate_answer": true
}
```

**Paramètres:**
- `question`: Question (min 3 caractères)
- `collection_name`: Nom collection
- `n_results`: Nombre chunks (1-20, défaut: 5)
- `filter_tables`: Ne chercher que dans tableaux
- `generate_answer`: Générer réponse avec Ollama

**Exemple:**

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quel est le chiffre d affaires 2024?",
    "collection_name": "lvmh_2024",
    "n_results": 5,
    "generate_answer": true
  }'
```

**Réponse:**

```json
{
  "question": "Quel est le chiffre d'affaires 2024?",
  "answer": "Le chiffre d'affaires de LVMH en 2024 s'élève à 86.2 milliards d'euros, en hausse de 14% par rapport à 2023.",
  "chunks": [
    {
      "chunk_id": "lvmh_2024_chunk_42",
      "text": "Chiffre d'affaires 2024: 86.2 milliards EUR (+14% vs 2023)...",
      "score": 0.8542,
      "content_type": "text",
      "num_tokens": 256,
      "metadata": {
        "page": 15,
        "section": "Financial Results"
      }
    }
  ],
  "collection_name": "lvmh_2024",
  "processing_time": 2.45
}
```

---

## Collections

### GET /collections - Liste Collections

**Description:** Liste toutes collections ChromaDB

**Exemple:**

```bash
curl http://localhost:8000/collections
```

**Réponse:**

```json
[
  {
    "name": "lvmh_2024",
    "total_chunks": 245,
    "text_chunks": 227,
    "table_chunks": 18,
    "table_percentage": 7.3
  },
  {
    "name": "bnp_2024",
    "total_chunks": 189,
    "text_chunks": 175,
    "table_chunks": 14,
    "table_percentage": 7.4
  }
]
```

---

### GET /collections/{collection_name} - Info Collection

**Description:** Détails d'une collection

**Exemple:**

```bash
curl http://localhost:8000/collections/lvmh_2024
```

**Réponse:**

```json
{
  "name": "lvmh_2024",
  "total_chunks": 245,
  "text_chunks": 227,
  "table_chunks": 18,
  "table_percentage": 7.3
}
```

**Erreurs:**
- 404: Collection non trouvée

---

### DELETE /collections/{collection_name} - Supprimer Collection

**Description:** Supprime une collection et tous ses documents

**Exemple:**

```bash
curl -X DELETE http://localhost:8000/collections/lvmh_2024
```

**Réponse:**

```json
{
  "message": "Collection 'lvmh_2024' supprimée avec succès"
}
```

---

## AI Agents

### POST /analyze/financial-report - Rapport Financier Multi-Agent

**Description:** Analyse approfondie avec 4 agents CrewAI

**Body:**

```json
{
  "companies": ["LVMH", "Hermès"],
  "collections": ["lvmh_2024", "hermes_2024"],
  "portfolio": {
    "positions": [...]
  }
}
```

**Agents utilisés:**
1. Document Analyst (RAG)
2. Market Research (Web)
3. Technical Expert (Charts)
4. Investment Advisor (Synthesis)

**Exemple:**

```bash
curl -X POST http://localhost:8000/analyze/financial-report \
  -H "Content-Type: application/json" \
  -d '{
    "companies": ["LVMH"],
    "collections": ["lvmh_2024"]
  }'
```

**Réponse:**

```json
{
  "report": "# RAPPORT D'ANALYSE FINANCIÈRE - LVMH\n\n## RECOMMANDATION: ACHETER 🟢\n**Confiance:** 85%\n...",
  "companies_analyzed": ["LVMH"],
  "processing_time": 125.67,
  "timestamp": "2026-02-01T14:23:45Z"
}
```

**Durée:** 2-5 minutes

---

### POST /build-portfolio - Construire Portfolio Optimal

**Description:** Construction portfolio PEA complet avec 6 agents

**Body:**

```json
{
  "budget": 10000,
  "risk_profile": "balanced",
  "sectors": ["luxury", "technology"],
  "exclude_companies": [],
  "min_companies": 8,
  "max_companies": 15
}
```

**Paramètres:**
- `budget`: Budget EUR (> 0)
- `risk_profile`: conservative, balanced, aggressive
- `sectors` (optionnel): Liste secteurs préférés
- `exclude_companies` (optionnel): Entreprises à exclure
- `min_companies`: Min positions (3-20)
- `max_companies`: Max positions (5-30)

**Exemple:**

```bash
curl -X POST http://localhost:8000/build-portfolio \
  -H "Content-Type: application/json" \
  --max-time 900 \
  -d '{
    "budget": 10000,
    "risk_profile": "balanced",
    "sectors": ["luxury", "technology"],
    "min_companies": 8,
    "max_companies": 12
  }'
```

**Réponse:**

```json
{
  "action_plan": "1. Acheter 1 action LVMH (MC.PA) à 752.30€\n2. Acheter 3 actions BNP Paribas (BNP.PA) à 55.20€\n...",
  "budget": 10000,
  "risk_profile": "balanced",
  "processing_time": 487.23,
  "timestamp": "2026-02-01T14:45:12Z",
  "data_collected": true
}
```

**Workflow agents:**
1. Data Collector: Collecte données top 30 PEA stocks
2. Fundamental Analyst: Analyse fondamentaux
3. Technical Analyst: Identifie points d'entrée
4. Risk Manager: Optimise risque
5. Sector Diversification: Équilibre secteurs
6. Portfolio Manager: Construction finale

**Durée:** 5-10 minutes

---

## Exemples cURL Complets

### Workflow Complet Portfolio

```bash
# 1. Vérifier santé API
curl http://localhost:8000/health

# 2. Ajouter première position
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"MC.PA","company_name":"LVMH","quantity":10,"price":750.0}'

# 3. Ajouter deuxième position
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"BNP.PA","company_name":"BNP Paribas","quantity":50,"price":55.0}'

# 4. Voir portfolio
curl http://localhost:8000/portfolio | jq

# 5. Vérifier santé portfolio
curl http://localhost:8000/portfolio/health | jq

# 6. Analyser action avant achat
curl "http://localhost:8000/analysis/complete/AIR.PA?company_name=Airbus" | jq

# 7. Acheter si bon signal
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AIR.PA","company_name":"Airbus","quantity":20,"price":125.0}'
```

### Workflow RAG Complet

```bash
# 1. Lister collections existantes
curl http://localhost:8000/collections | jq

# 2. Indexer nouveau document
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/lvmh_rapport_2024.pdf",
    "collection_name": "lvmh_2024"
  }'

# 3. Query simple (sans génération)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Chiffre d affaires 2024",
    "collection_name": "lvmh_2024",
    "n_results": 5,
    "generate_answer": false
  }' | jq

# 4. Query avec génération Ollama
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quels sont les principaux résultats financiers 2024?",
    "collection_name": "lvmh_2024",
    "n_results": 5,
    "generate_answer": true
  }' | jq
```

---

## Changelog

**Version 1.0.0 (Février 2026)**
- 23 endpoints opérationnels
- Portfolio management complet
- RAG documents avec ChromaDB
- Analyses techniques et sentiment
- Agents CrewAI pour portfolio builder
- Rate limiting 60 req/min

---

## Support

**Documentation:**
- Interactive: http://localhost:8000/docs
- Architecture: [ARCHITECTURE.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/ARCHITECTURE.md)
- Troubleshooting: [TROUBLESHOOTING.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/TROUBLESHOOTING.md)

**Issues:** GitHub Issues

---

**Document version:** 1.0.0
**Dernière mise à jour:** Février 2026
