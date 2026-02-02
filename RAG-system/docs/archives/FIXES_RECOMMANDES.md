# FIXES RECOMMANDÉS - BUGS CRITIQUES ET MAJEURS

Ce document contient les corrections de code recommandées pour les bugs identifiés lors de l'audit de qualité.

---

## 🔴 FIX #1: Migration Base de Données vers SQLite

**Problème**: Base de données portefeuille en mémoire, données perdues au redémarrage
**Priorité**: CRITIQUE
**Fichier**: `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/database/portfolio_db.py`

### Code Actuel (Problématique)
```python
class PortfolioDatabase:
    def __init__(self):
        self.portfolios = {}  # ❌ En mémoire
        self.transactions = {}  # ❌ En mémoire
```

### Code Corrigé (Recommandé)
```python
import sqlite3
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime

class PortfolioDatabase:
    def __init__(self, db_path: str = "../data/portfolio.db"):
        """Initialise la base de données SQLite"""
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Crée les tables si elles n'existent pas"""
        cursor = self.conn.cursor()

        # Table positions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                company_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                current_price REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, ticker)
            )
        """)

        # Table transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                transaction_type TEXT NOT NULL,  -- 'BUY' ou 'SELL'
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table analyses (historique)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                analysis_data TEXT NOT NULL,  -- JSON
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def add_position(self, ticker: str, company_name: str, quantity: float,
                     price: float, user_id: str = "default_user") -> bool:
        """Ajoute ou met à jour une position"""
        cursor = self.conn.cursor()

        try:
            # Vérifier si la position existe déjà
            cursor.execute("""
                SELECT quantity, avg_price FROM positions
                WHERE user_id = ? AND ticker = ?
            """, (user_id, ticker))

            existing = cursor.fetchone()

            if existing:
                # Position existe: calculer nouveau PRU
                old_qty = existing['quantity']
                old_price = existing['avg_price']

                new_qty = old_qty + quantity
                new_pru = (old_qty * old_price + quantity * price) / new_qty

                cursor.execute("""
                    UPDATE positions
                    SET quantity = ?, avg_price = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND ticker = ?
                """, (new_qty, new_pru, user_id, ticker))
            else:
                # Nouvelle position
                cursor.execute("""
                    INSERT INTO positions (user_id, ticker, company_name, quantity, avg_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, ticker, company_name, quantity, price))

            # Enregistrer la transaction
            cursor.execute("""
                INSERT INTO transactions (user_id, ticker, transaction_type, quantity, price)
                VALUES (?, ?, 'BUY', ?, ?)
            """, (user_id, ticker, quantity, price))

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"Erreur lors de l'ajout de position: {e}")
            return False

    def sell_position(self, ticker: str, quantity: float, price: float,
                      user_id: str = "default_user") -> bool:
        """Vend une position (partielle ou totale)"""
        cursor = self.conn.cursor()

        try:
            # Récupérer la position actuelle
            cursor.execute("""
                SELECT quantity FROM positions
                WHERE user_id = ? AND ticker = ?
            """, (user_id, ticker))

            existing = cursor.fetchone()

            if not existing:
                raise ValueError(f"Position {ticker} non trouvée pour l'utilisateur {user_id}")

            current_qty = existing['quantity']

            # ✅ FIX: Validation quantité
            if quantity > current_qty:
                raise ValueError(
                    f"Quantité insuffisante pour {ticker}: "
                    f"{current_qty} disponible, {quantity} demandé"
                )

            # Calculer nouvelle quantité
            new_qty = current_qty - quantity

            if new_qty == 0:
                # Vente totale: supprimer la position
                cursor.execute("""
                    DELETE FROM positions
                    WHERE user_id = ? AND ticker = ?
                """, (user_id, ticker))
            else:
                # Vente partielle: mettre à jour la quantité
                cursor.execute("""
                    UPDATE positions
                    SET quantity = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND ticker = ?
                """, (new_qty, user_id, ticker))

            # Enregistrer la transaction de vente
            cursor.execute("""
                INSERT INTO transactions (user_id, ticker, transaction_type, quantity, price)
                VALUES (?, ?, 'SELL', ?, ?)
            """, (user_id, ticker, quantity, price))

            self.conn.commit()
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"Erreur lors de la vente: {e}")
            return False

    def get_portfolio(self, user_id: str = "default_user") -> List[Dict]:
        """Récupère toutes les positions d'un utilisateur"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT ticker, company_name, quantity, avg_price, current_price, last_updated
            FROM positions
            WHERE user_id = ?
            ORDER BY company_name
        """, (user_id,))

        positions = []
        for row in cursor.fetchall():
            positions.append({
                'ticker': row['ticker'],
                'company_name': row['company_name'],
                'quantity': row['quantity'],
                'avg_price': row['avg_price'],
                'current_price': row['current_price'],
                'last_updated': row['last_updated']
            })

        return positions

    def get_transactions(self, ticker: str = None, user_id: str = "default_user",
                         limit: int = 50) -> List[Dict]:
        """Récupère l'historique des transactions"""
        cursor = self.conn.cursor()

        if ticker:
            cursor.execute("""
                SELECT * FROM transactions
                WHERE user_id = ? AND ticker = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, ticker, limit))
        else:
            cursor.execute("""
                SELECT * FROM transactions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))

        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'ticker': row['ticker'],
                'transaction_type': row['transaction_type'],
                'quantity': row['quantity'],
                'price': row['price'],
                'timestamp': row['timestamp']
            })

        return transactions

    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()
```

### Migration des Données Existantes
```python
# Script de migration (à exécuter une fois)
def migrate_to_sqlite():
    """Migre les données en mémoire vers SQLite"""
    from api.database.portfolio_db import PortfolioDatabase

    # Ancien système (si des données existent)
    old_data = {
        # Récupérer les données actuelles si possible
    }

    # Nouveau système
    new_db = PortfolioDatabase()

    # Migrer les positions
    for user_id, positions in old_data.items():
        for pos in positions:
            new_db.add_position(
                ticker=pos['ticker'],
                company_name=pos['company_name'],
                quantity=pos['quantity'],
                price=pos['avg_price'],
                user_id=user_id
            )

    print("Migration terminée!")
```

---

## 🔴 FIX #2: Gestion user_id Cohérente

**Problème**: user_id par défaut incohérent, risque de mélanger les données
**Priorité**: CRITIQUE
**Fichier**: `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/main.py`

### Code Corrigé
```python
from fastapi import Header, HTTPException
from typing import Optional

# Option 1: Header obligatoire
async def get_user_id_from_header(x_user_id: str = Header(...)) -> str:
    """Récupère le user_id depuis les headers (obligatoire)"""
    if not x_user_id or x_user_id.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Header X-User-Id requis"
        )
    return x_user_id

# Utilisation dans les endpoints
@app.post("/portfolio/add", tags=["Portfolio"])
async def add_position(
    request: PositionAddRequest,
    user_id: str = Depends(get_user_id_from_header)
):
    """Ajoute une position au portefeuille"""
    db = PortfolioDatabase()
    success = db.add_position(
        request.ticker,
        request.company_name,
        request.quantity,
        request.price,
        user_id=user_id  # ✅ user_id du header
    )

    if success:
        return {"message": f"Position {request.company_name} ajoutée", "ticker": request.ticker}
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de l'ajout")


# Option 2: JWT Token (plus sécurisé)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()
SECRET_KEY = "your-secret-key"  # À mettre dans .env
ALGORITHM = "HS256"

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extrait le user_id depuis le JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")

        return user_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

@app.post("/portfolio/add", tags=["Portfolio"])
async def add_position(
    request: PositionAddRequest,
    user_id: str = Depends(get_current_user)  # ✅ JWT
):
    # ...
```

### Modèles Mis à Jour
```python
# api/models.py

class PositionAddRequest(BaseModel):
    """Requête pour ajouter une position au portefeuille"""
    ticker: str = Field(..., description="Ticker de l'action (ex: MC.PA)")
    company_name: str = Field(..., description="Nom de l'entreprise (ex: LVMH)")
    quantity: float = Field(..., description="Nombre d'actions à acheter", gt=0)
    price: float = Field(..., description="Prix d'achat unitaire", gt=0)
    # ✅ Suppression du user_id du modèle (pris depuis header/token)
```

---

## 🟠 FIX #3: Cache Yahoo Finance

**Problème**: Appels API répétitifs, latence élevée
**Priorité**: MAJEURE
**Fichier**: `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/services/yahoo_finance_service.py`

### Code Corrigé
```python
from functools import lru_cache
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, Optional

class YahooFinanceService:
    def __init__(self):
        self.cache_duration = 300  # 5 minutes en secondes
        self._cache = {}
        self._cache_timestamps = {}

    def _is_cache_valid(self, key: str) -> bool:
        """Vérifie si le cache est encore valide"""
        if key not in self._cache_timestamps:
            return False

        age = (datetime.now() - self._cache_timestamps[key]).total_seconds()
        return age < self.cache_duration

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """
        Récupère les informations d'une action avec cache

        Cache: 5 minutes
        """
        cache_key = f"info_{ticker}"

        # Vérifier le cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or 'regularMarketPrice' not in info:
                return None

            # Mettre en cache
            self._cache[cache_key] = info
            self._cache_timestamps[cache_key] = datetime.now()

            return info

        except Exception as e:
            print(f"Erreur Yahoo Finance pour {ticker}: {e}")
            return None

    def get_historical_data(self, ticker: str, period: str = "1mo",
                           interval: str = "1d", use_cache: bool = True):
        """
        Récupère l'historique avec cache optionnel

        Cache désactivé par défaut pour l'historique (données changeantes)
        """
        cache_key = f"history_{ticker}_{period}_{interval}"

        if use_cache and self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if use_cache:
                self._cache[cache_key] = df
                self._cache_timestamps[cache_key] = datetime.now()

            return df

        except Exception as e:
            print(f"Erreur historique pour {ticker}: {e}")
            return None

    def clear_cache(self, ticker: str = None):
        """Nettoie le cache (tout ou pour un ticker spécifique)"""
        if ticker:
            keys_to_delete = [k for k in self._cache.keys() if ticker in k]
            for key in keys_to_delete:
                del self._cache[key]
                del self._cache_timestamps[key]
        else:
            self._cache.clear()
            self._cache_timestamps.clear()


# Utilisation alternative: Redis pour cache distribué
from redis import Redis
import pickle

class YahooFinanceServiceRedis:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = Redis.from_url(redis_url)
        self.cache_duration = 300  # 5 minutes

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """Récupère info avec cache Redis"""
        cache_key = f"yf:info:{ticker}"

        # Vérifier cache Redis
        cached = self.redis.get(cache_key)
        if cached:
            return pickle.loads(cached)

        # Récupérer données
        stock = yf.Ticker(ticker)
        info = stock.info

        if info:
            # Stocker dans Redis avec expiration
            self.redis.setex(
                cache_key,
                self.cache_duration,
                pickle.dumps(info)
            )

        return info
```

---

## 🟠 FIX #4: Circuit Breaker pour Ollama

**Problème**: Pas de protection si Ollama est down, timeout fixe
**Priorité**: MAJEURE
**Fichier**: `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/rag_manager.py`

### Code Corrigé
```python
import requests
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Tout va bien
    OPEN = "open"          # Trop d'erreurs, on bloque
    HALF_OPEN = "half_open"  # On teste si c'est revenu

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # secondes avant de réessayer
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        """Exécute une fonction avec protection circuit breaker"""

        # Si circuit ouvert, vérifier si on peut réessayer
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker OPEN: Service temporairement indisponible")

        try:
            result = func(*args, **kwargs)

            # Succès: réinitialiser
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
            self.failure_count = 0

            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

            raise e

class RAGManager:
    def __init__(self, ...):
        # ... existing code ...
        self.ollama_circuit_breaker = CircuitBreaker(
            failure_threshold=3,  # 3 échecs avant d'ouvrir
            timeout=30  # Réessayer après 30 secondes
        )

    def generate_answer(self, question: str, chunks: List[str],
                       metadatas: List[Dict]) -> str:
        """Génère une réponse avec protection circuit breaker"""

        # Construire le prompt
        context = self._build_context(chunks, metadatas)
        prompt = self._build_prompt(question, context)

        # Appeler Ollama avec circuit breaker
        def _call_ollama():
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 500  # ✅ Limite de tokens
                    },
                },
                timeout=30  # ✅ Timeout adaptatif
            )

            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.status_code}")

            return response.json().get("response", "")

        try:
            return self.ollama_circuit_breaker.call(_call_ollama)
        except Exception as e:
            # Fallback: retourner les chunks sans génération
            return f"[Génération indisponible] Voici les extraits pertinents:\n\n{context[:500]}..."
```

---

## Résumé des Fichiers à Modifier

1. `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/database/portfolio_db.py` - Migration SQLite
2. `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/main.py` - Gestion user_id
3. `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/models.py` - Suppression user_id des modèles
4. `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/services/yahoo_finance_service.py` - Cache
5. `/Users/maximedutertre/Desktop/projet-perso/agent-business/RAG-system/api/rag_manager.py` - Circuit breaker

## Ordre d'Implémentation Recommandé

1. **FIX #1** (Base SQLite) - 4-6 heures
2. **FIX #2** (user_id) - 2-3 heures
3. **FIX #3** (Cache Yahoo) - 2 heures
4. **FIX #4** (Circuit breaker) - 3 heures

**Total estimé**: 11-14 heures de développement
