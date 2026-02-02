"""
Système de logging structuré JSON pour le système RAG-PEA

Ce module fournit :
- Logs JSON structurés pour production
- Logs texte lisibles pour développement
- Rotation automatique des fichiers de logs
- Contexte enrichi (request_id, user_id, endpoint, etc.)
- Intégration avec FastAPI
"""

from __future__ import annotations

import logging
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from logging.handlers import RotatingFileHandler
from contextvars import ContextVar

from config import settings


# Context variables pour stocker les informations de requête
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
endpoint_var: ContextVar[Optional[str]] = ContextVar("endpoint", default=None)


class JSONFormatter(logging.Formatter):
    """
    Formateur de logs JSON structuré

    Génère des logs au format JSON avec tous les champs nécessaires
    pour l'analyse et le monitoring en production.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Formate un record de log en JSON structuré"""

        # Champs de base
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Ajouter le contexte de la requête si disponible
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        endpoint = endpoint_var.get()
        if endpoint:
            log_data["endpoint"] = endpoint

        # Ajouter les champs custom s'ils existent
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Ajouter les informations d'exception si présentes
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Ajouter le stack trace si disponible
        if hasattr(record, "stack_info") and record.stack_info:
            log_data["stack_trace"] = record.stack_info

        return json.dumps(log_data, ensure_ascii=False)


class ColoredTextFormatter(logging.Formatter):
    """
    Formateur de logs texte coloré pour le développement

    Produit des logs lisibles avec des couleurs ANSI pour faciliter
    le debugging en développement.
    """

    # Codes ANSI pour les couleurs
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Vert
        "WARNING": "\033[33m",    # Jaune
        "ERROR": "\033[31m",      # Rouge
        "CRITICAL": "\033[1;31m", # Rouge gras
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        """Formate un record de log en texte coloré"""

        # Obtenir la couleur selon le niveau
        color = self.COLORS.get(record.levelname, self.RESET)

        # Formater le timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Construire le message de base
        parts = [
            f"{color}{timestamp}{self.RESET}",
            f"{color}[{record.levelname}]{self.RESET}",
            f"{self.BOLD}{record.name}{self.RESET}",
        ]

        # Ajouter le contexte de requête si disponible
        request_id = request_id_var.get()
        if request_id:
            parts.append(f"[req:{request_id[:8]}]")

        user_id = user_id_var.get()
        if user_id:
            parts.append(f"[user:{user_id}]")

        endpoint = endpoint_var.get()
        if endpoint:
            parts.append(f"[{endpoint}]")

        # Ajouter le message
        parts.append("-")
        parts.append(record.getMessage())

        # Joindre toutes les parties
        log_line = " ".join(parts)

        # Ajouter l'exception si présente
        if record.exc_info:
            log_line += f"\n{color}{''.join(traceback.format_exception(*record.exc_info))}{self.RESET}"

        return log_line


class ContextLogger(logging.LoggerAdapter):
    """
    Logger adapter qui ajoute automatiquement le contexte

    Permet d'ajouter facilement des champs personnalisés à tous les logs.
    """

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Ajoute les champs extra au contexte du log"""

        # Récupérer ou créer le dict extra
        extra = kwargs.get("extra", {})

        # Ajouter le contexte de requête
        request_id = request_id_var.get()
        if request_id:
            extra["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            extra["user_id"] = user_id

        endpoint = endpoint_var.get()
        if endpoint:
            extra["endpoint"] = endpoint

        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging() -> None:
    """
    Configure le système de logging global

    Appelé au démarrage de l'application pour configurer tous les loggers.
    """

    # Niveau de log global
    log_level = getattr(logging, settings.logging.level)

    # Créer le répertoire de logs si nécessaire
    if settings.logging.file_path:
        log_file = Path(settings.logging.file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configurer le logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Supprimer les handlers existants
    root_logger.handlers.clear()

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Choisir le formateur selon l'environnement
    if settings.logging.format == "json" or settings.is_production:
        console_formatter = JSONFormatter()
    else:
        console_formatter = ColoredTextFormatter()

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Handler fichier avec rotation (si configuré)
    if settings.logging.file_path:
        file_handler = RotatingFileHandler(
            settings.logging.file_path,
            maxBytes=settings.logging.max_bytes,
            backupCount=settings.logging.backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)

        # Toujours JSON pour les fichiers
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Configurer les loggers spécifiques

    # Réduire le bruit des librairies externes
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    # Logger SQL si activé
    if settings.logging.log_sql_queries:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log de confirmation du démarrage
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging system initialized",
        extra={
            "level": settings.logging.level,
            "format": settings.logging.format,
            "file": settings.logging.file_path,
            "environment": settings.environment
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Obtient un logger configuré pour un module

    Args:
        name: Nom du module (généralement __name__)

    Returns:
        Logger configuré

    Exemple:
        ```python
        from api.logging_config import get_logger

        logger = get_logger(__name__)
        logger.info("Message de log")
        ```
    """
    return logging.getLogger(name)


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    endpoint: Optional[str] = None
) -> None:
    """
    Définit le contexte de la requête courante pour les logs

    Args:
        request_id: ID unique de la requête
        user_id: ID de l'utilisateur
        endpoint: Endpoint appelé

    Exemple:
        ```python
        from api.logging_config import set_request_context

        set_request_context(
            request_id="abc123",
            user_id="user_456",
            endpoint="/api/portfolio"
        )
        ```
    """
    if request_id:
        request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)
    if endpoint:
        endpoint_var.set(endpoint)


def clear_request_context() -> None:
    """Nettoie le contexte de requête (à appeler en fin de requête)"""
    request_id_var.set(None)
    user_id_var.set(None)
    endpoint_var.set(None)


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An error occurred",
    **extra_fields: Any
) -> None:
    """
    Log une exception avec contexte complet

    Args:
        logger: Logger à utiliser
        exception: Exception à logger
        message: Message descriptif
        **extra_fields: Champs supplémentaires à ajouter

    Exemple:
        ```python
        try:
            # Code dangereux
            result = risky_operation()
        except Exception as e:
            log_exception(
                logger,
                e,
                "Failed to perform risky operation",
                operation="risky_operation",
                input_data=data
            )
        ```
    """
    logger.error(
        message,
        exc_info=True,
        extra={"extra_fields": extra_fields}
    )


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    success: bool = True,
    **extra_fields: Any
) -> None:
    """
    Log les métriques de performance d'une opération

    Args:
        logger: Logger à utiliser
        operation: Nom de l'opération
        duration_ms: Durée en millisecondes
        success: Si l'opération a réussi
        **extra_fields: Champs supplémentaires

    Exemple:
        ```python
        import time
        from api.logging_config import log_performance

        start = time.time()
        result = expensive_operation()
        duration = (time.time() - start) * 1000

        log_performance(
            logger,
            "expensive_operation",
            duration,
            success=True,
            items_processed=len(result)
        )
        ```
    """
    performance_data = {
        "operation": operation,
        "duration_ms": round(duration_ms, 2),
        "success": success,
        **extra_fields
    }

    level = logging.INFO if success else logging.WARNING
    logger.log(
        level,
        f"Performance: {operation} completed in {duration_ms:.2f}ms",
        extra={"extra_fields": performance_data}
    )


class LoggerMixin:
    """
    Mixin pour ajouter un logger à une classe

    Exemple:
        ```python
        from api.logging_config import LoggerMixin

        class MyService(LoggerMixin):
            def process(self):
                self.logger.info("Processing started")
                # ...
                self.logger.info("Processing completed")
        ```
    """

    @property
    def logger(self) -> logging.Logger:
        """Retourne un logger configuré pour cette classe"""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__module__)
        return self._logger


# Initialiser le système de logging au chargement du module
setup_logging()
