"""
Modèles Pydantic pour l'API RAG
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    """Modèle pour l'upload de document"""
    document_name: str = Field(..., description="Nom du document")
    file_path: str = Field(..., description="Chemin vers le fichier PDF")
    collection_name: Optional[str] = Field(None, description="Nom de la collection (auto-généré si non fourni)")


class QueryRequest(BaseModel):
    """Modèle pour une requête RAG"""
    question: str = Field(..., description="Question à poser au système RAG")
    collection_name: str = Field(..., description="Nom de la collection à interroger")
    n_results: int = Field(5, description="Nombre de chunks à récupérer", ge=1, le=20)
    filter_tables: Optional[bool] = Field(None, description="Filtrer uniquement les tableaux (True) ou le texte (False)")
    generate_answer: bool = Field(True, description="Générer une réponse avec LLM")


class ChunkResponse(BaseModel):
    """Modèle pour un chunk retourné"""
    chunk_id: int
    text: str
    score: float
    content_type: str
    num_tokens: int
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    """Modèle pour la réponse à une requête"""
    question: str
    answer: Optional[str] = None
    chunks: List[ChunkResponse]
    collection_name: str
    processing_time: float


class CollectionInfo(BaseModel):
    """Informations sur une collection"""
    name: str
    total_chunks: int
    table_chunks: int
    text_chunks: int
    table_percentage: float
    document_name: Optional[str] = None


class HealthResponse(BaseModel):
    """Réponse de santé de l'API"""
    status: str
    ollama_available: bool
    collections: List[str]
    version: str


class IndexingResponse(BaseModel):
    """Réponse après indexation d'un document"""
    success: bool
    collection_name: str
    total_chunks: int
    table_chunks: int
    text_chunks: int
    message: str


class FinancialAnalysisRequest(BaseModel):
    """Requête pour une analyse financière"""
    companies: List[str] = Field(..., description="Liste des entreprises à analyser", min_items=1)
    collections: List[str] = Field(..., description="Collections RAG correspondantes", min_items=1)
    portfolio: Optional[Dict[str, Any]] = Field(None, description="Portefeuille actuel (optionnel)")


class FinancialAnalysisResponse(BaseModel):
    """Réponse d'analyse financière"""
    report: str = Field(..., description="Rapport d'analyse complet")
    companies_analyzed: List[str]
    processing_time: float
    timestamp: str


class PortfolioBuildRequest(BaseModel):
    """Requête pour construire un portefeuille PEA optimal de zéro"""
    budget: float = Field(..., description="Budget total disponible pour investir (en euros)", gt=0)
    risk_profile: str = Field(
        "balanced",
        description="Profil de risque: 'conservative' (prudent), 'balanced' (équilibré), 'aggressive' (dynamique)"
    )
    sectors: Optional[List[str]] = Field(
        None,
        description="Secteurs préférés (optionnel). Ex: ['luxe', 'technologie', 'santé']"
    )
    exclude_companies: Optional[List[str]] = Field(
        None,
        description="Entreprises à exclure de l'analyse (optionnel)"
    )
    min_companies: int = Field(5, description="Nombre minimum d'entreprises dans le portefeuille", ge=3, le=15)
    max_companies: int = Field(10, description="Nombre maximum d'entreprises dans le portefeuille", ge=5, le=20)


class PortfolioBuildResponse(BaseModel):
    """Réponse avec le plan de construction de portefeuille optimal"""
    action_plan: str = Field(..., description="Plan d'action détaillé pour construire le portefeuille")
    budget: float
    risk_profile: str
    processing_time: float
    timestamp: str
    data_collected: bool = Field(..., description="Indique si les données ont été collectées automatiquement")


class PositionAddRequest(BaseModel):
    """Requête pour ajouter une position au portefeuille"""
    ticker: str = Field(..., description="Ticker de l'action (ex: MC.PA)")
    company_name: str = Field(..., description="Nom de l'entreprise (ex: LVMH)")
    quantity: float = Field(..., description="Nombre d'actions à acheter", gt=0)
    price: float = Field(..., description="Prix d'achat unitaire", gt=0)
    user_id: str = Field("default_user", description="ID de l'utilisateur")


class PositionSellRequest(BaseModel):
    """Requête pour vendre une position"""
    ticker: str = Field(..., description="Ticker de l'action à vendre")
    quantity: float = Field(..., description="Nombre d'actions à vendre", gt=0)
    price: float = Field(..., description="Prix de vente unitaire", gt=0)
    user_id: str = Field("default_user", description="ID de l'utilisateur")


# ==========================================
# AUTH MODELS
# ==========================================

class LoginRequest(BaseModel):
    """Requête de login"""
    username: str = Field(..., description="Nom d'utilisateur")
    password: str = Field(..., description="Mot de passe")


class TokenResponse(BaseModel):
    """Réponse contenant le token JWT"""
    access_token: str = Field(..., description="Token JWT")
    token_type: str = Field("bearer", description="Type de token")
    expires_in_days: int = Field(30, description="Durée de validité en jours")


class TokenVerifyResponse(BaseModel):
    """Réponse de vérification de token"""
    valid: bool = Field(..., description="Token valide ou non")
    username: Optional[str] = Field(None, description="Nom d'utilisateur si token valide")
    expires_at: Optional[str] = Field(None, description="Date d'expiration du token")
