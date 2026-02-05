"""
Module d'authentification JWT pour usage personnel
"""

from datetime import datetime, timedelta
from typing import Optional
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# Configuration JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 30  # Usage personnel - token longue durée

# Credentials (single user)
API_USERNAME = os.getenv("API_USERNAME", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "changeme")

# Security scheme
security = HTTPBearer()


def create_access_token(username: str) -> str:
    """
    Génère un token JWT pour l'utilisateur

    Args:
        username: Nom d'utilisateur

    Returns:
        Token JWT signé
    """
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[str]:
    """
    Vérifie la validité d'un token JWT

    Args:
        token: Token JWT à vérifier

    Returns:
        Username si token valide, None sinon
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            return None

        return username

    except JWTError:
        return None


def authenticate_user(username: str, password: str) -> bool:
    """
    Vérifie les credentials utilisateur

    Args:
        username: Nom d'utilisateur
        password: Mot de passe

    Returns:
        True si credentials valides, False sinon
    """
    return username == API_USERNAME and password == API_PASSWORD


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency FastAPI pour extraire et valider le JWT

    Args:
        credentials: Credentials Bearer automatiquement extraites

    Returns:
        Username de l'utilisateur authentifié

    Raises:
        HTTPException: Si token invalide ou manquant
    """
    token = credentials.credentials

    username = verify_token(token)

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return username


def get_token_info(token: str) -> dict:
    """
    Récupère les informations du token sans validation stricte de l'expiration
    Utile pour le debugging

    Args:
        token: Token JWT

    Returns:
        Payload du token ou dict vide si erreur
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False}  # Ne pas vérifier l'expiration pour le debug
        )
        return payload
    except JWTError:
        return {}
