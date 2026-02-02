# Health Check - `/health`

## Vue d'ensemble

Endpoint de vérification de santé de l'API qui permet de s'assurer que tous les services sont opérationnels.

## Comment ça marche

### Flux de traitement

```
Client
  │
  ▼
GET /health
  │
  ├─> Vérifie la disponibilité d'Ollama
  ├─> Liste toutes les collections ChromaDB
  └─> Retourne le statut et la version
```

### Code concerné (main.py:77-85)

```python
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        ollama_available=rag_manager.check_ollama(),
        collections=rag_manager.list_collections(),
        version=__version__,
    )
```

### Que vérifie-t-il ?

1. **Statut de l'API** : Toujours "healthy" si le endpoint répond
2. **Ollama** : Vérifie si Ollama est accessible (requis pour la génération de réponses)
3. **Collections** : Liste toutes les collections ChromaDB disponibles
4. **Version** : Retourne la version de l'API

## Fichiers impliqués

| Fichier | Rôle |
|---------|------|
| `api/main.py` | Définition de l'endpoint |
| `api/models.py` | Modèle `HealthResponse` |
| `api/rag_manager.py` | Méthodes `check_ollama()` et `list_collections()` |

## Comment bien tester

### Test 1 : Health Check basique

```bash
curl http://localhost:8000/health
```

**Résultat attendu** :
```json
{
  "status": "healthy",
  "ollama_available": true,
  "collections": [
    "airbus_financial_statements_2024",
    "lvmh_annual_report_2023"
  ],
  "version": "1.0.0"
}
```

### Test 2 : Tester avec Ollama arrêté

```bash
# Arrêter Ollama
pkill ollama

# Tester
curl http://localhost:8000/health
```

**Résultat attendu** :
```json
{
  "status": "healthy",
  "ollama_available": false,  // <-- IMPORTANT
  "collections": [...],
  "version": "1.0.0"
}
```

### Test 3 : Health check dans un script

```python
import requests

def check_api_health():
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data['status']}")
            print(f"🤖 Ollama: {'✅' if data['ollama_available'] else '❌'}")
            print(f"📚 Collections: {len(data['collections'])}")
            return True
        return False
    except:
        print("❌ API is DOWN")
        return False

check_api_health()
```

### Test 4 : Monitoring continu

```bash
# Vérifier toutes les 30 secondes
watch -n 30 'curl -s http://localhost:8000/health | jq'
```

## Comment l'améliorer

### Amélioration 1 : Vérifications de santé plus détaillées

**Problème actuel** : Le statut est toujours "healthy" même si Ollama est down

**Solution** :
```python
@app.get("/health", response_model=HealthResponse)
async def health_check():
    ollama_available = rag_manager.check_ollama()
    collections = rag_manager.list_collections()

    # Déterminer le statut réel
    if not ollama_available:
        status = "degraded"  # Fonctionnel mais dégradé
    elif len(collections) == 0:
        status = "warning"   # Pas de données
    else:
        status = "healthy"

    return HealthResponse(
        status=status,
        ollama_available=ollama_available,
        collections=collections,
        version=__version__,
    )
```

### Amélioration 2 : Vérifier ChromaDB

**Ajout** :
```python
def check_chroma_health():
    try:
        rag_manager.chroma_client.heartbeat()
        return True
    except:
        return False

@app.get("/health")
async def health_check():
    return HealthResponse(
        status="healthy",
        ollama_available=rag_manager.check_ollama(),
        chroma_available=check_chroma_health(),  # NOUVEAU
        collections=rag_manager.list_collections(),
        version=__version__,
    )
```

### Amélioration 3 : Informations de performance

**Ajout** :
```python
import psutil
import os

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "ollama_available": rag_manager.check_ollama(),
        "collections": rag_manager.list_collections(),
        "version": __version__,
        # NOUVELLES MÉTRIQUES
        "performance": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "uptime_seconds": time.time() - start_time
    }
```

### Amélioration 4 : Santé des dépendances externes

**Ajout** :
```python
@app.get("/health")
async def health_check():
    # Vérifier Yahoo Finance
    yf_available = False
    try:
        yf = YahooFinanceService()
        yf.get_stock_info("AAPL")
        yf_available = True
    except:
        pass

    # Vérifier les API keys
    apis_configured = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "newsapi": bool(os.getenv("NEWSAPI_KEY")),
        "telegram": bool(os.getenv("TELEGRAM_BOT_TOKEN"))
    }

    return {
        "status": "healthy",
        "ollama_available": rag_manager.check_ollama(),
        "yahoo_finance_available": yf_available,
        "apis_configured": apis_configured,
        "collections": rag_manager.list_collections(),
        "version": __version__,
    }
```

### Amélioration 5 : Endpoint de "liveness" et "readiness" séparés

**Pour Kubernetes/Docker** :
```python
@app.get("/health/live")
async def liveness():
    """L'application est-elle en vie ?"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    """L'application est-elle prête à servir des requêtes ?"""
    ollama = rag_manager.check_ollama()
    chroma = check_chroma_health()

    if ollama and chroma:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Not ready")
```

## Cas d'usage

### 1. Monitoring automatisé

```bash
# Script de monitoring (cron)
#!/bin/bash
HEALTH=$(curl -s http://localhost:8000/health)
STATUS=$(echo $HEALTH | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
    # Envoyer une alerte
    curl -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
      -d "chat_id=$CHAT_ID" \
      -d "text=⚠️ API Health issue: $STATUS"
fi
```

### 2. Load Balancer Health Check

Pour un load balancer (nginx, AWS ALB, etc.) :
```nginx
upstream api_servers {
    server localhost:8000 max_fails=3 fail_timeout=30s;
    server localhost:8001 max_fails=3 fail_timeout=30s;

    # Health check
    check interval=10000 rise=2 fall=3 timeout=5000 type=http;
    check_http_send "GET /health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx;
}
```

### 3. CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Wait for API to be healthy
  run: |
    for i in {1..30}; do
      if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo "API is healthy"
        exit 0
      fi
      sleep 2
    done
    echo "API failed to become healthy"
    exit 1
```

## Métriques à surveiller

| Métrique | Valeur normale | Action si anormale |
|----------|----------------|-------------------|
| `status` | "healthy" | Investiguer les logs |
| `ollama_available` | true | Lancer `ollama serve` |
| `collections` | > 0 | Indexer des documents |
| Temps de réponse | < 100ms | Vérifier les ressources |

## Debugging

### Problème : Ollama toujours "false"

**Causes possibles** :
1. Ollama n'est pas démarré
2. Ollama écoute sur un port différent
3. Problème de réseau/firewall

**Solution** :
```bash
# Vérifier qu'Ollama tourne
ps aux | grep ollama

# Tester directement
curl http://localhost:11434/api/tags

# Vérifier la configuration dans rag_manager.py
```

### Problème : Collections vide alors que documents indexés

**Causes possibles** :
1. ChromaDB pointe vers le mauvais dossier
2. Base de données corrompue

**Solution** :
```bash
# Vérifier le chemin ChromaDB
ls -la data/chroma_db/

# Tester manuellement
python -c "
import chromadb
client = chromadb.PersistentClient(path='data/chroma_db')
print(client.list_collections())
"
```

## Bonnes pratiques

1. **Appeler /health avant chaque opération critique**
   ```python
   if not check_api_health():
       raise Exception("API not healthy")
   ```

2. **Logger les changements de statut**
   ```python
   previous_status = None
   while True:
       health = requests.get("/health").json()
       if health['status'] != previous_status:
           log(f"Status changed: {previous_status} -> {health['status']}")
           previous_status = health['status']
       time.sleep(60)
   ```

3. **Dashboard de monitoring**
   - Utiliser Grafana + Prometheus
   - Créer un endpoint `/metrics` pour Prometheus
   - Visualiser la santé en temps réel

## Conclusion

Le endpoint `/health` est essentiel pour :
- ✅ Vérifier que l'API est opérationnelle
- ✅ Détecter les problèmes de dépendances
- ✅ Automatiser le monitoring
- ✅ Intégrer avec des outils DevOps

**Prochaine amélioration recommandée** : Ajouter des métriques de performance et des vérifications de dépendances externes.
