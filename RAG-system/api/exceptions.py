"""
Système de gestion d'erreurs cohérent pour le système RAG-PEA

Ce module fournit :
- Hiérarchie d'exceptions custom pour chaque domaine
- Error handlers FastAPI standardisés
- Messages d'erreur cohérents et exploitables
- Codes HTTP appropriés
- Logging automatique des erreurs
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from logging_config import get_logger, log_exception


logger = get_logger(__name__)


# ==============================================================================
# EXCEPTIONS DE BASE
# ==============================================================================

class RAGSystemError(Exception):
    """
    Exception de base pour toutes les erreurs du système RAG

    Attributes:
        message: Message d'erreur descriptif
        error_code: Code d'erreur unique pour le tracking
        details: Détails supplémentaires sur l'erreur
        http_status: Code HTTP approprié
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Optional[dict[str, Any]] = None,
        http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.http_status = http_status
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convertit l'exception en dictionnaire pour la réponse JSON"""
        return {
            "error": {
                "message": self.message,
                "code": self.error_code,
                "details": self.details
            }
        }


# ==============================================================================
# EXCEPTIONS MÉTIER - BASE DE DONNÉES ET COLLECTIONS
# ==============================================================================

class DatabaseError(RAGSystemError):
    """Erreur liée à la base de données"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class CollectionNotFoundError(RAGSystemError):
    """Collection ChromaDB non trouvée"""

    def __init__(self, collection_name: str, available_collections: Optional[list[str]] = None):
        details = {"collection_name": collection_name}
        if available_collections:
            details["available_collections"] = available_collections

        super().__init__(
            message=f"Collection '{collection_name}' not found",
            error_code="COLLECTION_NOT_FOUND",
            details=details,
            http_status=status.HTTP_404_NOT_FOUND
        )


class CollectionAlreadyExistsError(RAGSystemError):
    """Tentative de création d'une collection qui existe déjà"""

    def __init__(self, collection_name: str):
        super().__init__(
            message=f"Collection '{collection_name}' already exists",
            error_code="COLLECTION_ALREADY_EXISTS",
            details={"collection_name": collection_name},
            http_status=status.HTTP_409_CONFLICT
        )


class DocumentIndexingError(RAGSystemError):
    """Erreur lors de l'indexation d'un document"""

    def __init__(self, document_path: str, reason: str, details: Optional[dict] = None):
        error_details = {"document_path": document_path, "reason": reason}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Failed to index document: {reason}",
            error_code="DOCUMENT_INDEXING_ERROR",
            details=error_details,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DocumentNotFoundError(RAGSystemError):
    """Document demandé non trouvé"""

    def __init__(self, document_path: str):
        super().__init__(
            message=f"Document not found: {document_path}",
            error_code="DOCUMENT_NOT_FOUND",
            details={"document_path": document_path},
            http_status=status.HTTP_404_NOT_FOUND
        )


# ==============================================================================
# EXCEPTIONS MÉTIER - OLLAMA ET GÉNÉRATION
# ==============================================================================

class OllamaError(RAGSystemError):
    """Erreur liée au service Ollama"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="OLLAMA_ERROR",
            details=details,
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class OllamaUnavailableError(OllamaError):
    """Service Ollama indisponible"""

    def __init__(self, ollama_url: str):
        super().__init__(
            message="Ollama service is unavailable. Please ensure Ollama is running.",
            details={
                "ollama_url": ollama_url,
                "suggestion": "Start Ollama with: ollama serve"
            }
        )


class OllamaTimeoutError(OllamaError):
    """Timeout lors de l'appel à Ollama"""

    def __init__(self, timeout: int):
        super().__init__(
            message=f"Ollama request timed out after {timeout} seconds",
            details={"timeout_seconds": timeout}
        )


class CircuitBreakerOpenError(OllamaError):
    """Circuit breaker ouvert, service temporairement indisponible"""

    def __init__(self, retry_after: int):
        super().__init__(
            message="Service temporarily unavailable due to repeated failures",
            details={
                "retry_after_seconds": retry_after,
                "reason": "Circuit breaker is open"
            }
        )


# ==============================================================================
# EXCEPTIONS MÉTIER - PORTFOLIO
# ==============================================================================

class PortfolioError(RAGSystemError):
    """Erreur liée à la gestion de portefeuille"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="PORTFOLIO_ERROR",
            details=details,
            http_status=status.HTTP_400_BAD_REQUEST
        )


class PositionNotFoundError(PortfolioError):
    """Position de portefeuille non trouvée"""

    def __init__(self, ticker: str, user_id: str):
        super().__init__(
            message=f"Position '{ticker}' not found in portfolio",
            details={"ticker": ticker, "user_id": user_id}
        )
        self.http_status = status.HTTP_404_NOT_FOUND


class InsufficientQuantityError(PortfolioError):
    """Quantité insuffisante pour effectuer une vente"""

    def __init__(self, ticker: str, available: float, requested: float):
        super().__init__(
            message=f"Insufficient quantity for {ticker}",
            details={
                "ticker": ticker,
                "available_quantity": available,
                "requested_quantity": requested
            }
        )


class InvalidTransactionError(PortfolioError):
    """Transaction invalide"""

    def __init__(self, reason: str, details: Optional[dict] = None):
        super().__init__(
            message=f"Invalid transaction: {reason}",
            details=details
        )


# ==============================================================================
# EXCEPTIONS MÉTIER - DONNÉES FINANCIÈRES
# ==============================================================================

class FinancialDataError(RAGSystemError):
    """Erreur liée aux données financières"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="FINANCIAL_DATA_ERROR",
            details=details,
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class TickerNotFoundError(FinancialDataError):
    """Ticker Yahoo Finance non trouvé"""

    def __init__(self, ticker: str):
        super().__init__(
            message=f"Ticker '{ticker}' not found",
            details={
                "ticker": ticker,
                "suggestion": "Verify ticker symbol (e.g., MC.PA for LVMH)"
            }
        )
        self.http_status = status.HTTP_404_NOT_FOUND


class MarketDataUnavailableError(FinancialDataError):
    """Données de marché temporairement indisponibles"""

    def __init__(self, source: str, reason: Optional[str] = None):
        details = {"source": source}
        if reason:
            details["reason"] = reason

        super().__init__(
            message=f"Market data from {source} temporarily unavailable",
            details=details
        )


# ==============================================================================
# EXCEPTIONS MÉTIER - AGENTS ET CREW
# ==============================================================================

class CrewAIError(RAGSystemError):
    """Erreur liée à l'exécution d'un Crew"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="CREWAI_ERROR",
            details=details,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class AgentExecutionError(CrewAIError):
    """Erreur lors de l'exécution d'un agent"""

    def __init__(self, agent_role: str, task_description: str, error: str):
        super().__init__(
            message=f"Agent '{agent_role}' failed to execute task",
            details={
                "agent_role": agent_role,
                "task_description": task_description,
                "error": error
            }
        )


class ToolExecutionError(CrewAIError):
    """Erreur lors de l'exécution d'un outil"""

    def __init__(self, tool_name: str, error: str, details: Optional[dict] = None):
        error_details = {"tool_name": tool_name, "error": error}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Tool '{tool_name}' execution failed",
            details=error_details
        )


# ==============================================================================
# EXCEPTIONS MÉTIER - VALIDATION
# ==============================================================================

class ValidationError(RAGSystemError):
    """Erreur de validation des données"""

    def __init__(self, field: str, message: str, value: Any = None):
        details = {"field": field}
        if value is not None:
            details["invalid_value"] = str(value)

        super().__init__(
            message=f"Validation error on field '{field}': {message}",
            error_code="VALIDATION_ERROR",
            details=details,
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class ConfigurationError(RAGSystemError):
    """Erreur de configuration"""

    def __init__(self, parameter: str, message: str):
        super().__init__(
            message=f"Configuration error for '{parameter}': {message}",
            error_code="CONFIGURATION_ERROR",
            details={"parameter": parameter},
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ==============================================================================
# ERROR HANDLERS FASTAPI
# ==============================================================================

async def rag_system_error_handler(request: Request, exc: RAGSystemError) -> JSONResponse:
    """
    Handler pour toutes les exceptions RAGSystemError

    Logs l'erreur et retourne une réponse JSON structurée
    """
    log_exception(
        logger,
        exc,
        f"RAG System Error: {exc.error_code}",
        endpoint=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict()
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler pour les erreurs de validation Pydantic

    Formate les erreurs de validation de manière cohérente
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        "Validation error",
        extra={
            "extra_fields": {
                "endpoint": request.url.path,
                "method": request.method,
                "errors": errors
            }
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Validation error",
                "code": "VALIDATION_ERROR",
                "details": {
                    "validation_errors": errors
                }
            }
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handler pour les exceptions HTTP standard

    Convertit les HTTPException en format JSON cohérent
    """
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "extra_fields": {
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": exc.status_code
            }
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "code": "HTTP_ERROR",
                "details": {"status_code": exc.status_code}
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler pour toutes les exceptions non gérées

    Logs l'erreur complète et retourne une erreur générique
    """
    log_exception(
        logger,
        exc,
        "Unhandled exception",
        endpoint=request.url.path,
        method=request.method
    )

    # En production, ne pas exposer les détails internes
    from api.config import settings

    if settings.is_production:
        message = "An internal error occurred"
        details = {}
    else:
        message = str(exc)
        details = {"exception_type": type(exc).__name__}

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": message,
                "code": "INTERNAL_ERROR",
                "details": details
            }
        }
    )


# ==============================================================================
# FONCTION D'INSTALLATION DES HANDLERS
# ==============================================================================

def install_error_handlers(app) -> None:
    """
    Installe tous les error handlers sur l'application FastAPI

    Args:
        app: Instance FastAPI

    Exemple:
        ```python
        from fastapi import FastAPI
        from api.exceptions import install_error_handlers

        app = FastAPI()
        install_error_handlers(app)
        ```
    """
    app.add_exception_handler(RAGSystemError, rag_system_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Error handlers installed successfully")


# ==============================================================================
# UTILITAIRES
# ==============================================================================

def raise_for_status(condition: bool, exception: RAGSystemError) -> None:
    """
    Raise une exception si la condition est False

    Args:
        condition: Condition à vérifier
        exception: Exception à lever si la condition est False

    Exemple:
        ```python
        from api.exceptions import raise_for_status, PositionNotFoundError

        position = get_position(ticker)
        raise_for_status(
            position is not None,
            PositionNotFoundError(ticker, user_id)
        )
        ```
    """
    if not condition:
        raise exception
