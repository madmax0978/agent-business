# API ENDPOINTS - Documentation Technique RAG-PEA

**Version**: 3.0 (ML + Backtesting + Intelligence)
**Base URL**: `http://localhost:8000`
**Authentication**: JWT Bearer Token (30 jours de validité)
**Date**: 2026-02-06

---

## 🆕 NOUVEAUTÉS VERSION 3.0

- **Machine Learning**: 8 endpoints ML pour entraînement et prédictions de prix (LSTM/Prophet)
- **Backtesting**: 6 endpoints pour tester stratégies historiques (6+ stratégies disponibles)
- **Intelligence**: Endpoint d'analyse complète combinant ML + Backtesting + Technical + Fundamental

---

## Table des Matières

1. [Authentification](#1-authentification)
2. [Santé du Système](#2-santé-du-système)
3. [Gestion des Collections](#3-gestion-des-collections)
4. [Gestion des Documents](#4-gestion-des-documents)
5. [Requêtes RAG](#5-requêtes-rag)
6. [Analyse Financière](#6-analyse-financière)
7. [Construction de Portefeuille](#7-construction-de-portefeuille)
8. [Gestion de Portefeuille](#8-gestion-de-portefeuille)
9. [Trésorerie PEA](#9-trésorerie-pea)
10. [Opportunités d'Investissement](#10-opportunités-dinvestissement)
11. [Données de Marché](#11-données-de-marché)
12. [Analyses Avancées](#12-analyses-avancées)
13. **[🆕 Machine Learning](#13-machine-learning)** ⭐
14. **[🆕 Backtesting](#14-backtesting)** ⭐
15. **[🆕 Intelligence (ML + Backtesting + Agents)](#15-intelligence)** 🔥
16. [Codes d'Erreur](#16-codes-derreur)
17. [Glossaire Technique](#17-glossaire-technique)

---

## 1. Authentification

### POST /auth/login

**Description**: Authentification utilisateur et génération d'un token JWT valide 30 jours.

**Outils utilisés**:
- `api/auth.py::authenticate_user()` - Validation credentials (bcrypt)
- `api/auth.py::create_access_token()` - Génération JWT
- `python-jose[cryptography]` - Bibliothèque JWT
- Hashage sécurisé avec bcrypt

**Request Body**:
```json
{
  "username": "admin",
  "password": "your_secure_password"
}
```

**Response 200**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTcwOTYzNTIwMH0.xyz...",
  "token_type": "bearer",
  "expires_in_days": 30
}
```

**Exemple cURL**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"secret"}'
```

**Exemple Python**:
```python
import requests

response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "admin", "password": "secret"}
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
```

**Erreurs**:
- `401 Unauthorized` - Credentials invalides
- `422 Unprocessable Entity` - Format JSON invalide

---

### GET /auth/verify

**Description**: Vérifie la validité d'un token JWT. Utile pour les clients (bot Telegram) pour vérifier si le token est encore valide.

**Outils utilisés**:
- `api/auth.py::verify_token()` - Validation JWT
- `api/auth.py::get_token_info()` - Extraction informations token
- Vérification signature HMAC-SHA256

**Headers**:
```
Authorization: Bearer <your_token>
```

**Response 200** (token valide):
```json
{
  "valid": true,
  "username": "admin",
  "expires_at": "2026-03-07T12:30:00"
}
```

**Response 200** (token invalide):
```json
{
  "valid": false,
  "username": null,
  "expires_at": null
}
```

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/auth/verify",
    headers=headers
)
is_valid = response.json()["valid"]
```

**Erreurs**:
- `401 Unauthorized` - Token manquant ou malformé

---

## 2. Santé du Système

### GET /

**Description**: Page d'accueil de l'API avec liens utiles.

**Outils utilisés**: Aucun (endpoint statique)

**Response 200**:
```json
{
  "message": "API RAG Multi-Documents",
  "version": "1.1.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

### GET /health

**Description**: Vérification complète de la santé de l'API (Ollama, ChromaDB, collections).

**Outils utilisés**:
- `api/rag_manager_v2.py::check_ollama()` - Test connexion Ollama (HTTP)
- `api/rag_manager_v2.py::list_collections()` - Liste collections ChromaDB
- ChromaDB client pour vérification base de données vectorielle
- Socket test pour vérifier disponibilité Ollama sur port 11434

**Response 200**:
```json
{
  "status": "healthy",
  "ollama_available": true,
  "collections": ["lvmh_2023", "hermes_2023", "loreal_2023"],
  "version": "1.1.0"
}
```

**Exemple Python**:
```python
response = requests.get("http://localhost:8000/health")
if response.json()["status"] == "healthy":
    print("API opérationnelle")
```

**Erreurs**:
- `503 Service Unavailable` - Ollama ou ChromaDB indisponible

---

### GET /rag-info

**Description**: Informations détaillées sur le système RAG utilisé (version, modèle embedding, cache).

**Outils utilisés**:
- `api/rag_manager_v2.py::OptimizedRAGManager` - Version v2 optimisée
- Modèle embedding: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- Cache embeddings activé pour performances

**Response 200**:
```json
{
  "rag_version": "v2 (optimisé)",
  "embedding_model": "paraphrase-multilingual-mpnet-base-v2",
  "cache_enabled": true,
  "is_v2": true,
  "info": "v2 utilise paraphrase-multilingual-mpnet-base-v2 (optimisé français)"
}
```

---

## 3. Gestion des Collections

### GET /collections

**Description**: Liste toutes les collections disponibles dans ChromaDB avec statistiques.

**Outils utilisés**:
- `api/rag_manager_v2.py::list_collections()` - Liste collections ChromaDB
- `api/rag_manager_v2.py::get_collection_info()` - Métadonnées collection
- ChromaDB query pour compter chunks par type (table/texte)

**Headers**:
```
Authorization: Bearer <your_token>
```

**Response 200**:
```json
[
  {
    "name": "lvmh_2023",
    "total_chunks": 245,
    "table_chunks": 78,
    "text_chunks": 167,
    "table_percentage": 31.8,
    "document_name": "LVMH_Rapport_Annuel_2023.pdf"
  },
  {
    "name": "hermes_2023",
    "total_chunks": 189,
    "table_chunks": 52,
    "text_chunks": 137,
    "table_percentage": 27.5,
    "document_name": "Hermes_Rapport_Annuel_2023.pdf"
  }
]
```

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/collections",
    headers=headers
)
collections = response.json()
print(f"Nombre de collections: {len(collections)}")
```

---

### GET /collections/{collection_name}

**Description**: Récupère les informations détaillées d'une collection spécifique.

**Outils utilisés**:
- `api/rag_manager_v2.py::get_collection_info()` - Métadonnées collection
- ChromaDB get() pour extraction métadonnées

**URL Parameters**:
- `collection_name` (string, required) - Nom de la collection

**Response 200**:
```json
{
  "name": "lvmh_2023",
  "total_chunks": 245,
  "table_chunks": 78,
  "text_chunks": 167,
  "table_percentage": 31.8,
  "document_name": "LVMH_Rapport_Annuel_2023.pdf"
}
```

**Erreurs**:
- `404 Not Found` - Collection inexistante

---

### DELETE /collections/{collection_name}

**Description**: Supprime définitivement une collection de ChromaDB.

**Outils utilisés**:
- `chromadb.Client::delete_collection()` - Suppression collection
- Nettoyage complet des embeddings et métadonnées

**URL Parameters**:
- `collection_name` (string, required) - Nom de la collection à supprimer

**Response 200**:
```json
{
  "message": "Collection 'lvmh_2023' supprimée avec succès"
}
```

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.delete(
    "http://localhost:8000/collections/old_collection",
    headers=headers
)
```

**Erreurs**:
- `404 Not Found` - Collection inexistante

---

## 4. Gestion des Documents

### POST /upload

**Description**: Upload et indexation automatique d'un document PDF dans ChromaDB.

**Outils utilisés**:
- `api/rag_manager_v2.py::index_document()` - Pipeline indexation complet
- `pymupdf` (fitz) - Extraction texte et tableaux PDF
- `sentence-transformers` - Génération embeddings (768 dimensions)
- `chromadb` - Stockage vectoriel
- `api/main.py::sanitize_collection_name()` - Nettoyage nom collection

**Pipeline d'indexation**:
1. Validation format PDF
2. Extraction texte et tableaux (PyMuPDF)
3. Chunking intelligent (500 tokens max par chunk)
4. Génération embeddings (paraphrase-multilingual-mpnet-base-v2)
5. Stockage ChromaDB avec métadonnées

**Form Data**:
```
file: <binary_pdf_file>
collection_name: "lvmh_2023" (optionnel, auto-généré depuis nom fichier sinon)
```

**Response 200**:
```json
{
  "success": true,
  "collection_name": "lvmh_2023",
  "total_chunks": 245,
  "table_chunks": 78,
  "text_chunks": 167,
  "message": "Document indexé avec succès en 12.45s"
}
```

**Exemple cURL**:
```bash
curl -X POST http://localhost:8000/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@LVMH_2023.pdf" \
  -F "collection_name=lvmh_2023"
```

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("LVMH_2023.pdf", "rb")}
data = {"collection_name": "lvmh_2023"}

response = requests.post(
    "http://localhost:8000/upload",
    headers=headers,
    files=files,
    data=data
)
result = response.json()
print(f"Indexé: {result['total_chunks']} chunks")
```

**Erreurs**:
- `400 Bad Request` - Fichier non-PDF
- `500 Internal Server Error` - Erreur indexation

---

### POST /index

**Description**: Indexe un document PDF existant depuis un chemin local.

**Outils utilisés**:
- Mêmes outils que `/upload`
- Lecture depuis système de fichiers local

**Request Body**:
```json
{
  "document_name": "LVMH Rapport Annuel 2023",
  "file_path": "/path/to/LVMH_2023.pdf",
  "collection_name": "lvmh_2023"
}
```

**Response 200**:
```json
{
  "success": true,
  "collection_name": "lvmh_2023",
  "total_chunks": 245,
  "table_chunks": 78,
  "text_chunks": 167,
  "message": "Document 'LVMH Rapport Annuel 2023' indexé avec succès"
}
```

**Erreurs**:
- `404 Not Found` - Fichier inexistant
- `500 Internal Server Error` - Erreur indexation

---

## 5. Requêtes RAG

### POST /query

**Description**: Effectue une requête RAG sur une collection avec génération de réponse par LLM.

**Outils utilisés**:
- `api/rag_manager_v2.py::search()` - Recherche sémantique (cosine similarity)
- `sentence-transformers` - Embedding de la question
- `chromadb::query()` - Recherche vectorielle
- `ollama::mistral` - Génération réponse (RAG)
- Calcul score de pertinence: `score = max(0, 1 - distance_cosine)`

**Pipeline RAG**:
1. Embedding de la question (768 dimensions)
2. Recherche cosine similarity dans ChromaDB
3. Récupération des N meilleurs chunks
4. Construction du contexte pour le LLM
5. Génération réponse avec Ollama (mistral)

**Request Body**:
```json
{
  "question": "Quel est le chiffre d'affaires de LVMH en 2023 ?",
  "collection_name": "lvmh_2023",
  "n_results": 5,
  "filter_tables": null,
  "generate_answer": true
}
```

**Response 200**:
```json
{
  "question": "Quel est le chiffre d'affaires de LVMH en 2023 ?",
  "answer": "Le chiffre d'affaires de LVMH en 2023 s'élève à 86,153 millions d'euros, en hausse de 13% par rapport à 2022.",
  "chunks": [
    {
      "chunk_id": 42,
      "text": "Le chiffre d'affaires 2023 s'établit à 86 153 M€...",
      "score": 0.92,
      "content_type": "table",
      "num_tokens": 245,
      "metadata": {
        "page": 12,
        "document": "LVMH_2023.pdf"
      }
    }
  ],
  "collection_name": "lvmh_2023",
  "processing_time": 2.34
}
```

**Paramètres de requête**:
- `question` (string, required) - Question en langage naturel
- `collection_name` (string, required) - Collection à interroger
- `n_results` (int, default=5) - Nombre de chunks à récupérer (1-20)
- `filter_tables` (bool, optional) - true=uniquement tableaux, false=uniquement texte, null=tous
- `generate_answer` (bool, default=true) - Générer réponse LLM ou juste retourner chunks

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
query = {
    "question": "Quel est le chiffre d'affaires de LVMH en 2023 ?",
    "collection_name": "lvmh_2023",
    "n_results": 5,
    "generate_answer": True
}

response = requests.post(
    "http://localhost:8000/query",
    headers=headers,
    json=query
)
answer = response.json()["answer"]
print(f"Réponse: {answer}")
```

**Erreurs**:
- `404 Not Found` - Collection inexistante
- `503 Service Unavailable` - Ollama indisponible
- `500 Internal Server Error` - Erreur génération

---

## 6. Analyse Financière

### POST /analyze/financial-report

**Description**: Génère un rapport d'analyse financière complet avec recommandations d'investissement en utilisant une équipe d'agents CrewAI.

**Outils utilisés**:
- **CrewAI Framework**: Orchestration multi-agents
- **Agents IA** (4 agents spécialisés):
  - `Analyste Fondamental` - Analyse bilans, P&L, ratios financiers
  - `Analyste Actualités` - Recherche web + indexation actualités
  - `Analyste Technique` - Analyse tendances et momentum
  - `Gestionnaire de Portefeuille` - Synthèse et décision ACHETER/GARDER/VENDRE
- **LLM**: Claude 3.5 Sonnet (priorité) ou GPT-4 (fallback)
- **Outils agents**:
  - `api/agents/tools.py::create_rag_tool()` - Accès documents indexés
  - `api/agents/tools.py::create_web_search_tool()` - Recherche web Tavily
  - `api/agents/tools.py::create_news_indexer_tool()` - Indexation actualités
- **Services**:
  - `api/rag_manager_v2.py` - RAG pour documents financiers
  - `tavily` API - Recherche web temps réel

**Workflow CrewAI** (durée ~60-90 secondes):
1. Analyste Fondamental lit documents RAG (bilans, P&L)
2. Analyste Actualités recherche news récentes (Tavily)
3. Analyste Technique calcule indicateurs (si données marché disponibles)
4. Gestionnaire synthétise et décide (ACHETER/GARDER/VENDRE)
5. Génération rapport markdown structuré

**Request Body**:
```json
{
  "companies": ["LVMH", "Hermès", "L'Oréal"],
  "collections": ["lvmh_2023", "hermes_2023", "loreal_2023"],
  "portfolio": {
    "LVMH": {
      "quantity": 10,
      "avg_price": 650.0
    }
  }
}
```

**Response 200**:
```json
{
  "report": "# RAPPORT D'ANALYSE FINANCIÈRE\n\n## LVMH (Louis Vuitton Moët Hennessy)\n\n### ANALYSE FONDAMENTALE\n- Chiffre d'affaires 2023: 86,2 Mds €...\n\n### RECOMMANDATION: ACHETER\n**Prix cible**: 920€...",
  "companies_analyzed": ["LVMH", "Hermès", "L'Oréal"],
  "processing_time": 78.5,
  "timestamp": "2026-02-05T14:30:00"
}
```

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
request = {
    "companies": ["LVMH", "Hermès"],
    "collections": ["lvmh_2023", "hermes_2023"],
    "portfolio": {
        "LVMH": {"quantity": 10, "avg_price": 650.0}
    }
}

response = requests.post(
    "http://localhost:8000/analyze/financial-report",
    headers=headers,
    json=request
)
report = response.json()["report"]
print(report)
```

**Erreurs**:
- `404 Not Found` - Collection inexistante
- `400 Bad Request` - Nombre companies != nombre collections
- `500 Internal Server Error` - Erreur agents CrewAI

---

## 7. Construction de Portefeuille

### POST /build-portfolio

**Description**: Construit un portefeuille PEA optimal de zéro avec collecte automatique de données, analyse profonde et allocation optimisée selon profil de risque.

**Outils utilisés**:
- **CrewAI Portfolio Builder Crew** (6 agents spécialisés):
  - `Data Collector` - Collecte rapports financiers et actualités top 50 entreprises PEA
  - `Financial Analyst` - Analyse fondamentale approfondie
  - `Risk Assessor` - Évaluation risques et volatilité
  - `Portfolio Optimizer` - Optimisation allocation selon profil risque
  - `Compliance Officer` - Vérification éligibilité PEA
  - `Portfolio Manager` - Décision finale et plan d'action
- **Sources de données**:
  - Zone Bourse, Boursorama - Rapports financiers PDF
  - Tavily API - Actualités récentes
  - Yahoo Finance - Données de marché
- **Modèles ML** (optionnel):
  - Optimisation Markowitz (moyenne-variance)
  - Calcul Sharpe ratio, volatilité
- **LLM**: Claude 3.5 Sonnet

**Pipeline complet** (durée ~5-8 minutes):
1. Identification top entreprises éligibles PEA par secteur
2. Collecte automatique rapports financiers (PDFs)
3. Indexation RAG des documents collectés
4. Analyse fondamentale multi-critères
5. Évaluation risques par entreprise
6. Optimisation allocation selon budget et profil
7. Génération plan d'action détaillé

**Request Body**:
```json
{
  "budget": 10000.0,
  "risk_profile": "balanced",
  "sectors": ["luxe", "technologie", "santé"],
  "exclude_companies": ["Total", "Société Générale"],
  "min_companies": 5,
  "max_companies": 8
}
```

**Profils de risque**:
- `conservative` - Prudent (dividendes, blue chips, faible volatilité)
- `balanced` - Équilibré (mix croissance/dividendes)
- `aggressive` - Dynamique (croissance forte, volatilité acceptée)

**Response 200**:
```json
{
  "action_plan": "# PLAN D'ACTION PORTEFEUILLE PEA\n\n**Budget total**: 10 000€\n**Profil**: Équilibré\n\n## ALLOCATION RECOMMANDÉE\n\n### 1. LVMH (MC.PA) - 25% (2 500€)\n- Acheter: 3 actions à 850€\n- Justification: Leader luxe mondial...\n\n### 2. Hermès (RMS.PA) - 20% (2 000€)...",
  "budget": 10000.0,
  "risk_profile": "balanced",
  "processing_time": 342.8,
  "timestamp": "2026-02-05T14:45:00",
  "data_collected": true
}
```

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
request = {
    "budget": 10000.0,
    "risk_profile": "balanced",
    "sectors": ["luxe", "technologie"],
    "min_companies": 5,
    "max_companies": 8
}

response = requests.post(
    "http://localhost:8000/build-portfolio",
    headers=headers,
    json=request,
    timeout=600  # 10 minutes timeout
)
plan = response.json()["action_plan"]
print(plan)
```

**Erreurs**:
- `400 Bad Request` - Profil risque invalide
- `500 Internal Server Error` - Erreur collecte données ou agents

---

## 8. Gestion de Portefeuille

### POST /portfolio/add

**Description**: Ajoute une position au portefeuille (achat d'actions).

**Outils utilisés**:
- `database/portfolio_db.py::PortfolioDatabase.add_position()` - Insertion SQLite
- `api/validators.py::validate_financial_amount()` - Validation Decimal montants
- `services/yahoo_finance_service.py` - Récupération prix marché
- SQLite transactions ACID pour cohérence

**Opérations effectuées**:
1. Validation montants (Decimal, 2 décimales max)
2. Vérification cash disponible suffisant
3. Insertion position ou update si existe
4. Déduction cash disponible
5. Enregistrement transaction dans historique

**Request Body**:
```json
{
  "ticker": "MC.PA",
  "company_name": "LVMH",
  "quantity": 10,
  "price": 850.50,
  "user_id": "default_user"
}
```

**Response 200**:
```json
{
  "message": "Position LVMH ajoutée avec succès",
  "ticker": "MC.PA"
}
```

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
position = {
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "price": 850.50
}

response = requests.post(
    "http://localhost:8000/portfolio/add",
    headers=headers,
    json=position
)
```

**Erreurs**:
- `400 Bad Request` - Montant invalide, solde insuffisant
- `500 Internal Server Error` - Erreur base de données

---

### POST /portfolio/sell

**Description**: Vend une position (partiellement ou totalement).

**Outils utilisés**:
- `database/portfolio_db.py::PortfolioDatabase.sell_position()` - MAJ SQLite
- Validation quantité disponible
- Calcul plus/moins-value réalisée
- Ajout cash au compte PEA

**Request Body**:
```json
{
  "ticker": "MC.PA",
  "quantity": 5,
  "price": 920.00,
  "user_id": "default_user"
}
```

**Response 200**:
```json
{
  "message": "Vente de 5 actions MC.PA enregistrée"
}
```

**Erreurs**:
- `400 Bad Request` - Quantité invalide, position inexistante
- `500 Internal Server Error` - Erreur base de données

---

### GET /portfolio

**Description**: Récupère le portefeuille complet avec prix à jour et statistiques.

**Outils utilisés**:
- `database/portfolio_db.py::update_current_prices()` - Refresh prix Yahoo Finance
- `database/portfolio_db.py::get_portfolio_summary()` - Calcul statistiques
- `yfinance` - Données marché temps réel

**Query Parameters**:
- `user_id` (string, default="default_user") - ID utilisateur

**Response 200**:
```json
{
  "total_positions": 3,
  "total_value": 25430.50,
  "total_invested": 23500.00,
  "total_gain_loss": 1930.50,
  "total_gain_loss_percent": 8.21,
  "cash_ratio": 15.2,
  "investment_ratio": 84.8,
  "pea_treasury": {
    "total_deposits": 30000.00,
    "cash_available": 4569.50,
    "cash_invested": 23500.00,
    "pea_total_value": 30000.00,
    "pea_gain_loss": 1930.50,
    "pea_gain_loss_percent": 6.43,
    "pea_opening_date": "2024-01-15",
    "last_deposit_date": "2025-12-01"
  },
  "positions": [
    {
      "ticker": "MC.PA",
      "company_name": "LVMH",
      "quantity": 10,
      "avg_price": 850.50,
      "current_price": 920.00,
      "current_value": 9200.00,
      "invested": 8505.00,
      "gain_loss": 695.00,
      "gain_loss_percent": 8.17,
      "last_updated": "2026-02-05T14:30:00"
    }
  ]
}
```

---

### GET /portfolio/context

**Description**: Contexte du portefeuille formaté pour l'IA (analyse textuelle complète).

**Outils utilisés**:
- `services/portfolio_manager.py::get_portfolio_context_for_ai()` - Génération contexte
- Calcul ratios, statistiques, opportunités
- Format markdown optimisé pour LLM

**Response 200**:
```json
{
  "context": "PORTEFEUILLE PEA DE L'UTILISATEUR:\n\n💰 TRÉSORERIE PEA:\n   • Valeur totale PEA: 30,000.00 €\n   • Total déposé: 30,000.00 €..."
}
```

---

### GET /portfolio/health

**Description**: Analyse la santé du portefeuille avec score 0-100 et recommandations.

**Outils utilisés**:
- `services/portfolio_manager.py::get_portfolio_health_score()` - Calcul score
- **Critères évalués** (100 points max):
  - Diversification (30 points) - Nombre positions optimal: 6-10
  - Concentration (25 points) - Aucune position > 25%
  - Performance globale (25 points) - P&L positif
  - Positions en perte (20 points) - < 50% positions en perte

**Response 200**:
```json
{
  "score": 82,
  "grade": "A (Très Bien)",
  "total_positions": 7,
  "total_value": 25430.50,
  "performance": 8.21,
  "issues": [
    "Aucun problème majeur détecté"
  ],
  "recommendations": [
    "Portefeuille en bonne santé, continuer le suivi régulier"
  ]
}
```

**Grille de notation**:
- 90-100: A+ (Excellent)
- 80-89: A (Très Bien)
- 70-79: B (Bien)
- 60-69: C (Moyen)
- 50-59: D (Faible)
- 0-49: F (Mauvais)

---

### GET /portfolio/rebalance

**Description**: Vérifie si le portefeuille nécessite un rééquilibrage.

**Outils utilisés**:
- `services/portfolio_manager.py::should_rebalance()` - Détection déséquilibres
- **Règles de rééquilibrage**:
  - Position > 25% → REDUCE à 20%
  - Position < 5% et < 15 positions → INCREASE à 8%
  - < 5 positions → DIVERSIFY

**Response 200**:
```json
{
  "needs_rebalance": true,
  "portfolio_size": 7,
  "total_value": 25430.50,
  "recommendations": [
    {
      "action": "REDUCE",
      "ticker": "MC.PA",
      "company": "LVMH",
      "current_weight": 28.5,
      "target_weight": 20,
      "reason": "Concentration excessive (>25%)",
      "urgency": "HIGH"
    }
  ]
}
```

---

### GET /portfolio/position/{ticker}

**Description**: Récupère tous les détails d'une position (portfolio + marché + historique).

**Outils utilisés**:
- `services/portfolio_manager.py::get_position_details()` - Agrégation données
- `services/yahoo_finance_service.py::get_stock_info()` - Données marché
- `database/portfolio_db.py::get_transactions()` - Historique transactions
- `database/portfolio_db.py::get_analysis_history()` - Analyses passées

**URL Parameters**:
- `ticker` (string, required) - Ticker de l'action

**Response 200**:
```json
{
  "position": {
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "avg_price": 850.50,
    "current_price": 920.00
  },
  "market_data": {
    "currentPrice": 920.00,
    "marketCap": 465000000000,
    "pe_ratio": 23.5,
    "dividend_yield": 1.8
  },
  "transactions": [
    {
      "date": "2024-01-15",
      "type": "BUY",
      "quantity": 10,
      "price": 850.50
    }
  ],
  "past_analyses": []
}
```

---

## 9. Trésorerie PEA

### POST /portfolio/deposit

**Description**: Dépose de l'argent sur le PEA (alimentation compte).

**Outils utilisés**:
- `database/portfolio_db.py::deposit_cash()` - Insertion SQLite
- `api/validators.py::validate_financial_amount()` - Validation montant
- **Validations**:
  - Montant > 0
  - Montant <= 150 000€ (plafond PEA)
  - Total dépôts <= 150 000€ (plafond PEA)

**Request Parameters**:
- `amount` (float, required) - Montant à déposer (euros)
- `user_id` (string, default="default_user") - ID utilisateur
- `notes` (string, optional) - Notes sur le dépôt

**Request Body** (query params ou JSON):
```json
{
  "amount": 5000.00,
  "user_id": "default_user",
  "notes": "Versement mensuel février 2026"
}
```

**Response 200**:
```json
{
  "message": "Dépôt de 5000.00€ effectué avec succès",
  "new_cash_available": 9569.50,
  "total_deposits": 35000.00
}
```

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
params = {
    "amount": 5000.00,
    "notes": "Versement février 2026"
}

response = requests.post(
    "http://localhost:8000/portfolio/deposit",
    headers=headers,
    params=params
)
```

**Erreurs**:
- `400 Bad Request` - Montant invalide, plafond PEA dépassé (150 000€)

---

### GET /portfolio/treasury

**Description**: Récupère l'état complet de la trésorerie PEA.

**Outils utilisés**:
- `database/portfolio_db.py::get_treasury_status()` - Calcul trésorerie
- Agrégation des dépôts, achats, ventes

**Response 200**:
```json
{
  "total_deposits": 35000.00,
  "cash_available": 9569.50,
  "cash_invested": 23500.00,
  "pea_total_value": 35000.00,
  "pea_gain_loss": 1930.50,
  "pea_gain_loss_percent": 5.52,
  "pea_opening_date": "2024-01-15",
  "last_deposit_date": "2026-02-05",
  "days_since_opening": 751,
  "is_pea_5_years_eligible": false
}
```

**Calculs**:
- `pea_total_value` = cash_available + valeur_positions_actuelles
- `pea_gain_loss` = pea_total_value - total_deposits
- `pea_gain_loss_percent` = (pea_gain_loss / total_deposits) * 100

---

### GET /portfolio/treasury/deposits

**Description**: Récupère l'historique des dépôts effectués sur le PEA.

**Outils utilisés**:
- `database/portfolio_db.py::get_deposit_history()` - Query SQLite

**Query Parameters**:
- `user_id` (string, default="default_user")
- `limit` (int, default=50) - Nombre max de dépôts

**Response 200**:
```json
{
  "user_id": "default_user",
  "total_deposits": 7,
  "deposits": [
    {
      "id": 7,
      "amount": 5000.00,
      "date": "2026-02-05T14:30:00",
      "notes": "Versement février 2026"
    },
    {
      "id": 6,
      "amount": 5000.00,
      "date": "2025-12-01T10:00:00",
      "notes": "Versement décembre 2025"
    }
  ]
}
```

---

### GET /portfolio/treasury/cashflow

**Description**: Récupère l'historique des flux de trésorerie (dépôts, achats, ventes).

**Outils utilisés**:
- `database/portfolio_db.py::get_cash_flow_events()` - Agrégation événements

**Query Parameters**:
- `user_id` (string, default="default_user")
- `event_type` (string, optional) - Filtre: "DEPOSIT", "BUY", "SELL", ou null pour tous
- `limit` (int, default=100) - Nombre max d'événements

**Response 200**:
```json
{
  "user_id": "default_user",
  "event_type_filter": "ALL",
  "total_events": 15,
  "events": [
    {
      "date": "2026-02-05T14:30:00",
      "type": "DEPOSIT",
      "amount": 5000.00,
      "description": "Versement février 2026",
      "cash_balance_after": 9569.50
    },
    {
      "date": "2026-02-01T09:15:00",
      "type": "BUY",
      "ticker": "MC.PA",
      "quantity": 5,
      "price": 920.00,
      "amount": -4600.00,
      "cash_balance_after": 4569.50
    }
  ]
}
```

---

## 10. Opportunités d'Investissement

### POST /portfolio/opportunities/analyze

**Description**: Analyse le cash disponible et suggère des opportunités d'investissement intelligentes.

**Outils utilisés**:
- `services/portfolio_manager.py::analyze_cash_opportunities()` - Analyse opportunités
- **Règles de détection**:
  - Cash disponible >= 100€
  - Diversification < 5 positions → DIVERSIFY
  - Position gagnante (>5%) + poids < 20% → ADD_TO_EXISTING
  - Cash ratio > 30% → REBALANCE_CASH

**Query Parameters**:
- `user_id` (string, default="default_user")

**Response 200**:
```json
{
  "has_opportunities": true,
  "cash_available": 9569.50,
  "cash_ratio": 27.3,
  "portfolio_size": 7,
  "total_value": 35000.00,
  "opportunities": [
    {
      "type": "ADD_TO_EXISTING",
      "ticker": "MC.PA",
      "company_name": "LVMH",
      "priority": "MEDIUM",
      "description": "Renforcer LVMH (performance: +8.2%, poids actuel: 18.5%)",
      "suggested_amount": 2000.00,
      "suggested_quantity": 2,
      "current_price": 920.00,
      "current_weight": 18.5,
      "target_weight": 24.0,
      "reasoning": "Position performante avec potentiel de renforcement sans surconcentration"
    }
  ]
}
```

**Types d'opportunités**:
- `DIVERSIFY` - Ajouter nouvelles positions (< 5 positions)
- `ADD_TO_EXISTING` - Renforcer position gagnante
- `REBALANCE_CASH` - Trop de cash dormant (> 30%)

---

### GET /portfolio/opportunities/pending

**Description**: Récupère toutes les opportunités en attente de décision utilisateur.

**Outils utilisés**:
- `services/portfolio_manager.py::get_pending_opportunities()` - Query SQLite

**Query Parameters**:
- `user_id` (string, default="default_user")
- `include_expired` (bool, default=false) - Inclure opportunités expirées

**Response 200**:
```json
{
  "success": true,
  "count": 2,
  "opportunities": [
    {
      "id": 1,
      "ticker": "MC.PA",
      "company_name": "LVMH",
      "recommendation_type": "ADD_TO_EXISTING",
      "suggested_amount": 2000.00,
      "suggested_quantity": 2,
      "target_price": 920.00,
      "reasoning": "Position performante...",
      "confidence_score": 0.78,
      "risk_level": "MEDIUM",
      "status": "PENDING",
      "created_at": "2026-02-05T14:00:00",
      "expires_at": "2026-02-12T14:00:00",
      "cash_available_at_time": 9569.50,
      "portfolio_value_at_time": 35000.00
    }
  ]
}
```

---

### POST /portfolio/opportunities/create

**Description**: Crée manuellement une nouvelle opportunité d'investissement.

**Outils utilisés**:
- `services/portfolio_manager.py::save_opportunity_to_db()` - Insertion SQLite

**Request Parameters**:
```json
{
  "ticker": "MC.PA",
  "company_name": "LVMH",
  "recommendation_type": "ADD_TO_EXISTING",
  "suggested_amount": 2000.00,
  "reasoning": "Position performante avec potentiel",
  "user_id": "default_user",
  "suggested_quantity": 2,
  "target_price": 920.00,
  "confidence_score": 0.78,
  "risk_level": "MEDIUM",
  "expires_in_days": 7
}
```

**Types de recommandation**:
- `NEW_POSITION` - Nouvelle position à créer
- `ADD_TO_EXISTING` - Renforcer position existante
- `DIVERSIFY` - Diversifier le portefeuille

**Response 200**:
```json
{
  "success": true,
  "message": "Opportunité créée avec succès"
}
```

---

### POST /portfolio/opportunities/{opportunity_id}/accept

**Description**: Accepte une opportunité et exécute automatiquement la transaction.

**Outils utilisés**:
- `services/portfolio_manager.py::accept_opportunity()` - Orchestration
- `database/portfolio_db.py::add_position()` - Exécution achat
- `services/yahoo_finance_service.py::get_stock_info()` - Prix marché actuel
- **Validations**:
  - Opportunité existe et PENDING
  - Non expirée
  - Cash disponible suffisant
  - Montants valides (Decimal)

**URL Parameters**:
- `opportunity_id` (int, required) - ID de l'opportunité

**Request Body** (optionnel):
```json
{
  "user_id": "default_user",
  "actual_quantity": 3,
  "actual_price": 915.00
}
```

**Response 200**:
```json
{
  "success": true,
  "ticker": "MC.PA",
  "company_name": "LVMH",
  "quantity": 3,
  "price": 915.00,
  "total_amount": 2745.00,
  "message": "Transaction exécutée: 3 actions de LVMH à 915.00€"
}
```

**Erreurs**:
- `400 Bad Request` - Opportunité expirée, cash insuffisant
- `404 Not Found` - Opportunité inexistante

---

### POST /portfolio/opportunities/{opportunity_id}/reject

**Description**: Rejette une opportunité d'investissement.

**Outils utilisés**:
- `services/portfolio_manager.py::reject_opportunity()` - MAJ statut SQLite

**Request Body**:
```json
{
  "user_id": "default_user",
  "reason": "Préfère attendre baisse du prix"
}
```

**Response 200**:
```json
{
  "success": true,
  "message": "Opportunité rejetée"
}
```

---

### GET /portfolio/opportunities/{opportunity_id}

**Description**: Récupère les détails d'une opportunité spécifique.

**Response 200**:
```json
{
  "success": true,
  "opportunity": {
    "id": 1,
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "recommendation_type": "ADD_TO_EXISTING",
    "suggested_amount": 2000.00,
    "status": "PENDING"
  }
}
```

---

## 11. Données de Marché

### GET /market/stock/{ticker}

**Description**: Récupère les informations de marché d'une action en temps réel.

**Outils utilisés**:
- `services/yahoo_finance_service.py::get_stock_info()` - Wrapper yfinance
- `yfinance` - API Yahoo Finance
- **Données récupérées**:
  - Prix actuel, ouverture, clôture précédente
  - Plus haut/plus bas 52 semaines
  - Capitalisation boursière
  - P/E ratio, PEG ratio
  - Dividende et rendement
  - Beta, volume moyen

**URL Parameters**:
- `ticker` (string, required) - Ticker Yahoo Finance (ex: MC.PA pour LVMH)

**Response 200**:
```json
{
  "ticker": "MC.PA",
  "shortName": "LVMH",
  "currentPrice": 920.00,
  "previousClose": 915.50,
  "open": 918.00,
  "dayHigh": 925.00,
  "dayLow": 916.00,
  "fiftyTwoWeekHigh": 950.00,
  "fiftyTwoWeekLow": 680.00,
  "marketCap": 465000000000,
  "volume": 850000,
  "averageVolume": 900000,
  "dividendYield": 0.018,
  "trailingPE": 23.5,
  "forwardPE": 21.2,
  "beta": 1.15,
  "currency": "EUR"
}
```

**Exemple Python**:
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/market/stock/MC.PA",
    headers=headers
)
price = response.json()["currentPrice"]
print(f"Prix LVMH: {price}€")
```

**Erreurs**:
- `404 Not Found` - Ticker inexistant ou invalide

---

### GET /market/history/{ticker}

**Description**: Récupère l'historique des cours d'une action.

**Outils utilisés**:
- `services/yahoo_finance_service.py::get_historical_data()` - Wrapper yfinance
- `yfinance::download()` - Téléchargement données historiques
- Retour format pandas DataFrame converti en JSON

**URL Parameters**:
- `ticker` (string, required) - Ticker de l'action

**Query Parameters**:
- `period` (string, default="1y") - Période: "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"
- `interval` (string, default="1d") - Intervalle: "1d", "1wk", "1mo"

**Response 200**:
```json
{
  "ticker": "MC.PA",
  "period": "1y",
  "interval": "1d",
  "data_points": 252,
  "data": [
    {
      "Date": "2025-02-05",
      "Open": 850.00,
      "High": 860.00,
      "Low": 845.00,
      "Close": 855.50,
      "Volume": 1200000
    }
  ]
}
```

**Note**: La réponse est limitée aux 100 premiers points par défaut pour éviter les réponses trop volumineuses.

---

## 12. Analyses Avancées

### GET /analysis/news/{company_name}

**Description**: Récupère les actualités récentes d'une entreprise depuis le web.

**Outils utilisés**:
- `services/news_aggregator.py::NewsAggregator.get_company_news()` - Agrégation news
- **Sources**:
  - Tavily API - Recherche web temps réel
  - Google News RSS (fallback)
- Filtrage par pertinence et date

**URL Parameters**:
- `company_name` (string, required) - Nom de l'entreprise

**Query Parameters**:
- `days_back` (int, default=7) - Nombre de jours dans le passé

**Response 200**:
```json
{
  "company": "LVMH",
  "news_count": 12,
  "articles": [
    {
      "title": "LVMH annonce une croissance record au Q4 2025",
      "url": "https://...",
      "source": "Les Échos",
      "published_date": "2026-02-04T10:30:00",
      "snippet": "Le groupe de luxe français LVMH a publié des résultats trimestriels...",
      "relevance_score": 0.95
    }
  ]
}
```

---

### GET /analysis/sentiment/{company_name}

**Description**: Analyse le sentiment des actualités pour une entreprise (positif/négatif/neutre).

**Outils utilisés**:
- `services/news_aggregator.py::get_company_news()` - Récupération actualités
- `services/sentiment_analyzer.py::SentimentAnalyzer.analyze_news_sentiment()` - Analyse sentiment
- **Modèle NLP**:
  - Claude 3.5 Sonnet (provider="claude") - Analyse sentiment contextualisée
  - GPT-4 (provider="openai", fallback) - Analyse sentiment
- **Méthode**:
  - Analyse article par article avec LLM
  - Agrégation scores (positif: +1, neutre: 0, négatif: -1)
  - Score moyen et distribution

**URL Parameters**:
- `company_name` (string, required) - Nom de l'entreprise

**Query Parameters**:
- `days_back` (int, default=7) - Période d'analyse

**Response 200**:
```json
{
  "company": "LVMH",
  "period_days": 7,
  "total_articles": 12,
  "sentiment_score": 0.68,
  "sentiment_label": "POSITIVE",
  "distribution": {
    "positive": 8,
    "neutral": 3,
    "negative": 1
  },
  "confidence": 0.85,
  "key_themes": [
    "Croissance Q4",
    "Expansion Asie",
    "Innovation produits"
  ],
  "articles_analyzed": [
    {
      "title": "LVMH annonce une croissance record...",
      "sentiment": "POSITIVE",
      "score": 0.9
    }
  ]
}
```

**Labels de sentiment**:
- `VERY_POSITIVE` - Score > 0.6
- `POSITIVE` - Score 0.2 à 0.6
- `NEUTRAL` - Score -0.2 à 0.2
- `NEGATIVE` - Score -0.6 à -0.2
- `VERY_NEGATIVE` - Score < -0.6

---

### GET /analysis/technical/{ticker}

**Description**: Analyse technique complète d'une action (indicateurs, signaux, niveaux).

**Outils utilisés**:
- `services/yahoo_finance_service.py::get_historical_data()` - Données historiques
- `services/technical_analysis.py::TechnicalAnalyzer` - Calcul indicateurs
- **Indicateurs calculés**:
  - Moyennes mobiles: SMA 50, SMA 200, EMA 20
  - RSI (Relative Strength Index, 14 périodes)
  - MACD (Moving Average Convergence Divergence)
  - Bandes de Bollinger (20 périodes, 2 écarts-types)
  - Volume moyen
- **Bibliothèques**:
  - `pandas-ta` (priorité) - Calculs indicateurs optimisés
  - Calculs manuels (fallback si pandas-ta indisponible)

**URL Parameters**:
- `ticker` (string, required) - Ticker de l'action

**Query Parameters**:
- `period` (string, default="6mo") - Période d'analyse

**Response 200**:
```json
{
  "ticker": "MC.PA",
  "signals": {
    "score": 45,
    "recommendation": "ACHETER",
    "signals": [
      "Prix au-dessus des MA 50 et 200 (haussier)",
      "RSI à 42.5 - Zone neutre",
      "MACD au-dessus du signal (momentum haussier)",
      "Prix proche de la bande basse de Bollinger (opportunité)"
    ],
    "current_price": 920.00,
    "sma_50": 895.20,
    "sma_200": 850.00,
    "rsi": 42.5,
    "macd": 5.2
  },
  "levels": {
    "supports": [900.00, 880.00, 850.00],
    "resistances": [950.00, 980.00, 1000.00],
    "current_price": 920.00
  },
  "trend": "HAUSSIER"
}
```

**Score de signal** (-100 à +100):
- >= 50: ACHETER FORT
- 25 à 49: ACHETER
- 10 à 24: ACCUMULER
- -10 à 9: CONSERVER
- -25 à -11: ALLÉGER
- < -25: VENDRE

**Tendance**:
- `HAUSSIER` - Pente SMA > +5% sur période
- `BAISSIER` - Pente SMA < -5% sur période
- `NEUTRE` - Pente SMA entre -5% et +5%

---

### GET /analysis/complete/{ticker}

**Description**: Analyse complète all-in-one combinant données marché, actualités, sentiment et technique.

**Outils utilisés** (TOUS):
- `services/yahoo_finance_service.py` - Données marché
- `services/news_aggregator.py` - Actualités récentes
- `services/sentiment_analyzer.py` - Analyse sentiment
- `services/technical_analysis.py` - Analyse technique
- **Pipeline** (durée ~15-20 secondes):
  1. Récupération données marché (2s)
  2. Recherche actualités 7 derniers jours (5s)
  3. Analyse sentiment avec Claude (8s)
  4. Calcul indicateurs techniques (3s)
  5. Agrégation résultats (1s)

**URL Parameters**:
- `ticker` (string, required) - Ticker de l'action
- `company_name` (string, required) - Nom de l'entreprise

**Response 200**:
```json
{
  "ticker": "MC.PA",
  "company": "LVMH",
  "market_data": {
    "currentPrice": 920.00,
    "marketCap": 465000000000,
    "pe_ratio": 23.5,
    "dividend_yield": 0.018
  },
  "news_sentiment": {
    "sentiment_score": 0.68,
    "sentiment_label": "POSITIVE",
    "total_articles": 12,
    "distribution": {
      "positive": 8,
      "neutral": 3,
      "negative": 1
    }
  },
  "technical_analysis": {
    "signals": {
      "score": 45,
      "recommendation": "ACHETER",
      "current_price": 920.00,
      "rsi": 42.5
    },
    "levels": {
      "supports": [900.00, 880.00, 850.00],
      "resistances": [950.00, 980.00, 1000.00]
    },
    "trend": "HAUSSIER"
  }
}
```

**Exemple Python (analyse complète)**:
```python
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/analysis/complete/MC.PA",
    headers=headers,
    params={"company_name": "LVMH"}
)
analysis = response.json()

# Décision basée sur tous les signaux
market_cap = analysis["market_data"]["marketCap"]
sentiment = analysis["news_sentiment"]["sentiment_label"]
tech_rec = analysis["technical_analysis"]["signals"]["recommendation"]
trend = analysis["technical_analysis"]["trend"]

print(f"Capitalisation: {market_cap/1e9:.1f}B€")
print(f"Sentiment: {sentiment}")
print(f"Technique: {tech_rec}")
print(f"Tendance: {trend}")

# Logique de décision simple
if sentiment == "POSITIVE" and tech_rec in ["ACHETER", "ACHETER FORT"] and trend == "HAUSSIER":
    print("SIGNAL D'ACHAT FORT")
```

---

## 13. Machine Learning

### 13.1 Train Model
**Endpoint**: `POST /ml/train/{ticker}`
**Auth**: JWT Token requis
**Description**: Entraîne un modèle de prédiction de prix (LSTM/Prophet/Ensemble)

**Outils utilisés**:
- **TensorFlow/Keras** (LSTM deep learning)
- **Prophet** (Facebook time series)
- **yfinance** (données historiques)
- **pandas-ta** (feature engineering: RSI, MACD, SMA)
- **scikit-learn** (normalisation, métriques)

**Body**:
```json
{
  "ticker": "MC.PA",
  "model_type": "ensemble",
  "period": "2y",
  "epochs": 100,
  "test_size": 0.2,
  "save_model": true
}
```

**Réponse**:
```json
{
  "success": true,
  "ticker": "MC.PA",
  "model_type": "ensemble",
  "trained_at": "2026-02-06T10:30:00Z",
  "training_metrics": {
    "mae": 12.5,
    "rmse": 18.3,
    "mape": 2.1,
    "direction_accuracy": 0.68
  }
}
```

**Temps d'exécution**: 2-5 minutes

---

### 13.2 Predict Prices
**Endpoint**: `GET /ml/predict/{ticker}`
**Auth**: JWT Token requis
**Description**: Prédit les prix futurs d'une action

**Outils utilisés**:
- **TensorFlow/Keras** (modèle LSTM chargé)
- **Prophet** (modèle time series chargé)
- **joblib** (chargement modèle)

**Paramètres**:
- `horizon`: Jours à prédire (1-90, défaut: 30)
- `model_type`: lstm, prophet, ensemble (défaut: ensemble)

**Réponse**:
```json
{
  "ticker": "MC.PA",
  "current_price": 730.0,
  "predictions": [
    {"date": "2026-02-07", "price": 735.0, "confidence_low": 720.0, "confidence_high": 750.0}
  ],
  "trend": "BULLISH",
  "price_change_pct": 3.2,
  "expected_return_30d": 3.2,
  "confidence_avg": 0.75,
  "recommendation": "BUY"
}
```

**Performance**: < 2 secondes

---

### 13.3 Evaluate Model
**Endpoint**: `GET /ml/evaluate/{ticker}`
**Description**: Évalue la performance d'un modèle

**Outils utilisés**: scikit-learn (métriques), numpy

**Réponse**:
```json
{
  "ticker": "MC.PA",
  "model_type": "ensemble",
  "metrics": {
    "mae": 12.5,
    "rmse": 18.3,
    "mape": 2.1,
    "direction_accuracy": 0.68
  }
}
```

---

### 13.4 List Models
**Endpoint**: `GET /ml/models`
**Description**: Liste tous les modèles entraînés

---

### 13.5 Delete Model
**Endpoint**: `DELETE /ml/models/{ticker}`
**Description**: Supprime un modèle (irréversible)

---

### 13.6 Model Info
**Endpoint**: `GET /ml/models/{ticker}/info`
**Description**: Informations détaillées sur un modèle

---

### 13.7 Retrain Model
**Endpoint**: `POST /ml/retrain/{ticker}`
**Description**: Re-entraîne un modèle avec données récentes (background task)

---

### 13.8 ML Status
**Endpoint**: `GET /ml/status`
**Description**: Statut du système ML

**Réponse**:
```json
{
  "status": "operational",
  "models_loaded": ["lstm", "prophet", "ensemble"],
  "tensorflow_version": "2.13.0",
  "gpu_available": false
}
```

---

## 14. Backtesting

### 14.1 Run Backtest
**Endpoint**: `POST /backtesting/run`
**Auth**: JWT Token requis
**Description**: Lance un backtest pour une stratégie

**Outils utilisés**:
- **BacktestEngine** (moteur custom)
- **yfinance** (données historiques)
- **numpy/pandas** (calculs vectorisés)
- **Stratégies**: MA Crossover, RSI, MACD, Bollinger, Momentum, Buy&Hold

**Body**:
```json
{
  "ticker": "MC.PA",
  "strategy": "ma_crossover",
  "params": {"fast_period": 20, "slow_period": 50},
  "start_date": "2021-01-01",
  "end_date": "2026-01-01",
  "initial_capital": 10000.0,
  "commission": 0.001,
  "slippage": 0.0005
}
```

**Réponse**:
```json
{
  "backtest_id": "a7f3c2d9e1b4",
  "strategy": "Moving Average Crossover",
  "ticker": "MC.PA",
  "period": "2021-01-01 to 2026-01-01",
  "performance": {
    "total_return": 45.3,
    "annualized_return": 8.2,
    "sharpe_ratio": 1.35,
    "sortino_ratio": 1.82,
    "max_drawdown": -15.7,
    "win_rate": 0.58,
    "profit_factor": 1.65,
    "num_trades": 28
  },
  "trades": [
    {
      "entry_date": "2021-03-15",
      "exit_date": "2021-05-20",
      "type": "LONG",
      "entry_price": 620.0,
      "exit_price": 670.0,
      "pnl": 800.0
    }
  ]
}
```

---

### 14.2 List Strategies
**Endpoint**: `GET /backtesting/strategies`
**Description**: Liste toutes les stratégies disponibles (6 stratégies)

**Réponse**:
```json
{
  "total": 6,
  "strategies": [
    {
      "name": "ma_crossover",
      "display_name": "Moving Average Crossover",
      "default_params": {"fast_period": 20, "slow_period": 50}
    },
    {
      "name": "rsi_strategy",
      "display_name": "RSI Strategy",
      "default_params": {"rsi_period": 14, "oversold": 30, "overbought": 70}
    }
  ]
}
```

---

### 14.3 Compare Strategies
**Endpoint**: `POST /backtesting/compare`
**Description**: Compare plusieurs stratégies sur mêmes données

**Outils utilisés**: BacktestEngine, yfinance, plotly

---

### 14.4 Optimize Strategy
**Endpoint**: `POST /backtesting/optimize`
**Description**: Optimise paramètres via Grid Search

**Outils utilisés**: BacktestEngine, itertools

**Temps d'exécution**: 1-10 minutes

---

### 14.5 Get Results
**Endpoint**: `GET /backtesting/results/{backtest_id}`
**Description**: Récupère résultats complets d'un backtest

---

### 14.6 Get Visualization
**Endpoint**: `GET /backtesting/visualization/{backtest_id}`
**Description**: Génère visualisation interactive

**Outils utilisés**: plotly, pandas

**Paramètres**:
- `chart_type`: equity, drawdown, returns

---

## 15. Intelligence (ML + Backtesting + Agents)

### 15.1 Complete Intelligence Analysis 🔥
**Endpoint**: `POST /intelligence/analyze/{ticker}`
**Auth**: JWT Token requis
**Description**: **Analyse d'investissement complète** combinant ML, backtesting, technique et fondamentale

**🔥 ENDPOINT PRINCIPAL - Agrège tous les outils d'analyse**

**Outils utilisés**:
- **ML**: PricePredictor (LSTM/Prophet) - Prédictions 30 jours
- **Backtesting**: BacktestEngine (6+ stratégies) - Test historique
- **Technical**: RSI, MACD, Bollinger - Indicateurs techniques
- **Fundamental**: CrewAI agents (optionnel) - Analyse fondamentale
- **Aggregation**: Vote pondéré par confiance

**Paramètres**:
- `ticker`: Symbole boursier (ex: MC.PA)
- `include_ml`: Inclure ML (défaut: true)
- `include_backtesting`: Inclure backtesting (défaut: true)
- `include_technical`: Inclure technique (défaut: true)
- `include_fundamental`: Inclure fundamental (défaut: false)
- `backtest_period`: Période - 1Y, 2Y, 5Y (défaut: 5Y)

**Réponse**:
```json
{
  "ticker": "MC.PA",
  "timestamp": "2026-02-06T10:30:00Z",
  "current_price": 730.0,

  "ml_prediction": {
    "expected_return_30d": 3.2,
    "confidence_avg": 0.75,
    "trend": "BULLISH",
    "price_30d": 753.36
  },

  "backtesting": {
    "best_strategy": "rsi_strategy",
    "sharpe_ratio": 1.68,
    "total_return": 52.3,
    "max_drawdown": -12.4,
    "win_rate": 0.64,
    "signal": "BUY"
  },

  "technical_analysis": {
    "rsi": 65.2,
    "macd": "BUY",
    "bollinger": "NEUTRAL",
    "signal": "BUY"
  },

  "aggregated_recommendation": {
    "decision": "BUY",
    "confidence": 0.78,
    "signals_count": {"BUY": 3, "HOLD": 1, "SELL": 0},
    "target_price": 803.0,
    "stop_loss": 693.5,
    "expected_return": 10.0,
    "risk_level": "MODERATE",
    "time_horizon": "30_DAYS",
    "reasoning": "Decision: BUY (confidence: 0.78). ML predicts +3.2% | Backtesting: rsi_strategy (Sharpe: 1.68) | Technical: BUY signals"
  },

  "reasoning": "ML predicts +3.2% in 30 days. Best backtest: rsi_strategy (Sharpe: 1.68). Technical: RSI=65.2. Final: BUY (conf: 0.78).",

  "signals": [
    {
      "source": "ML",
      "decision": "BUY",
      "confidence": 0.75,
      "reasoning": "ML predicts +3.2% over 30 days (BULLISH trend)"
    },
    {
      "source": "BACKTESTING",
      "decision": "BUY",
      "confidence": 0.85,
      "reasoning": "Best strategy: rsi_strategy (Sharpe: 1.68, Return: +52.3%)"
    },
    {
      "source": "TECHNICAL",
      "decision": "BUY",
      "confidence": 0.70,
      "reasoning": "RSI: 65.2 (HOLD), MACD: BUY, Bollinger: NEUTRAL"
    }
  ]
}
```

**Exemple**:
```python
response = requests.post(
    "http://localhost:8000/intelligence/analyze/MC.PA",
    params={
        "include_ml": True,
        "include_backtesting": True,
        "include_technical": True,
        "backtest_period": "5Y"
    },
    headers={"Authorization": f"Bearer {token}"}
)

analysis = response.json()
print(f"Recommandation: {analysis['aggregated_recommendation']['decision']}")
print(f"Confiance: {analysis['aggregated_recommendation']['confidence']}")
print(f"Prix cible: {analysis['aggregated_recommendation']['target_price']} €")
```

**Pipeline**:
1. Récupération données marché
2. ML Predictions (30 jours)
3. Backtesting (3 meilleures stratégies)
4. Analyse technique (RSI, MACD, Bollinger)
5. Analyse fondamentale (optionnel)
6. Agrégation vote pondéré
7. Recommandation finale BUY/HOLD/SELL

**Temps d'exécution**:
- Sans ML training: 10-20 secondes
- Avec ML training: 2-5 minutes

---

## 16. Codes d'Erreur

| Code | Signification | Cause | Solution |
|------|---------------|-------|----------|
| **400** | Bad Request | Paramètres invalides, validation échouée | Vérifier format JSON, types de données, contraintes |
| **401** | Unauthorized | Token JWT manquant, invalide ou expiré | Se reconnecter avec `/auth/login` |
| **404** | Not Found | Ressource inexistante (collection, ticker, opportunité) | Vérifier que la ressource existe avec endpoints de listing |
| **422** | Unprocessable Entity | Validation Pydantic échouée | Vérifier le schéma de requête (types, champs requis) |
| **500** | Internal Server Error | Erreur serveur (base de données, LLM, agents) | Consulter logs serveur, vérifier services externes |
| **503** | Service Unavailable | Service externe indisponible (Ollama, Yahoo Finance, Tavily) | Vérifier que tous les services sont démarrés |

---

### Exemples de Gestion d'Erreurs

**Python**:
```python
import requests

def safe_api_call(url, headers, **kwargs):
    """Wrapper avec gestion d'erreurs"""
    try:
        response = requests.get(url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Token expiré, reconnexion nécessaire")
            # Relancer authentification
        elif e.response.status_code == 404:
            print("Ressource non trouvée")
        elif e.response.status_code == 503:
            print("Service temporairement indisponible")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur réseau: {e}")
        return None

# Usage
result = safe_api_call(
    "http://localhost:8000/portfolio",
    headers={"Authorization": f"Bearer {token}"}
)
```

---

## 17. Glossaire Technique

### Termes Financiers

- **PEA (Plan d'Épargne en Actions)**: Compte-titres français avec avantages fiscaux. Plafond versements: 150 000€. Exonération fiscale après 5 ans.
- **Ticker**: Symbole boursier unique d'une action (ex: MC.PA pour LVMH sur Euronext Paris)
- **PRU (Prix de Revient Unitaire)**: Prix moyen d'achat d'une action
- **P/E Ratio (Price-to-Earnings)**: Ratio cours/bénéfice. Valorisation relative.
- **Sharpe Ratio**: Rendement ajusté au risque. > 1 = bon, > 2 = excellent
- **Drawdown**: Perte maximale depuis le pic historique
- **RSI (Relative Strength Index)**: Indicateur de surachat (>70) / survente (<30)
- **MACD**: Indicateur de momentum et tendance
- **Golden Cross**: Croisement haussier MA courte > MA longue
- **Death Cross**: Croisement baissier MA courte < MA longue

### Termes Techniques

- **RAG (Retrieval-Augmented Generation)**: Architecture combinant recherche vectorielle et génération LLM
- **Embedding**: Représentation vectorielle d'un texte (768 dimensions pour paraphrase-multilingual-mpnet-base-v2)
- **ChromaDB**: Base de données vectorielle pour stockage embeddings
- **Cosine Similarity**: Mesure de similarité entre vecteurs (-1 à 1)
- **Chunking**: Découpage de document en morceaux (chunks) de taille optimale
- **LLM (Large Language Model)**: Modèle de langage (Claude, GPT-4, Mistral)
- **CrewAI**: Framework d'orchestration multi-agents IA
- **JWT (JSON Web Token)**: Token d'authentification sécurisé
- **ACID**: Propriétés transactionnelles (Atomicité, Cohérence, Isolation, Durabilité)

### Modèles et Services

- **Claude 3.5 Sonnet**: LLM Anthropic utilisé pour analyses et agents (200K tokens contexte)
- **Mistral**: LLM open-source via Ollama pour génération RAG
- **sentence-transformers/paraphrase-multilingual-mpnet-base-v2**: Modèle embedding optimisé français (768 dimensions)
- **yfinance**: Bibliothèque Python pour données Yahoo Finance
- **Tavily API**: Moteur de recherche web pour actualités temps réel
- **bcrypt**: Algorithme de hashage sécurisé pour mots de passe
- **python-jose**: Bibliothèque JWT pour authentification

### Architecture Système

- **FastAPI**: Framework web Python haute performance avec auto-documentation
- **Pydantic**: Validation de données et sérialisation
- **SQLite**: Base de données relationnelle pour portefeuille et transactions
- **Uvicorn**: Serveur ASGI pour FastAPI
- **PyMuPDF (fitz)**: Extraction de contenu PDF
- **pandas**: Manipulation de données tabulaires
- **numpy**: Calculs numériques et statistiques

---

## Notes d'Utilisation

### Authentification

Tous les endpoints (sauf `/`, `/health`, `/auth/login`) nécessitent un token JWT:

```python
# 1. Login
response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "admin", "password": "secret"}
)
token = response.json()["access_token"]

# 2. Utiliser le token pour tous les appels
headers = {"Authorization": f"Bearer {token}"}
```

### Bonnes Pratiques

1. **Caching des tokens**: Stocker le token et le réutiliser (validité 30 jours)
2. **Gestion d'erreurs**: Implémenter retry logic pour erreurs 503
3. **Timeouts**: Configurer timeouts longs pour endpoints lents (CrewAI: 10 min)
4. **Validation locale**: Valider données côté client avant envoi API
5. **Logging**: Logger toutes les requêtes et réponses pour debugging

### Limitations

- **Rate Limiting**: Pas de rate limiting actuellement (usage personnel)
- **Taille uploads**: Max 100 MB par fichier PDF
- **Nombre de collections**: Pas de limite technique (limite pratique: performances ChromaDB)
- **Plafond PEA**: 150 000€ de versements maximum (contrainte légale française)
- **Ollama**: Doit être démarré localement (`ollama serve`)

---

**Documentation générée automatiquement le 2026-02-05**
**Pour plus d'informations**: Consultez la documentation interactive Swagger à `/docs`
