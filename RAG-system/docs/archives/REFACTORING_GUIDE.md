# GUIDE DE REFACTORING - EXEMPLES CONCRETS

## Vue d'ensemble

Ce guide fournit des exemples de code concrets pour refactorer le système RAG-PEA selon les recommandations architecturales. Chaque section montre l'état actuel et la solution recommandée.

---

## 1. CONFIGURATION CENTRALISÉE

### État Actuel (Problématique)

Code dispersé dans plusieurs fichiers avec valeurs hardcodées:

```python
# rag_manager.py
class RAGManager:
    def __init__(
        self,
        db_path: str = "../data/vector_db",  # ❌ Hardcodé
        embed_model_id: str = "sentence-transformers/all-MiniLM-L6-v2",  # ❌ Hardcodé
        ollama_url: str = "http://localhost:11434",  # ❌ Hardcodé
        ollama_model: str = "mistral",  # ❌ Hardcodé
    ):

# portfolio_db.py
class PortfolioDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = Path(__file__).parent.parent.parent / "data"  # ❌ Calcul relatif
            db_path = str(base_dir / "portfolio.db")

# main.py
UPLOAD_DIR = Path("../data/uploads")  # ❌ Relatif
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
```

### Solution Recommandée

**1. Créer le fichier de configuration**

```python
# api/config/settings.py

from pydantic import BaseSettings, Field, validator
from pathlib import Path
from typing import Optional
from functools import lru_cache
import os

class Settings(BaseSettings):
    """
    Configuration centralisée de l'application.

    Toutes les variables sont configurables via:
    - Fichier .env
    - Variables d'environnement système
    - Valeurs par défaut
    """

    # ====================
    # APPLICATION
    # ====================
    app_name: str = "RAG-PEA API"
    app_version: str = "1.0.0"
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("development", env="ENVIRONMENT")  # development, staging, production

    # ====================
    # SERVER
    # ====================
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_workers: int = Field(4, env="API_WORKERS")

    # ====================
    # PATHS (Absolus)
    # ====================
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)

    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def vector_db_path(self) -> Path:
        return self.data_dir / "vector_db"

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def chunks_dir(self) -> Path:
        return self.data_dir / "chunks"

    @property
    def logs_dir(self) -> Path:
        return self.base_dir / "logs"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "portfolio.db"

    # ====================
    # DATABASE
    # ====================
    database_url: str = Field(
        "sqlite:///data/portfolio.db",
        env="DATABASE_URL"
    )
    db_pool_size: int = Field(20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(10, env="DB_MAX_OVERFLOW")

    # ====================
    # VECTOR DATABASE (ChromaDB)
    # ====================
    embed_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        env="EMBED_MODEL"
    )
    vector_db_batch_size: int = Field(5000, env="VECTOR_DB_BATCH_SIZE")

    # ====================
    # OLLAMA (LLM Local)
    # ====================
    ollama_url: str = Field("http://localhost:11434", env="OLLAMA_URL")
    ollama_model: str = Field("mistral", env="OLLAMA_MODEL")
    ollama_timeout: int = Field(60, env="OLLAMA_TIMEOUT")

    # ====================
    # EXTERNAL APIS
    # ====================
    anthropic_api_key: str = Field("", env="ANTHROPIC_API_KEY")
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    news_api_key: str = Field("", env="NEWS_API_KEY")
    serpapi_key: str = Field("", env="SERPAPI_KEY")

    # ====================
    # CREWAI
    # ====================
    crew_timeout: int = Field(600, env="CREW_TIMEOUT")  # 10 minutes
    crew_verbose: bool = Field(True, env="CREW_VERBOSE")

    # ====================
    # CACHE
    # ====================
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    cache_ttl_stock_info: int = Field(3600, env="CACHE_TTL_STOCK_INFO")  # 1h
    cache_ttl_news: int = Field(1800, env="CACHE_TTL_NEWS")  # 30min

    # ====================
    # RATE LIMITING
    # ====================
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")

    # ====================
    # LOGGING
    # ====================
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")  # json or text

    # ====================
    # SECURITY
    # ====================
    secret_key: str = Field(..., env="SECRET_KEY")  # Requis
    cors_origins: list = Field(
        ["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Créer les répertoires nécessaires
        self._create_directories()

    def _create_directories(self):
        """Crée tous les répertoires nécessaires"""
        directories = [
            self.data_dir,
            self.vector_db_path,
            self.upload_dir,
            self.chunks_dir,
            self.logs_dir,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Retourne l'instance singleton des settings.

    Le décorateur @lru_cache assure qu'une seule instance existe
    pendant toute la durée de vie de l'application.

    Returns:
        Settings: Instance configurée

    Example:
        >>> from config.settings import get_settings
        >>> settings = get_settings()
        >>> print(settings.api_port)
        8000
    """
    return Settings()


# Variables d'environnement pour testing
class TestSettings(Settings):
    """Settings pour tests avec valeurs de test"""

    class Config:
        env_file = ".env.test"

    def __init__(self):
        super().__init__()
        # Override pour tests
        self.database_url = "sqlite:///:memory:"
        self.debug = True
```

**2. Fichier .env mis à jour**

```bash
# .env

# ====================
# APPLICATION
# ====================
DEBUG=false
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here-change-in-production

# ====================
# SERVER
# ====================
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# ====================
# DATABASE
# ====================
DATABASE_URL=postgresql://user:password@localhost:5432/rag_pea
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# ====================
# OLLAMA
# ====================
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=60

# ====================
# EXTERNAL APIS
# ====================
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key
NEWS_API_KEY=your-newsapi-key
SERPAPI_KEY=your-serpapi-key

# ====================
# REDIS CACHE
# ====================
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL_STOCK_INFO=3600
CACHE_TTL_NEWS=1800

# ====================
# LOGGING
# ====================
LOG_LEVEL=INFO
LOG_FORMAT=json

# ====================
# SECURITY
# ====================
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,https://myapp.com

# ====================
# CREWAI
# ====================
CREW_TIMEOUT=600
CREW_VERBOSE=true

# ====================
# RATE LIMITING
# ====================
RATE_LIMIT_PER_MINUTE=60
```

**3. Utilisation dans les modules**

```python
# rag_manager.py (REFACTORÉ)

from config.settings import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class RAGManager:
    """Gestionnaire centralisé pour le système RAG"""

    def __init__(self):
        """Initialise le RAG Manager avec les settings globales"""
        # ✓ Plus de paramètres hardcodés
        self.db_path = str(settings.vector_db_path)
        self.embed_model_id = settings.embed_model
        self.ollama_url = settings.ollama_url
        self.ollama_model = settings.ollama_model

        logger.info(f"RAGManager initialized with model: {self.embed_model_id}")

        # Initialiser les composants
        self.chroma_client = self._init_chromadb()
        self.embed_model = self._init_embedding_model()

    # ... reste du code ...


# portfolio_db.py (REFACTORÉ)

from config.settings import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class PortfolioDatabase:
    """Gestion de la base de données du portefeuille"""

    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: Chemin personnalisé (pour tests), sinon utilise settings
        """
        if db_path is None:
            db_path = str(settings.db_path)  # ✓ Chemin absolu depuis settings

        self.db_path = db_path
        logger.info(f"PortfolioDatabase initialized at: {db_path}")
        self.init_database()

    # ... reste du code ...


# main.py (REFACTORÉ)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import get_settings
from config.logging_config import setup_logging
import logging

# Initialiser logging AVANT tout
setup_logging()
logger = logging.getLogger(__name__)

# Charger settings
settings = get_settings()

# Créer l'application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# CORS depuis settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ✓ Depuis config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser le gestionnaire RAG
rag_manager = RAGManager()  # ✓ Utilise automatiquement les settings

# Upload directory depuis settings
UPLOAD_DIR = settings.upload_dir  # ✓ Chemin absolu depuis settings

logger.info(f"Application started in {settings.environment} mode")

# ... endpoints ...
```

---

## 2. LOGGING STRUCTURÉ

### État Actuel (Problématique)

```python
# Code actuel dispersé dans tous les fichiers:

print(f"Erreur Yahoo Finance pour {ticker}: {e}")  # ❌
print("⚠️ pandas-ta non disponible, utilisation de calculs manuels")  # ❌
print(f"✅ Fichier .env chargé depuis: {env_path}")  # ❌

# Ou pire: silencieux
except Exception:
    pass  # ❌ Aucune trace
```

### Solution Recommandée

**1. Configuration du logging**

```python
# api/config/logging_config.py

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
from config.settings import get_settings

settings = get_settings()


def get_logging_config() -> Dict[str, Any]:
    """
    Retourne la configuration de logging selon l'environnement.

    Returns:
        Dict de configuration compatible avec logging.config.dictConfig
    """

    log_level = settings.log_level.upper()
    log_format = settings.log_format

    # Format des logs
    if log_format == "json":
        formatter_class = "pythonjsonlogger.jsonlogger.JsonFormatter"
        format_string = "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
    else:
        formatter_class = "logging.Formatter"
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "class": formatter_class,
                "format": format_string,
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": str(settings.logs_dir / "api.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "standard",
                "filename": str(settings.logs_dir / "errors.log"),
                "maxBytes": 10485760,
                "backupCount": 10,
            },
        },
        "loggers": {
            # Root logger
            "": {
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
                "propagate": False,
            },
            # Logger pour l'API
            "api": {
                "handlers": ["console", "file", "error_file"],
                "level": "DEBUG",
                "propagate": False,
            },
            # Logger pour les services
            "services": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            },
            # Logger pour les agents
            "agents": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            # Silence les logs trop verbeux
            "httpx": {
                "level": "WARNING",
            },
            "urllib3": {
                "level": "WARNING",
            },
        },
    }

    return config


def setup_logging():
    """
    Configure le logging pour toute l'application.

    À appeler AU DÉBUT de main.py, avant tout autre import.

    Example:
        >>> from config.logging_config import setup_logging
        >>> setup_logging()
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    # Créer le dossier logs s'il n'existe pas
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    # Charger la configuration
    config = get_logging_config()
    logging.config.dictConfig(config)

    # Log initial
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {settings.log_level}, Format: {settings.log_format}")
    logger.info(f"Log files: {settings.logs_dir}")


# Utility pour créer un logger contextualisé
def get_logger(name: str) -> logging.Logger:
    """
    Crée un logger avec le nom spécifié.

    Args:
        name: Nom du logger (typiquement __name__)

    Returns:
        Logger configuré

    Example:
        >>> from config.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Message")
    """
    return logging.getLogger(name)
```

**2. Utilisation dans les modules**

```python
# services/yahoo_finance_service.py (REFACTORÉ)

import logging
from typing import Dict, Optional
import yfinance as yf

logger = logging.getLogger(__name__)

class YahooFinanceService:
    """Service pour interagir avec Yahoo Finance API"""

    @staticmethod
    def get_stock_info(ticker: str) -> Dict:
        """
        Récupère les informations complètes d'une action.

        Args:
            ticker: Ticker Yahoo Finance (ex: "MC.PA")

        Returns:
            Dict avec toutes les infos

        Raises:
            ValueError: Si ticker invalide
            YahooFinanceError: Si erreur API
        """
        logger.debug(f"Fetching stock info for ticker: {ticker}")

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Valider la réponse
            if not info or 'currentPrice' not in info:
                logger.warning(f"Invalid or empty info for ticker: {ticker}")
                raise ValueError(f"Invalid ticker: {ticker}")

            logger.info(
                f"Successfully fetched stock info for {ticker}",
                extra={
                    "ticker": ticker,
                    "price": info.get("currentPrice"),
                    "market_cap": info.get("marketCap")
                }
            )

            return {
                "ticker": ticker,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                # ... reste ...
            }

        except ValueError:
            # Re-raise les ValueError
            raise

        except Exception as e:
            # ✓ Log structuré avec contexte
            logger.error(
                f"Failed to fetch stock info for {ticker}",
                exc_info=True,
                extra={
                    "ticker": ticker,
                    "error_type": type(e).__name__
                }
            )
            raise YahooFinanceError(f"Failed to fetch info for {ticker}") from e


# rag_manager.py (REFACTORÉ)

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RAGManager:
    def index_document(self, file_path: str, collection_name: str) -> Dict[str, Any]:
        """Indexe un document PDF complet"""

        logger.info(
            f"Starting document indexation",
            extra={
                "file_path": file_path,
                "collection_name": collection_name
            }
        )

        start_time = time.time()

        try:
            # 1. Vérifier que le fichier existe
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                raise FileNotFoundError(f"Fichier non trouvé : {file_path}")

            # 2. Convertir le document
            logger.debug(f"Converting document: {file_path}")
            converter = DocumentConverter()
            doc = converter.convert(source=file_path).document

            # ... reste de la logique ...

            processing_time = time.time() - start_time

            logger.info(
                f"Document indexation completed successfully",
                extra={
                    "collection_name": collection_name,
                    "total_chunks": len(processed_chunks),
                    "processing_time": processing_time
                }
            )

            return {
                "success": True,
                "collection_name": collection_name,
                "total_chunks": len(processed_chunks),
                "processing_time": processing_time,
            }

        except FileNotFoundError:
            raise

        except Exception as e:
            logger.error(
                f"Document indexation failed",
                exc_info=True,
                extra={
                    "file_path": file_path,
                    "collection_name": collection_name,
                    "error_type": type(e).__name__
                }
            )
            raise IndexingError(f"Failed to index document: {file_path}") from e


# main.py (REFACTORÉ)

from config.logging_config import setup_logging
import logging

# ✓ TRÈS IMPORTANT: Setup logging AVANT tout
setup_logging()
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request
import time

app = FastAPI(...)

# Middleware pour logger toutes les requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log toutes les requêtes HTTP"""
    start_time = time.time()

    # Log la requête entrante
    logger.info(
        f"Request started",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None
        }
    )

    # Traiter la requête
    response = await call_next(request)

    # Log la réponse
    processing_time = time.time() - start_time
    logger.info(
        f"Request completed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "processing_time": processing_time
        }
    )

    return response


@app.on_event("startup")
async def startup_event():
    """Appelé au démarrage de l'application"""
    logger.info(
        f"Application startup",
        extra={
            "environment": settings.environment,
            "debug": settings.debug,
            "version": settings.app_version
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Appelé à l'arrêt de l'application"""
    logger.info("Application shutdown")
```

**3. Visualisation des logs**

```bash
# Logs en temps réel
$ tail -f logs/api.log | jq .

# Filtrer les erreurs
$ grep ERROR logs/api.log | jq .

# Chercher un ticker spécifique
$ grep "MC.PA" logs/api.log | jq .

# Analyser les temps de réponse
$ jq 'select(.processing_time > 1)' logs/api.log
```

---

## 3. GESTION D'ERREURS ROBUSTE

### État Actuel (Problématique)

```python
# Patterns problématiques actuels:

# ❌ Exception trop générale
try:
    result = operation()
except Exception as e:
    print(f"Erreur: {e}")
    return {}

# ❌ Exception silencieuse
try:
    self.chroma_client.delete_collection(name=collection_name)
except Exception:
    pass

# ❌ Pas de validation d'input
def add_position(self, ticker, company_name, quantity, price):
    # Que se passe-t-il si quantity = -10 ?
    # Que se passe-t-il si price = 0 ?
    pass
```

### Solution Recommandée

**1. Hiérarchie d'exceptions custom**

```python
# api/exceptions.py

"""
Hiérarchie d'exceptions pour le système RAG-PEA.

Toutes les exceptions custom héritent de RAGSystemError.
"""

class RAGSystemError(Exception):
    """
    Exception de base pour toutes les erreurs du système.

    Attributes:
        message: Message d'erreur
        details: Détails additionnels (dict)
        original_error: Exception originale si wrapped
    """

    def __init__(
        self,
        message: str,
        details: dict = None,
        original_error: Exception = None
    ):
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Sérialise l'exception en dict pour API"""
        result = {
            "error_type": self.__class__.__name__,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


# ====================
# DATABASE ERRORS
# ====================

class DatabaseError(RAGSystemError):
    """Erreur générale de base de données"""
    pass


class PositionNotFoundError(DatabaseError):
    """Position non trouvée dans le portefeuille"""
    pass


class InsufficientQuantityError(DatabaseError):
    """Quantité insuffisante pour vendre"""
    pass


class DuplicatePositionError(DatabaseError):
    """Position déjà existante"""
    pass


# ====================
# RAG ERRORS
# ====================

class RAGError(RAGSystemError):
    """Erreur générale du système RAG"""
    pass


class CollectionNotFoundError(RAGError):
    """Collection RAG non trouvée"""
    pass


class IndexingError(RAGError):
    """Erreur lors de l'indexation d'un document"""
    pass


class SearchError(RAGError):
    """Erreur lors de la recherche RAG"""
    pass


# ====================
# EXTERNAL API ERRORS
# ====================

class ExternalAPIError(RAGSystemError):
    """Erreur générale d'API externe"""
    pass


class YahooFinanceError(ExternalAPIError):
    """Erreur Yahoo Finance API"""
    pass


class OllamaError(ExternalAPIError):
    """Erreur Ollama API"""
    pass


class NewsAPIError(ExternalAPIError):
    """Erreur NewsAPI"""
    pass


# ====================
# VALIDATION ERRORS
# ====================

class ValidationError(RAGSystemError):
    """Erreur de validation d'input"""
    pass


class InvalidTickerError(ValidationError):
    """Ticker invalide"""
    pass


class InvalidQuantityError(ValidationError):
    """Quantité invalide (négative ou zéro)"""
    pass


class InvalidPriceError(ValidationError):
    """Prix invalide (négatif ou zéro)"""
    pass


# ====================
# AGENT ERRORS
# ====================

class AgentError(RAGSystemError):
    """Erreur générale des agents CrewAI"""
    pass


class AgentTimeoutError(AgentError):
    """Agent a dépassé le timeout"""
    pass


class AgentExecutionError(AgentError):
    """Erreur lors de l'exécution d'un agent"""
    pass
```

**2. Middleware de gestion d'erreurs global**

```python
# api/middleware/error_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from api.exceptions import RAGSystemError

logger = logging.getLogger(__name__)


async def rag_exception_handler(request: Request, exc: RAGSystemError) -> JSONResponse:
    """
    Handler pour toutes les exceptions RAGSystemError.

    Args:
        request: Requête FastAPI
        exc: Exception levée

    Returns:
        JSONResponse avec détails de l'erreur
    """
    logger.error(
        f"RAG System Error: {exc.message}",
        exc_info=True,
        extra={
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "details": exc.details
        }
    )

    # Déterminer le status code selon le type d'erreur
    status_code_map = {
        "CollectionNotFoundError": status.HTTP_404_NOT_FOUND,
        "PositionNotFoundError": status.HTTP_404_NOT_FOUND,
        "ValidationError": status.HTTP_400_BAD_REQUEST,
        "InvalidTickerError": status.HTTP_400_BAD_REQUEST,
        "InvalidQuantityError": status.HTTP_400_BAD_REQUEST,
        "InvalidPriceError": status.HTTP_400_BAD_REQUEST,
        "DuplicatePositionError": status.HTTP_409_CONFLICT,
        "InsufficientQuantityError": status.HTTP_400_BAD_REQUEST,
        "AgentTimeoutError": status.HTTP_504_GATEWAY_TIMEOUT,
    }

    status_code = status_code_map.get(
        type(exc).__name__,
        status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handler pour les erreurs de validation Pydantic"""
    logger.warning(
        f"Validation error",
        extra={
            "path": request.url.path,
            "errors": exc.errors()
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_type": "ValidationError",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler pour toutes les exceptions non gérées.

    Catch-all pour éviter de renvoyer des erreurs 500 non formatées.
    """
    logger.exception(
        f"Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__
        }
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_type": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc)} if settings.debug else {}
        }
    )


def register_exception_handlers(app):
    """
    Enregistre tous les handlers d'exceptions.

    Args:
        app: Instance FastAPI

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    app.add_exception_handler(RAGSystemError, rag_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
```

**3. Validation systématique dans les services**

```python
# services/portfolio_manager.py (REFACTORÉ)

import logging
from typing import Dict
from api.exceptions import (
    InvalidTickerError,
    InvalidQuantityError,
    InvalidPriceError,
    PositionNotFoundError
)

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Gestionnaire de portefeuille intelligent"""

    def __init__(self):
        self.db = PortfolioDatabase()
        self.yf = YahooFinanceService()

    def validate_ticker(self, ticker: str) -> str:
        """
        Valide et normalise un ticker.

        Args:
            ticker: Ticker à valider

        Returns:
            Ticker normalisé (uppercase, trimmed)

        Raises:
            InvalidTickerError: Si ticker invalide
        """
        if not ticker:
            raise InvalidTickerError(
                "Ticker cannot be empty",
                details={"ticker": ticker}
            )

        ticker = ticker.strip().upper()

        if len(ticker) < 2:
            raise InvalidTickerError(
                "Ticker must be at least 2 characters",
                details={"ticker": ticker}
            )

        # Valider format (lettres, chiffres, point)
        if not ticker.replace(".", "").isalnum():
            raise InvalidTickerError(
                "Ticker contains invalid characters",
                details={"ticker": ticker}
            )

        return ticker

    def validate_quantity(self, quantity: float) -> float:
        """
        Valide une quantité.

        Args:
            quantity: Quantité à valider

        Returns:
            Quantité validée

        Raises:
            InvalidQuantityError: Si quantité invalide
        """
        if not isinstance(quantity, (int, float)):
            raise InvalidQuantityError(
                "Quantity must be a number",
                details={"quantity": quantity, "type": type(quantity).__name__}
            )

        if quantity <= 0:
            raise InvalidQuantityError(
                "Quantity must be positive",
                details={"quantity": quantity}
            )

        return float(quantity)

    def validate_price(self, price: float) -> float:
        """
        Valide un prix.

        Args:
            price: Prix à valider

        Returns:
            Prix validé

        Raises:
            InvalidPriceError: Si prix invalide
        """
        if not isinstance(price, (int, float)):
            raise InvalidPriceError(
                "Price must be a number",
                details={"price": price, "type": type(price).__name__}
            )

        if price <= 0:
            raise InvalidPriceError(
                "Price must be positive",
                details={"price": price}
            )

        return float(price)

    def get_position_details(self, ticker: str, user_id: str = "default_user") -> Dict:
        """
        Récupère tous les détails d'une position.

        Args:
            ticker: Ticker de l'action
            user_id: ID utilisateur

        Returns:
            Dict avec tous les détails

        Raises:
            InvalidTickerError: Si ticker invalide
            PositionNotFoundError: Si position non trouvée
        """
        # ✓ Valider l'input
        ticker = self.validate_ticker(ticker)

        logger.debug(f"Fetching position details for {ticker}")

        try:
            # Données du portefeuille
            positions = self.db.get_portfolio(user_id)
            position = next((p for p in positions if p['ticker'] == ticker), None)

            if not position:
                raise PositionNotFoundError(
                    f"Position not found: {ticker}",
                    details={"ticker": ticker, "user_id": user_id}
                )

            # Données de marché
            market_data = self.yf.get_stock_info(ticker)

            # Historique
            transactions = self.db.get_transactions(ticker, user_id, limit=10)
            analyses = self.db.get_analysis_history(ticker, user_id, limit=5)

            logger.info(
                f"Position details fetched successfully",
                extra={
                    "ticker": ticker,
                    "user_id": user_id,
                    "current_value": position.get("current_value")
                }
            )

            return {
                "position": position,
                "market_data": market_data,
                "transactions": transactions,
                "past_analyses": analyses
            }

        except PositionNotFoundError:
            raise

        except YahooFinanceError as e:
            logger.warning(
                f"Failed to fetch market data for {ticker}, continuing with portfolio data only",
                extra={"ticker": ticker, "error": str(e)}
            )
            # Retourner quand même les données disponibles
            return {
                "position": position,
                "market_data": None,
                "transactions": transactions,
                "past_analyses": analyses,
                "warnings": ["Market data unavailable"]
            }

        except Exception as e:
            logger.error(
                f"Failed to fetch position details",
                exc_info=True,
                extra={"ticker": ticker, "user_id": user_id}
            )
            raise DatabaseError(
                f"Failed to fetch position details for {ticker}",
                original_error=e
            ) from e
```

**4. Utilisation dans les endpoints**

```python
# main.py (REFACTORÉ)

from fastapi import FastAPI, Depends, HTTPException
from api.middleware.error_handler import register_exception_handlers
from api.exceptions import InvalidTickerError, PositionNotFoundError
import logging

logger = logging.getLogger(__name__)

app = FastAPI(...)

# ✓ Enregistrer les handlers d'exceptions
register_exception_handlers(app)


@app.get("/portfolio/position/{ticker}", tags=["Portfolio"])
async def get_position_details(
    ticker: str,
    user_id: str = "default_user",
    manager: PortfolioManager = Depends()
):
    """
    Récupère tous les détails d'une position.

    Args:
        ticker: Ticker de l'action
        user_id: ID utilisateur

    Returns:
        Détails complets de la position

    Raises:
        400: Si ticker invalide
        404: Si position non trouvée
        500: Erreur serveur
    """
    # ✓ Plus besoin de try/except ici, géré par les handlers
    return manager.get_position_details(ticker, user_id)

    # Les exceptions InvalidTickerError, PositionNotFoundError
    # sont automatiquement transformées en réponses JSON appropriées
```

---

## 4. TESTS AUTOMATISÉS

### Structure Recommandée

```
tests/
├── __init__.py
├── conftest.py                 # Fixtures pytest
├── unit/
│   ├── __init__.py
│   ├── test_yahoo_finance.py
│   ├── test_technical_analysis.py
│   ├── test_portfolio_manager.py
│   └── test_rag_manager.py
├── integration/
│   ├── __init__.py
│   ├── test_api_endpoints.py
│   └── test_database.py
└── e2e/
    ├── __init__.py
    └── test_full_workflow.py
```

**1. Configuration pytest**

```python
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.main import app
from api.database.portfolio_db import PortfolioDatabase
from api.config.settings import get_settings, Settings

# Override settings pour tests
class TestSettings(Settings):
    class Config:
        env_file = ".env.test"

    database_url: str = "sqlite:///:memory:"
    debug: bool = True
    log_level: str = "DEBUG"


@pytest.fixture(scope="session")
def test_settings():
    """Settings pour tests"""
    return TestSettings()


@pytest.fixture(scope="function")
def test_db():
    """
    Database en mémoire pour chaque test.

    Scope: function = nouvelle DB pour chaque test (isolation)
    """
    db = PortfolioDatabase(db_path=":memory:")
    yield db
    # Cleanup automatique (in-memory)


@pytest.fixture(scope="module")
def client():
    """Client de test FastAPI"""
    return TestClient(app)


@pytest.fixture
def sample_portfolio_data():
    """Données de test pour portfolio"""
    return [
        {
            "ticker": "MC.PA",
            "company_name": "LVMH",
            "quantity": 10,
            "price": 850.0
        },
        {
            "ticker": "OR.PA",
            "company_name": "L'Oréal",
            "quantity": 20,
            "price": 450.0
        }
    ]
```

**2. Tests unitaires**

```python
# tests/unit/test_portfolio_manager.py

import pytest
from api.services.portfolio_manager import PortfolioManager
from api.exceptions import (
    InvalidTickerError,
    InvalidQuantityError,
    InvalidPriceError
)


class TestPortfolioManagerValidation:
    """Tests de validation du PortfolioManager"""

    def test_validate_ticker_valid(self):
        """Test avec ticker valide"""
        manager = PortfolioManager()
        result = manager.validate_ticker("MC.PA")
        assert result == "MC.PA"

    def test_validate_ticker_lowercase(self):
        """Test normalisation en uppercase"""
        manager = PortfolioManager()
        result = manager.validate_ticker("mc.pa")
        assert result == "MC.PA"

    def test_validate_ticker_with_spaces(self):
        """Test trim des espaces"""
        manager = PortfolioManager()
        result = manager.validate_ticker("  MC.PA  ")
        assert result == "MC.PA"

    def test_validate_ticker_empty(self):
        """Test ticker vide"""
        manager = PortfolioManager()
        with pytest.raises(InvalidTickerError) as exc_info:
            manager.validate_ticker("")
        assert "cannot be empty" in str(exc_info.value)

    def test_validate_ticker_too_short(self):
        """Test ticker trop court"""
        manager = PortfolioManager()
        with pytest.raises(InvalidTickerError) as exc_info:
            manager.validate_ticker("A")
        assert "at least 2 characters" in str(exc_info.value)

    def test_validate_ticker_invalid_chars(self):
        """Test caractères invalides"""
        manager = PortfolioManager()
        with pytest.raises(InvalidTickerError):
            manager.validate_ticker("MC@PA")

    def test_validate_quantity_valid(self):
        """Test quantité valide"""
        manager = PortfolioManager()
        result = manager.validate_quantity(10.5)
        assert result == 10.5

    def test_validate_quantity_zero(self):
        """Test quantité zéro (invalide)"""
        manager = PortfolioManager()
        with pytest.raises(InvalidQuantityError):
            manager.validate_quantity(0)

    def test_validate_quantity_negative(self):
        """Test quantité négative (invalide)"""
        manager = PortfolioManager()
        with pytest.raises(InvalidQuantityError):
            manager.validate_quantity(-5)

    def test_validate_price_valid(self):
        """Test prix valide"""
        manager = PortfolioManager()
        result = manager.validate_price(850.50)
        assert result == 850.50

    def test_validate_price_zero(self):
        """Test prix zéro (invalide)"""
        manager = PortfolioManager()
        with pytest.raises(InvalidPriceError):
            manager.validate_price(0)


# tests/unit/test_portfolio_db.py

import pytest
from api.database.portfolio_db import PortfolioDatabase


class TestPortfolioDatabase:
    """Tests de la base de données portfolio"""

    def test_add_position_new(self, test_db):
        """Test ajout nouvelle position"""
        success = test_db.add_position(
            ticker="MC.PA",
            company_name="LVMH",
            quantity=10,
            price=850.0
        )

        assert success is True

        portfolio = test_db.get_portfolio()
        assert len(portfolio) == 1
        assert portfolio[0]["ticker"] == "MC.PA"
        assert portfolio[0]["quantity"] == 10
        assert portfolio[0]["avg_price"] == 850.0

    def test_add_position_duplicate_updates_avg(self, test_db):
        """Test ajout position existante met à jour la moyenne"""
        # Premier achat: 10 actions @ 850
        test_db.add_position("MC.PA", "LVMH", 10, 850.0)

        # Deuxième achat: 10 actions @ 900
        test_db.add_position("MC.PA", "LVMH", 10, 900.0)

        portfolio = test_db.get_portfolio()
        assert len(portfolio) == 1
        assert portfolio[0]["quantity"] == 20
        # Moyenne pondérée: (10*850 + 10*900) / 20 = 875
        assert portfolio[0]["avg_price"] == 875.0

    def test_sell_position_partial(self, test_db):
        """Test vente partielle"""
        # Acheter 10 actions
        test_db.add_position("MC.PA", "LVMH", 10, 850.0)

        # Vendre 5 actions
        success = test_db.sell_position("MC.PA", 5, 900.0)
        assert success is True

        portfolio = test_db.get_portfolio()
        assert len(portfolio) == 1
        assert portfolio[0]["quantity"] == 5

    def test_sell_position_total(self, test_db):
        """Test vente totale supprime position"""
        test_db.add_position("MC.PA", "LVMH", 10, 850.0)
        test_db.sell_position("MC.PA", 10, 900.0)

        portfolio = test_db.get_portfolio()
        assert len(portfolio) == 0

    def test_sell_position_insufficient(self, test_db):
        """Test vente avec quantité insuffisante"""
        test_db.add_position("MC.PA", "LVMH", 10, 850.0)

        # Essayer de vendre 15 (plus que détenu)
        success = test_db.sell_position("MC.PA", 15, 900.0)
        assert success is False

    def test_get_portfolio_summary(self, test_db, sample_portfolio_data):
        """Test résumé du portefeuille"""
        # Ajouter plusieurs positions
        for pos in sample_portfolio_data:
            test_db.add_position(**pos)

        summary = test_db.get_portfolio_summary()

        assert summary["total_positions"] == 2
        assert summary["total_invested"] == (10 * 850.0) + (20 * 450.0)
        assert len(summary["positions"]) == 2
```

**3. Tests d'intégration**

```python
# tests/integration/test_api_endpoints.py

import pytest
from fastapi.testclient import TestClient


class TestPortfolioEndpoints:
    """Tests des endpoints portfolio"""

    def test_add_position_success(self, client):
        """Test ajout position via API"""
        response = client.post(
            "/portfolio/add",
            json={
                "ticker": "MC.PA",
                "company_name": "LVMH",
                "quantity": 10,
                "price": 850.0,
                "user_id": "test_user"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["ticker"] == "MC.PA"

    def test_add_position_invalid_ticker(self, client):
        """Test validation ticker invalide"""
        response = client.post(
            "/portfolio/add",
            json={
                "ticker": "",  # Invalide
                "company_name": "LVMH",
                "quantity": 10,
                "price": 850.0
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "error_type" in data
        assert data["error_type"] == "InvalidTickerError"

    def test_get_portfolio(self, client):
        """Test récupération du portefeuille"""
        # D'abord ajouter une position
        client.post(
            "/portfolio/add",
            json={
                "ticker": "MC.PA",
                "company_name": "LVMH",
                "quantity": 10,
                "price": 850.0,
                "user_id": "test_user"
            }
        )

        # Récupérer le portfolio
        response = client.get("/portfolio?user_id=test_user")

        assert response.status_code == 200
        data = response.json()
        assert data["total_positions"] >= 1


class TestRAGEndpoints:
    """Tests des endpoints RAG"""

    def test_health_check(self, client):
        """Test health check"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_list_collections(self, client):
        """Test listage des collections"""
        response = client.get("/collections")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.skipif(
        not os.path.exists("test_data/sample.pdf"),
        reason="Test PDF file not found"
    )
    def test_upload_document(self, client):
        """Test upload d'un document"""
        with open("test_data/sample.pdf", "rb") as f:
            response = client.post(
                "/upload",
                files={"file": ("sample.pdf", f, "application/pdf")},
                params={"collection_name": "test_collection"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_chunks" in data
```

**4. Tests End-to-End**

```python
# tests/e2e/test_full_workflow.py

import pytest
from fastapi.testclient import TestClient


class TestFullInvestmentWorkflow:
    """
    Tests du workflow complet d'investissement.

    Simule le parcours complet d'un utilisateur.
    """

    def test_complete_investment_workflow(self, client):
        """
        Test du workflow complet:
        1. Créer portefeuille
        2. Ajouter positions
        3. Consulter santé
        4. Analyser rebalancing
        5. Vendre position
        """
        user_id = "test_user_workflow"

        # 1. Vérifier portefeuille vide initialement
        response = client.get(f"/portfolio?user_id={user_id}")
        assert response.status_code == 200
        assert response.json()["total_positions"] == 0

        # 2. Ajouter première position (LVMH)
        response = client.post(
            "/portfolio/add",
            json={
                "ticker": "MC.PA",
                "company_name": "LVMH",
                "quantity": 10,
                "price": 850.0,
                "user_id": user_id
            }
        )
        assert response.status_code == 200

        # 3. Ajouter deuxième position (L'Oréal)
        response = client.post(
            "/portfolio/add",
            json={
                "ticker": "OR.PA",
                "company_name": "L'Oréal",
                "quantity": 20,
                "price": 450.0,
                "user_id": user_id
            }
        )
        assert response.status_code == 200

        # 4. Vérifier le portefeuille
        response = client.get(f"/portfolio?user_id={user_id}")
        data = response.json()
        assert data["total_positions"] == 2
        assert data["total_invested"] > 0

        # 5. Vérifier la santé du portefeuille
        response = client.get(f"/portfolio/health?user_id={user_id}")
        assert response.status_code == 200
        health = response.json()
        assert "score" in health
        assert "grade" in health

        # 6. Vérifier le rebalancing
        response = client.get(f"/portfolio/rebalance?user_id={user_id}")
        assert response.status_code == 200
        rebalance = response.json()
        assert "needs_rebalance" in rebalance

        # 7. Vendre partiellement une position
        response = client.post(
            "/portfolio/sell",
            json={
                "ticker": "MC.PA",
                "quantity": 5,
                "price": 900.0,
                "user_id": user_id
            }
        )
        assert response.status_code == 200

        # 8. Vérifier que la vente a bien eu lieu
        response = client.get(f"/portfolio?user_id={user_id}")
        data = response.json()
        lvmh_position = next(
            (p for p in data["positions"] if p["ticker"] == "MC.PA"),
            None
        )
        assert lvmh_position is not None
        assert lvmh_position["quantity"] == 5  # 10 - 5 = 5
```

**5. Exécution des tests**

```bash
# Installer les dépendances de test
pip install pytest pytest-cov pytest-asyncio httpx

# Exécuter tous les tests
pytest tests/

# Exécuter avec couverture
pytest tests/ --cov=api --cov-report=html --cov-report=term

# Exécuter uniquement les tests unitaires
pytest tests/unit/

# Exécuter un fichier spécifique
pytest tests/unit/test_portfolio_manager.py

# Exécuter avec logs visibles
pytest tests/ -v -s

# Exécuter tests en parallèle (plus rapide)
pip install pytest-xdist
pytest tests/ -n auto

# Générer rapport HTML
pytest tests/ --html=report.html --self-contained-html
```

**6. Configuration pytest.ini**

```ini
# pytest.ini

[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Marqueurs personnalisés
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (database, API)
    e2e: End-to-end tests (full workflow)
    slow: Tests that take a long time
    external_api: Tests that call external APIs

# Options par défaut
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=api
    --cov-report=term-missing
    --cov-report=html

# Filtrer les warnings
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning

# Coverage minimum requis
[coverage:run]
source = api

[coverage:report]
fail_under = 80
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

---

## CONCLUSION

Ce guide de refactoring fournit des exemples concrets pour transformer le code actuel en code production-ready. Les points clés:

1. **Configuration centralisée** - Élimine les hardcoded values
2. **Logging structuré** - Observabilité complète
3. **Gestion d'erreurs robuste** - Exceptions typées et handlers
4. **Tests automatisés** - 80%+ de couverture

Chaque refactoring est incrémental et peut être appliqué module par module sans tout casser d'un coup.

**Prochaines étapes recommandées:**
1. Commencer par la configuration centralisée (settings.py)
2. Ajouter le logging (logging_config.py)
3. Implémenter les exceptions (exceptions.py)
4. Écrire les premiers tests (conftest.py + test_*.py)
5. Refactorer module par module avec les nouveaux patterns
