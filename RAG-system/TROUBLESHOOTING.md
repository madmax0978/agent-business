# Guide de Dépannage - RAG-PEA System

**Version:** 1.0.0
**Dernière mise à jour:** Février 2026

---

## Table des Matières

- [Démarrage](#démarrage)
- [RAG & Documents](#rag--documents)
- [Portfolio](#portfolio)
- [Agents CrewAI](#agents-crewai)
- [Base de Données](#base-de-données)
- [Performance](#performance)
- [Logs & Debugging](#logs--debugging)
- [Services Externes](#services-externes)

---

## Démarrage

### API ne démarre pas

**Symptôme:**
```bash
$ uvicorn api.main:app
ERROR: Could not import module "api.main"
```

**Cause:** Module path incorrect ou dépendances manquantes

**Solution:**

```bash
# 1. Vérifier que vous êtes dans le bon répertoire
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system

# 2. Vérifier structure
ls api/main.py  # Doit exister

# 3. Installer toutes dépendances
pip install -r requirements.txt

# 4. Démarrer depuis racine projet
python -m uvicorn api.main:app --reload

# OU depuis répertoire api
cd api
python -m uvicorn main:app --reload
```

**Prévention:** Toujours démarrer depuis le bon répertoire

---

### Port 8000 déjà utilisé

**Symptôme:**
```
ERROR: [Errno 48] Address already in use
```

**Solution:**

```bash
# Option 1: Trouver et tuer le processus
lsof -ti:8000 | xargs kill -9

# Option 2: Utiliser un autre port
uvicorn api.main:app --port 8001

# Option 3: Vérifier processus en cours
ps aux | grep uvicorn
kill <PID>
```

---

### Ollama non disponible

**Symptôme:**
```json
{
  "ollama_available": false
}
```

**Cause:** Serveur Ollama pas démarré

**Solution:**

```bash
# 1. Vérifier si Ollama est installé
ollama --version

# 2. Démarrer Ollama
ollama serve

# 3. Vérifier dans un autre terminal
curl http://localhost:11434/api/tags

# 4. Télécharger modèle si nécessaire
ollama pull llama3.2:3b

# 5. Tester génération
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Hello"
}'
```

**Prévention:** Ajouter Ollama au démarrage auto système

---

### Imports manquants

**Symptôme:**
```python
ModuleNotFoundError: No module named 'chromadb'
```

**Solution:**

```bash
# Installer toutes dépendances
pip install -r requirements.txt

# Si problème persiste, upgrade pip
pip install --upgrade pip

# Réinstaller package spécifique
pip install chromadb --upgrade

# Vérifier installation
python -c "import chromadb; print(chromadb.__version__)"
```

---

### Erreur de configuration

**Symptôme:**
```
pydantic.ValidationError: 1 validation error for Settings
```

**Cause:** Variable d'environnement manquante ou invalide

**Solution:**

```bash
# 1. Vérifier .env existe
ls .env

# 2. Créer depuis template si nécessaire
cp .env.example .env

# 3. Éditer .env avec vos clés
nano .env

# 4. Vérifier format clés API
# OPENAI_API_KEY=sk-...  (commence par sk-)
# ANTHROPIC_API_KEY=sk-ant-...  (commence par sk-ant-)

# 5. Tester configuration
python -c "from api.config import settings; print(settings.model_dump_safe())"
```

---

## RAG & Documents

### Collection non trouvée

**Symptôme:**
```json
{
  "error": {
    "code": "COLLECTION_NOT_FOUND",
    "message": "Collection 'lvmh_2024' not found"
  }
}
```

**Solution:**

```bash
# 1. Lister collections existantes
curl http://localhost:8000/collections | jq '.[] | .name'

# 2. Vérifier nom exact (sensible à la casse)
curl http://localhost:8000/collections/lvmh_2024

# 3. Créer collection si nécessaire
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.pdf",
    "collection_name": "lvmh_2024"
  }'
```

**Prévention:** Toujours vérifier nom collection avant query

---

### Indexation lente/échoue

**Symptôme:**
```
Indexation de 500 pages: 15 minutes
OU TimeoutError après 5 minutes
```

**Causes possibles:**
1. Document très volumineux (> 1000 pages)
2. Beaucoup de tableaux complexes
3. CPU lent
4. Pas assez de RAM

**Solutions:**

```bash
# 1. Vérifier taille document
ls -lh /path/to/document.pdf

# 2. Augmenter timeout
# Dans api/config.py:
# timeout: int = 300  # 5 min → 600  # 10 min

# 3. Indexer par lots si très gros
python batch_index_documents.py --batch-size 50

# 4. Surveiller ressources
htop  # Linux/Mac
# Vérifier CPU et RAM usage

# 5. Nettoyer ChromaDB si pleine
rm -rf data/chroma_db/*
# Puis ré-indexer
```

**Optimisations:**

```python
# Ajuster chunk size pour documents volumineux
# Dans api/rag_manager.py:
chunk_size = 1024  # au lieu de 512
overlap = 100      # au lieu de 50
```

---

### Embeddings erreur

**Symptôme:**
```
RuntimeError: Failed to generate embeddings
```

**Cause:** Modèle sentence-transformers pas téléchargé

**Solution:**

```python
# Télécharger modèle manuellement
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print('Model downloaded successfully')
"

# Vérifier emplacement
ls ~/.cache/torch/sentence_transformers/
```

---

### Réponses vides du RAG

**Symptôme:**
```json
{
  "chunks": [],
  "answer": null
}
```

**Causes:**
1. Question trop différente du contenu
2. Seuil de similarité trop élevé
3. Collection vide

**Solutions:**

```bash
# 1. Vérifier collection a des documents
curl http://localhost:8000/collections/collection_name
# Vérifier total_chunks > 0

# 2. Essayer question plus générique
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "résultats financiers",
    "collection_name": "collection_name",
    "n_results": 10
  }'

# 3. Augmenter n_results
# Plus de chunks = plus de chances de trouver pertinent

# 4. Vérifier langue document vs question
# Si document en français, question en français
```

---

## Portfolio

### Position non ajoutée

**Symptôme:**
```json
{
  "error": "Failed to add position"
}
```

**Causes possibles:**
1. Ticker invalide
2. Base de données locked
3. Paramètres invalides

**Solutions:**

```bash
# 1. Vérifier ticker existe sur Yahoo Finance
curl "http://localhost:8000/market/stock/MC.PA"
# Si 404, ticker invalide

# 2. Vérifier DB pas locked
lsof data/portfolio.db
# Si processus existe, tuer

# 3. Vérifier paramètres
curl -X POST http://localhost:8000/portfolio/add \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "MC.PA",
    "company_name": "LVMH",
    "quantity": 10,
    "price": 750.0,
    "user_id": "default_user"
  }'

# Quantity et price doivent être > 0
```

---

### Prix non mis à jour

**Symptôme:**
```json
{
  "current_price": null,
  "last_updated": "2 days ago"
}
```

**Cause:** Yahoo Finance indisponible ou ticker invalide

**Solutions:**

```bash
# 1. Forcer mise à jour
curl "http://localhost:8000/portfolio?user_id=default_user"
# Déclenche update automatique

# 2. Vérifier Yahoo Finance accessible
curl "https://finance.yahoo.com/quote/MC.PA"

# 3. Vider cache Yahoo Finance
# Redémarrer API pour reset cache

# 4. Vérifier ticker correct
# MC.PA (correct) vs MC (incorrect)
```

---

### Score santé incorrect

**Symptôme:**
```json
{
  "score": 15,
  "grade": "F (Mauvais)"
}
```

**Diagnostic:**

```bash
# Récupérer détails
curl http://localhost:8000/portfolio/health | jq

# Vérifier issues
{
  "issues": [
    "Diversification insuffisante (2 positions)",
    "Concentration excessive sur LVMH (70%)",
    "Performance très négative (-35%)"
  ]
}
```

**Explication scores:**
- **Score < 50:** Problèmes majeurs (concentration, pertes)
- **Score 50-70:** Améliorations nécessaires
- **Score 70-85:** Bon portefeuille
- **Score 85+:** Excellent portefeuille

**Action:** Suivre recommendations pour améliorer

---

## Agents CrewAI

### Timeout agents

**Symptôme:**
```
TimeoutError: Agent execution exceeded 600 seconds
```

**Causes:**
1. Agent bloqué sur web search
2. Trop de données à analyser
3. LLM lent

**Solutions:**

```bash
# 1. Augmenter timeout dans requête
curl -X POST http://localhost:8000/build-portfolio \
  -H "Content-Type: application/json" \
  --max-time 900 \  # 15 min
  -d '{...}'

# 2. Réduire scope
# Au lieu de min_companies: 10, max: 15
# Utiliser min: 5, max: 8

# 3. Vérifier logs agents
tail -f logs/app.log | grep -i "agent"

# 4. Vérifier pas de loop infini
# Dans agents/portfolio_builder_crew.py
# Ajouter max_iterations si nécessaire
```

---

### Erreur tools

**Symptôme:**
```
ToolExecutionError: Tool 'yahoo_finance_tool' execution failed
```

**Solutions:**

```python
# 1. Vérifier tool accessible
from api.agents.tools import yahoo_finance_tool

result = yahoo_finance_tool.run("MC.PA")
print(result)

# 2. Vérifier dépendances tool
# Yahoo Finance → service yahoo_finance_service.py
# Si erreur, vérifier service fonctionne:

from api.services.yahoo_finance_service import YahooFinanceService
yf = YahooFinanceService()
info = yf.get_stock_info("MC.PA")
print(info)

# 3. Ajouter error handling dans tool
# Si tool fail, agent devrait continuer
```

---

### Pas de recommandations

**Symptôme:**
```json
{
  "action_plan": "",
  "positions": []
}
```

**Causes:**
1. Critères trop restrictifs
2. Erreur agent manager
3. Pas de données collectées

**Solutions:**

```bash
# 1. Assouplir critères
{
  "budget": 10000,
  "risk_profile": "balanced",
  "sectors": null,  # Accepter tous secteurs
  "min_companies": 3,  # Minimum réduit
  "max_companies": 20  # Maximum élevé
}

# 2. Vérifier logs détaillés
# Dans api/agents/portfolio_builder_crew.py
# Mettre verbose=2 pour debug complet

# 3. Tester agents individuellement
python -c "
from api.agents.portfolio_builder_crew import create_fundamental_analyst
agent = create_fundamental_analyst([])
# Tester agent isolé
"
```

---

## Base de Données

### DB locked

**Symptôme:**
```
sqlite3.OperationalError: database is locked
```

**Cause:** Autre processus a lock sur DB

**Solutions:**

```bash
# 1. Identifier processus
lsof data/portfolio.db

# 2. Tuer processus si bloqué
kill -9 <PID>

# 3. Si persiste, corrompue → backup
cp data/portfolio.db data/portfolio.db.backup
rm data/portfolio.db

# 4. Recréer DB vide
python -c "
from api.database.portfolio_db import PortfolioDatabase
db = PortfolioDatabase()
print('Database recreated')
"

# 5. Réimporter données si backup
# (Utiliser script migration si disponible)
```

**Prévention:** N'ouvrir qu'une seule connexion DB à la fois

---

### Transactions échouent

**Symptôme:**
```
IntegrityError: UNIQUE constraint failed
```

**Cause:** Tentative d'ajouter doublon

**Solution:**

```python
# Utiliser UPDATE au lieu de INSERT si existe
from api.database.portfolio_db import PortfolioDatabase

db = PortfolioDatabase()

# ✅ Bon: add_position gère UPDATE automatique
db.add_position("MC.PA", "LVMH", 10, 700.0)

# ❌ Mauvais: INSERT direct peut échouer
cursor.execute("INSERT INTO positions ...")
```

---

### Migrations

**Symptôme:**
```
sqlite3.OperationalError: no such table: analyses
```

**Cause:** Schéma DB obsolète

**Solution:**

```bash
# 1. Vérifier version schéma
sqlite3 data/portfolio.db "SELECT * FROM schema_version;"

# 2. Appliquer migration
python scripts/migrate_db.py  # Si script existe

# 3. OU recréer DB (PERD DONNÉES!)
rm data/portfolio.db
python -c "from api.database.portfolio_db import PortfolioDatabase; PortfolioDatabase()"

# 4. Backup avant migration
cp data/portfolio.db data/portfolio_backup_$(date +%Y%m%d).db
```

---

## Performance

### API lente

**Symptôme:** Temps de réponse > 5 secondes

**Diagnostic:**

```bash
# 1. Mesurer endpoints spécifiques
time curl http://localhost:8000/portfolio

# 2. Vérifier X-Response-Time header
curl -I http://localhost:8000/portfolio
# X-Response-Time: 3245.67ms

# 3. Identifier bottleneck dans logs
grep "duration_ms" logs/app.log | sort -k4 -n | tail -20
```

**Solutions:**

```bash
# Si Yahoo Finance lent:
# → Vérifier cache fonctionne
# → Réduire nombre de positions

# Si RAG lent:
# → Réduire n_results
# → Upgrade CPU
# → Utiliser GPU pour embeddings

# Si DB lente:
# → Ajouter indexes
# → Vacuum DB
sqlite3 data/portfolio.db "VACUUM;"

# Si génération Ollama lente:
# → Utiliser modèle plus petit (llama3.2:1b)
# → Utiliser GPU
# → Réduire max_tokens
```

---

### Cache inefficace

**Symptôme:**
```
Cache hit rate: 15% (trop bas)
```

**Causes:**
1. TTL trop court
2. Cache trop petit
3. Requêtes toutes différentes

**Solutions:**

```python
# 1. Augmenter TTL dans config.py
YAHOO_FINANCE_CACHE_TTL = 600  # 10 min au lieu de 5

# 2. Augmenter taille cache
MAX_CACHE_SIZE = 256  # au lieu de 128

# 3. Vérifier stats cache
from api.services.yahoo_finance_service import YahooFinanceService
yf = YahooFinanceService()
print(yf._cache.get_stats())
# {
#   "size": 124,
#   "hits": 1523,
#   "misses": 287,
#   "hit_rate": 0.84
# }
```

---

### Mémoire haute

**Symptôme:**
```bash
$ free -m
              total        used        free
Mem:          16384       15800         584
```

**Causes:**
1. ChromaDB cache trop gros
2. Trop de collections chargées
3. Memory leak

**Solutions:**

```bash
# 1. Monitorer mémoire
ps aux | grep uvicorn
# Regarder RSS column

# 2. Limiter collections
# Supprimer collections inutilisées
curl -X DELETE http://localhost:8000/collections/old_collection

# 3. Redémarrer API périodiquement
# Ajouter dans crontab:
0 3 * * * systemctl restart ragpea-api

# 4. Vérifier memory leaks
pip install memory_profiler
python -m memory_profiler api/main.py
```

---

## Logs & Debugging

### Où trouver logs

**Emplacements:**

```bash
# Logs API
tail -f logs/app.log

# Logs système (si service systemd)
journalctl -u ragpea-api -f

# Logs erreurs Python
tail -f logs/errors.log

# Logs Ollama
tail -f ~/.ollama/logs/server.log
```

---

### Interpréter logs JSON

**Format:**

```json
{
  "timestamp": "2026-02-01T14:23:45.123456Z",
  "level": "ERROR",
  "logger": "api.services.yahoo_finance_service",
  "message": "Failed to fetch stock data",
  "request_id": "abc123-def456",
  "exception": {
    "type": "TimeoutError",
    "message": "Request timed out after 10s",
    "traceback": ["..."]
  },
  "ticker": "MC.PA",
  "duration_ms": 10234
}
```

**Filtrer logs:**

```bash
# Logs ERROR uniquement
jq 'select(.level == "ERROR")' logs/app.log

# Logs d'une requête spécifique
jq 'select(.request_id == "abc123")' logs/app.log

# Logs lents (> 1s)
jq 'select(.duration_ms > 1000)' logs/app.log | less

# Top 10 endpoints les plus lents
jq -r '.endpoint + " " + (.duration_ms | tostring)' logs/app.log \
  | sort -k2 -n | tail -10
```

---

### Niveaux de log

**Configuration:**

```bash
# Dans .env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Niveau par défaut: INFO
# DEBUG: tout (verbose)
# INFO: normal
# WARNING: avertissements seulement
# ERROR: erreurs seulement
```

**Quand utiliser:**
- **DEBUG:** Développement, investigation bugs
- **INFO:** Production normale
- **WARNING:** Production avec monitoring
- **ERROR:** Production minimale (erreurs critiques)

---

## Services Externes

### Yahoo Finance indisponible

**Symptôme:**
```
MarketDataUnavailableError: Yahoo Finance temporarily unavailable
```

**Solutions:**

```bash
# 1. Vérifier Yahoo Finance en ligne
curl https://finance.yahoo.com

# 2. Attendre et réessayer
# Souvent indispo temporairement (5-15 min)

# 3. Utiliser cache si disponible
# API retournera données cachées même si anciennes

# 4. Fallback manuel
# Si urgent, entrer prix manuellement:
curl -X POST http://localhost:8000/portfolio/add \
  -d '{"ticker":"MC.PA", "quantity":10, "price":750.0}'
```

---

### NewsAPI rate limit

**Symptôme:**
```json
{
  "error": "Rate limit exceeded (100 requests/day)"
}
```

**Solutions:**

```bash
# 1. Vérifier quota restant
curl "https://newsapi.org/v2/everything?q=LVMH&apiKey=YOUR_KEY"
# Header: X-RateLimit-Remaining

# 2. Upgrade plan NewsAPI
# Free: 100 req/jour
# Developer: 1000 req/jour ($449/mois)

# 3. Utiliser cache agressif
# Ne fetch news qu'une fois par jour
# Dans config: NEWS_CACHE_TTL = 86400  # 24h

# 4. Fallback RSS feeds
# Si NewsAPI épuisée, utiliser Google News RSS
```

---

### OpenAI/Anthropic erreur

**Symptôme:**
```
AuthenticationError: Invalid API key
```

**Solutions:**

```bash
# 1. Vérifier clé API dans .env
cat .env | grep API_KEY

# 2. Tester clé
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 3. Vérifier format
# OpenAI: sk-...
# Anthropic: sk-ant-...

# 4. Régénérer clé si nécessaire
# OpenAI: https://platform.openai.com/api-keys
# Anthropic: https://console.anthropic.com/settings/keys
```

---

## Checklist Debug Générale

Quand quelque chose ne marche pas:

1. **Vérifier logs**
   ```bash
   tail -f logs/app.log
   ```

2. **Vérifier health API**
   ```bash
   curl http://localhost:8000/health | jq
   ```

3. **Vérifier services externes**
   - Ollama: `curl http://localhost:11434/api/tags`
   - Yahoo Finance: `curl http://localhost:8000/market/stock/MC.PA`

4. **Vérifier configuration**
   ```python
   python -c "from api.config import settings; print(settings.model_dump_safe())"
   ```

5. **Redémarrer API**
   ```bash
   # Tuer processus
   lsof -ti:8000 | xargs kill -9

   # Redémarrer
   uvicorn api.main:app --reload
   ```

6. **Vérifier ressources système**
   ```bash
   htop  # CPU et RAM
   df -h # Espace disque
   ```

7. **Consulter documentation**
   - [ARCHITECTURE.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/ARCHITECTURE.md)
   - [TESTING.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/TESTING.md)
   - [README.md](/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/README.md)

---

## Support

**Problème non résolu?**

1. Chercher dans issues GitHub existantes
2. Créer nouvelle issue avec:
   - Description problème
   - Steps to reproduce
   - Logs pertinents
   - Configuration (sanitized)
   - Version système/Python

**Informations utiles à fournir:**

```bash
# Version système
uname -a

# Version Python
python --version

# Versions packages
pip list | grep -E "(fastapi|chromadb|crewai|pydantic)"

# Configuration (sanitized)
python -c "from api.config import settings; print(settings.model_dump_safe())" | jq

# Logs récents
tail -100 logs/app.log

# Health check
curl http://localhost:8000/health | jq
```

---

**Document version:** 1.0.0
**Dernière mise à jour:** Février 2026
