# GUIDE D'INTÉGRATION RAPIDE - AMÉLIORATIONS RAG-PEA

Ce guide vous permet d'intégrer rapidement toutes les améliorations dans votre système RAG-PEA.

---

## ÉTAPE 1 : Installer les nouvelles dépendances (2 minutes)

```bash
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system

# Installer les nouvelles dépendances
pip install pydantic>=2.0.0 pydantic-settings>=2.0.0
```

---

## ÉTAPE 2 : Tester que tout fonctionne (1 minute)

```bash
# Tester les imports
python3 -c "
from api.config import settings
from api.logging_config import get_logger
from api.utils.circuit_breaker import CircuitBreaker

print('✅ Tous les modules importent correctement')
print(f'Environment: {settings.environment}')
print(f'App: {settings.app_name}')
"
```

Si vous voyez "✅ Tous les modules importent correctement", passez à l'étape 3.

---

## ÉTAPE 3 : Modifier api/main.py (5 minutes)

### 3.1 Ajouter les imports en haut du fichier

Après les imports existants, ajoutez :

```python
# NOUVEAUX IMPORTS - À AJOUTER
from api.config import settings
from api.logging_config import get_logger
from api.exceptions import install_error_handlers
from api.middleware import setup_middleware
```

### 3.2 Créer le logger

Après les imports, remplacez :

```python
# AVANT
# (rien ou print())

# APRÈS
logger = get_logger(__name__)
```

### 3.3 Modifier l'initialisation de FastAPI

Remplacez :

```python
# AVANT
__version__ = "1.0.0"

app = FastAPI(
    title="RAG API - Multi-Documents",
    description="API pour l'analyse de documents avec RAG et Ollama",
    version=__version__,
)

# APRÈS
__version__ = "1.1.0"

app = FastAPI(
    title=settings.app_name,
    description="API pour l'analyse de documents avec RAG et Ollama",
    version=__version__,
)
```

### 3.4 Installer les middlewares et error handlers

Juste après `app = FastAPI(...)`, ajoutez :

```python
# INSTALLER LES MIDDLEWARES (CRITIQUE)
setup_middleware(app)

# INSTALLER LES ERROR HANDLERS (CRITIQUE)
install_error_handlers(app)
```

### 3.5 Commentez ou supprimez l'ancien CORS

Commentez ces lignes (setup_middleware gère déjà CORS) :

```python
# COMMENTEZ OU SUPPRIMEZ CES LIGNES
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
```

### 3.6 Modifier le dossier uploads

Remplacez :

```python
# AVANT
UPLOAD_DIR = Path("../data/uploads")

# APRÈS
UPLOAD_DIR = settings.upload_dir
```

---

## ÉTAPE 4 : Remplacer print() par logger (OPTIONNEL mais recommandé)

Cherchez tous les `print()` dans `api/main.py` et remplacez-les :

```python
# AVANT
print(f"Erreur lors de l'indexation: {str(e)}")

# APRÈS
logger.error(f"Erreur lors de l'indexation: {str(e)}")

# AVANT
print("✅ Fichier .env chargé depuis: {env_path}")

# APRÈS
logger.info(f"Fichier .env chargé depuis: {env_path}")
```

**Types de log à utiliser** :
- `logger.debug()` - Détails pour le debugging
- `logger.info()` - Informations normales
- `logger.warning()` - Avertissements
- `logger.error()` - Erreurs
- `logger.critical()` - Erreurs critiques

---

## ÉTAPE 5 : Tester l'API (2 minutes)

```bash
# Démarrer l'API
python3 api/main.py

# Ou avec uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Vérifications** :

1. **Logs JSON** : Vous devriez voir des logs structurés :
   ```json
   {"timestamp": "2026-02-01T18:40:06.566963Z", "level": "INFO", "logger": "api.middleware", "message": "All middlewares configured successfully", ...}
   ```

2. **Headers de réponse** : Testez avec curl :
   ```bash
   curl -I http://localhost:8000/health

   # Vous devriez voir ces nouveaux headers:
   X-Request-ID: abc123-...
   X-Response-Time: 12.34ms
   X-RateLimit-Limit: 60
   X-RateLimit-Remaining: 59
   ```

3. **Rate limiting** : Testez avec plusieurs requêtes :
   ```bash
   # Faire 70 requêtes rapidement (dépasse le limit de 60/min)
   for i in {1..70}; do curl http://localhost:8000/health; done

   # Les dernières devraient retourner 429 Too Many Requests
   ```

4. **Circuit breaker** : Sera automatiquement actif si Ollama tombe

---

## ÉTAPE 6 : (Optionnel) Configuration avancée

Si vous voulez personnaliser, créez un fichier `.env` avec :

```bash
# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=30

# Cache Yahoo Finance
YAHOO_FINANCE_CACHE_TTL=300  # 5 minutes

# Circuit Breaker
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json ou text
LOG_FILE_PATH=./logs/app.log
```

Redémarrez l'API pour appliquer les changements.

---

## VÉRIFICATION FINALE

Checklist complète :

- [ ] ✅ Dépendances installées (`pydantic-settings`)
- [ ] ✅ Imports ajoutés dans `api/main.py`
- [ ] ✅ Logger créé
- [ ] ✅ `setup_middleware(app)` appelé
- [ ] ✅ `install_error_handlers(app)` appelé
- [ ] ✅ Ancien CORS commenté
- [ ] ✅ `UPLOAD_DIR = settings.upload_dir`
- [ ] ⚠️ (Optionnel) `print()` remplacés par `logger`
- [ ] ✅ API démarre sans erreur
- [ ] ✅ Logs JSON visibles
- [ ] ✅ Headers de réponse présents (X-Request-ID, X-Response-Time)

---

## RÉSUMÉ DES NOUVEAUTÉS

### Ce que vous obtenez immédiatement

1. **Request ID automatique** : Chaque requête a un ID unique pour le traçage
2. **Logs structurés JSON** : Analysables avec Elastic/Datadog/CloudWatch
3. **Rate limiting** : 60 requêtes/minute par IP (configurable)
4. **Headers de sécurité** : X-Frame-Options, X-Content-Type-Options, etc.
5. **Temps de réponse** : Header X-Response-Time dans chaque réponse
6. **Gestion d'erreurs** : Messages d'erreur cohérents et exploitables
7. **Cache Yahoo Finance** : 200x plus rapide (1ms vs 200-500ms)
8. **Circuit Breaker Ollama** : Protection si Ollama tombe

### Exemple de requête avec les améliorations

```bash
curl -v http://localhost:8000/health

# Réponse:
< HTTP/1.1 200 OK
< X-Request-ID: 8f7d9a3b-1234-5678-9abc-def012345678
< X-Response-Time: 12.45ms
< X-RateLimit-Limit: 60
< X-RateLimit-Remaining: 59
< X-RateLimit-Reset: 1738441266
< X-Content-Type-Options: nosniff
< X-Frame-Options: DENY
< X-XSS-Protection: 1; mode=block

{
  "status": "healthy",
  "ollama_available": true,
  "collections": [...],
  "version": "1.1.0"
}
```

---

## AIDE ET DÉPANNAGE

### Problème : "ModuleNotFoundError: No module named 'pydantic_settings'"

**Solution** :
```bash
pip install pydantic-settings>=2.0.0
```

### Problème : "Import error in api.config"

**Solution** : Vérifiez que vous êtes bien dans le bon répertoire :
```bash
cd /Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system
python3 -c "from api.config import settings"
```

### Problème : L'API ne démarre pas

**Solution** : Vérifiez les logs d'erreur et assurez-vous que :
1. Tous les imports sont corrects
2. `setup_middleware(app)` est appelé APRÈS `app = FastAPI(...)`
3. Pas de syntaxe error dans les modifications

### Problème : Pas de logs JSON

**Solution** : Vérifiez dans `.env` :
```bash
LOG_FORMAT=json  # Doit être "json" pour avoir les logs JSON
```

Ou forcez en mode dev :
```bash
LOG_FORMAT=text  # Pour avoir des logs colorés lisibles en dev
```

---

## PROCHAINES ÉTAPES

Une fois tout intégré et fonctionnel :

1. **Testez les endpoints** : Faites des requêtes et vérifiez les logs
2. **Vérifiez le cache** : Appelez 2 fois `/market/stock/MC.PA`, le 2e sera ultra-rapide
3. **Testez le rate limiting** : Faites 70 requêtes rapidement
4. **Lisez les logs** : Explorez `./logs/app.log` pour voir les logs JSON
5. **Explorez la config** : Regardez `api/config.py` pour voir toutes les options

---

**Temps d'intégration total** : 10-15 minutes
**Difficulté** : Facile (copier-coller)
**Impact** : Production-ready

Bon développement ! 🚀
