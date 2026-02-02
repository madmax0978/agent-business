"""
Circuit Breaker Pattern pour la résilience des services externes

Ce module implémente le pattern Circuit Breaker pour protéger l'application
contre les défaillances en cascade lors d'appels à des services externes (Ollama, APIs, etc.)

Le circuit breaker a 3 états :
- CLOSED: Tout fonctionne normalement, les requêtes passent
- OPEN: Trop d'échecs détectés, les requêtes sont bloquées
- HALF_OPEN: Phase de test pour voir si le service est rétabli
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Callable, TypeVar, Any, Optional
from datetime import datetime, timedelta
from threading import Lock

from api.logging_config import get_logger


logger = get_logger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """États possibles du circuit breaker"""
    CLOSED = "closed"        # Tout va bien, les appels passent
    OPEN = "open"            # Trop d'erreurs, on bloque les appels
    HALF_OPEN = "half_open"  # On teste si le service est revenu


class CircuitBreakerOpenError(Exception):
    """
    Exception levée quand le circuit breaker est ouvert

    Attributes:
        retry_after: Nombre de secondes avant de pouvoir réessayer
        failure_count: Nombre d'échecs qui ont causé l'ouverture
    """

    def __init__(self, retry_after: int, failure_count: int):
        self.retry_after = retry_after
        self.failure_count = failure_count
        super().__init__(
            f"Circuit breaker is OPEN. "
            f"Service unavailable after {failure_count} failures. "
            f"Retry after {retry_after} seconds."
        )


class CircuitBreaker:
    """
    Implémentation du pattern Circuit Breaker

    Le circuit breaker surveille les appels à un service externe et bascule
    automatiquement entre les états CLOSED, OPEN et HALF_OPEN selon les échecs.

    Attributes:
        failure_threshold: Nombre d'échecs avant d'ouvrir le circuit
        timeout: Temps d'attente en secondes avant de réessayer (état OPEN)
        half_open_max_calls: Nombre d'appels de test en état HALF_OPEN
        expected_exceptions: Tuple d'exceptions considérées comme des échecs

    Example:
        >>> circuit_breaker = CircuitBreaker(
        ...     failure_threshold=3,
        ...     timeout=60,
        ...     name="OllamaService"
        ... )
        >>>
        >>> @circuit_breaker.protect
        ... def call_ollama():
        ...     return requests.post("http://localhost:11434/api/generate", ...)
        >>>
        >>> # Ou utilisation directe
        >>> result = circuit_breaker.call(risky_function, arg1, arg2)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_max_calls: int = 3,
        expected_exceptions: tuple[type[Exception], ...] = (Exception,),
        name: str = "CircuitBreaker"
    ):
        """
        Initialise le circuit breaker

        Args:
            failure_threshold: Nombre d'échecs consécutifs avant d'ouvrir
            timeout: Temps d'attente en secondes avant de passer en HALF_OPEN
            half_open_max_calls: Nombre d'appels de test en HALF_OPEN
            expected_exceptions: Exceptions à intercepter (default: toutes)
            name: Nom du circuit breaker pour les logs
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exceptions = expected_exceptions
        self.name = name

        # État du circuit
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

        # Thread safety
        self._lock = Lock()

        logger.info(
            f"Circuit breaker '{name}' initialized",
            extra={
                "extra_fields": {
                    "failure_threshold": failure_threshold,
                    "timeout": timeout,
                    "half_open_max_calls": half_open_max_calls
                }
            }
        )

    @property
    def state(self) -> CircuitState:
        """Retourne l'état actuel du circuit"""
        return self._state

    @property
    def failure_count(self) -> int:
        """Retourne le nombre d'échecs consécutifs"""
        return self._failure_count

    @property
    def is_closed(self) -> bool:
        """Vérifie si le circuit est fermé (état normal)"""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Vérifie si le circuit est ouvert (service indisponible)"""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Vérifie si le circuit est en test (half-open)"""
        return self._state == CircuitState.HALF_OPEN

    def _transition_to_open(self) -> None:
        """Transition vers l'état OPEN"""
        with self._lock:
            self._state = CircuitState.OPEN
            self._last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker '{self.name}' transitioned to OPEN",
                extra={
                    "extra_fields": {
                        "failure_count": self._failure_count,
                        "threshold": self.failure_threshold
                    }
                }
            )

    def _transition_to_half_open(self) -> None:
        """Transition vers l'état HALF_OPEN"""
        with self._lock:
            self._state = CircuitState.HALF_OPEN
            self._half_open_calls = 0

            logger.info(
                f"Circuit breaker '{self.name}' transitioned to HALF_OPEN",
                extra={
                    "extra_fields": {
                        "downtime_seconds": time.time() - self._last_failure_time
                        if self._last_failure_time else 0
                    }
                }
            )

    def _transition_to_closed(self) -> None:
        """Transition vers l'état CLOSED"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0

            logger.info(
                f"Circuit breaker '{self.name}' transitioned to CLOSED",
                extra={"extra_fields": {"status": "service_recovered"}}
            )

    def _should_attempt_reset(self) -> bool:
        """
        Vérifie si on doit tenter de réinitialiser le circuit

        Returns:
            True si le timeout est écoulé et qu'on peut passer en HALF_OPEN
        """
        if not self._last_failure_time:
            return False

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.timeout

    def _record_success(self) -> None:
        """Enregistre un succès"""
        with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                self._half_open_calls += 1

                # Si tous les appels de test réussissent, on ferme le circuit
                if self._success_count >= self.half_open_max_calls:
                    self._transition_to_closed()

            elif self._state == CircuitState.CLOSED:
                # Succès en état normal, rien de spécial
                pass

    def _record_failure(self, exception: Exception) -> None:
        """
        Enregistre un échec

        Args:
            exception: Exception qui a causé l'échec
        """
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            logger.warning(
                f"Circuit breaker '{self.name}' recorded failure",
                extra={
                    "extra_fields": {
                        "failure_count": self._failure_count,
                        "threshold": self.failure_threshold,
                        "exception_type": type(exception).__name__,
                        "exception_message": str(exception)
                    }
                }
            )

            if self._state == CircuitState.HALF_OPEN:
                # Échec en test : on réouvre immédiatement
                self._transition_to_open()

            elif self._failure_count >= self.failure_threshold:
                # Trop d'échecs : on ouvre le circuit
                self._transition_to_open()

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Exécute une fonction avec protection circuit breaker

        Args:
            func: Fonction à appeler
            *args: Arguments positionnels
            **kwargs: Arguments nommés

        Returns:
            Résultat de la fonction

        Raises:
            CircuitBreakerOpenError: Si le circuit est ouvert
            Exception: Exception originale si l'appel échoue

        Example:
            >>> cb = CircuitBreaker(name="API")
            >>> result = cb.call(requests.get, "https://api.example.com")
        """
        # Vérifier l'état du circuit
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                retry_after = int(self.timeout - (time.time() - self._last_failure_time))
                raise CircuitBreakerOpenError(retry_after, self._failure_count)

        elif self._state == CircuitState.HALF_OPEN:
            with self._lock:
                self._half_open_calls += 1
                if self._half_open_calls > self.half_open_max_calls:
                    # Trop d'appels en half-open, on réouvre
                    self._transition_to_open()
                    raise CircuitBreakerOpenError(self.timeout, self._failure_count)

        # Tenter l'appel
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result

        except self.expected_exceptions as e:
            self._record_failure(e)
            raise

    def protect(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Décorateur pour protéger une fonction avec le circuit breaker

        Args:
            func: Fonction à protéger

        Returns:
            Fonction décorée

        Example:
            >>> cb = CircuitBreaker(name="Database")
            >>>
            >>> @cb.protect
            ... def query_database(query):
            ...     return db.execute(query)
        """
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return self.call(func, *args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    def call_with_fallback(
        self,
        func: Callable[..., T],
        fallback: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Exécute une fonction avec fallback automatique si le circuit est ouvert

        Args:
            func: Fonction principale
            fallback: Fonction de secours si le circuit est ouvert
            *args: Arguments positionnels
            **kwargs: Arguments nommés

        Returns:
            Résultat de func ou de fallback

        Example:
            >>> cb = CircuitBreaker(name="API")
            >>>
            >>> def get_data_from_api():
            ...     return requests.get("https://api.example.com").json()
            >>>
            >>> def get_cached_data():
            ...     return {"cached": True}
            >>>
            >>> result = cb.call_with_fallback(get_data_from_api, get_cached_data)
        """
        try:
            return self.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            logger.info(
                f"Circuit breaker '{self.name}' is OPEN, using fallback",
                extra={"extra_fields": {"fallback": fallback.__name__}}
            )
            return fallback(*args, **kwargs)

    def reset(self) -> None:
        """
        Réinitialise manuellement le circuit breaker

        Utile pour les tests ou les interventions manuelles
        """
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._last_failure_time = None

            logger.info(f"Circuit breaker '{self.name}' manually reset")

    def get_stats(self) -> dict[str, Any]:
        """
        Retourne les statistiques du circuit breaker

        Returns:
            Dictionnaire avec les métriques

        Example:
            >>> cb = CircuitBreaker(name="Service")
            >>> stats = cb.get_stats()
            >>> print(f"State: {stats['state']}, Failures: {stats['failure_count']}")
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "timeout": self.timeout,
            "last_failure_time": datetime.fromtimestamp(self._last_failure_time).isoformat()
            if self._last_failure_time else None,
            "time_until_half_open": max(
                0,
                int(self.timeout - (time.time() - self._last_failure_time))
            ) if self._last_failure_time and self._state == CircuitState.OPEN else None
        }
