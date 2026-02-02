# 🚀 Guide de Test Rapide - Toutes les Fonctionnalités

Guide de test express pour valider rapidement que toutes les fonctionnalités de l'API fonctionnent correctement.

## ⚡ Tests en 5 minutes

### Prérequis

```bash
# 1. API lancée
cd api && python -m uvicorn main:app --reload

# 2. Dans un autre terminal
export API_URL="http://localhost:8000"
```

---

## 🏥 Health & System

### 1. Health Check
```bash
curl $API_URL/health | jq
```
**Attendu** : `status: "healthy"`, `ollama_available: true/false`

### 2. Collections List
```bash
curl $API_URL/collections | jq
```
**Attendu** : Tableau des collections avec `chunk_count`, `total_tokens`

---

## 📄 Documents

### 3. Upload Document
```bash
curl -X POST $API_URL/upload \
  -F "file=@/path/to/document.pdf" | jq
```
**Attendu** : `success: true`, `total_chunks > 0`

### 4. Index Document
```bash
curl -X POST $API_URL/index \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/doc.pdf", "document_name": "test"}' | jq
```
**Attendu** : `success: true`, `collection_name`, `total_chunks`

---

## 🔍 RAG Query

### 5. Query (sans génération)
```bash
curl -X POST $API_URL/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "test question",
    "collection_name": "your_collection",
    "n_results": 3,
    "generate_answer": false
  }' | jq
```
**Attendu** : `chunks` array avec `score`, `text`, `metadata`

---

## 💼 Portfolio Management

### 6. Add Position
```bash
curl -X POST $API_URL/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "price": 750.00
  }' | jq
```
**Attendu** : `message: "Position ajoutée"`, `ticker: "MC.PA"`

### 7. Get Portfolio
```bash
curl $API_URL/portfolio | jq
```
**Attendu** : `total_value`, `positions` array, `total_gain_loss`

### 8. Portfolio Health
```bash
curl $API_URL/portfolio/health | jq
```
**Attendu** : `health_score: 0-100`, `grade: "A-F"`, `recommendations`

### 9. Portfolio Rebalance
```bash
curl $API_URL/portfolio/rebalance | jq
```
**Attendu** : `needs_rebalancing: true/false`, `recommendations`

### 10. Position Details
```bash
curl $API_URL/portfolio/position/MC.PA | jq
```
**Attendu** : Détails position avec `ticker`, `quantity`, `average_price`

### 11. Portfolio Context
```bash
curl $API_URL/portfolio/context | jq
```
**Attendu** : `context` string formaté pour IA

### 12. Sell Position
```bash
curl -X POST $API_URL/portfolio/sell \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "quantity": 5,
    "price": 760.00
  }' | jq
```
**Attendu** : `message: "Vente enregistrée"`

---

## 📊 Market Data

### 13. Stock Info
```bash
curl $API_URL/market/stock/MC.PA | jq
```
**Attendu** : `ticker`, `current_price`, `pe_ratio`, `dividend_yield`

### 14. Stock History
```bash
curl "$API_URL/market/history/MC.PA?period=1mo&interval=1d" | jq
```
**Attendu** : `ticker`, `data_points`, `data` array

---

## 📰 Analysis

### 15. News
```bash
curl "$API_URL/analysis/news/LVMH?days_back=7" | jq
```
**Attendu** : `company: "LVMH"`, `news_count`, `articles` array

### 16. Sentiment
```bash
curl "$API_URL/analysis/sentiment/LVMH?days_back=7" | jq
```
**Attendu** : `sentiment: "POSITIF/NÉGATIF"`, `impact_score: 0-10`, `recommendation`

### 17. Technical Analysis
```bash
curl "$API_URL/analysis/technical/MC.PA?period=6mo" | jq
```
**Attendu** : `signals`, `levels` (support/resistance), `trend`

### 18. Complete Analysis
```bash
curl "$API_URL/analysis/complete/MC.PA?company_name=LVMH" | jq
```
**Attendu** : `market_data`, `news_sentiment`, `technical_analysis`

---

## 🤖 CrewAI (Avancé)

### 19. Financial Analysis
```bash
curl -X POST $API_URL/analyze/financial-report \
  -H "Content-Type: application/json" \
  -d '{
    "companies": ["LVMH"],
    "collections": ["lvmh_2023"],
    "portfolio": null
  }' | jq
```
**Attendu** : `report` (texte long), `processing_time`

⏱️ **Durée** : 3-5 minutes

### 20. Portfolio Building
```bash
curl -X POST $API_URL/build-portfolio \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 10000,
    "risk_profile": "balanced",
    "min_companies": 5,
    "max_companies": 10
  }' | jq
```
**Attendu** : `action_plan` (texte long), `budget`, `processing_time`

⏱️ **Durée** : 5-10 minutes

---

## 🧪 Script de Test Complet (Python)

```python
#!/usr/bin/env python3
"""Test rapide de toutes les fonctionnalités"""

import requests
import time
from typing import Dict, Any

API_URL = "http://localhost:8000"

def test_endpoint(name: str, method: str, endpoint: str, data: Dict = None) -> bool:
    """Teste un endpoint"""
    start = time.time()

    try:
        if method == "GET":
            response = requests.get(f"{API_URL}{endpoint}", timeout=10)
        elif method == "POST":
            response = requests.post(f"{API_URL}{endpoint}", json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(f"{API_URL}{endpoint}", timeout=10)

        elapsed = time.time() - start

        if response.status_code in [200, 201]:
            print(f"✅ {name:40} ({elapsed:.2f}s)")
            return True
        else:
            print(f"❌ {name:40} ({response.status_code})")
            return False

    except Exception as e:
        print(f"❌ {name:40} ({str(e)})")
        return False

def main():
    """Lance tous les tests"""
    print("\n🧪 TEST DE TOUTES LES FONCTIONNALITÉS\n")
    print("=" * 70)

    results = []

    # Health & System
    print("\n🏥 HEALTH & SYSTEM")
    results.append(test_endpoint("Health Check", "GET", "/health"))
    results.append(test_endpoint("Collections List", "GET", "/collections"))

    # Portfolio
    print("\n💼 PORTFOLIO")
    results.append(test_endpoint(
        "Add Position",
        "POST",
        "/portfolio/add",
        {"ticker": "MC.PA", "company_name": "LVMH", "quantity": 1, "price": 750}
    ))
    results.append(test_endpoint("Get Portfolio", "GET", "/portfolio"))
    results.append(test_endpoint("Portfolio Health", "GET", "/portfolio/health"))
    results.append(test_endpoint("Portfolio Context", "GET", "/portfolio/context"))
    results.append(test_endpoint("Position Details", "GET", "/portfolio/position/MC.PA"))

    # Market Data
    print("\n📊 MARKET DATA")
    results.append(test_endpoint("Stock Info", "GET", "/market/stock/MC.PA"))
    results.append(test_endpoint("Stock History", "GET", "/market/history/MC.PA?period=1mo"))

    # Analysis
    print("\n📰 ANALYSIS")
    results.append(test_endpoint("News", "GET", "/analysis/news/LVMH?days_back=7"))
    results.append(test_endpoint("Sentiment", "GET", "/analysis/sentiment/LVMH"))
    results.append(test_endpoint("Technical", "GET", "/analysis/technical/MC.PA"))
    results.append(test_endpoint("Complete", "GET", "/analysis/complete/MC.PA?company_name=LVMH"))

    # Résumé
    print("\n" + "=" * 70)
    success = sum(results)
    total = len(results)
    print(f"\n📊 RÉSULTATS: {success}/{total} tests réussis ({success/total*100:.0f}%)")

    if success == total:
        print("✅ TOUS LES TESTS SONT PASSÉS !")
    else:
        print(f"⚠️  {total - success} test(s) ont échoué")

    print()

if __name__ == "__main__":
    main()
```

**Utilisation** :
```bash
python test_all_endpoints.py
```

---

## 🐛 Debugging Rapide

### Si un endpoint ne répond pas :

1. **Vérifier l'API**
   ```bash
   curl $API_URL/health
   ```

2. **Vérifier les logs**
   ```bash
   # Voir les logs de l'API (terminal où uvicorn tourne)
   ```

3. **Tester manuellement**
   ```bash
   # Ouvrir http://localhost:8000/docs dans navigateur
   ```

### Codes d'erreur courants :

| Code | Signification | Solution |
|------|---------------|----------|
| 404 | Not Found | Vérifier l'URL et les paramètres |
| 422 | Validation Error | Vérifier le format du JSON |
| 500 | Server Error | Consulter les logs API |
| 503 | Service Unavailable | Vérifier Ollama/ChromaDB |

---

## ✅ Checklist de Test Complet

Avant de déployer en production, vérifier :

- [ ] Health Check fonctionne
- [ ] Au moins 1 collection existe
- [ ] Query RAG fonctionne
- [ ] Portfolio Add/Get fonctionnent
- [ ] Market data fonctionne
- [ ] Analyses (news, sentiment, technical) fonctionnent
- [ ] Ollama est disponible (si génération de réponses)
- [ ] Toutes les clés API sont configurées (.env)
- [ ] Logs ne montrent pas d'erreurs critiques

---

## 📝 Notes

- Les tests CrewAI (19-20) prennent 5-10 minutes
- Certains tests nécessitent des données (collections, positions)
- Adapter les chemins de fichiers selon votre environnement
- Tester d'abord sans Ollama (generate_answer=false)

---

**Guide créé le** : Janvier 2025
**Dernière mise à jour** : Janvier 2025
**Pour** : API RAG System v1.0.0
