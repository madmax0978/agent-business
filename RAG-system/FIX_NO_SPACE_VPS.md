# 🔧 Fix: "No Space Left on Device" sur VPS

## 🚨 Problème

```
ERROR: failed to solve: write /usr/local/lib/python3.12/site-packages/torch/lib/libtorch_cuda.so:
no space left on device
```

**Cause**: PyTorch avec CUDA (~4GB) + TensorFlow GPU (~2GB) = ~6GB d'espace requis. Ton VPS manque d'espace.

**Solution**: Utiliser les versions CPU-only (~600MB total) car le VPS n'a pas de GPU.

---

## ✅ Solution Complète (sur le VPS)

### Étape 1: Diagnostic

```bash
# Voir l'espace disque disponible
df -h

# Voir l'espace utilisé par Docker
docker system df
```

### Étape 2: Nettoyer Docker

```bash
# Arrêter tous les containers
docker-compose down

# Nettoyer TOUT Docker (images, containers, volumes, cache)
docker system prune -a --volumes -f

# Nettoyer le cache de build
docker builder prune -a -f

# Vérifier l'espace récupéré
df -h
```

**Tu devrais récupérer plusieurs GB d'espace.**

### Étape 3: Récupérer les changements GitHub

```bash
cd ~/agent-business/RAG-system

# Pull la nouvelle version avec PyTorch CPU-only
git pull origin main
```

**Changements appliqués**:
- Ajout `--extra-index-url https://download.pytorch.org/whl/cpu` → Force installation CPU
- `torch>=2.0.0` depuis l'index CPU (4GB → 200MB)
- `tensorflow>=2.13.0` → `tensorflow-cpu>=2.13.0` (2GB → 400MB)
- Économie totale: **~5.5GB → ~600MB**

### Étape 4: Rebuild avec la nouvelle config

```bash
# Rebuild sans cache pour forcer l'utilisation des nouvelles dépendances
docker-compose build --no-cache

# Démarrer
docker-compose up -d

# Vérifier les logs
docker logs -f agent-pea-api
```

**Tu devrais voir**:
```
Application startup complete
Uvicorn running on http://0.0.0.0:8000
```

---

## 🎯 Vérification Post-Installation

```bash
# 1. Vérifier que l'API fonctionne
curl http://localhost:8000/health

# 2. Vérifier PyTorch CPU
docker exec -it agent-pea-api python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
# Devrait afficher: CUDA available: False (c'est normal, on utilise CPU)

# 3. Vérifier TensorFlow CPU
docker exec -it agent-pea-api python -c "import tensorflow as tf; print(f'TensorFlow: {tf.__version__}'); print(f'GPU devices: {len(tf.config.list_physical_devices(\"GPU\"))}')"
# Devrait afficher: GPU devices: 0 (c'est normal, on utilise CPU)

# 4. Vérifier l'espace disque restant
df -h
```

---

## 🚀 Performance: CPU vs GPU

**Impact sur les performances ML:**
- ✅ **Prédictions**: Quasi identique (< 2s pour 30 jours)
- ✅ **Backtesting**: Aucun impact (n'utilise pas GPU)
- ⚠️ **Entraînement ML**: 2-3x plus lent (5-10 min au lieu de 2-5 min)

**Pour un VPS de production sans GPU, CPU-only est le choix optimal:**
- Économie d'espace: 5.5GB → 600MB
- Prédictions rapides (modèles pré-entraînés)
- Pas besoin de CUDA pour l'inférence

---

## 🔥 Si Toujours "No Space"

### Option 1: Augmenter l'espace VPS

Chez ton hébergeur, augmente la taille du disque (recommandé: 20-30GB minimum).

### Option 2: Nettoyer le système Ubuntu

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

### Option 3: Désactiver temporairement le ML (si vraiment critique)

Si tu veux juste faire tourner l'API sans ML pour l'instant:

```bash
# Éditer docker-compose.yml
nano docker-compose.yml

# Commenter les variables ML (lignes avec ANTHROPIC_API_KEY, etc.)
# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## 📊 Comparaison Espace Requis

| Package | Version GPU | Version CPU | Économie |
|---------|-------------|-------------|----------|
| PyTorch | ~4GB | ~200MB | 95% |
| TensorFlow | ~2GB | ~400MB | 80% |
| **Total ML** | **~6GB** | **~600MB** | **90%** |

---

## ✅ Checklist Finale

- [ ] `docker system prune -a --volumes -f` exécuté
- [ ] `git pull` effectué
- [ ] `docker-compose build --no-cache` terminé sans erreur
- [ ] `docker-compose up -d` démarré
- [ ] `curl http://localhost:8000/health` retourne `{"status": "healthy"}`
- [ ] `df -h` montre au moins 5GB disponibles

---

**🎉 Une fois ces étapes terminées, ton API devrait tourner sans problème d'espace !**

**Support**: Si toujours un problème, vérifie avec `df -h` combien d'espace total tu as sur ton VPS.
