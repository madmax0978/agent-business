# Roadmap RAG-PEA - Production & Évolutions

**Version:** 1.1.0 → 2.0.0
**Date:** 2026-02-02
**Statut:** Plan de développement pour production

---

## État Actuel du Projet

### Résultats des Audits

#### Architecture: 7.2/10 ✅
- ✅ 23 endpoints FastAPI fonctionnels
- ✅ RAG avec ChromaDB + Ollama opérationnel
- ✅ 10 agents CrewAI (analyse financière + construction portfolio)
- ✅ Middleware de sécurité, logging, rate limiting
- ✅ Circuit breaker pour résilience
- ⚠️ Manque: Dependency injection, ORM, architecture en couches
- ⚠️ SQLite naïf (besoin PostgreSQL pour production)

#### Sécurité: 3.5/10 ❌ NON PRODUCTION-READY
- ❌ CRITIQUE: Aucune authentification sur les endpoints
- ❌ CRITIQUE: Vulnérabilités path traversal
- ❌ MAJEUR: CORS trop permissif (`allow_origins=["*"]`)
- ❌ MAJEUR: Dépendances non verrouillées
- ⚠️ Logs peuvent exposer des secrets

**Conclusion:** Fonctionnel en développement, mais DOIT être sécurisé avant production.

---

## Phase 1: Sécurité & Production-Ready 🔴 CRITIQUE

**Durée:** 1-2 semaines
**Priorité:** MAXIMALE
**Bloquant:** Toute mise en production

### 1.1 Authentification JWT (3-4 jours)

**Objectif:** Sécuriser tous les endpoints

**Implémentation:**

```python
# api/auth.py (à créer)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # À ajouter dans .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Appliquer sur tous les endpoints protégés
@app.post("/portfolio/add", dependencies=[Depends(get_current_user)])
async def add_position(request: PositionAddRequest):
    # ...
```

**Checklist:**
- [ ] Installer `python-jose[cryptography]` et `passlib[bcrypt]`
- [ ] Créer `api/auth.py` avec JWT
- [ ] Créer endpoint `/auth/login` pour obtenir token
- [ ] Créer endpoint `/auth/register` (si multi-utilisateurs)
- [ ] Ajouter `dependencies=[Depends(get_current_user)]` sur tous les endpoints protégés
- [ ] Tester avec Postman/curl
- [ ] Documenter dans API_REFERENCE.md

### 1.2 Sécurisation des fichiers (1-2 jours)

**Objectif:** Bloquer path traversal

**Correctif:**

```python
from pathlib import Path
import re

def sanitize_filename(filename: str) -> str:
    """Nettoie et valide le nom de fichier"""
    # Retire les caractères dangereux
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Bloque les séquences de traversée
    if '..' in filename or filename.startswith('/'):
        raise ValueError("Nom de fichier invalide")
    return filename

@app.post("/upload")
async def upload_file(file: UploadFile, user_id: str = Depends(get_current_user)):
    safe_filename = sanitize_filename(file.filename)
    file_path = UPLOAD_DIR / safe_filename

    # Vérification que le chemin reste dans UPLOAD_DIR
    if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(400, "Chemin invalide")

    # Sauvegarde sécurisée...
```

**Checklist:**
- [ ] Créer fonction `sanitize_filename()`
- [ ] Valider tous les chemins de fichiers avec `.resolve().is_relative_to()`
- [ ] Appliquer sur `/upload`, `/index/file`, `/index/directory`
- [ ] Tester avec payloads malicieux: `../../../etc/passwd`, `..\\..\\windows\\system32`

### 1.3 Configuration CORS (30 min)

**Correctif:**

```python
# api/config.py
class CORSSettings(BaseModel):
    allow_origins: list[str] = Field(
        default=["https://votre-domaine.com"],  # Domaine spécifique
        env="CORS_ALLOWED_ORIGINS"
    )
```

**Checklist:**
- [ ] Remplacer `["*"]` par votre domaine réel
- [ ] Ajouter `CORS_ALLOWED_ORIGINS` dans `.env`
- [ ] Pour dev local: `["http://localhost:3000", "http://127.0.0.1:3000"]`
- [ ] Tester avec différentes origines

### 1.4 Dépendances verrouillées (1 jour)

**Checklist:**
- [ ] Exécuter `pip freeze > requirements.lock`
- [ ] Scanner les CVEs: `pip install safety && safety check`
- [ ] Vérifier les versions obsolètes: `pip list --outdated`
- [ ] Mettre à jour si nécessaire
- [ ] Documenter les versions requises

### 1.5 Sanitisation des logs (1 jour)

**Correctif:**

```python
import re

SENSITIVE_PATTERNS = [
    (re.compile(r'("api_key"\s*:\s*")[^"]+'), r'\1***REDACTED***'),
    (re.compile(r'("password"\s*:\s*")[^"]+'), r'\1***REDACTED***'),
    (re.compile(r'(Bearer\s+)[^\s]+'), r'\1***REDACTED***'),
]

def sanitize_log_data(data: dict) -> dict:
    """Retire les données sensibles avant logging"""
    json_str = json.dumps(data)
    for pattern, replacement in SENSITIVE_PATTERNS:
        json_str = pattern.sub(replacement, json_str)
    return json.loads(json_str)
```

**Checklist:**
- [ ] Créer fonction `sanitize_log_data()`
- [ ] Appliquer dans `RequestLoggingMiddleware`
- [ ] Tester avec requêtes contenant tokens/secrets

---

## Phase 2: Déploiement VPS Hostinger

**Durée:** 2-3 semaines
**Priorité:** Haute (après Phase 1)

### 2.1 Migration Base de Données (3-4 jours)

**De:** SQLite naïf
**Vers:** PostgreSQL avec SQLAlchemy ORM

**Implémentation:**

```python
# api/database/models.py (à créer)
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    quantity = Column(Float)
    avg_price = Column(Float)
    current_price = Column(Float)
    created_at = Column(DateTime)

# api/database/session.py
from sqlalchemy.orm import Session

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/ragpea")
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dans les endpoints
@app.post("/portfolio/add")
async def add_position(
    request: PositionAddRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    position = Position(ticker=request.ticker, quantity=request.quantity, ...)
    db.add(position)
    db.commit()
    return {"status": "success"}
```

**Checklist:**
- [ ] Installer PostgreSQL sur VPS Hostinger
- [ ] Créer base de données `ragpea`
- [ ] Installer `sqlalchemy` et `psycopg2-binary`
- [ ] Créer modèles SQLAlchemy dans `api/database/models.py`
- [ ] Créer migrations avec Alembic: `alembic init migrations`
- [ ] Script de migration des données SQLite → PostgreSQL
- [ ] Tester toutes les opérations CRUD
- [ ] Supprimer `api/database/portfolio_db.py` (ancien)

### 2.2 Containerisation Docker (2-3 jours)

**Structure:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dépendances système pour PostgreSQL
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ragpea
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ragpea
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://ragpea:${DB_PASSWORD}@postgres:5432/ragpea
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

**Checklist:**
- [ ] Créer `Dockerfile`
- [ ] Créer `docker-compose.yml`
- [ ] Tester build local: `docker-compose build`
- [ ] Tester run local: `docker-compose up`
- [ ] Vérifier santé des services
- [ ] Optimiser image (multi-stage build)

### 2.3 Configuration Nginx (1 jour)

```nginx
# nginx.conf
upstream fastapi {
    server app:8000;
}

server {
    listen 80;
    server_name votre-domaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    client_max_body_size 50M;  # Pour upload de fichiers

    location / {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (si besoin)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        access_log off;
        proxy_pass http://fastapi/health;
    }
}
```

**Checklist:**
- [ ] Obtenir certificat SSL (Let's Encrypt avec `certbot`)
- [ ] Configurer Nginx avec proxy reverse
- [ ] Activer HTTPS redirect
- [ ] Tester avec `curl https://votre-domaine.com/health`

### 2.4 Déploiement VPS (2-3 jours)

**Prérequis Hostinger VPS:**
- VPS avec Ubuntu 22.04 LTS
- Minimum 4GB RAM (recommandé 8GB pour Ollama)
- 50GB SSD

**Checklist:**
- [ ] Configurer accès SSH
- [ ] Installer Docker & Docker Compose
- [ ] Cloner le repo: `git clone https://github.com/votre-repo/RAG-system.git`
- [ ] Créer `.env` avec secrets production
- [ ] Ouvrir ports: 80, 443, 8000 (firewall)
- [ ] `docker-compose up -d`
- [ ] Configurer logs: `docker-compose logs -f`
- [ ] Mettre en place backup automatique PostgreSQL
- [ ] Configurer monitoring (Prometheus + Grafana ou équivalent)

### 2.5 CI/CD Pipeline (2-3 jours)

```yaml
# .github/workflows/deploy.yml
name: Deploy to VPS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/

      - name: Build Docker image
        run: docker build -t ragpea:latest .

      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /app/RAG-system
            git pull
            docker-compose pull
            docker-compose up -d --build
            docker-compose exec app alembic upgrade head
```

**Checklist:**
- [ ] Créer workflow GitHub Actions
- [ ] Ajouter secrets dans GitHub
- [ ] Tests automatiques sur chaque commit
- [ ] Déploiement automatique si tests passent
- [ ] Rollback automatique en cas d'erreur

---

## Phase 3: Bot Telegram Intelligent

**Durée:** 2-3 semaines
**Priorité:** Haute

### 3.1 Configuration Telegram Bot (1 jour)

**Checklist:**
- [ ] Créer bot avec @BotFather
- [ ] Récupérer `TELEGRAM_BOT_TOKEN`
- [ ] Installer `python-telegram-bot`: `pip install python-telegram-bot`
- [ ] Ajouter token dans `.env`

### 3.2 Structure du Bot (3-4 jours)

```python
# api/telegram/bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

class TelegramBot:
    def __init__(self, token: str, api_base_url: str):
        self.token = token
        self.api_base_url = api_base_url
        self.app = Application.builder().token(token).build()

        # Enregistrement des commandes
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("portfolio", self.show_portfolio))
        self.app.add_handler(CommandHandler("add", self.add_position))
        self.app.add_handler(CommandHandler("sell", self.sell_position))
        self.app.add_handler(CommandHandler("analyze", self.analyze_ticker))
        self.app.add_handler(CommandHandler("build", self.build_portfolio))
        self.app.add_handler(CommandHandler("health", self.system_health))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_question))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📊 Portfolio", callback_data="portfolio")],
            [InlineKeyboardButton("📈 Analyser action", callback_data="analyze")],
            [InlineKeyboardButton("🤖 Construire portfolio", callback_data="build")],
        ]
        await update.message.reply_text(
            "👋 Bienvenue sur RAG-PEA Bot!\n\n"
            "Commandes disponibles:\n"
            "/portfolio - Voir ton portfolio\n"
            "/add TICKER QTY PRIX - Ajouter position\n"
            "/sell TICKER QTY - Vendre position\n"
            "/analyze TICKER - Analyser action\n"
            "/build MONTANT PROFIL - Construire portfolio\n"
            "/health - État du système\n\n"
            "Ou pose-moi une question directement!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def show_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Appel API
        response = await self._call_api("/portfolio/positions")

        message = "📊 *Ton Portfolio PEA*\n\n"
        total_value = 0
        for pos in response['positions']:
            value = pos['quantity'] * pos['current_price']
            total_value += value
            pnl_pct = ((pos['current_price'] - pos['avg_price']) / pos['avg_price']) * 100

            message += f"*{pos['ticker']}*\n"
            message += f"  Qté: {pos['quantity']} @ {pos['avg_price']:.2f}€\n"
            message += f"  Prix actuel: {pos['current_price']:.2f}€\n"
            message += f"  P&L: {pnl_pct:+.2f}% ({value - pos['quantity']*pos['avg_price']:+.2f}€)\n\n"

        message += f"*Total:* {total_value:.2f}€"
        await update.message.reply_text(message, parse_mode="Markdown")

    async def analyze_ticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Usage: /analyze TICKER")
            return

        ticker = context.args[0].upper()
        await update.message.reply_text(f"🔍 Analyse de {ticker} en cours...")

        # Appel API analyse complète
        response = await self._call_api(f"/analysis/complete?ticker={ticker}")

        message = f"📈 *Analyse {ticker}*\n\n"
        message += f"*Prix actuel:* {response['price']:.2f}€\n"
        message += f"*Tendance:* {response['technical']['trend']}\n"
        message += f"*RSI:* {response['technical']['rsi']:.1f}\n"
        message += f"*Signal:* {response['recommendation']['action']}\n"
        message += f"*Confiance:* {response['recommendation']['confidence']}%\n\n"
        message += f"*Analyse:*\n{response['recommendation']['reasoning']}"

        await update.message.reply_text(message, parse_mode="Markdown")

    async def handle_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        question = update.message.text
        await update.message.reply_text("🤔 Je réfléchis...")

        # Appel RAG pour répondre
        response = await self._call_api("/rag/query", method="POST", json={"query": question})

        await update.message.reply_text(
            f"💡 *Réponse:*\n\n{response['answer']}\n\n"
            f"_Sources: {', '.join(response['sources'])}_",
            parse_mode="Markdown"
        )

    async def _call_api(self, endpoint: str, method: str = "GET", **kwargs):
        # Appel HTTP vers FastAPI
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_base_url}{endpoint}"
            async with session.request(method, url, **kwargs) as resp:
                return await resp.json()

    def run(self):
        self.app.run_polling()
```

**Checklist:**
- [ ] Créer `api/telegram/bot.py`
- [ ] Implémenter commandes de base
- [ ] Tester chaque commande manuellement
- [ ] Gérer erreurs gracieusement
- [ ] Logs détaillés pour debug

### 3.3 Système d'Alertes Automatiques (4-5 jours)

```python
# api/telegram/alerts.py
from datetime import datetime
import asyncio

class AlertSystem:
    def __init__(self, bot, db_session):
        self.bot = bot
        self.db = db_session
        self.user_chat_ids = {}  # user_id -> chat_id

    async def start_monitoring(self):
        """Lance les tâches de monitoring en background"""
        asyncio.create_task(self.daily_morning_report())
        asyncio.create_task(self.monitor_positions())
        asyncio.create_task(self.weekly_performance())

    async def daily_morning_report(self):
        """Rapport quotidien avant ouverture marché (8h45)"""
        while True:
            now = datetime.now()
            if now.hour == 8 and now.minute == 45:
                for user_id, chat_id in self.user_chat_ids.items():
                    positions = await self._get_user_positions(user_id)

                    message = "🌅 *Rapport Matinal PEA*\n\n"
                    message += f"📅 {now.strftime('%d/%m/%Y')}\n\n"

                    # Résumé portfolio
                    total_value = sum(p['value'] for p in positions)
                    total_pnl = sum(p['pnl'] for p in positions)
                    message += f"💼 Valeur totale: {total_value:.2f}€\n"
                    message += f"📊 P&L global: {total_pnl:+.2f}€ ({total_pnl/total_value*100:+.2f}%)\n\n"

                    # Top performers
                    top_gainers = sorted(positions, key=lambda x: x['pnl_pct'], reverse=True)[:3]
                    message += "*🚀 Top Performers:*\n"
                    for p in top_gainers:
                        message += f"  • {p['ticker']}: {p['pnl_pct']:+.2f}%\n"

                    # Actions à surveiller
                    watchlist = await self._get_watchlist_signals(user_id)
                    if watchlist:
                        message += "\n*👀 À surveiller aujourd'hui:*\n"
                        for signal in watchlist:
                            message += f"  • {signal['ticker']}: {signal['reason']}\n"

                    await self.bot.send_message(chat_id, message, parse_mode="Markdown")

            await asyncio.sleep(60)  # Check chaque minute

    async def monitor_positions(self):
        """Surveillance temps réel des positions"""
        while True:
            for user_id, chat_id in self.user_chat_ids.items():
                positions = await self._get_user_positions(user_id)

                for pos in positions:
                    # Alerte si objectif atteint
                    if 'target_price' in pos and pos['current_price'] >= pos['target_price']:
                        await self.bot.send_message(
                            chat_id,
                            f"🎯 *OBJECTIF ATTEINT!*\n\n"
                            f"{pos['ticker']} a atteint {pos['current_price']:.2f}€\n"
                            f"Objectif: {pos['target_price']:.2f}€\n"
                            f"P&L: {pos['pnl_pct']:+.2f}%\n\n"
                            f"💡 *Recommandation:* VENDRE pour sécuriser profit",
                            parse_mode="Markdown"
                        )

                    # Alerte si stop loss
                    if 'stop_loss' in pos and pos['current_price'] <= pos['stop_loss']:
                        await self.bot.send_message(
                            chat_id,
                            f"⚠️ *STOP LOSS DÉCLENCHÉ!*\n\n"
                            f"{pos['ticker']} a chuté à {pos['current_price']:.2f}€\n"
                            f"Stop: {pos['stop_loss']:.2f}€\n"
                            f"P&L: {pos['pnl_pct']:+.2f}%\n\n"
                            f"💡 *Action:* VENDRE pour limiter la perte",
                            parse_mode="Markdown"
                        )

                    # Alerte opportunité d'achat
                    if await self._is_buy_opportunity(pos['ticker']):
                        await self.bot.send_message(
                            chat_id,
                            f"🔔 *OPPORTUNITÉ D'ACHAT*\n\n"
                            f"{pos['ticker']} montre des signaux positifs:\n"
                            f"  • RSI en zone de survente\n"
                            f"  • Support technique solide\n"
                            f"  • Sentiment positif\n\n"
                            f"Prix suggéré: {pos['suggested_buy_price']:.2f}€\n"
                            f"Objectif: {pos['target']:.2f}€ (+{pos['upside']:.1f}%)",
                            parse_mode="Markdown"
                        )

            await asyncio.sleep(300)  # Check toutes les 5 minutes

    async def weekly_performance(self):
        """Rapport hebdomadaire dimanche soir"""
        while True:
            now = datetime.now()
            if now.weekday() == 6 and now.hour == 20:  # Dimanche 20h
                for user_id, chat_id in self.user_chat_ids.items():
                    stats = await self._get_weekly_stats(user_id)

                    message = "📊 *Rapport Hebdomadaire PEA*\n\n"
                    message += f"📅 Semaine du {stats['start_date']} au {stats['end_date']}\n\n"
                    message += f"*Performance:*\n"
                    message += f"  • P&L: {stats['weekly_pnl']:+.2f}€ ({stats['weekly_pnl_pct']:+.2f}%)\n"
                    message += f"  • Meilleure position: {stats['best_performer']} ({stats['best_pnl']:+.2f}%)\n"
                    message += f"  • Pire position: {stats['worst_performer']} ({stats['worst_pnl']:+.2f}%)\n\n"
                    message += f"*Transactions:*\n"
                    message += f"  • Achats: {stats['num_buys']}\n"
                    message += f"  • Ventes: {stats['num_sells']}\n\n"
                    message += f"*Recommandations:*\n"
                    message += f"  • Rééquilibrage suggéré: {stats['rebalance_needed']}\n"
                    message += f"  • Diversification: {stats['diversification_score']}/10\n"

                    await self.bot.send_message(chat_id, message, parse_mode="Markdown")

            await asyncio.sleep(3600)  # Check chaque heure
```

**Format des Alertes:**

**Alerte Achat:**
```
🟢 SIGNAL D'ACHAT

LVMH (MC.PA)
Prix: 842.50€
Confiance: 85%

Signaux:
  ✅ RSI: 32 (survente)
  ✅ Support: 835€
  ✅ Sentiment: Positif (score 8/10)

Objectif: 920€ (+9.2%)
Stop loss: 810€ (-3.9%)

Montant suggéré: 1 500€
Quantité: 1-2 actions
```

**Alerte Vente:**
```
🔴 SIGNAL DE VENTE

TotalEnergies (TTE.PA)
Prix actuel: 68.20€
P&L: +12.5% (+2 340€)

Raisons:
  ⚠️ RSI: 78 (surachat)
  ⚠️ Résistance atteinte
  ⚠️ Sentiment en baisse

Action: VENDRE pour sécuriser profit
```

**Checklist:**
- [ ] Créer `api/telegram/alerts.py`
- [ ] Implémenter rapport matinal (8h45)
- [ ] Surveillance temps réel (5 min)
- [ ] Alertes stop-loss et take-profit
- [ ] Rapport hebdomadaire (dimanche 20h)
- [ ] Rapport mensuel avec statistiques complètes
- [ ] Système de notifications personnalisables

### 3.4 Modèle Questions/Réponses (2-3 jours)

**Format structuré pour RAG:**

```python
# api/telegram/qa_model.py

QUESTION_PATTERNS = {
    "portfolio_value": [
        "combien vaut mon portfolio",
        "quelle est la valeur",
        "combien j'ai",
    ],
    "best_performer": [
        "quelle est ma meilleure action",
        "top performer",
        "qui performe le mieux",
    ],
    "recommendation": [
        "que dois-je acheter",
        "quelle action acheter",
        "recommandation d'achat",
    ],
    "market_analysis": [
        "comment va le marché",
        "analyse du marché",
        "tendance actuelle",
    ],
}

async def classify_question(question: str) -> str:
    """Classifie la question pour orienter la réponse"""
    question_lower = question.lower()
    for category, patterns in QUESTION_PATTERNS.items():
        if any(pattern in question_lower for pattern in patterns):
            return category
    return "general"

async def generate_answer(question: str, context: dict) -> str:
    """Génère réponse structurée selon type de question"""
    category = await classify_question(question)

    if category == "portfolio_value":
        return f"💼 Ton portfolio PEA vaut actuellement *{context['total_value']:.2f}€*\n\n" \
               f"Performance globale: {context['total_pnl_pct']:+.2f}% ({context['total_pnl']:+.2f}€)"

    elif category == "recommendation":
        # Appel à l'agent de recommandation
        rec = await get_recommendation_agent(context)
        return f"💡 *Recommandation d'achat:*\n\n" \
               f"*{rec['ticker']}*\n" \
               f"Prix: {rec['price']:.2f}€\n" \
               f"Objectif: {rec['target']:.2f}€ (+{rec['upside']:.1f}%)\n\n" \
               f"*Justification:*\n{rec['reasoning']}"

    else:
        # RAG général
        return await query_rag_system(question)
```

**Checklist:**
- [ ] Créer patterns de questions courantes
- [ ] Classification automatique des questions
- [ ] Réponses structurées par catégorie
- [ ] Intégration avec RAG pour questions complexes
- [ ] Historique de conversation pour contexte

---

## Phase 4: Machine Learning & Prédictions

**Durée:** 4-6 semaines
**Priorité:** Moyenne

### 4.1 Infrastructure ML (1 semaine)

**Structure:**

```
api/ml/
├── __init__.py
├── models/
│   ├── lstm_predictor.py       # Prédiction prix LSTM
│   ├── xgboost_classifier.py   # Classification tendance
│   ├── prophet_forecaster.py   # Séries temporelles
│   └── ensemble.py             # Modèle ensemble
├── training/
│   ├── data_pipeline.py        # Pipeline données
│   ├── feature_engineering.py  # Features techniques
│   └── train.py                # Scripts d'entraînement
├── inference/
│   └── predictor.py            # Inférence temps réel
└── backtesting/
    └── engine.py               # Moteur backtest
```

**Checklist:**
- [ ] Installer PyTorch, XGBoost, Prophet
- [ ] Créer pipeline de données historiques
- [ ] Feature engineering (indicateurs techniques)
- [ ] Infrastructure d'entraînement

### 4.2 LSTM pour Prédiction de Prix (2 semaines)

**Implémentation:**

```python
# api/ml/models/lstm_predictor.py
import torch
import torch.nn as nn

class LSTMPredictor(nn.Module):
    def __init__(self, input_size=10, hidden_size=128, num_layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True, dropout=dropout
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        prediction = self.fc(lstm_out[:, -1, :])
        return prediction

# Entraînement
def train_lstm(ticker: str, lookback_days=60, forecast_days=5):
    # Récupération données historiques
    data = get_historical_data(ticker, days=365*3)

    # Feature engineering
    features = calculate_features(data)  # OHLCV + indicateurs techniques

    # Préparation sequences
    X, y = create_sequences(features, lookback=lookback_days, forecast=forecast_days)

    # Split train/val
    split = int(0.8 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    # Entraînement
    model = LSTMPredictor()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    for epoch in range(100):
        model.train()
        optimizer.zero_grad()
        predictions = model(X_train)
        loss = criterion(predictions, y_train)
        loss.backward()
        optimizer.step()

    # Sauvegarde
    torch.save(model.state_dict(), f"models/{ticker}_lstm.pt")

    return model

# Prédiction
async def predict_price(ticker: str, days_ahead=5):
    model = load_model(ticker)
    recent_data = get_recent_data(ticker, days=60)
    features = calculate_features(recent_data)

    with torch.no_grad():
        prediction = model(features)

    return {
        "ticker": ticker,
        "current_price": recent_data[-1]['close'],
        "predicted_price": prediction.item(),
        "days_ahead": days_ahead,
        "confidence": calculate_confidence(model, features),
    }
```

**Checklist:**
- [ ] Implémenter architecture LSTM
- [ ] Features: OHLCV + RSI, MACD, Bollinger, volume
- [ ] Entraînement sur 3 ans de données
- [ ] Validation walk-forward
- [ ] Endpoint `/ml/predict/{ticker}`

### 4.3 XGBoost pour Classification Tendance (1 semaine)

```python
# api/ml/models/xgboost_classifier.py
import xgboost as xgb

class TrendClassifier:
    def __init__(self):
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
        )

    def train(self, ticker: str):
        data = get_historical_data(ticker)

        # Features
        features = calculate_technical_indicators(data)

        # Labels: -1 (baisse), 0 (neutre), 1 (hausse)
        labels = classify_trends(data, threshold=0.02)

        self.model.fit(features, labels)

    async def predict(self, ticker: str):
        current_features = get_current_features(ticker)
        prediction = self.model.predict_proba(current_features)

        return {
            "trend": ["BAISSE", "NEUTRE", "HAUSSE"][prediction.argmax()],
            "confidence": prediction.max(),
            "probabilities": {
                "baisse": prediction[0][0],
                "neutre": prediction[0][1],
                "hausse": prediction[0][2],
            }
        }
```

**Checklist:**
- [ ] Features: 20+ indicateurs techniques
- [ ] Classification ternaire: baisse/neutre/hausse
- [ ] Optimisation hyperparamètres
- [ ] Validation croisée temporelle
- [ ] Endpoint `/ml/trend/{ticker}`

### 4.4 Backtesting Avancé (2 semaines)

```python
# api/ml/backtesting/engine.py
from dataclasses import dataclass
from typing import List
import pandas as pd

@dataclass
class BacktestResult:
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    trades: List[dict]

class BacktestEngine:
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []

    async def run(
        self,
        strategy: callable,
        tickers: List[str],
        start_date: str,
        end_date: str,
        walk_forward=True
    ):
        """
        Backtesting avec walk-forward optimization

        Args:
            strategy: Fonction de stratégie de trading
            tickers: Liste d'actions à trader
            start_date: Date de début
            end_date: Date de fin
            walk_forward: Si True, ré-entraîne modèles périodiquement
        """
        # Récupération données
        data = get_historical_data_multi(tickers, start_date, end_date)

        # Walk-forward: entraîne sur N jours, test sur M jours
        train_window = 252  # 1 an
        test_window = 63    # 3 mois

        for i in range(0, len(data) - train_window - test_window, test_window):
            # Période d'entraînement
            train_data = data[i:i+train_window]

            if walk_forward:
                # Ré-entraînement des modèles
                for ticker in tickers:
                    train_lstm(ticker, data=train_data[ticker])
                    train_xgboost(ticker, data=train_data[ticker])

            # Période de test
            test_data = data[i+train_window:i+train_window+test_window]

            for day in test_data:
                # Génération signaux
                signals = await strategy(day, self.positions)

                # Exécution trades
                for signal in signals:
                    self.execute_trade(signal, day)

        # Calcul métriques
        return self.calculate_metrics()

    def execute_trade(self, signal: dict, market_data: dict):
        if signal['action'] == 'BUY':
            price = market_data[signal['ticker']]['close']
            quantity = signal['quantity']
            cost = price * quantity

            if cost <= self.capital:
                self.capital -= cost
                self.positions[signal['ticker']] = {
                    'quantity': quantity,
                    'avg_price': price,
                }
                self.trades.append({
                    'date': market_data['date'],
                    'action': 'BUY',
                    'ticker': signal['ticker'],
                    'price': price,
                    'quantity': quantity,
                })

        elif signal['action'] == 'SELL':
            if signal['ticker'] in self.positions:
                pos = self.positions[signal['ticker']]
                price = market_data[signal['ticker']]['close']
                revenue = price * pos['quantity']

                self.capital += revenue
                pnl = revenue - (pos['avg_price'] * pos['quantity'])

                self.trades.append({
                    'date': market_data['date'],
                    'action': 'SELL',
                    'ticker': signal['ticker'],
                    'price': price,
                    'quantity': pos['quantity'],
                    'pnl': pnl,
                })

                del self.positions[signal['ticker']]

    def calculate_metrics(self) -> BacktestResult:
        # Portfolio final value
        final_value = self.capital + sum(
            pos['quantity'] * get_current_price(ticker)
            for ticker, pos in self.positions.items()
        )

        total_return = (final_value - self.initial_capital) / self.initial_capital

        # Calcul Sharpe ratio
        returns = pd.Series([t['pnl'] for t in self.trades if 'pnl' in t])
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)

        # Max drawdown
        cumulative = returns.cumsum()
        max_dd = (cumulative.cummax() - cumulative).max() / self.initial_capital

        # Win rate
        winning_trades = len([t for t in self.trades if t.get('pnl', 0) > 0])
        total_trades = len([t for t in self.trades if 'pnl' in t])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        return BacktestResult(
            total_return=total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            win_rate=win_rate,
            num_trades=total_trades,
            trades=self.trades,
        )

# Endpoint
@app.post("/ml/backtest")
async def run_backtest(request: BacktestRequest):
    engine = BacktestEngine(initial_capital=request.capital)

    # Stratégie ML
    async def ml_strategy(day, positions):
        signals = []
        for ticker in request.tickers:
            # Prédiction LSTM
            price_pred = await predict_price(ticker)
            # Classification XGBoost
            trend_pred = await predict_trend(ticker)

            # Logique de trading
            if trend_pred['trend'] == 'HAUSSE' and trend_pred['confidence'] > 0.7:
                if ticker not in positions:
                    signals.append({
                        'action': 'BUY',
                        'ticker': ticker,
                        'quantity': calculate_position_size(request.capital, price_pred['current_price']),
                    })

            elif trend_pred['trend'] == 'BAISSE' and ticker in positions:
                signals.append({
                    'action': 'SELL',
                    'ticker': ticker,
                    'quantity': positions[ticker]['quantity'],
                })

        return signals

    result = await engine.run(
        strategy=ml_strategy,
        tickers=request.tickers,
        start_date=request.start_date,
        end_date=request.end_date,
        walk_forward=True
    )

    return {
        "performance": {
            "total_return": f"{result.total_return*100:.2f}%",
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": f"{result.max_drawdown*100:.2f}%",
            "win_rate": f"{result.win_rate*100:.2f}%",
        },
        "trades": result.trades,
        "num_trades": result.num_trades,
    }
```

**Métriques:**
- Total return (%)
- Sharpe ratio (rendement ajusté au risque)
- Max drawdown (perte maximale)
- Win rate (% trades gagnants)
- Profit factor (gains/pertes)
- Value at Risk (VaR 95%)

**Checklist:**
- [ ] Moteur de backtesting complet
- [ ] Walk-forward optimization
- [ ] Métriques de performance complètes
- [ ] Visualisations (equity curve, drawdown)
- [ ] Endpoint `/ml/backtest`
- [ ] Comparaison avec buy-and-hold

---

## Phase 5: Analyse Automatisée & Alertes Intelligentes

**Durée:** 3-4 semaines
**Priorité:** Haute

### 5.1 Analyse Quotidienne Automatique (1 semaine)

```python
# api/scheduler/daily_analysis.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=8, minute=45)  # Avant ouverture marché
async def daily_morning_analysis():
    """Analyse quotidienne avant ouverture"""

    # 1. Récupération positions utilisateur
    users = await get_all_users()

    for user in users:
        positions = await get_user_positions(user.id)

        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "portfolio_value": 0,
            "daily_pnl": 0,
            "positions_analysis": [],
            "alerts": [],
            "recommendations": [],
        }

        # 2. Analyse de chaque position
        for pos in positions:
            # Prix actuel
            current_price = await get_real_time_price(pos['ticker'])

            # Prédiction ML
            prediction = await predict_price(pos['ticker'], days_ahead=5)
            trend = await predict_trend(pos['ticker'])

            # Analyse technique
            technical = await analyze_technical(pos['ticker'])

            # Sentiment news
            sentiment = await analyze_sentiment(pos['ticker'])

            # Synthèse
            analysis = {
                "ticker": pos['ticker'],
                "current_price": current_price,
                "quantity": pos['quantity'],
                "value": current_price * pos['quantity'],
                "pnl": (current_price - pos['avg_price']) * pos['quantity'],
                "pnl_pct": ((current_price - pos['avg_price']) / pos['avg_price']) * 100,
                "prediction": prediction,
                "trend": trend,
                "technical": technical,
                "sentiment": sentiment,
                "recommendation": generate_recommendation(prediction, trend, technical, sentiment),
            }

            report['positions_analysis'].append(analysis)
            report['portfolio_value'] += analysis['value']
            report['daily_pnl'] += analysis['pnl']

            # Génération alertes
            if analysis['recommendation']['action'] == 'SELL' and analysis['recommendation']['urgency'] == 'HIGH':
                report['alerts'].append({
                    "type": "SELL_URGENT",
                    "ticker": pos['ticker'],
                    "reason": analysis['recommendation']['reasoning'],
                })

            if analysis['recommendation']['action'] == 'BUY_MORE' and analysis['recommendation']['confidence'] > 0.8:
                report['alerts'].append({
                    "type": "BUY_OPPORTUNITY",
                    "ticker": pos['ticker'],
                    "target_price": analysis['recommendation']['target_price'],
                })

        # 3. Opportunités nouvelles positions
        watchlist = await get_user_watchlist(user.id)
        for ticker in watchlist:
            analysis = await full_analysis(ticker)
            if analysis['score'] > 8:
                report['recommendations'].append({
                    "ticker": ticker,
                    "action": "BUY",
                    "price": analysis['current_price'],
                    "target": analysis['target_price'],
                    "upside": analysis['upside_potential'],
                    "reasoning": analysis['reasoning'],
                })

        # 4. Vérification rééquilibrage
        rebalance = await check_rebalancing_needed(positions)
        if rebalance['needed']:
            report['alerts'].append({
                "type": "REBALANCE",
                "reason": rebalance['reason'],
                "actions": rebalance['suggested_actions'],
            })

        # 5. Envoi rapport
        await send_telegram_report(user.chat_id, report)
        await save_report_to_db(user.id, report)

def generate_recommendation(prediction, trend, technical, sentiment):
    """Génère recommandation basée sur multiples signaux"""

    score = 0
    reasons = []

    # Prédiction prix
    if prediction['predicted_price'] > prediction['current_price'] * 1.05:
        score += 3
        reasons.append(f"Prix prédit: {prediction['predicted_price']:.2f}€ (+{((prediction['predicted_price']/prediction['current_price'])-1)*100:.1f}%)")
    elif prediction['predicted_price'] < prediction['current_price'] * 0.95:
        score -= 3
        reasons.append(f"Prix prédit en baisse: {prediction['predicted_price']:.2f}€")

    # Tendance
    if trend['trend'] == 'HAUSSE' and trend['confidence'] > 0.7:
        score += 2
        reasons.append(f"Tendance haussière (confiance {trend['confidence']*100:.0f}%)")
    elif trend['trend'] == 'BAISSE' and trend['confidence'] > 0.7:
        score -= 2
        reasons.append(f"Tendance baissière (confiance {trend['confidence']*100:.0f}%)")

    # Technique
    if technical['rsi'] < 30:
        score += 2
        reasons.append(f"RSI en survente ({technical['rsi']:.0f})")
    elif technical['rsi'] > 70:
        score -= 2
        reasons.append(f"RSI en surachat ({technical['rsi']:.0f})")

    if technical['macd']['signal'] == 'BUY':
        score += 1
        reasons.append("MACD positif")
    elif technical['macd']['signal'] == 'SELL':
        score -= 1
        reasons.append("MACD négatif")

    # Sentiment
    if sentiment['score'] > 7:
        score += 1
        reasons.append(f"Sentiment positif ({sentiment['score']}/10)")
    elif sentiment['score'] < 3:
        score -= 1
        reasons.append(f"Sentiment négatif ({sentiment['score']}/10)")

    # Décision finale
    if score >= 5:
        action = "BUY" if score >= 7 else "BUY_MORE"
        urgency = "HIGH" if score >= 7 else "MEDIUM"
    elif score <= -5:
        action = "SELL"
        urgency = "HIGH" if score <= -7 else "MEDIUM"
    else:
        action = "HOLD"
        urgency = "LOW"

    return {
        "action": action,
        "score": score,
        "confidence": min(abs(score) / 10, 1.0),
        "urgency": urgency,
        "reasoning": " | ".join(reasons),
    }
```

**Checklist:**
- [ ] Scheduler avec APScheduler
- [ ] Analyse quotidienne 8h45
- [ ] Intégration ML predictions
- [ ] Synthèse multi-signaux
- [ ] Génération recommandations
- [ ] Envoi Telegram automatique

### 5.2 Surveillance Temps Réel (1 semaine)

```python
# api/realtime/monitor.py
import asyncio

class RealTimeMonitor:
    def __init__(self):
        self.active_monitors = {}

    async def start(self):
        """Lance surveillance temps réel"""
        asyncio.create_task(self.monitor_positions())
        asyncio.create_task(self.monitor_market_events())

    async def monitor_positions(self):
        """Check positions toutes les 5 minutes pendant heures de marché"""
        while True:
            if is_market_open():
                users = await get_all_users()

                for user in users:
                    positions = await get_user_positions(user.id)

                    for pos in positions:
                        current_price = await get_real_time_price(pos['ticker'])
                        pnl_pct = ((current_price - pos['avg_price']) / pos['avg_price']) * 100

                        # Stop-loss
                        if 'stop_loss' in pos and current_price <= pos['stop_loss']:
                            await send_alert(user.chat_id, {
                                "type": "STOP_LOSS",
                                "ticker": pos['ticker'],
                                "current_price": current_price,
                                "stop_loss": pos['stop_loss'],
                                "loss": pnl_pct,
                            })

                        # Take-profit
                        if 'take_profit' in pos and current_price >= pos['take_profit']:
                            await send_alert(user.chat_id, {
                                "type": "TAKE_PROFIT",
                                "ticker": pos['ticker'],
                                "current_price": current_price,
                                "target": pos['take_profit'],
                                "gain": pnl_pct,
                            })

                        # Mouvement important (±5%)
                        if abs(pnl_pct) >= 5:
                            await send_alert(user.chat_id, {
                                "type": "BIG_MOVE",
                                "ticker": pos['ticker'],
                                "movement": pnl_pct,
                                "current_price": current_price,
                            })

            await asyncio.sleep(300)  # 5 minutes

    async def monitor_market_events(self):
        """Surveille événements de marché importants"""
        while True:
            # News importantes
            news = await fetch_breaking_news()
            for article in news:
                affected_tickers = extract_tickers(article['content'])
                sentiment = await analyze_sentiment(article['content'])

                if abs(sentiment['score'] - 5) > 3:  # Score très positif ou négatif
                    users_affected = await get_users_with_positions(affected_tickers)
                    for user in users_affected:
                        await send_alert(user.chat_id, {
                            "type": "MARKET_NEWS",
                            "headline": article['title'],
                            "affected_tickers": affected_tickers,
                            "sentiment": sentiment,
                        })

            await asyncio.sleep(600)  # 10 minutes
```

**Checklist:**
- [ ] Monitoring prix temps réel
- [ ] Alertes stop-loss automatiques
- [ ] Alertes take-profit
- [ ] Détection mouvements importants (±5%)
- [ ] Veille news temps réel
- [ ] Seulement pendant heures de marché

### 5.3 Rééquilibrage Automatique (1 semaine)

```python
# api/portfolio/rebalancing.py

class RebalancingEngine:
    def __init__(self, target_allocation: dict, rebalance_threshold=0.05):
        """
        Args:
            target_allocation: {"CAC40": 0.4, "Technology": 0.3, "Healthcare": 0.3}
            rebalance_threshold: Écart minimal pour déclencher (5%)
        """
        self.target_allocation = target_allocation
        self.threshold = rebalance_threshold

    async def check_rebalancing_needed(self, positions: List[dict]) -> dict:
        """Vérifie si rééquilibrage nécessaire"""

        # Calcul allocation actuelle
        total_value = sum(p['value'] for p in positions)
        current_allocation = {}

        for pos in positions:
            sector = await get_ticker_sector(pos['ticker'])
            current_allocation[sector] = current_allocation.get(sector, 0) + pos['value']

        # Normalisation en pourcentages
        current_allocation = {k: v/total_value for k, v in current_allocation.items()}

        # Calcul écarts
        deviations = {}
        max_deviation = 0

        for sector, target_pct in self.target_allocation.items():
            current_pct = current_allocation.get(sector, 0)
            deviation = current_pct - target_pct
            deviations[sector] = deviation
            max_deviation = max(max_deviation, abs(deviation))

        # Rééquilibrage nécessaire ?
        if max_deviation > self.threshold:
            actions = self.generate_rebalancing_actions(positions, deviations, total_value)

            return {
                "needed": True,
                "max_deviation": max_deviation,
                "current_allocation": current_allocation,
                "target_allocation": self.target_allocation,
                "deviations": deviations,
                "suggested_actions": actions,
                "estimated_cost": self.calculate_transaction_costs(actions),
            }

        return {"needed": False}

    def generate_rebalancing_actions(self, positions, deviations, total_value):
        """Génère actions de rééquilibrage"""
        actions = []

        for sector, deviation in deviations.items():
            if abs(deviation) < 0.01:  # Ignore petits écarts (<1%)
                continue

            target_value = self.target_allocation[sector] * total_value
            current_value = sum(
                p['value'] for p in positions
                if await get_ticker_sector(p['ticker']) == sector
            )

            if deviation > 0:  # Sur-pondéré → vendre
                amount_to_sell = (current_value - target_value)

                # Sélection positions à vendre (moins performantes)
                sector_positions = sorted(
                    [p for p in positions if await get_ticker_sector(p['ticker']) == sector],
                    key=lambda x: x['pnl_pct']
                )

                remaining = amount_to_sell
                for pos in sector_positions:
                    if remaining <= 0:
                        break

                    sell_value = min(pos['value'], remaining)
                    sell_qty = sell_value / pos['current_price']

                    actions.append({
                        "type": "SELL",
                        "ticker": pos['ticker'],
                        "quantity": sell_qty,
                        "value": sell_value,
                        "reason": f"Réduire exposition {sector}",
                    })

                    remaining -= sell_value

            elif deviation < 0:  # Sous-pondéré → acheter
                amount_to_buy = (target_value - current_value)

                # Sélection meilleures opportunités dans le secteur
                opportunities = await get_sector_opportunities(sector)

                for opp in opportunities[:3]:  # Top 3
                    buy_value = amount_to_buy / 3
                    buy_qty = buy_value / opp['current_price']

                    actions.append({
                        "type": "BUY",
                        "ticker": opp['ticker'],
                        "quantity": buy_qty,
                        "value": buy_value,
                        "reason": f"Augmenter exposition {sector}",
                        "score": opp['score'],
                    })

        return actions

    def calculate_transaction_costs(self, actions):
        """Calcule frais de transaction"""
        # PEA: 0.6% par ordre typiquement
        total_cost = sum(action['value'] * 0.006 for action in actions)
        return total_cost

# Scheduler mensuel
@scheduler.scheduled_job('cron', day=1, hour=9)  # Premier du mois
async def monthly_rebalancing():
    """Rééquilibrage mensuel automatique"""

    users = await get_all_users()

    for user in users:
        if not user.auto_rebalance_enabled:
            continue

        positions = await get_user_positions(user.id)
        target_allocation = user.target_allocation  # Défini dans profil

        engine = RebalancingEngine(target_allocation)
        rebalance = await engine.check_rebalancing_needed(positions)

        if rebalance['needed']:
            # Envoi proposition
            await send_telegram_message(user.chat_id, format_rebalance_proposal(rebalance))

            # Si auto-execute activé
            if user.auto_execute_rebalance and rebalance['estimated_cost'] < 100:
                for action in rebalance['suggested_actions']:
                    await execute_trade(user.id, action)

                await send_telegram_message(
                    user.chat_id,
                    f"✅ Rééquilibrage exécuté automatiquement\n"
                    f"Coût total: {rebalance['estimated_cost']:.2f}€"
                )
```

**Format proposition rééquilibrage:**
```
🔄 RÉÉQUILIBRAGE RECOMMANDÉ

Écart maximal: 8.5%

Allocation actuelle:
  • CAC40: 48% (cible 40%)
  • Technology: 25% (cible 30%)
  • Healthcare: 27% (cible 30%)

Actions suggérées:
🔴 VENDRE
  • TotalEnergies: 2 actions (-680€)
  • BNP Paribas: 3 actions (-195€)

🟢 ACHETER
  • ASML: 1 action (+750€)
  • Sanofi: 1 action (+90€)

Coût transaction: ~10€
Optimisation allocation: +2.5% rendement annuel estimé

Voulez-vous exécuter ? (/rebalance confirm)
```

**Checklist:**
- [ ] Moteur de rééquilibrage
- [ ] Calcul déviations allocation
- [ ] Génération actions optimales
- [ ] Estimation coûts transaction
- [ ] Scheduler mensuel
- [ ] Mode manuel vs automatique
- [ ] Seuils personnalisables

### 5.4 Rapports Réguliers (1 semaine)

**Quotidien (8h45):**
- Valeur portfolio
- P&L du jour
- Top/flop performers
- Actions à surveiller
- Opportunités d'achat

**Hebdomadaire (Dimanche 20h):**
- Performance semaine
- Comparaison avec indices (CAC40, etc.)
- Transactions effectuées
- Recommandations rééquilibrage
- Score diversification

**Mensuel (1er du mois):**
- Bilan complet du mois
- Graphiques performance
- Comparaison objectifs
- Fiscalité PEA (gain net, plafond)
- Stratégie mois suivant

**Checklist:**
- [ ] Template rapports quotidiens
- [ ] Template rapports hebdomadaires
- [ ] Template rapports mensuels
- [ ] Génération graphiques (matplotlib)
- [ ] Calculs fiscaux PEA
- [ ] Comparaison benchmarks

---

## Phase 6: Optimisations Avancées

**Durée:** 6-8 semaines
**Priorité:** Basse (après production)

### 6.1 Optimisation Performance

**Checklist:**
- [ ] Cache distribué Redis pour prix/analyses
- [ ] Optimisation queries SQL (index, explain)
- [ ] Async partout (async/await)
- [ ] Connection pooling
- [ ] Rate limiting intelligent
- [ ] CDN pour assets statiques

### 6.2 Monitoring & Observabilité

**Checklist:**
- [ ] Prometheus pour métriques
- [ ] Grafana dashboards
- [ ] Alertes PagerDuty/OpsGenie
- [ ] Distributed tracing (Jaeger)
- [ ] Log aggregation (ELK stack)
- [ ] Uptime monitoring (UptimeRobot)

### 6.3 Features Avancées

**Checklist:**
- [ ] Multi-utilisateurs avec isolation données
- [ ] Partage portfolios (lecture seule)
- [ ] Alertes personnalisables par utilisateur
- [ ] Backtesting interactif avec UI
- [ ] Comparaison portfolios vs benchmarks
- [ ] Simulation scénarios (stress testing)

---

## Timeline Globale

```
Mois 1-2: SÉCURITÉ & PRODUCTION-READY ⚠️ PRIORITAIRE
├─ Semaine 1-2: Phase 1 (Sécurité)
└─ Semaine 3-4: Phase 2 (Déploiement VPS)

Mois 3: BOT TELEGRAM
├─ Semaine 1: Configuration + commandes de base
├─ Semaine 2: Alertes automatiques
└─ Semaine 3-4: Modèle Q&A + tests

Mois 4-5: MACHINE LEARNING
├─ Semaine 1-2: Infrastructure ML + LSTM
├─ Semaine 3: XGBoost classification
└─ Semaine 4-6: Backtesting avancé

Mois 6: ANALYSE AUTOMATISÉE
├─ Semaine 1-2: Analyse quotidienne + surveillance temps réel
├─ Semaine 3: Rééquilibrage automatique
└─ Semaine 4: Rapports réguliers

Mois 7-8: OPTIMISATIONS (optionnel)
└─ Performance, monitoring, features avancées
```

---

## Budget Estimé

### Infrastructure (mensuel)
- VPS Hostinger (8GB RAM): ~15-25€/mois
- PostgreSQL managé (optionnel): ~10€/mois
- Redis managé (optionnel): ~10€/mois
- Domaine + SSL: ~15€/an
- Backup automatique: ~5€/mois

**Total infrastructure:** ~30-50€/mois

### APIs & Services
- OpenAI (embeddings + GPT): ~20-50€/mois selon usage
- Ollama: Gratuit (self-hosted)
- Yahoo Finance: Gratuit
- Telegram Bot: Gratuit
- GitHub Actions: Gratuit (limite 2000 min/mois)

**Total services:** ~20-50€/mois

### Développement
- Temps estimé: 400-600 heures sur 6 mois
- Si freelance: 20-50€/h = 8 000 - 30 000€

**TOTAL:** ~70-100€/mois récurrent + développement initial

---

## Critères de Succès

### Phase 1: Sécurité
- ✅ 100% endpoints authentifiés
- ✅ Scan sécurité sans vulnérabilités critiques
- ✅ CORS restreint
- ✅ Secrets chiffrés

### Phase 2: Production
- ✅ Uptime > 99.5%
- ✅ Latence < 500ms (p95)
- ✅ Backup quotidien automatique
- ✅ CI/CD fonctionnel

### Phase 3: Telegram
- ✅ Toutes commandes fonctionnelles
- ✅ Alertes envoyées en <10s
- ✅ Rapport matinal quotidien
- ✅ 95% messages traités correctement

### Phase 4: ML
- ✅ Prédiction prix avec erreur < 5% (MAPE)
- ✅ Classification tendance accuracy > 65%
- ✅ Backtesting Sharpe ratio > 1.0
- ✅ Win rate > 55%

### Phase 5: Analyse Auto
- ✅ Analyse quotidienne 100% fiable
- ✅ Alertes temps réel <5 min
- ✅ Rééquilibrage mensuel automatique
- ✅ Rentabilité PEA positive (objectif +8-12%/an)

---

## Prochaines Étapes Immédiates

### Cette semaine (Priorité MAXIMALE)
1. ✅ Lire ce document complètement
2. ⚠️ **PHASE 1.1**: Implémenter JWT authentication (3-4 jours)
3. ⚠️ **PHASE 1.2**: Corriger path traversal (1-2 jours)

### Semaine prochaine
4. PHASE 1.3-1.5: CORS, dépendances, logs (2-3 jours)
5. Tests de sécurité complets
6. Début Phase 2: PostgreSQL migration

### Ce mois
7. Déploiement VPS Hostinger
8. Configuration CI/CD
9. Monitoring de base

---

## Ressources & Documentation

### À lire
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Docker for Python](https://docs.docker.com/language/python/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [MLOps Best Practices](https://ml-ops.org/)

### Exemples de code
- JWT authentication: `api/auth.py` (à créer)
- Docker setup: `Dockerfile` + `docker-compose.yml`
- ML training: `api/ml/training/train.py`
- Backtesting: `api/ml/backtesting/engine.py`

---

## Conclusion

Ce projet RAG-PEA a **un excellent potentiel** mais nécessite **impérativement** les phases 1-2 avant production.

**Points forts actuels:**
- Architecture fonctionnelle (7.2/10)
- RAG + CrewAI opérationnels
- Base solide pour évolutions

**Risques bloquants:**
- ⚠️ Sécurité insuffisante (3.5/10)
- ⚠️ Infrastructure dev (SQLite)
- ⚠️ Pas de monitoring

**Après sécurisation (Phases 1-2):**
- Système production-ready
- Base saine pour ML et Telegram
- Scalable et maintenable

**Vision finale (après Phase 5):**
- Bot Telegram intelligent 24/7
- Prédictions ML fiables
- Alertes automatiques personnalisées
- Rééquilibrage automatique
- **Objectif: Rentabilité PEA maximale**

---

**Prêt à démarrer avec la Phase 1?** 🚀
