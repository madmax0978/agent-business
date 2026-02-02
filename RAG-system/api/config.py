"""
Configuration centralisée avec Pydantic Settings pour le système RAG-PEA

Ce module gère toute la configuration de l'application avec :
- Chargement automatique des variables d'environnement
- Validation automatique des types et valeurs
- Valeurs par défaut intelligentes
- Type hints complets pour l'autocomplétion IDE
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional
from pydantic import Field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Configuration de la base de données"""

    url: str = Field(
        default="sqlite:///./data/portfolio.db",
        description="URL de connexion à la base de données"
    )
    echo: bool = Field(
        default=False,
        description="Activer les logs SQL (debug uniquement)"
    )

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False
    )


class OllamaSettings(BaseSettings):
    """Configuration d'Ollama pour la génération de réponses"""

    url: str = Field(
        default="http://localhost:11434",
        description="URL du serveur Ollama"
    )
    model: str = Field(
        default="llama3.2:3b",
        description="Modèle Ollama à utiliser"
    )
    timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Timeout en secondes pour les requêtes Ollama"
    )
    max_tokens: int = Field(
        default=500,
        ge=100,
        le=4096,
        description="Nombre maximum de tokens dans les réponses"
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Température pour la génération (0=déterministe, 2=créatif)"
    )

    model_config = SettingsConfigDict(
        env_prefix="OLLAMA_",
        case_sensitive=False
    )


class ChromaDBSettings(BaseSettings):
    """Configuration de ChromaDB pour le stockage vectoriel"""

    persist_directory: str = Field(
        default="./data/chroma_db",
        description="Répertoire de persistance ChromaDB"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Modèle d'embeddings Sentence Transformers"
    )
    collection_metadata: dict = Field(
        default_factory=lambda: {"hnsw:space": "cosine"},
        description="Métadonnées par défaut pour les collections"
    )

    model_config = SettingsConfigDict(
        env_prefix="CHROMA_",
        case_sensitive=False
    )


class YahooFinanceSettings(BaseSettings):
    """Configuration de Yahoo Finance"""

    enabled: bool = Field(
        default=True,
        description="Activer le service Yahoo Finance"
    )
    cache_ttl: int = Field(
        default=300,
        ge=0,
        description="Durée de vie du cache en secondes (0=désactivé)"
    )
    max_cache_size: int = Field(
        default=128,
        ge=0,
        description="Taille maximale du cache LRU (0=illimité)"
    )
    request_timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Timeout pour les requêtes Yahoo Finance"
    )

    model_config = SettingsConfigDict(
        env_prefix="YAHOO_FINANCE_",
        case_sensitive=False
    )


class APISettings(BaseSettings):
    """Configuration des clés API externes"""

    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Clé API Anthropic Claude"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="Clé API OpenAI"
    )
    news_api_key: Optional[str] = Field(
        default=None,
        description="Clé API NewsAPI"
    )
    serpapi_key: Optional[str] = Field(
        default=None,
        description="Clé API SerpAPI"
    )
    telegram_bot_token: Optional[str] = Field(
        default=None,
        description="Token du bot Telegram"
    )
    telegram_chat_id: Optional[str] = Field(
        default=None,
        description="Chat ID Telegram pour les notifications"
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False
    )

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Valide que la clé Anthropic commence par sk-ant-"""
        if v and not v.startswith("sk-ant-"):
            raise ValueError("La clé Anthropic doit commencer par 'sk-ant-'")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Valide que la clé OpenAI commence par sk-"""
        if v and not v.startswith("sk-"):
            raise ValueError("La clé OpenAI doit commencer par 'sk-'")
        return v


class LoggingSettings(BaseSettings):
    """Configuration du système de logging"""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Niveau de log"
    )
    format: Literal["json", "text"] = Field(
        default="json",
        description="Format des logs (json pour production, text pour dev)"
    )
    file_path: Optional[str] = Field(
        default="./logs/app.log",
        description="Chemin du fichier de logs (None=console uniquement)"
    )
    max_bytes: int = Field(
        default=10485760,
        ge=1024,
        description="Taille maximale du fichier de logs en bytes (10MB par défaut)"
    )
    backup_count: int = Field(
        default=5,
        ge=0,
        description="Nombre de fichiers de backup à conserver"
    )
    log_sql_queries: bool = Field(
        default=False,
        description="Logger les requêtes SQL (debug uniquement)"
    )

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        case_sensitive=False
    )


class CircuitBreakerSettings(BaseSettings):
    """Configuration du circuit breaker pour Ollama"""

    failure_threshold: int = Field(
        default=5,
        ge=1,
        description="Nombre d'échecs avant d'ouvrir le circuit"
    )
    timeout: int = Field(
        default=60,
        ge=10,
        description="Temps d'attente avant de réessayer (secondes)"
    )
    half_open_max_calls: int = Field(
        default=3,
        ge=1,
        description="Nombre de tentatives en mode half-open"
    )

    model_config = SettingsConfigDict(
        env_prefix="CIRCUIT_BREAKER_",
        case_sensitive=False
    )


class CORSSettings(BaseSettings):
    """Configuration CORS pour l'API"""

    allow_origins: list[str] = Field(
        default=["*"],
        description="Origines autorisées pour CORS"
    )
    allow_credentials: bool = Field(
        default=True,
        description="Autoriser les credentials dans les requêtes CORS"
    )
    allow_methods: list[str] = Field(
        default=["*"],
        description="Méthodes HTTP autorisées"
    )
    allow_headers: list[str] = Field(
        default=["*"],
        description="Headers autorisés"
    )

    model_config = SettingsConfigDict(
        env_prefix="CORS_",
        case_sensitive=False
    )


class RateLimitSettings(BaseSettings):
    """Configuration du rate limiting"""

    enabled: bool = Field(
        default=True,
        description="Activer le rate limiting"
    )
    requests_per_minute: int = Field(
        default=120,
        ge=1,
        description="Nombre de requêtes autorisées par minute"
    )
    requests_per_hour: int = Field(
        default=1000,
        ge=1,
        description="Nombre de requêtes autorisées par heure"
    )

    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        case_sensitive=False
    )


class Settings(BaseSettings):
    """
    Configuration principale de l'application RAG-PEA

    Toutes les sous-configurations sont accessibles via des propriétés.
    Les variables d'environnement sont chargées automatiquement depuis .env

    Exemple d'utilisation:
        ```python
        from api.config import settings

        # Accéder à une configuration
        print(settings.database.url)
        print(settings.ollama.model)

        # Vérifier si une API est configurée
        if settings.api.anthropic_api_key:
            # Utiliser Claude
            pass
        ```
    """

    # Métadonnées de l'application
    app_name: str = Field(
        default="RAG-PEA Financial Analysis System",
        description="Nom de l'application"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Version de l'application"
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environnement d'exécution"
    )
    debug: bool = Field(
        default=False,
        description="Mode debug (activer les logs verbeux)"
    )

    # Configuration serveur
    api_host: str = Field(
        default="0.0.0.0",
        description="Host de l'API"
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port de l'API"
    )
    reload: bool = Field(
        default=True,
        description="Recharger automatiquement l'API au changement de code (dev uniquement)"
    )

    # Chemins
    upload_dir: Path = Field(
        default=Path("./data/uploads"),
        description="Répertoire pour les fichiers uploadés"
    )
    logs_dir: Path = Field(
        default=Path("./logs"),
        description="Répertoire pour les logs"
    )

    # Sous-configurations
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    chromadb: ChromaDBSettings = Field(default_factory=ChromaDBSettings)
    yahoo_finance: YahooFinanceSettings = Field(default_factory=YahooFinanceSettings)
    api_keys: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    circuit_breaker: CircuitBreakerSettings = Field(default_factory=CircuitBreakerSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        """Vérifie si l'environnement est production"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Vérifie si l'environnement est development"""
        return self.environment == "development"

    def create_directories(self) -> None:
        """Crée les répertoires nécessaires s'ils n'existent pas"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Créer le répertoire pour ChromaDB
        Path(self.chromadb.persist_directory).mkdir(parents=True, exist_ok=True)

        # Créer le répertoire pour la base de données
        if self.database.url.startswith("sqlite"):
            db_path = self.database.url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def model_dump_safe(self) -> dict:
        """
        Exporte la configuration en masquant les secrets

        Utile pour le logging et le debugging
        """
        config_dict = self.model_dump()

        # Masquer les clés API
        if config_dict.get("api_keys"):
            for key in config_dict["api_keys"]:
                if config_dict["api_keys"][key]:
                    config_dict["api_keys"][key] = "***HIDDEN***"

        return config_dict


# Instance globale de la configuration
# À importer dans les autres modules : from api.config import settings
settings = Settings()

# Créer les répertoires au démarrage
settings.create_directories()


# Fonction utilitaire pour recharger la configuration
def reload_settings() -> Settings:
    """
    Recharge la configuration depuis le fichier .env

    Utile pour les tests ou le rechargement à chaud
    """
    global settings
    settings = Settings()
    settings.create_directories()
    return settings


# Fonction de validation de la configuration
def validate_configuration() -> tuple[bool, list[str]]:
    """
    Valide que la configuration minimale est présente

    Returns:
        Tuple (est_valide, liste_des_erreurs)
    """
    errors = []

    # Vérifier qu'au moins une clé IA est configurée
    if not settings.api_keys.anthropic_api_key and not settings.api_keys.openai_api_key:
        errors.append(
            "Aucune clé API IA configurée. "
            "Configurez ANTHROPIC_API_KEY ou OPENAI_API_KEY dans .env"
        )

    # Vérifier que les répertoires peuvent être créés
    try:
        settings.create_directories()
    except Exception as e:
        errors.append(f"Impossible de créer les répertoires nécessaires: {e}")

    # Vérifier les valeurs critiques
    if settings.ollama.timeout < 5:
        errors.append("OLLAMA_TIMEOUT doit être >= 5 secondes")

    if settings.yahoo_finance.cache_ttl < 0:
        errors.append("YAHOO_FINANCE_CACHE_TTL ne peut pas être négatif")

    return len(errors) == 0, errors


# Validation au démarrage (en mode développement)
if settings.is_development:
    is_valid, validation_errors = validate_configuration()
    if not is_valid:
        import warnings
        for error in validation_errors:
            warnings.warn(f"Configuration warning: {error}", UserWarning)
