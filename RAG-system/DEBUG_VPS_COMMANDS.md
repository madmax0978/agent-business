# 🔍 Commandes de Debug VPS - Container Unhealthy

## 🚨 Erreur: "Container is unhealthy"

Exécute ces commandes dans l'ordre pour diagnostiquer:

### 1. Voir les logs de l'API (le plus important)

```bash
# Logs en temps réel
docker logs -f agent-pea-api

# Dernières 100 lignes
docker logs --tail 100 agent-pea-api

# Chercher les erreurs
docker logs agent-pea-api 2>&1 | grep -i error
```

### 2. Vérifier le statut des containers

```bash
docker-compose ps

# Ou
docker ps -a
```

### 3. Inspecter le healthcheck

```bash
# Voir les détails du healthcheck
docker inspect agent-pea-api | grep -A 20 Health
```

### 4. Tester le healthcheck manuellement

```bash
# Entrer dans le container
docker exec -it agent-pea-api bash

# Tester la commande healthcheck
curl -f http://localhost:8000/health || exit 1

# Sortir
exit
```

---

## 🔧 Solutions Courantes

### Problème 1: Port 8000 déjà utilisé

```bash
# Vérifier si port 8000 est déjà utilisé
sudo lsof -i :8000

# Ou
sudo netstat -tulpn | grep 8000

# Tuer le processus si nécessaire
sudo kill -9 <PID>
```

### Problème 2: Variables d'environnement manquantes

```bash
# Vérifier que .env existe
ls -la .env

# Voir le contenu (masquer les secrets)
cat .env | grep -v "API_KEY"
```

### Problème 3: Problème d'import Python

Les logs montrent souvent:
```
ImportError: No module named 'xxx'
ModuleNotFoundError: No module named 'yyy'
```

**Solution**:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Problème 4: Base de données ChromaDB corrompue

```bash
# Supprimer et recréer les volumes
docker-compose down -v
docker-compose up -d
```

---

## 🚀 Commandes Rapides de Résolution

### Reset Complet (si rien ne fonctionne)

```bash
# 1. Tout arrêter
docker-compose down -v

# 2. Nettoyer Docker
docker system prune -a -f
docker builder prune -a -f

# 3. Rebuild from scratch
docker-compose build --no-cache

# 4. Démarrer
docker-compose up -d

# 5. Surveiller les logs
docker logs -f agent-pea-api
```

### Redémarrer Juste l'API

```bash
docker-compose restart api
docker logs -f agent-pea-api
```

### Forcer Rebuild d'un Service

```bash
docker-compose up -d --build --force-recreate api
```

---

## 📋 Checklist de Diagnostic

Remplis cette checklist pour identifier le problème:

- [ ] `docker logs agent-pea-api` montre des erreurs Python
- [ ] `docker logs agent-pea-api` montre "Application startup complete"
- [ ] `curl http://localhost:8000/health` depuis le VPS fonctionne
- [ ] `.env` existe et contient les variables nécessaires
- [ ] Port 8000 n'est pas déjà utilisé (`lsof -i :8000`)
- [ ] Espace disque disponible (`df -h` > 5GB libre)
- [ ] Tous les containers sont "Up" (`docker-compose ps`)

---

## 🎯 Commande Magique (Debug Complet)

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
ls -la .env
echo ""
```

Copie ce script dans un fichier `debug.sh`, rends-le exécutable avec `chmod +x debug.sh`, puis lance `./debug.sh` pour avoir un diagnostic complet.

---

## 📞 Ce qu'il me faut pour t'aider

Si tu es bloqué, envoie-moi:

```bash
# 1. Logs API
docker logs --tail 100 agent-pea-api > api_logs.txt

# 2. Statut containers
docker-compose ps > containers_status.txt

# 3. Variables env (MASQUE LES SECRETS!)
cat .env | grep -v "KEY" | grep -v "TOKEN" > env_check.txt

# Envoie-moi ces 3 fichiers
```

---

**💡 Dans 90% des cas, le problème est visible dans `docker logs agent-pea-api`**

Commence par là !
