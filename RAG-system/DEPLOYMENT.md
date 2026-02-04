# Guide de Déploiement VPS - Agent PEA

## 🚀 Déploiement rapide sur VPS

### Prérequis

- VPS Ubuntu 22.04+ ou Debian 11+
- Docker et Docker Compose installés
- Accès SSH au VPS
- Token Telegram Bot configuré

---

## 📦 Installation sur VPS

### 1. Connexion au VPS

```bash
ssh user@your-vps-ip
```

### 2. Installer Docker

```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Installer Docker Compose
sudo apt install docker-compose -y

# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER
newgrp docker

# Vérifier l'installation
docker --version
docker-compose --version
```

### 3. Cloner le Repository

```bash
# Cloner depuis GitHub
git clone https://github.com/VOTRE_USERNAME/agent-business.git
cd agent-business/RAG-system
```

### 4. Configuration

```bash
# Copier le fichier .env
cp .env.example .env

# Éditer le fichier .env
nano .env
```

**Variables obligatoires:**

```env
# API
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=123456789

# API URL (interne Docker)
API_BASE_URL=http://api:8000
```

### 5. Démarrer tous les services

```bash
# Build et démarrer
docker-compose up -d --build

# Vérifier les logs
docker-compose logs -f
```

### 6. Vérifier que tout fonctionne

```bash
# Vérifier les containers
docker ps

# Tester l'API
curl http://localhost:8000/health

# Logs du bot Telegram
docker-compose logs telegram-bot

# Logs du scheduler
docker-compose logs scheduler
```

---

## 🔧 Commandes Utiles

### Gestion des containers

```bash
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Redémarrer
docker-compose restart

# Rebuild
docker-compose up -d --build

# Voir les logs
docker-compose logs -f [service]
```

### Logs spécifiques

```bash
# API
docker-compose logs -f api

# Bot Telegram
docker-compose logs -f telegram-bot

# Scheduler
docker-compose logs -f scheduler
```

### Accéder à un container

```bash
# Shell dans le container API
docker exec -it agent-pea-api bash

# Shell dans le bot
docker exec -it agent-pea-telegram-bot bash
```

### Mettre à jour le code

```bash
# Pull les dernières modifications
git pull origin main

# Rebuild et redémarrer
docker-compose up -d --build
```

---

## 🔒 Sécurité

### Firewall UFW

```bash
# Installer UFW
sudo apt install ufw

# Autoriser SSH
sudo ufw allow 22/tcp

# Autoriser l'API (si accès externe)
sudo ufw allow 8000/tcp

# Activer le firewall
sudo ufw enable
```

### SSL/HTTPS avec Nginx (optionnel)

```bash
# Installer Nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# Configurer Nginx
sudo nano /etc/nginx/sites-available/agent-pea

# Contenu:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Activer le site
sudo ln -s /etc/nginx/sites-available/agent-pea /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Obtenir un certificat SSL
sudo certbot --nginx -d your-domain.com
```

---

## 📊 Monitoring

### Logs en temps réel

```bash
# Tous les services
docker-compose logs -f

# Filtrer par service
docker-compose logs -f api
docker-compose logs -f telegram-bot
docker-compose logs -f scheduler
```

### Utilisation des ressources

```bash
# Stats des containers
docker stats

# Espace disque
df -h

# Mémoire
free -h
```

### Backup de la base de données

```bash
# Créer un backup
docker exec agent-pea-api tar czf /tmp/data-backup.tar.gz /app/data
docker cp agent-pea-api:/tmp/data-backup.tar.gz ./backups/

# Restaurer un backup
docker cp ./backups/data-backup.tar.gz agent-pea-api:/tmp/
docker exec agent-pea-api tar xzf /tmp/data-backup.tar.gz -C /app
```

---

## 🔄 Automatisation avec Systemd (alternative à Docker restart)

Si vous préférez gérer avec systemd:

```bash
# Créer le service
sudo nano /etc/systemd/system/agent-pea.service

# Contenu:
[Unit]
Description=Agent PEA Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/agent-business/RAG-system
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target

# Activer le service
sudo systemctl enable agent-pea
sudo systemctl start agent-pea
sudo systemctl status agent-pea
```

---

## 🐛 Troubleshooting

### Bot ne démarre pas

```bash
# Vérifier les logs
docker-compose logs telegram-bot

# Vérifier les variables d'environnement
docker exec agent-pea-telegram-bot env | grep TELEGRAM
```

### API inaccessible

```bash
# Vérifier que le container tourne
docker ps | grep api

# Tester depuis le VPS
curl http://localhost:8000/health

# Vérifier les logs
docker-compose logs api
```

### Scheduler ne s'exécute pas

```bash
# Vérifier les logs
docker-compose logs scheduler

# Vérifier l'heure du serveur
date

# Relancer le scheduler
docker-compose restart scheduler
```

### Manque de mémoire

```bash
# Vérifier la mémoire
free -h

# Augmenter la swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Rendre permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 📈 Performance

### Optimisations recommandées

1. **Utiliser un VPS avec au moins:**
   - 2 GB RAM
   - 2 vCPU
   - 20 GB stockage SSD

2. **Activer la compression:**
   - Nginx gzip
   - Docker logs rotation

3. **Monitoring:**
   - Installer `htop` pour surveiller les ressources
   - Configurer des alertes

---

## 🔐 Variables d'Environnement

### Obligatoires

```env
TELEGRAM_BOT_TOKEN=...    # Token du bot
TELEGRAM_CHAT_ID=...      # ID du chat
OPENAI_API_KEY=...        # Pour analyses IA
```

### Optionnelles

```env
ANTHROPIC_API_KEY=...     # Pour Claude AI
NEWSAPI_KEY=...           # Pour actualités
API_BASE_URL=...          # URL de l'API (défaut: http://api:8000)
```

---

## 📞 Support

En cas de problème:

1. Consulter les logs: `docker-compose logs -f`
2. Vérifier la configuration: `docker-compose config`
3. Redémarrer les services: `docker-compose restart`
4. Rebuild: `docker-compose up -d --build`

---

## ✅ Checklist de Déploiement

- [ ] VPS configuré avec Docker
- [ ] Repository cloné
- [ ] Fichier `.env` configuré
- [ ] `docker-compose up -d --build` exécuté
- [ ] API accessible (curl localhost:8000/health)
- [ ] Bot Telegram répond à /start
- [ ] Scheduler actif (logs visibles)
- [ ] Firewall configuré
- [ ] Backup planifié

**Votre Agent PEA est maintenant déployé ! 🎉**
