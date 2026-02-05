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

## 7. Gestion de Trésorerie PEA

### Qu'est-ce que le PEA ?

Le **Plan d'Épargne en Actions (PEA)** est un compte d'investissement français avec des règles spécifiques:
- L'argent déposé **ne peut pas être retiré** (avant 5 ans sans clôture)
- Plafond maximum: 150 000€ de versements
- Le cash non investi ne rapporte rien → importance de l'investir

### Déposer de l'Argent

```bash
curl -X POST "http://localhost:8000/portfolio/deposit?amount=5000&notes=Depot_initial"
```

**Réponse:**
```json
{
    "message": "Dépôt de 5000.00€ effectué avec succès",
    "new_cash_available": 5000.0,
    "total_deposits": 5000.0
}
```

### Consulter la Trésorerie

```bash
curl "http://localhost:8000/portfolio/treasury"
```

**Réponse:**
```json
{
    "total_deposits": 5000.0,
    "cash_available": 3200.0,
    "cash_invested": 1800.0,
    "pea_opening_date": "2026-02-04",
    "last_deposit_date": "2026-02-04"
}
```

**Informations clés:**
- `total_deposits`: Total déposé depuis l'ouverture (jamais diminué)
- `cash_available`: Argent disponible pour investir
- `cash_invested`: Valeur actuelle de vos positions

### Gestion Automatique du Cash

#### Lors d'un Achat

```bash
curl -X POST "http://localhost:8000/portfolio/add" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "MC.PA", "company_name": "LVMH", "quantity": 5, "price": 750.0}'
```

**Comportement automatique:**
1. ✅ Vérifie que vous avez assez de cash (5 × 750 = 3750€)
2. ✅ Déduit automatiquement 3750€ du cash disponible
3. ✅ Ajoute la position à votre portfolio
4. ✅ Enregistre la transaction dans l'historique

**Si cash insuffisant:**
```json
{"detail": "Cash insuffisant. Disponible: 1000.00€, Requis: 3750.00€"}
```

#### Lors d'une Vente

```bash
curl -X POST "http://localhost:8000/portfolio/sell" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "MC.PA", "quantity": 2, "price": 800.0}'
```

**Comportement automatique:**
1. ✅ Vend 2 actions à 800€ = 1600€
2. ✅ Ajoute automatiquement 1600€ au cash disponible
3. ✅ Met à jour la position (quantité diminue)
4. ✅ Enregistre la transaction

**Important:** L'argent de la vente reste dans le PEA (ne peut pas être retiré).

### Opportunités d'Investissement IA

Le système détecte automatiquement des opportunités quand vous avez du cash disponible:

```bash
curl -X POST "http://localhost:8000/portfolio/opportunities/analyze"
```

**Types d'opportunités:**

1. **DIVERSIFY** (Priorité: HIGH)
   - Détectée si: < 5 positions dans le portfolio
   - Suggestion: Ajouter 2-3 nouvelles positions
   - Montant suggéré: 30% du cash disponible

2. **ADD_TO_EXISTING** (Priorité: MEDIUM)
   - Détectée si: Position performante (+5%) ET poids < 20%
   - Suggestion: Renforcer la position gagnante
   - Inclut: ticker, quantité suggérée

3. **REBALANCE_CASH** (Priorité: MEDIUM)
   - Détectée si: Ratio de cash > 30%
   - Suggestion: Investir 50% du cash progressivement

**Exemple de réponse:**
```json
{
    "has_opportunities": true,
    "cash_available": 3200.0,
    "cash_ratio": 64.0,
    "opportunities": [
        {
            "type": "DIVERSIFY",
            "priority": "HIGH",
            "reasoning": "Vous avez 2 positions. Recommandation: diversifier avec 5-8 positions.",
            "suggested_amount": 960.0,
            "action": "Rechercher de nouvelles opportunités dans des secteurs différents"
        }
    ]
}
```

### Accepter une Opportunité

```bash
# Liste les opportunités en attente
curl "http://localhost:8000/portfolio/opportunities/pending"

# Accepter une opportunité (exécute l'achat automatiquement)
curl -X POST "http://localhost:8000/portfolio/opportunities/123/accept"
```

**Comportement:**
1. Récupère les infos de l'opportunité
2. Obtient le prix du marché actuel
3. Exécute automatiquement l'achat
4. Déduit le cash automatiquement
5. Marque l'opportunité comme 'ACCEPTED'

### Historique et Flux

```bash
# Historique des dépôts
curl "http://localhost:8000/portfolio/treasury/deposits"

# Tous les flux de trésorerie
curl "http://localhost:8000/portfolio/treasury/cashflow"

# Seulement les achats
curl "http://localhost:8000/portfolio/treasury/cashflow?event_type=BUY"

# Seulement les ventes
curl "http://localhost:8000/portfolio/treasury/cashflow?event_type=SELL"
```

---

## 8. Bot Telegram - Agent PEA

### Configuration du Bot

**1. Créer un bot Telegram:**
- Parler à [@BotFather](https://t.me/BotFather) sur Telegram
- Créer un nouveau bot: `/newbot`
- Copier le token reçu

**2. Obtenir votre User ID Telegram:**

Le bot utilise une **whitelist de sécurité** pour limiter l'accès. Vous devez configurer votre User ID Telegram.

**Comment obtenir votre User ID:**
1. Sur Telegram, cherchez le bot **@userinfobot**
2. Démarrez une conversation avec ce bot
3. Le bot vous répondra avec vos informations, dont votre **User ID** (numérique)

Exemple de réponse de @userinfobot:
```
Id: 123456789
First name: John
Username: @johndoe
```

**IMPORTANT:** Utilisez l'**ID numérique** (123456789), PAS le username (@johndoe).

**3. Configurer le fichier `.env`:**

```env
# Bot Token (obtenu depuis @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABC...

# Chat ID pour les notifications (obtenu depuis @userinfobot)
TELEGRAM_CHAT_ID=123456789

# SÉCURITÉ: Whitelist des utilisateurs autorisés (OBLIGATOIRE)
# Utilisez votre User ID obtenu avec @userinfobot
TELEGRAM_AUTHORIZED_USER_IDS=123456789

# API
API_BASE_URL=http://localhost:8000
OPENAI_API_KEY=sk-...
```

**SÉCURITÉ - Whitelist Protection:**

Le bot utilise une **whitelist obligatoire** pour protéger vos données financières:

- **Single utilisateur (recommandé):** `TELEGRAM_AUTHORIZED_USER_IDS=123456789`
- **Multiple utilisateurs:** `TELEGRAM_AUTHORIZED_USER_IDS=123456789,987654321`

**Comportement:**
- Si `TELEGRAM_AUTHORIZED_USER_IDS` n'est **pas configuré**: Le bot affichera un **WARNING** et sera accessible à TOUS (mode dev uniquement)
- Si configuré: Seuls les User IDs dans la liste peuvent utiliser le bot
- Tentative d'accès non autorisé: Message de refus + log d'alerte

**4. Lancer le bot:**
```bash
python telegram_bot_main.py
```

**5. Vérifier la sécurité:**

Au démarrage, vérifiez les logs:
```
INFO - ✅ Handler enregistré: /balance
INFO - ✅ Handler enregistré: /portfolio
...
INFO - 🤖 Bot Telegram démarré !
```

Si un utilisateur non autorisé tente d'accéder:
```
WARNING - 🚨 Unauthorized access attempt: user_id=987654321, username=@attacker, name=Attacker, command=balance_command
```

### Onboarding Initial

Lorsque vous envoyez `/start` au bot:

1. **Dépôt initial:** Le bot demande combien déposer sur le PEA
2. **Positions existantes:** Possibilité d'ajouter vos positions actuelles
3. **Configuration automatique:** Le bot configure tout via l'API

**Exemple d'onboarding:**
```
Bot: Quel montant déposer sur votre PEA ?
Vous: 10000

Bot: Avez-vous déjà des positions ?
Vous: [Oui] ou [Non]

Si Oui:
Bot: Ticker de la première action ?
Vous: MC.PA
Bot: Quantité ?
Vous: 10
Bot: Prix d'achat ?
Vous: 750

Bot: ✅ Configuration terminée !
```

### Commandes Principales

#### 💰 Trésorerie PEA

```
/balance        - Voir trésorerie complète
/deposit 5000   - Déposer 5000€
/history        - Historique des dépôts
/cashflow       - Tous les flux de trésorerie
```

**Exemple de réponse `/balance`:**
```
💰 TRÉSORERIE PEA

📥 Total déposé: 10,000.00 €
💵 Cash disponible: 3,200.00 €
📊 Cash investi: 6,800.00 €

📈 Valeur totale PEA: 9,950.00 €
   Performance: -0.50%

💡 Ratio cash: 32.2%
   Ratio investi: 67.8%
```

#### 📊 Portfolio

```
/portfolio      - Vue complète du portfolio
/positions      - Liste toutes les positions
/health         - Score de santé (0-100)
/rebalance      - Recommandations rééquilibrage
```

**Exemple de réponse `/portfolio`:**
```
📊 PORTFOLIO - maxime

💰 Valeur totale: 9,950.00 €
📈 Gain/Perte: -50.00 € (-0.50%)

🎯 POSITIONS (3)

🟢 LVMH (MC.PA)
   • Quantité: 10 actions
   • PRU: 750.00 € | Prix actuel: 745.00 €
   • Valeur: 7,450.00 €
   • Performance: -0.67%

🟢 Air Liquide (AI.PA)
   • Quantité: 15 actions
   • PRU: 150.00 € | Prix actuel: 160.00 €
   • Valeur: 2,400.00 €
   • Performance: +6.67%
```

#### 💎 Opportunités

```
/opportunities  - Détecter opportunités (IA)
/pending        - Opportunités en attente
/accept 123     - Accepter opportunité #123
/reject 123     - Rejeter opportunité #123
```

**Exemple de réponse `/opportunities`:**
```
💎 OPPORTUNITÉS D'INVESTISSEMENT

💵 Cash disponible: 3,200.00 €
📊 Ratio cash: 32.2%

🔴 OPPORTUNITÉ 1 - DIVERSIFY (HIGH)
   Vous avez 3 positions. Recommandation:
   diversifier avec 5-8 positions différentes.

   💰 Montant suggéré: 960.00 €
   🎯 Action: Rechercher de nouvelles opportunités

🟡 OPPORTUNITÉ 2 - ADD_TO_EXISTING (MEDIUM)
   Renforcer Air Liquide (AI.PA) qui performe bien

   💰 Montant suggéré: 800.00 €
   📊 Quantité: 5 actions à ~160€

💡 Tapez /accept <id> pour accepter une opportunité
```

#### 🛒 Transactions

```
/buy MC.PA 5 750    - Acheter 5 LVMH à 750€
/sell MC.PA 2 800   - Vendre 2 LVMH à 800€
```

**Exemple de réponse `/buy`:**
```
✅ ACHAT RÉUSSI

📊 LVMH (MC.PA)
   • Quantité: 5 actions
   • Prix: 750.00 €
   • Total: 3,750.00 €

💰 Nouveau cash disponible: 1,250.00 €
```

#### 🔍 Analyses IA

```
/analyze MC.PA         - Analyse complète IA
/news LVMH            - Actualités récentes
/technical MC.PA      - Analyse technique
```

**Exemple de réponse `/analyze`:**
```
🔍 ANALYSE COMPLÈTE - LVMH (MC.PA)

📊 DONNÉES MARCHÉ
   • Prix actuel: 745.00 €
   • P/E Ratio: 25.3
   • Dividende: 2.8%
   • Capitalisation: 372B €

📈 ANALYSE TECHNIQUE
   • RSI: 58 (neutre)
   • MACD: Signal haussier
   • Support: 720€ | Résistance: 780€
   • Tendance: Haussière (SMA 50 > SMA 200)

📰 SENTIMENT (IA)
   Score: 0.75 (Positif)
   Confiance: 85%

💡 RECOMMANDATION: BUY
   Confiance: 78%

   Le titre présente une bonne dynamique avec
   un sentiment positif et des fondamentaux solides.
```

#### 📈 Market Data

```
/stock MC.PA          - Infos temps réel
/markethistory MC.PA  - Historique des cours
```

#### ⚙️ Aide

```
/help         - Liste toutes les commandes
/usecases     - Exemples d'utilisation
/examples     - Exemples concrets
```

### Rapports Automatiques

Le système envoie automatiquement des rapports:

**1. Rapport Quotidien (si cash > 100€):**
- Envoyé tous les jours à 9h00
- État de la trésorerie
- Opportunités détectées
- Performance du portfolio

**2. Rapport Hebdomadaire (tous les lundis):**
- Vue d'ensemble du PEA
- Santé du portfolio (score)
- Recommandations de rééquilibrage
- Top 3 positions

**Exemple de rapport quotidien:**
```
🌅 RAPPORT QUOTIDIEN - 04/02/2026

💰 TRÉSORERIE PEA
• Cash disponible: 3,200.00 €
• Cash investi: 6,800.00 €
• Ratio cash: 32.2%

📊 PORTFOLIO
• Positions: 3
• Valeur totale: 9,950.00 €
• Performance: -0.50%

💎 OPPORTUNITÉS DÉTECTÉES

🔴 DIVERSIFY (Priorité: HIGH)
   Vous avez 3 positions. Recommandation:
   ajouter 2-3 nouvelles positions.
   • Montant suggéré: 960.00€

💡 Tapez /opportunities pour voir tous les détails

_Rapport automatique quotidien_
```

### Cas d'Usage Complets

#### Cas 1: Démarrage

```
1. /start
   → Onboarding: dépôt initial + positions existantes
2. /portfolio
   → Voir le résumé
3. /opportunities
   → Détecter opportunités
```

#### Cas 2: Suivi Quotidien

```
1. Rapport automatique reçu à 9h
2. /health
   → Vérifier score de santé
3. /opportunities
   → Voir nouvelles opportunités
4. /accept 123
   → Accepter une opportunité
```

#### Cas 3: Analyser Avant d'Acheter

```
1. /analyze MC.PA
   → Analyse IA complète
2. /technical MC.PA
   → Analyse technique détaillée
3. /news LVMH
   → Actualités récentes
4. /buy MC.PA 5 750
   → Acheter si convaincu
```

#### Cas 4: Vente et Réinvestissement

```
1. /sell MC.PA 5 800
   → Vendre avec plus-value
2. /balance
   → Vérifier le cash récupéré
3. /opportunities
   → Voir où réinvestir
4. /buy AI.PA 10 160
   → Réinvestir dans autre position
```

---

## 9. Roadmap

### ✅ Fonctionnalités Actuelles

- RAG v2 optimisé (multilingue, cache, cosine similarity)
- Portfolio management complet
- **Trésorerie PEA** (dépôts, cash tracking, opportunités IA)
- **Bot Telegram complet** (onboarding + 22 commandes)
- **Rapports automatiques** (quotidiens + hebdomadaires)
- Analyse technique avancée
- Agents IA multi-agents (CrewAI)
- API REST complète (33 endpoints)
- Tests automatisés (36 tests)
- Données temps réel gratuites (Yahoo Finance)
- **Déploiement VPS** (Docker + docker-compose)

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
