# Troubleshooting & Tests - RAG-PEA System

Guide de diagnostic, tests et résolution des problèmes courants.

---

## Table des Matières

1. [Tests Automatisés](#1-tests-automatisés)
2. [Diagnostic RAG](#2-diagnostic-rag)
3. [Problèmes Courants](#3-problèmes-courants)
4. [Vérification du Système](#4-vérification-du-système)
5. [Logs et Debugging](#5-logs-et-debugging)

---

## 1. Tests Automatisés

### Lancer Tous les Tests

\`\`\`bash
# Tous les tests (36 tests)
./run_tests.sh

# Tests spécifiques
pytest tests/test_portfolio.py
pytest tests/test_rag_workflow.py
pytest tests/test_financial_analysis.py
pytest tests/test_integration.py
\`\`\`

**Résultat attendu:** ✅ 36/36 tests passed

### Structure des Tests

| Fichier | Tests | Description |
|---------|-------|-------------|
| \`test_portfolio.py\` | 10 | Gestion portfolio (add, sell, PRU, health) |
| \`test_rag_workflow.py\` | 8 | RAG v2 (indexation, recherche, qualité) |
| \`test_financial_analysis.py\` | 10 | Analyse marché (données, technique, sentiment) |
| \`test_integration.py\` | 8 | Tests bout-en-bout |

### Tests RAG Spécifiques

\`\`\`bash
# Vérifier version RAG
python3 verifier_rag_version.py

# Diagnostic RAG complet
python3 diagnose_rag.py
\`\`\`

### Tester l'API Manuellement

\`\`\`bash
# 1. Santé globale
curl http://localhost:8000/health

# 2. Tester une requête RAG
curl -X POST http://localhost:8000/query \\
  -H "Content-Type: application/json" \\
  -d '{"question": "chiffre affaires", "collection_name": "LVMH_Financiers_2024", "n_results": 3}'

# 3. Tester données marché
curl http://localhost:8000/market/stock/MC.PA
\`\`\`

---

## 2. Diagnostic RAG

### Vérifier la Version RAG

\`\`\`bash
python3 verifier_rag_version.py
\`\`\`

**Output attendu:**
\`\`\`
✅ Version: v2 (optimisé)
✅ Modèle: paraphrase-multilingual-mpnet-base-v2
✅ Cache activé: True
\`\`\`

### Problèmes RAG Courants

#### Problème: 0 chunks trouvés

**Solution:**
\`\`\`bash
# Supprimer collections v1 et réindexer
rm -rf data/vector_db
python3 scripts/quick_index.py
\`\`\`

#### Problème: Scores trop bas (< 0.15)

**Solutions:**
- Reformuler la question plus clairement
- Vérifier la bonne collection
- Utiliser \`filter_tables\` si recherche dans tables

#### Problème: "readonly database"

**Solution:**
\`\`\`bash
rm -rf data/vector_db
mkdir -p data/vector_db
chmod 755 data/vector_db
\`\`\`

---

## 3. Problèmes Courants

### API ne démarre pas

#### Port déjà utilisé
\`\`\`bash
lsof -ti:8000 | xargs kill -9
\`\`\`

#### Module manquant
\`\`\`bash
ls api/rag_manager_v2.py  # Vérifier existence
pip install -r requirements.txt
\`\`\`

#### Ollama pas disponible
\`\`\`bash
ollama serve  # Démarrer Ollama
curl http://localhost:11434/api/tags  # Tester
\`\`\`

### Tests Échouent

#### test_rag_search_semantic échoue

\`\`\`bash
# Réindexer avec v2
rm -rf data/vector_db
python3 scripts/quick_index.py
pytest tests/test_rag_workflow.py -v
\`\`\`

### Portfolio

#### User not found
\`\`\`bash
# Toujours fournir user_id
curl http://localhost:8000/portfolio?user_id=maxime
\`\`\`

### Analyse Marché

#### Ticker invalide
\`\`\`bash
# ✅ Format correct: MC.PA, AIR.PA, BNP.PA
# ❌ Format incorrect: MC, LVMH, BNP
\`\`\`

---

## 4. Vérification du Système

### Checklist Complète

\`\`\`bash
# 1. API
curl http://localhost:8000/health

# 2. RAG v2
python3 verifier_rag_version.py | grep "v2 (optimisé)"

# 3. Collections
curl http://localhost:8000/collections

# 4. Recherche
curl -X POST http://localhost:8000/query \\
  -H "Content-Type: application/json" \\
  -d '{"question": "test", "collection_name": "LVMH_Financiers_2024", "n_results": 1}'

# 5. Marché
curl http://localhost:8000/market/stock/MC.PA

# 6. Tests
./run_tests.sh
\`\`\`

### Benchmark Performances

\`\`\`bash
# Vitesse RAG (avec cache)
time curl -X POST http://localhost:8000/query \\
  -H "Content-Type: application/json" \\
  -d '{"question": "chiffre affaires", "collection_name": "LVMH_Financiers_2024", "n_results": 5}'

# Attendu: ~5-10ms avec cache, ~100ms sans
\`\`\`

---

## 5. Logs et Debugging

### Logs Détaillés

\`\`\`bash
cd api
uvicorn main:app --reload --log-level debug
\`\`\`

### Debug ChromaDB

\`\`\`bash
# Taille base
du -sh data/vector_db

# Nombre collections
ls -1 data/vector_db | wc -l
\`\`\`

---

## 🆘 Reset Complet (Dernier Recours)

\`\`\`bash
# ⚠️ Supprime toutes les données

# 1. Arrêter API
pkill -f uvicorn

# 2. Nettoyer ChromaDB
rm -rf data/vector_db
mkdir -p data/vector_db
chmod 755 data/vector_db

# 3. Réindexer
python3 scripts/quick_index.py

# 4. Relancer
cd api && python -m uvicorn main:app --reload

# 5. Tester
./run_tests.sh
\`\`\`

---

## 📊 Métriques de Santé

### Système Sain ✅
- API < 100ms
- RAG scores 0.4-0.6
- 36/36 tests passent
- Collections indexées
- Ollama disponible

### Système à Risque ⚠️
- API > 500ms
- RAG scores < 0.15
- Tests échouent
- Pas de collections

---

**Documentation:** README.md | GUIDE_UTILISATION.md | http://localhost:8000/docs
