"""
Middleware FastAPI pour le système RAG-PEA

Ce module fournit :
- Request ID tracking pour tracer les requêtes
- Logging automatique de toutes les requêtes/réponses
- Mesure des temps de réponse
- Rate limiting basique
- CORS amélioré avec configuration flexible
"""

from __future__ import annotations

import time
import uuid
from typing import Callable
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from api.config import settings
from api.logging_config import get_logger, set_request_context, clear_request_context, log_performance


logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour ajouter un ID unique à chaque requête

    L'ID est disponible dans :
    - Les logs (automatiquement via le contexte)
    - Les headers de réponse (X-Request-ID)
    - Le state de la requête (request.state.request_id)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Traite la requête en ajoutant un request ID

        Args:
            request: Requête FastAPI
            call_next: Fonction suivante dans la chaîne

        Returns:
            Réponse avec header X-Request-ID
        """
        # Générer ou récupérer un request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Stocker dans le state de la requête
        request.state.request_id = request_id

        # Configurer le contexte de logging
        user_id = request.headers.get("X-User-ID", "anonymous")
        endpoint = f"{request.method} {request.url.path}"

        set_request_context(
            request_id=request_id,
            user_id=user_id,
            endpoint=endpoint
        )

        try:
            # Traiter la requête
            response = await call_next(request)

            # Ajouter le request ID dans les headers de réponse
            response.headers["X-Request-ID"] = request_id

            return response

        finally:
            # Nettoyer le contexte
            clear_request_context()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour logger toutes les requêtes et réponses

    Logs :
    - Méthode HTTP, endpoint, query params
    - Temps de traitement
    - Code de statut HTTP
    - Taille de la réponse
    - IP du client
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Traite la requête en loggant les informations

        Args:
            request: Requête FastAPI
            call_next: Fonction suivante dans la chaîne

        Returns:
            Réponse de l'API
        """
        # Capturer le début du traitement
        start_time = time.time()

        # Informations de la requête
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        # Logger la requête entrante
        logger.info(
            f"Incoming request: {method} {path}",
            extra={
                "extra_fields": {
                    "client_ip": client_ip,
                    "query_params": query_params,
                    "user_agent": request.headers.get("user-agent", "unknown")
                }
            }
        )

        # Traiter la requête
        try:
            response = await call_next(request)

            # Calculer le temps de traitement
            duration_ms = (time.time() - start_time) * 1000

            # Logger la réponse
            log_performance(
                logger,
                operation=f"{method} {path}",
                duration_ms=duration_ms,
                success=response.status_code < 400,
                status_code=response.status_code,
                client_ip=client_ip
            )

            # Ajouter des headers de performance
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            return response

        except Exception as e:
            # Logger l'erreur
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                f"Request failed: {method} {path}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "duration_ms": duration_ms,
                        "client_ip": client_ip,
                        "exception_type": type(e).__name__
                    }
                }
            )

            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting basique

    Limite le nombre de requêtes par IP sur une période donnée.
    Pour une solution production, utiliser Redis + SlowAPI ou similar.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        """
        Initialise le rate limiter

        Args:
            app: Application FastAPI
            requests_per_minute: Nombre de requêtes autorisées par minute
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

        logger.info(
            f"Rate limiter initialized: {requests_per_minute} requests/minute",
            extra={"extra_fields": {"rate_limit": requests_per_minute}}
        )

    def _clean_old_requests(self, ip: str, current_time: float) -> None:
        """
        Nettoie les requêtes anciennes (> 1 minute)

        Args:
            ip: Adresse IP
            current_time: Timestamp actuel
        """
        cutoff_time = current_time - 60  # 1 minute
        self.requests[ip] = [
            req_time for req_time in self.requests[ip]
            if req_time > cutoff_time
        ]

    def _is_rate_limited(self, ip: str) -> bool:
        """
        Vérifie si l'IP est rate limitée

        Args:
            ip: Adresse IP

        Returns:
            True si rate limitée, False sinon
        """
        current_time = time.time()

        # Nettoyer les anciennes requêtes
        self._clean_old_requests(ip, current_time)

        # Vérifier le nombre de requêtes
        return len(self.requests[ip]) >= self.requests_per_minute

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Traite la requête avec rate limiting

        Args:
            request: Requête FastAPI
            call_next: Fonction suivante dans la chaîne

        Returns:
            Réponse ou erreur 429 si rate limité
        """
        # Désactiver rate limiting si configuré
        if not settings.rate_limit.enabled:
            return await call_next(request)

        # Obtenir l'IP du client
        client_ip = request.client.host if request.client else "unknown"

        # Vérifier le rate limit
        if self._is_rate_limited(client_ip):
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip}",
                extra={
                    "extra_fields": {
                        "endpoint": request.url.path,
                        "requests_count": len(self.requests[client_ip])
                    }
                }
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "message": "Rate limit exceeded",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "details": {
                            "limit": self.requests_per_minute,
                            "window": "1 minute",
                            "retry_after": 60
                        }
                    }
                },
                headers={"Retry-After": "60"}
            )

        # Enregistrer la requête
        self.requests[client_ip].append(time.time())

        # Traiter la requête
        response = await call_next(request)

        # Ajouter les headers de rate limit
        remaining = self.requests_per_minute - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour ajouter des headers de sécurité

    Headers ajoutés :
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security (HSTS)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Ajoute les headers de sécurité à la réponse

        Args:
            request: Requête FastAPI
            call_next: Fonction suivante dans la chaîne

        Returns:
            Réponse avec headers de sécurité
        """
        response = await call_next(request)

        # Headers de sécurité
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS (seulement en HTTPS/production)
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


def setup_middleware(app) -> None:
    """
    Configure tous les middlewares sur l'application FastAPI

    Args:
        app: Instance FastAPI

    Example:
        ```python
        from fastapi import FastAPI
        from api.middleware import setup_middleware

        app = FastAPI()
        setup_middleware(app)
        ```
    """
    # CORS (doit être ajouté en premier)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_credentials=settings.cors.allow_credentials,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Rate limiting
    if settings.rate_limit.enabled:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.rate_limit.requests_per_minute
        )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # Request ID (doit être en dernier pour que l'ID soit disponible partout)
    app.add_middleware(RequestIDMiddleware)

    logger.info(
        "All middlewares configured successfully",
        extra={
            "extra_fields": {
                "rate_limit_enabled": settings.rate_limit.enabled,
                "cors_origins": settings.cors.allow_origins,
                "environment": settings.environment
            }
        }
    )
