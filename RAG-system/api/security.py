"""
Module de gestion sécurisée des secrets pour Docker et développement local

Ce module implémente un système de lecture de secrets qui:
1. Priorité 1: Lit depuis /run/secrets/ (Docker Secrets en production)
2. Priorité 2: Fallback sur os.environ (développement local avec .env)
3. Validation et masquage automatique des secrets dans les logs

Sécurité:
- Aucun secret n'est jamais loggé en clair
- Validation des formats de clés API
- Permissions fichiers vérifiées (600) en production
- Support de la rotation des secrets sans redémarrage
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)

# Chemin des secrets Docker (standard Docker Swarm/Compose)
DOCKER_SECRETS_PATH = Path("/run/secrets")


class SecretNotFoundError(Exception):
    """Exception levée quand un secret obligatoire n'est pas trouvé"""
    pass


class SecretValidationError(Exception):
    """Exception levée quand un secret a un format invalide"""
    pass


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """
    Masque un secret pour le logging sécurisé

    Args:
        secret: Le secret à masquer
        visible_chars: Nombre de caractères visibles au début

    Returns:
        Secret masqué (ex: "sk-a***")

    Example:
        >>> mask_secret("sk-ant-1234567890")
        'sk-a***'
        >>> mask_secret("123456789:ABCdefGHI")
        '1234***'
    """
    if not secret:
        return "***EMPTY***"

    if len(secret) <= visible_chars:
        return "***"

    return f"{secret[:visible_chars]}***"


def validate_secret_format(name: str, value: str) -> None:
    """
    Valide le format d'un secret selon son type

    Args:
        name: Nom du secret (ex: "anthropic_api_key")
        value: Valeur du secret

    Raises:
        SecretValidationError: Si le format est invalide
    """
    if not value:
        return

    validations = {
        "anthropic_api_key": lambda v: v.startswith("sk-ant-"),
        "openai_api_key": lambda v: v.startswith("sk-"),
        "telegram_bot_token": lambda v: ":" in v and len(v.split(":")[0]) > 5,
        "jwt_secret_key": lambda v: len(v) >= 32,
        "api_password": lambda v: len(v) >= 8,
    }

    validator = validations.get(name)
    if validator and not validator(value):
        formats = {
            "anthropic_api_key": "doit commencer par 'sk-ant-'",
            "openai_api_key": "doit commencer par 'sk-'",
            "telegram_bot_token": "format attendu: '123456789:ABC...'",
            "jwt_secret_key": "doit contenir au moins 32 caractères",
            "api_password": "doit contenir au moins 8 caractères",
        }
        raise SecretValidationError(
            f"Secret '{name}' invalide: {formats.get(name, 'format incorrect')}"
        )


def check_secret_file_permissions(secret_path: Path) -> bool:
    """
    Vérifie les permissions d'un fichier secret (doit être 600 ou 400)

    Args:
        secret_path: Chemin du fichier secret

    Returns:
        True si les permissions sont sécurisées
    """
    try:
        stat_info = secret_path.stat()
        mode = stat_info.st_mode & 0o777

        # Permissions acceptables: 600 (rw-------) ou 400 (r--------)
        secure_modes = [0o600, 0o400]

        if mode not in secure_modes:
            logger.warning(
                f"Secret file {secret_path} has insecure permissions: {oct(mode)}. "
                f"Should be 600 or 400"
            )
            return False

        return True
    except Exception as e:
        logger.warning(f"Could not check permissions for {secret_path}: {e}")
        return False


@lru_cache(maxsize=128)
def get_secret(
    name: str,
    fallback_env: Optional[str] = None,
    required: bool = False,
    validate: bool = True
) -> Optional[str]:
    """
    Récupère un secret de manière sécurisée

    Ordre de priorité:
    1. /run/secrets/{name} (Docker Secrets)
    2. Variable d'environnement fallback_env ou name en UPPERCASE

    Args:
        name: Nom du secret (ex: "telegram_bot_token")
        fallback_env: Nom de la variable d'environnement (ex: "TELEGRAM_BOT_TOKEN")
        required: Si True, lève une exception si le secret n'existe pas
        validate: Si True, valide le format du secret

    Returns:
        Valeur du secret ou None

    Raises:
        SecretNotFoundError: Si required=True et secret non trouvé
        SecretValidationError: Si validate=True et format invalide

    Example:
        >>> # En production (Docker Secrets)
        >>> token = get_secret("telegram_bot_token", required=True)

        >>> # En développement (fallback .env)
        >>> key = get_secret("openai_api_key", fallback_env="OPENAI_API_KEY")
    """
    secret_value: Optional[str] = None
    source: str = ""

    # 1. Priorité: Docker Secrets (/run/secrets/)
    secret_path = DOCKER_SECRETS_PATH / name
    if secret_path.exists() and secret_path.is_file():
        try:
            # Vérifier les permissions en production
            if os.getenv("ENVIRONMENT", "development") == "production":
                check_secret_file_permissions(secret_path)

            secret_value = secret_path.read_text().strip()
            source = f"Docker Secret ({secret_path})"

            logger.info(
                f"Secret '{name}' loaded from Docker Secrets: {mask_secret(secret_value)}"
            )
        except Exception as e:
            logger.error(f"Error reading Docker Secret '{name}': {e}")

    # 2. Fallback: Variable d'environnement
    if not secret_value:
        env_var = fallback_env or name.upper()
        secret_value = os.getenv(env_var)

        if secret_value:
            source = f"Environment variable ({env_var})"
            logger.info(
                f"Secret '{name}' loaded from env: {mask_secret(secret_value)}"
            )

    # Validation du format
    if secret_value and validate:
        try:
            validate_secret_format(name, secret_value)
        except SecretValidationError as e:
            logger.error(f"Secret validation failed: {e}")
            if required:
                raise
            return None

    # Vérifier si le secret est requis
    if required and not secret_value:
        error_msg = (
            f"Required secret '{name}' not found. "
            f"Provide it via Docker Secret (/run/secrets/{name}) "
            f"or environment variable ({fallback_env or name.upper()})"
        )
        logger.error(error_msg)
        raise SecretNotFoundError(error_msg)

    return secret_value


def get_all_secrets() -> Dict[str, Optional[str]]:
    """
    Récupère tous les secrets définis pour l'application

    Returns:
        Dictionnaire {nom_secret: valeur_masquée}
        Les valeurs sont masquées pour le logging sécurisé

    Example:
        >>> secrets = get_all_secrets()
        >>> print(secrets)
        {
            'telegram_bot_token': '1234***',
            'anthropic_api_key': 'sk-a***',
            'openai_api_key': None,
            ...
        }
    """
    secret_names = [
        ("telegram_bot_token", "TELEGRAM_BOT_TOKEN"),
        ("anthropic_api_key", "ANTHROPIC_API_KEY"),
        ("openai_api_key", "OPENAI_API_KEY"),
        ("newsapi_key", "NEWSAPI_KEY"),
        ("jwt_secret_key", "JWT_SECRET_KEY"),
        ("api_password", "API_PASSWORD"),
    ]

    secrets = {}
    for name, env_var in secret_names:
        try:
            value = get_secret(name, fallback_env=env_var, required=False)
            secrets[name] = mask_secret(value) if value else None
        except Exception as e:
            logger.error(f"Error loading secret '{name}': {e}")
            secrets[name] = "***ERROR***"

    return secrets


def clear_secrets_cache():
    """
    Vide le cache des secrets

    Utile pour:
    - Rotation des secrets en production
    - Tests
    - Rechargement de configuration

    Example:
        >>> # Rotation d'un secret
        >>> clear_secrets_cache()
        >>> new_token = get_secret("telegram_bot_token", required=True)
    """
    get_secret.cache_clear()
    logger.info("Secrets cache cleared")


def validate_all_secrets(required_secrets: Optional[list] = None) -> tuple[bool, list[str]]:
    """
    Valide que tous les secrets requis sont présents et valides

    Args:
        required_secrets: Liste des secrets obligatoires
                         Si None, utilise une liste par défaut

    Returns:
        Tuple (est_valide, liste_erreurs)

    Example:
        >>> is_valid, errors = validate_all_secrets(["telegram_bot_token"])
        >>> if not is_valid:
        ...     print("\\n".join(errors))
    """
    if required_secrets is None:
        # Secrets minimum pour le fonctionnement de base
        required_secrets = ["telegram_bot_token"]

    errors = []

    for secret_name in required_secrets:
        try:
            # Tenter de charger le secret
            value = get_secret(
                secret_name,
                fallback_env=secret_name.upper(),
                required=True,
                validate=True
            )

            if not value:
                errors.append(f"Secret '{secret_name}' is empty")

        except SecretNotFoundError as e:
            errors.append(str(e))
        except SecretValidationError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Unexpected error loading '{secret_name}': {e}")

    return len(errors) == 0, errors


# Variables non-sensibles (peuvent rester dans .env public)
def get_public_config() -> dict:
    """
    Récupère les variables de configuration publiques (non-sensibles)

    Ces variables peuvent être versionnées et ne nécessitent pas Docker Secrets

    Returns:
        Dictionnaire de configuration publique
    """
    return {
        "api_base_url": os.getenv("API_BASE_URL", "http://api:8000"),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "api_username": os.getenv("API_USERNAME", "admin"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
    }


if __name__ == "__main__":
    # Test du module (mode développement uniquement)
    print("=== Test du module de sécurité ===\n")

    print("1. Configuration publique:")
    public_config = get_public_config()
    for key, value in public_config.items():
        print(f"  - {key}: {value}")

    print("\n2. Secrets (masqués):")
    secrets = get_all_secrets()
    for key, value in secrets.items():
        status = "✓ OK" if value and value != "***ERROR***" else "✗ Missing"
        print(f"  - {key}: {value or 'None'} [{status}]")

    print("\n3. Validation des secrets requis:")
    is_valid, validation_errors = validate_all_secrets()
    if is_valid:
        print("  ✓ Tous les secrets requis sont valides")
    else:
        print("  ✗ Erreurs de validation:")
        for error in validation_errors:
            print(f"    - {error}")
