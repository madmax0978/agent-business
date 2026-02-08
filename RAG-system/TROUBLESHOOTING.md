# 🔧 Guide de Dépannage - Agent PEA

Guide complet pour résoudre les problèmes courants lors du déploiement et de l'utilisation.

---

## 📋 Table des Matières

1. [Container Unhealthy](#container-unhealthy)
2. [No Space Left on Device](#no-space-left-on-device)
3. [Telegram Bot Restarting](#telegram-bot-restarting)
4. [Erreurs Python/Imports](#erreurs-pythonimports)
5. [Problèmes ML/TensorFlow](#problèmes-mltensorflow)
6. [Commandes de Diagnostic](#commandes-de-diagnostic)

---

## 🚨 Container Unhealthy

### Symptôme
```
ERROR: for scheduler  Container "xxx" is unhealthy.
ERROR: for telegram-bot  Container "xxx" is unhealthy.
```

### Diagnostic

```bash
# 1. Voir les logs de l'API
docker logs --tail 100 agent-pea-api

# 2. Vérifier le statut
docker-compose ps

# 3. Inspecter le healthcheck
docker inspect agent-pea-api | grep -A 20 Health
```

### Solutions

#### Solution 1: Timing du healthcheck
L'API prend du temps à démarrer (TensorFlow/PyTorch).

**Fix**: Le `docker-compose.yml` est configuré avec `start_period: 120s`. Attendre 2 minutes.

#### Solution 2: Port déjà utilisé
```bash
# Vérifier si port 8000 est utilisé
sudo lsof -i :8000

# Tuer le processus
sudo kill -9 <PID>
```

#### Solution 3: Variables d'environnement
```bash
# Vérifier que .env existe
ls -la .env

# Vérifier les clés nécessaires
cat .env | grep -E "ANTHROPIC|OPENAI|TELEGRAM"
```

#### Solution 4: Rebuild complet
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

---

## 💾 No Space Left on Device

### Symptôme
```
ERROR: failed to solve: write /usr/local/lib/.../torch/lib/libtorch_cuda.so:
no space left on device
```

### Cause
PyTorch CUDA (~4GB) + TensorFlow GPU (~2GB) = ~6GB requis. Le VPS manque d'espace.

### Solution

#### Étape 1: Diagnostic
```bash
# Voir l'espace disque disponible
df -h

# Voir l'espace utilisé par Docker
docker system df
```

#### Étape 2: Nettoyer Docker
```bash
# Arrêter tous les containers
docker-compose down

# Nettoyer TOUT Docker (images, containers, volumes, cache)
docker system prune -a --volumes -f
docker builder prune -a -f

# Vérifier l'espace récupéré
df -h
```

**Tu devrais récupérer plusieurs GB d'espace.**

#### Étape 3: Vérifier requirements.txt
Le projet utilise **CPU-only versions** pour économiser de l'espace:

```bash
grep -A 3 "PyTorch CPU-only" requirements.txt
```

Doit afficher:
```
# PyTorch CPU-only (léger pour VPS sans GPU)
--extra-index-url https://download.pytorch.org/whl/cpu
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0
```

Et:
```bash
grep "tensorflow-cpu" requirements.txt
```

Doit afficher:
```
tensorflow-cpu>=2.13.0
```

#### Étape 4: Rebuild
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Économie d'Espace

| Package | Version GPU | Version CPU | Économie |
|---------|-------------|-------------|----------|
| PyTorch | ~4GB | ~200MB | 95% |
| TensorFlow | ~2GB | ~400MB | 80% |
| **Total ML** | **~6GB** | **~600MB** | **90%** |

### Si Toujours Problème d'Espace

#### Option 1: Augmenter l'espace VPS
Chez ton hébergeur, augmente la taille du disque (recommandé: 20-30GB minimum).

#### Option 2: Nettoyer le système Ubuntu
```bash
# Nettoyer les paquets inutilisés
sudo apt autoremove -y
sudo apt clean

# Nettoyer les logs
sudo journalctl --vacuum-time=7d

# Nettoyer les fichiers temporaires
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# Vérifier l'espace
df -h
```

---

## 🤖 Telegram Bot Restarting

### Symptôme
```bash
docker-compose ps
# Affiche: agent-pea-telegram-bot  Restarting
```

### Diagnostic
```bash
docker logs --tail 50 agent-pea-telegram-bot
```

### Erreur 1: Token manquant ou invalide

**Erreur:**
```
telegram.error.InvalidToken: The token `xxx` was rejected
```

**Solution:**

1. **Créer/Récupérer un token valide** via [@BotFather](https://t.me/BotFather):
   ```
   /newbot
   # Suivre les instructions
   # Copier le token donné
   ```

2. **Tester le token**:
   ```bash
   curl https://api.telegram.org/bot<TON_TOKEN>/getMe
   ```

   Doit retourner `{"ok": true, ...}`

3. **Mettre à jour .env**:
   ```bash
   nano .env
   # Modifier: TELEGRAM_BOT_TOKEN=ton_nouveau_token
   ```

4. **Redémarrer**:
   ```bash
   docker-compose restart telegram-bot
   ```

### Erreur 2: CHAT_ID manquant

**Erreur:**
```
TypeError: None is not a valid value for chat_id
```

**Solution:**

1. **Obtenir ton ID** via [@userinfobot](https://t.me/userinfobot)
   - Il te donne ton ID: `123456789`

2. **Ajouter dans .env**:
   ```bash
   TELEGRAM_CHAT_ID=123456789
   TELEGRAM_AUTHORIZED_USER_IDS=123456789
   ```

3. **Redémarrer**:
   ```bash
   docker-compose restart telegram-bot
   ```

### Erreur 3: Module manquant (apscheduler pour scheduler)

**Erreur:**
```
ModuleNotFoundError: No module named 'apscheduler'
```

**Solution:**

Vérifier que `requirements.txt` contient:
```bash
grep "apscheduler" requirements.txt
```

Si absent:
```bash
echo "apscheduler>=3.10.0" >> requirements.txt
docker-compose build --no-cache
docker-compose up -d
```

---

## 🐍 Erreurs Python/Imports

### Erreur: ImportError relative import

**Symptôme:**
```
ImportError: attempted relative import beyond top-level package
```

**Cause:** Dans Docker, les imports relatifs `from ..module` ne fonctionnent pas.

**Solution:** Utiliser des imports absolus.

**Exemple:**
```python
# ❌ MAUVAIS (ne fonctionne pas dans Docker)
from ..auth import get_current_user
from ..services.data_fetcher import DataFetcher

# ✅ BON (fonctionne dans Docker)
from auth import get_current_user
from services.yahoo_finance_service import YahooFinanceService
```

### Erreur: ModuleNotFoundError

**Symptôme:**
```
ModuleNotFoundError: No module named 'xxx'
```

**Solutions:**

1. **Vérifier requirements.txt** contient le module
2. **Rebuild sans cache**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

---

## 🧠 Problèmes ML/TensorFlow

### Erreur: Keras 3 incompatible

**Symptôme:**
```
ValueError: Your currently installed version of Keras is Keras 3,
but this is not yet supported in Transformers.
Please install the backwards-compatible tf-keras package.
```

**Solution:**

Vérifier que `requirements.txt` contient:
```bash
grep "tf-keras" requirements.txt
```

Doit afficher:
```
tf-keras>=2.13.0
```

Si absent, rebuild:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Performances lentes ML

**Symptôme:** Prédictions ML très lentes

**Cause:** Versions CPU de PyTorch/TensorFlow (normal sur VPS sans GPU)

**Impact:**
- ✅ Prédictions: Quasi identique (< 2s pour 30 jours)
- ✅ Backtesting: Aucun impact
- ⚠️ Entraînement ML: 2-3x plus lent (5-10 min au lieu de 2-5 min)

**Pour un VPS de production sans GPU, CPU-only est optimal.**

---

## 🔍 Commandes de Diagnostic

### Diagnostic Complet

```bash
#!/bin/bash
echo "=== DIAGNOSTIC COMPLET ==="
echo ""
echo "1. Statut containers:"
docker-compose ps
echo ""
echo "2. Logs API (dernières 50 lignes):"
docker logs --tail 50 agent-pea-api
echo ""
echo "3. Healthcheck status:"
docker inspect agent-pea-api | grep -A 10 Health
echo ""
echo "4. Port 8000:"
sudo lsof -i :8000
echo ""
echo "5. Espace disque:"
df -h
echo ""
echo "6. Variables env (sans secrets):"
cat .env | grep -v "KEY" | grep -v "TOKEN" | head -n 20
echo ""
```

Copie ce script dans `diagnostic.sh`, rends-le exécutable avec `chmod +x diagnostic.sh`, puis lance `./diagnostic.sh`.

### Logs des Containers

```bash
# API
docker logs --tail 100 agent-pea-api

# Bot Telegram
docker logs --tail 100 agent-pea-telegram-bot

# Scheduler
docker logs --tail 100 agent-pea-scheduler

# Suivre en temps réel
docker logs -f agent-pea-api
```

### État du Système

```bash
# Statut Docker
docker-compose ps

# Espace disque
df -h

# Utilisation Docker
docker system df

# Processus écoutant sur port 8000
sudo lsof -i :8000

# Variables d'environnement (masquer les secrets)
cat .env | grep -v "KEY" | grep -v "TOKEN"
```

### Reset Complet

Si rien ne fonctionne:

```bash
# 1. Tout arrêter
docker-compose down -v

# 2. Nettoyer Docker
docker system prune -a -f
docker builder prune -a -f

# 3. Pull les dernières modifications
git pull origin main

# 4. Rebuild from scratch
docker-compose build --no-cache

# 5. Démarrer
docker-compose up -d

# 6. Surveiller les logs
docker logs -f agent-pea-api
```

---

## 📞 Que faire si bloqué?

### Informations à collecter

```bash
# 1. Logs API
docker logs --tail 100 agent-pea-api > api_logs.txt

# 2. Statut containers
docker-compose ps > containers_status.txt

# 3. Diagnostic système
df -h > disk_space.txt
docker system df >> disk_space.txt

# 4. Variables env (MASQUER LES SECRETS!)
cat .env | grep -v "KEY" | grep -v "TOKEN" > env_check.txt
```

### Checklist de Vérification

- [ ] `docker logs agent-pea-api` ne montre pas d'erreur Python
- [ ] `docker logs agent-pea-api` montre "Application startup complete"
- [ ] `curl http://localhost:8000/health` retourne `{"status":"healthy"}`
- [ ] `.env` existe et contient les variables nécessaires
- [ ] Port 8000 n'est pas déjà utilisé (`lsof -i :8000`)
- [ ] Espace disque > 5GB disponible (`df -h`)
- [ ] Tous les containers sont "Up" (`docker-compose ps`)
- [ ] `requirements.txt` contient `tf-keras>=2.13.0`
- [ ] `requirements.txt` contient `apscheduler>=3.10.0`

---

## 💡 Conseils de Maintenance

### Mises à jour régulières

```bash
# Toutes les semaines
cd ~/agent-business/RAG-system
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

### Nettoyage périodique

```bash
# Tous les mois
docker system prune -a -f
docker builder prune -a -f
```

### Surveillance

```bash
# Vérifier l'espace disque
df -h

# Vérifier l'utilisation Docker
docker system df

# Vérifier les logs pour erreurs
docker logs --tail 100 agent-pea-api | grep -i error
```

---

**💡 Dans 90% des cas, le problème est visible dans `docker logs agent-pea-api`**

**Commence toujours par là!**
