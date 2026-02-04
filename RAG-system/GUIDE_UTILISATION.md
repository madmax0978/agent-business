# Guide d'Utilisation - RAG-PEA System

Guide complet pour utiliser toutes les fonctionnalités du système.

---

## Table des Matières

1. [RAG v2 - Recherche Documents](#1-rag-v2---recherche-documents)
2. [Portfolio Management](#2-portfolio-management)
3. [Analyse de Marché](#3-analyse-de-marché)
4. [Agents IA Multi-Agents](#4-agents-ia-multi-agents)
5. [API Reference Rapide](#5-api-reference-rapide)
6. [Exemples Pratiques](#6-exemples-pratiques)
7. [Roadmap](#7-roadmap)

---

## 1. RAG v2 - Recherche Documents

### Qu'est-ce que le RAG v2 ?

Le RAG (Retrieval-Augmented Generation) v2 est un système de recherche sémantique optimisé pour interroger vos documents financiers en français.

**Améliorations v2:**
- Modèle multilingual: `paraphrase-multilingual-mpnet-base-v2` (768 dimensions)
- Scores 0.4-0.6 pour le français (+1500% vs v1)
- Cache des embeddings (20x plus rapide)
- Cosine similarity (vs L2 distance)

### Indexer des Documents

#### Option 1: Indexation Rapide (3 PDFs de test)

```bash
python3 scripts/quick_index.py
```

Indexe automatiquement 3 documents depuis `data/context/`:
- hermes_rapport.pdf → Hermes_2023
- lvmh_document_financier.pdf → LVMH_Financiers_2024
- safran_fy_2024.pdf → Safran_FY_2024

#### Option 2: Indexation Complète (tous les PDFs)

```bash
python3 scripts/index_all_pdfs.py
```

Indexe TOUS les PDFs du dossier `data/context/` (79 documents).

**Performances:**
- ~45s pour 80 pages PDF
- ~12 chunks/seconde
- Détection automatique des tables

#### Option 3: Via API (upload + indexation)

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@rapport_lvmh_2024.pdf" \
  -F "collection_name=LVMH_2024"
```

### Rechercher dans les Documents

#### Recherche Simple (sans génération)

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quel est le chiffre d affaires 2024?",
    "collection_name": "LVMH_Financiers_2024",
    "n_results": 5,
    "generate_answer": false
  }'
```

Retourne:
- Les 5 chunks les plus pertinents
- Score de similarité (0-1)
- Métadonnées (page, type de contenu)

#### Recherche avec Génération de Réponse

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelle est la croissance du chiffre d affaires?",
    "collection_name": "LVMH_Financiers_2024",
    "n_results": 5,
    "generate_answer": true
  }'
```

Utilise Ollama (Mistral) pour générer une réponse synthétique basée sur les chunks trouvés.

#### Filtrer par Type de Contenu

```bash
# Seulement les tables
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "données financières",
    "collection_name": "LVMH_Financiers_2024",
    "filter_tables": true
  }'

# Seulement le texte
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "stratégie entreprise",
    "collection_name": "LVMH_Financiers_2024",
    "filter_tables": false
  }'
```

### Gérer les Collections

```bash
# Lister toutes les collections
curl http://localhost:8000/collections

# Détails d'une collection
curl http://localhost:8000/collection/LVMH_Financiers_2024

# Supprimer une collection
curl -X DELETE http://localhost:8000/collection/LVMH_Financiers_2024
```

---

## 2. Portfolio Management

### Ajouter une Position

```bash
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "maxime",
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "price": 750.00,
    "transaction_date": "2024-02-01"
  }'
```

**Calcul automatique du PRU (Prix de Revient Unitaire):**
- Achat 1: 10 actions à 750€ → PRU = 750€
- Achat 2: 5 actions à 800€ → PRU = (10×750 + 5×800) / 15 = 766.67€

### Vendre une Position

```bash
curl -X POST http://localhost:8000/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "maxime",
    "ticker": "MC.PA",
    "quantity": 5,
    "price": 820.00,
    "transaction_date": "2024-03-01"
  }'
```

Calcule automatiquement:
- Plus-value: (820 - 766.67) × 5 = +266.65€
- Nouveau PRU: inchangé (reste 766.67€)
- Nouvelle quantité: 15 - 5 = 10 actions

### Consulter le Portfolio

```bash
curl http://localhost:8000/portfolio?user_id=maxime
```

Retourne:
```json
{
  "user_id": "maxime",
  "positions": [
    {
      "ticker": "MC.PA",
      "company_name": "LVMH",
      "quantity": 10,
      "average_price": 766.67,
      "current_price": 850.00,
      "total_invested": 7666.70,
      "current_value": 8500.00,
      "gain_loss": 833.30,
      "gain_loss_percent": 10.87
    }
  ],
  "total_invested": 7666.70,
  "total_value": 8500.00,
  "total_gain_loss": 833.30
}
```

### Score de Santé (0-100)

```bash
curl http://localhost:8000/portfolio/health?user_id=maxime
```

Évalue:
- **Diversification** (40%): nombre de secteurs et titres
- **Performance** (30%): gain/perte moyen
- **Exposition au risque** (30%): volatilité et concentration

Score > 70 = Bon portfolio ✅
Score < 50 = Rééquilibrage recommandé ⚠️

### Recommandations de Rééquilibrage

```bash
curl http://localhost:8000/portfolio/rebalance?user_id=maxime
```

Suggère:
- Actions sous-pondérées à acheter
- Actions surpondérées à vendre
- Nouveaux secteurs à explorer

---

## 3. Analyse de Marché

### Données Temps Réel (Gratuit)

```bash
# Informations d'une action
curl http://localhost:8000/market/stock/MC.PA

# Historique sur 1 an
curl http://localhost:8000/market/history/MC.PA?period=1y&interval=1d
```

Données disponibles:
- Prix actuel, plus haut/bas 52 semaines
- P/E ratio, dividend yield
- Capitalisation boursière
- Volume moyen

### Analyse Technique Complète

```bash
curl http://localhost:8000/analysis/technical/MC.PA
```

Retourne:
- **RSI** (Relative Strength Index): surachat (>70) ou survente (<30)
- **MACD**: signal haussier/baissier
- **Bollinger Bands**: volatilité et zones de prix
- **Support/Résistance**: niveaux clés
- **SMA 50/200**: tendance moyen/long terme
- **Signaux**: Golden Cross, Death Cross

### Actualités et Sentiment

```bash
# Actualités récentes
curl http://localhost:8000/analysis/news/LVMH

# Analyse de sentiment IA
curl http://localhost:8000/analysis/sentiment/LVMH?company_name=LVMH
```

Analyse le sentiment (positif/négatif/neutre) des actualités avec IA.

### Analyse Complète

```bash
curl "http://localhost:8000/analysis/complete/MC.PA?company_name=LVMH"
```

Combine TOUT:
- Données marché
- Analyse technique
- Actualités
- Sentiment IA
- **Recommandation finale**: Buy/Hold/Sell avec score de confiance

---

## 4. Agents IA Multi-Agents

### Construire un Portfolio Optimal

Utilise 6 agents CrewAI spécialisés pour construire un portfolio de 0:

```bash
curl -X POST http://localhost:8000/build-portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 10000,
    "risk_profile": "balanced",
    "sectors": ["technology", "healthcare", "finance"],
    "min_companies": 10,
    "max_companies": 15,
    "user_id": "maxime"
  }'
```

**Les 6 agents:**
1. **Portfolio Strategist** - Définit la stratégie d'allocation
2. **Market Analyst** - Analyse les tendances du marché
3. **Stock Researcher** - Recherche les meilleures actions CAC40
4. **Risk Assessor** - Évalue les risques
5. **Portfolio Optimizer** - Optimise les allocations
6. **Recommendation Writer** - Rédige le rapport final

**Durée:** 5-10 minutes (analyse approfondie)

**Résultat:** Portfolio complet avec:
- Allocations précises par action
- Ordres d'achat détaillés
- Justifications pour chaque choix
- Analyse des risques

### Analyser un Rapport Financier

Utilise 4 agents pour analyse approfondie d'un document:

```bash
curl -X POST http://localhost:8000/analyze/financial-report \
  -H "Content-Type: application/json" \
  -d '{
    "document_path": "data/context/lvmh_rapport_2024.pdf",
    "analysis_focus": ["financial_performance", "growth_strategy"]
  }'
```

**Les 4 agents:**
1. **Financial Analyst** - Analyse les chiffres clés
2. **Strategy Analyst** - Évalue la stratégie
3. **Risk Analyst** - Identifie les risques
4. **Report Synthesizer** - Synthétise tout

---

## 5. API Reference Rapide

### Portfolio

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/portfolio/add` | POST | Ajouter/modifier position |
| `/portfolio/sell` | POST | Vendre position |
| `/portfolio` | GET | Voir portfolio complet |
| `/portfolio/health` | GET | Score santé 0-100 |
| `/portfolio/rebalance` | GET | Recommandations |
| `/portfolio/position/{ticker}` | GET | Détails position |
| `/portfolio/context` | GET | Contexte pour agents IA |

### Marché & Analyse

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/market/stock/{ticker}` | GET | Info temps réel |
| `/market/history/{ticker}` | GET | Historique |
| `/analysis/technical/{ticker}` | GET | Analyse technique |
| `/analysis/news/{company}` | GET | Actualités |
| `/analysis/sentiment/{company}` | GET | Sentiment IA |
| `/analysis/complete/{ticker}` | GET | Analyse totale |

### RAG

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/query` | POST | Rechercher dans documents |
| `/collections` | GET | Lister collections |
| `/collection/{name}` | GET | Détails collection |
| `/collection/{name}` | DELETE | Supprimer collection |
| `/upload` | POST | Upload & indexer PDF |
| `/index` | POST | Indexer fichier existant |
| `/rag-info` | GET | Infos version RAG |

### Agents IA

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/build-portfolio` | POST | Construire portfolio (6 agents) |
| `/analyze/financial-report` | POST | Analyser rapport (4 agents) |

### Santé

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/health` | GET | État API + Ollama |
| `/docs` | GET | Documentation interactive |

---

## 6. Exemples Pratiques

### Exemple Python: Monitoring Quotidien

```python
import requests
from datetime import datetime

API = "http://localhost:8000"
USER_ID = "maxime"

def daily_check():
    # 1. Portfolio actuel
    portfolio = requests.get(f"{API}/portfolio", params={"user_id": USER_ID}).json()
    print(f"💰 Valeur: {portfolio['total_value']:.2f}€")
    print(f"📈 Gain: {portfolio['total_gain_loss']:.2f}€")

    # 2. Score de santé
    health = requests.get(f"{API}/portfolio/health", params={"user_id": USER_ID}).json()
    score = health['health_score']
    print(f"❤️  Santé: {score}/100")

    if score < 60:
        # 3. Recommandations de rééquilibrage
        rebalance = requests.get(f"{API}/portfolio/rebalance", params={"user_id": USER_ID}).json()
        print("\n⚠️  Rééquilibrage recommandé:")
        for rec in rebalance['recommendations']:
            print(f"  - {rec}")

    # 4. Analyse technique des positions
    for position in portfolio['positions']:
        ticker = position['ticker']
        analysis = requests.get(f"{API}/analysis/technical/{ticker}").json()

        if analysis['signals']:
            print(f"\n🚨 {ticker}: {', '.join(analysis['signals'])}")

if __name__ == "__main__":
    daily_check()
```

### Exemple: Automatiser l'Indexation

```bash
#!/bin/bash
# watch_and_index.sh
# Surveille un dossier et indexe automatiquement les nouveaux PDFs

WATCH_DIR="data/context"
API="http://localhost:8000"

while true; do
    for pdf in "$WATCH_DIR"/*.pdf; do
        filename=$(basename "$pdf")
        collection_name="${filename%.*}"

        # Vérifier si déjà indexé
        indexed=$(curl -s "$API/collections" | grep -c "$collection_name")

        if [ $indexed -eq 0 ]; then
            echo "📄 Indexation: $filename"
            curl -X POST "$API/index" \
                -H "Content-Type: application/json" \
                -d "{\"file_path\": \"$pdf\", \"collection_name\": \"$collection_name\"}"
        fi
    done

    sleep 3600  # Vérifier toutes les heures
done
```

---

## 7. Roadmap

### ✅ Fonctionnalités Actuelles

- RAG v2 optimisé (multilingue, cache, cosine similarity)
- Portfolio management complet
- Analyse technique avancée
- Agents IA multi-agents (CrewAI)
- API REST complète (23 endpoints)
- Tests automatisés (36 tests)
- Données temps réel gratuites (Yahoo Finance)

### 🚧 En Cours

- Backtesting avancé (plusieurs stratégies)
- Optimisation walk-forward
- Dashboard web (React)

### 📋 Roadmap Q1-Q2 2026

**Q1 2026:**
- [ ] WebSocket pour données temps réel
- [ ] Plus de stratégies de backtesting (RSI, Bollinger, MACD)
- [ ] Multi-utilisateurs avec authentification
- [ ] Dashboard web interactif

**Q2 2026:**
- [ ] Intégration courtier (Interactive Brokers, Trading212)
- [ ] Prédictions ML (prix futurs)
- [ ] Application mobile (React Native)
- [ ] Export rapports PDF

**Futur:**
- [ ] Fine-tuning modèle RAG sur vocabulaire financier CAC40
- [ ] Hybrid search (vectoriel + BM25)
- [ ] RAG multi-modal (images/graphiques PDFs)
- [ ] Auto-évaluation qualité des réponses

---

## 📝 Notes Importantes

### Limites Connues

- **Yahoo Finance**: délai 15-20 min (gratuit, pas de données tick-by-tick)
- **Ollama**: requis pour génération de réponses (installer localement)
- **Mono-utilisateur**: pas d'authentification par défaut
- **Ordres manuels**: pas d'intégration courtier

### Bonnes Pratiques

1. **Indexation**: Indexez vos PDFs une seule fois, le cache fait le reste
2. **User ID**: Utilisez des user_id uniques pour multi-utilisateurs
3. **Tests**: Lancez `./run_tests.sh` après chaque modification
4. **Backup**: Sauvegardez `data/vector_db` et `data/portfolio.db` régulièrement
5. **Performance**: Le cache RAG rend les recherches répétées 20x plus rapides

---

**Besoin d'aide ?** Consultez **TROUBLESHOOTING.md** pour les problèmes courants.

**Documentation API complète**: [http://localhost:8000/docs](http://localhost:8000/docs)
