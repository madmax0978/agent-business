"""
API FastAPI pour le système RAG multi-documents
"""

import time
import re
from typing import List, Optional
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# NOUVEAUX IMPORTS - Améliorations production-ready
from config import settings
from logging_config import get_logger
from exceptions import install_error_handlers
from middleware import setup_middleware

from models import (
    QueryRequest,
    QueryResponse,
    ChunkResponse,
    CollectionInfo,
    HealthResponse,
    IndexingResponse,
    DocumentUpload,
    FinancialAnalysisRequest,
    FinancialAnalysisResponse,
    PortfolioBuildRequest,
    PortfolioBuildResponse,
    PositionAddRequest,
    PositionSellRequest,
)
# Import RAG Manager v2 optimisé (v2 uniquement, pas de fallback v1)
from rag_manager_v2 import OptimizedRAGManager as RAGManager
_rag_version = "v2 (optimisé)"
from agents.financial_crew import generate_financial_report
from agents.portfolio_builder_crew import build_optimal_pea_portfolio
from datetime import datetime

# Import des nouveaux services
from database.portfolio_db import PortfolioDatabase
from services.portfolio_manager import PortfolioManager
from services.yahoo_finance_service import YahooFinanceService, get_ticker
from services.sentiment_analyzer import SentimentAnalyzer
from services.news_aggregator import NewsAggregator
from services.technical_analysis import TechnicalAnalyzer

# Logger au lieu de print
logger = get_logger(__name__)

__version__ = "1.1.0"

# Initialiser l'API avec configuration
app = FastAPI(
    title=settings.app_name,
    description="API pour l'analyse de documents avec RAG et Ollama",
    version=__version__,
)

# INSTALLER LES MIDDLEWARES (CRITIQUE - doit être fait AVANT le CORS)
setup_middleware(app)

# CORS (après les middlewares personnalisés)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# INSTALLER LES ERROR HANDLERS (CRITIQUE)
install_error_handlers(app)

# Initialiser le gestionnaire RAG
rag_manager = RAGManager()
logger.info(f"RAG Manager {_rag_version} initialized successfully")

# Dossier pour les uploads (utiliser settings)
UPLOAD_DIR = settings.upload_dir
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"Upload directory configured: {UPLOAD_DIR}")


def sanitize_collection_name(name: str) -> str:
    """
    Nettoie le nom de collection pour respecter le format ChromaDB requis:
    - 3-512 caractères
    - Uniquement [a-zA-Z0-9._-]
    - Commence et finit par [a-zA-Z0-9]

    Args:
        name: Nom brut à nettoyer

    Returns:
        Nom nettoyé et valide pour ChromaDB
    """
    # Remplacer espaces par underscore
    name = name.replace(" ", "_")

    # Supprimer les accents (é → e, à → a, etc.)
    import unicodedata
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ASCII', 'ignore').decode('ASCII')

    # Garder seulement les caractères autorisés [a-zA-Z0-9._-]
    name = re.sub(r'[^a-zA-Z0-9._-]', '', name)

    # Supprimer les underscores/points/tirets multiples consécutifs
    name = re.sub(r'[._-]+', '_', name)

    # S'assurer que le nom commence et finit par [a-zA-Z0-9]
    name = name.strip('._-')

    # S'assurer que le nom fait au moins 3 caractères
    if len(name) < 3:
        name = f"doc_{name}_001"

    # Limiter à 512 caractères
    if len(name) > 512:
        name = name[:512].rstrip('._-')

    return name


@app.get("/", tags=["Health"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "API RAG Multi-Documents",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Vérification de santé de l'API"""
    return HealthResponse(
        status="healthy",
        ollama_available=rag_manager.check_ollama(),
        collections=rag_manager.list_collections(),
        version=__version__,
    )


@app.get("/rag-info", tags=["Health"])
async def rag_info():
    """Informations sur le système RAG utilisé"""
    # Récupérer le modèle d'embedding utilisé
    embed_model = getattr(rag_manager, 'embed_model_id', 'unknown')
    cache_enabled = getattr(rag_manager, 'enable_cache', False)

    return {
        "rag_version": _rag_version,
        "embedding_model": embed_model,
        "cache_enabled": cache_enabled,
        "is_v2": "v2" in _rag_version.lower(),
        "info": "v2 utilise paraphrase-multilingual-mpnet-base-v2 (optimisé français)"
    }


@app.get("/collections", response_model=List[CollectionInfo], tags=["Collections"])
async def list_collections():
    """Liste toutes les collections disponibles"""
    collections = rag_manager.list_collections()
    collection_infos = []

    for col_name in collections:
        try:
            info = rag_manager.get_collection_info(col_name)
            collection_infos.append(CollectionInfo(**info))
        except Exception as e:
            continue

    return collection_infos


@app.get("/collections/{collection_name}", response_model=CollectionInfo, tags=["Collections"])
async def get_collection(collection_name: str):
    """Récupère les informations d'une collection spécifique"""
    try:
        info = rag_manager.get_collection_info(collection_name)
        return CollectionInfo(**info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/upload", response_model=IndexingResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...), collection_name: str = None):
    """
    Upload et indexe un document PDF
    """
    # Vérifier que c'est un PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")

    # Générer un nom de collection si non fourni
    if not collection_name:
        collection_name = sanitize_collection_name(Path(file.filename).stem)

    # Sauvegarder le fichier
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Indexer le document
        result = rag_manager.index_document(str(file_path), collection_name)

        return IndexingResponse(
            success=result["success"],
            collection_name=result["collection_name"],
            total_chunks=result["total_chunks"],
            table_chunks=result["table_chunks"],
            text_chunks=result["text_chunks"],
            message=f"Document indexé avec succès en {result['processing_time']:.2f}s",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'indexation: {str(e)}")


@app.post("/index", response_model=IndexingResponse, tags=["Documents"])
async def index_existing_document(doc: DocumentUpload):
    """
    Indexe un document existant depuis un chemin
    """
    # Générer un nom de collection si non fourni
    collection_name = doc.collection_name or sanitize_collection_name(Path(doc.file_path).stem)

    try:
        # Indexer le document
        result = rag_manager.index_document(doc.file_path, collection_name)

        return IndexingResponse(
            success=result["success"],
            collection_name=result["collection_name"],
            total_chunks=result["total_chunks"],
            table_chunks=result["table_chunks"],
            text_chunks=result["text_chunks"],
            message=f"Document '{doc.document_name}' indexé avec succès",
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'indexation: {str(e)}")


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_rag(request: QueryRequest):
    """
    Effectue une requête RAG sur une collection
    """
    start_time = time.time()

    try:
        # Rechercher les chunks pertinents
        chunks, metadatas, distances = rag_manager.search(
            question=request.question,
            collection_name=request.collection_name,
            n_results=request.n_results,
            filter_tables=request.filter_tables,
        )

        # Préparer la réponse des chunks
        chunk_responses = []
        for chunk, metadata, distance in zip(chunks, metadatas, distances):
            chunk_responses.append(
                ChunkResponse(
                    chunk_id=metadata["chunk_id"],
                    text=chunk,
                    score=max(0.0, 1.0 - distance),
                    content_type=metadata.get("content_type", "unknown"),
                    num_tokens=metadata["num_tokens"],
                    metadata=metadata,
                )
            )

        # Générer une réponse si demandé
        answer = None
        if request.generate_answer:
            if not rag_manager.check_ollama():
                raise HTTPException(
                    status_code=503,
                    detail="Ollama n'est pas disponible. Lancez 'ollama serve'",
                )

            answer = rag_manager.generate_answer(request.question, chunks, metadatas)

        processing_time = time.time() - start_time

        return QueryResponse(
            question=request.question,
            answer=answer,
            chunks=chunk_responses,
            collection_name=request.collection_name,
            processing_time=processing_time,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la requête: {str(e)}")


@app.delete("/collections/{collection_name}", tags=["Collections"])
async def delete_collection(collection_name: str):
    """Supprime une collection"""
    try:
        rag_manager.chroma_client.delete_collection(name=collection_name)
        return {"message": f"Collection '{collection_name}' supprimée avec succès"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Collection non trouvée: {str(e)}")


@app.post("/analyze/financial-report", response_model=FinancialAnalysisResponse, tags=["Financial Analysis"])
async def generate_financial_analysis(request: FinancialAnalysisRequest):
    """
    Génère un rapport d'analyse financière complet avec recommandations d'investissement

    Cette analyse utilise une équipe d'agents CrewAI pour :
    - Analyser les fondamentaux via les documents RAG
    - Rechercher l'actualité récente sur le web
    - Évaluer les aspects techniques
    - Fournir des recommandations claires (ACHETER/GARDER/VENDRE)
    """
    start_time = time.time()

    try:
        # Vérifier que les collections existent
        existing_collections = rag_manager.list_collections()
        for collection in request.collections:
            if collection not in existing_collections:
                raise HTTPException(
                    status_code=404,
                    detail=f"Collection '{collection}' non trouvée. Collections disponibles: {existing_collections}",
                )

        # Vérifier que le nombre de companies correspond au nombre de collections
        if len(request.companies) != len(request.collections):
            raise HTTPException(
                status_code=400,
                detail="Le nombre d'entreprises doit correspondre au nombre de collections",
            )

        # Générer le rapport
        report = generate_financial_report(
            companies=request.companies,
            collections=request.collections,
            portfolio=request.portfolio,
        )

        processing_time = time.time() - start_time

        return FinancialAnalysisResponse(
            report=report,
            companies_analyzed=request.companies,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de l'analyse financière: {str(e)}"
        )


@app.post("/build-portfolio", response_model=PortfolioBuildResponse, tags=["Portfolio Building"])
async def build_portfolio_from_scratch(request: PortfolioBuildRequest):
    """
    Construit un portefeuille PEA optimal de zéro avec collecte automatique de données

    Ce système autonome va :
    1. **Collecter automatiquement** les rapports financiers et actualités pour les meilleures entreprises éligibles PEA
    2. **Analyser l'historique** sur 5-10 ans pour identifier les opportunités long terme
    3. **Optimiser l'allocation** selon votre profil de risque et budget
    4. **Analyser en profondeur** chaque entreprise sélectionnée (fondamentaux + technique)
    5. **Générer un plan d'action** avec les ordres d'achat précis

    Args:
        request: Configuration du portefeuille (budget, profil de risque, préférences)

    Returns:
        Plan d'action détaillé pour construire votre portefeuille optimal

    Example:
        ```json
        {
            "budget": 10000,
            "risk_profile": "balanced",
            "sectors": ["luxe", "technologie"],
            "min_companies": 5,
            "max_companies": 8
        }
        ```
    """
    start_time = time.time()

    try:
        # Valider le profil de risque
        valid_profiles = ["conservative", "balanced", "aggressive"]
        if request.risk_profile not in valid_profiles:
            raise HTTPException(
                status_code=400,
                detail=f"Profil de risque invalide. Utilisez: {', '.join(valid_profiles)}"
            )

        # Construire le portefeuille optimal
        action_plan = build_optimal_pea_portfolio(
            budget=request.budget,
            risk_profile=request.risk_profile,
            sectors=request.sectors,
            exclude_companies=request.exclude_companies,
            min_companies=request.min_companies,
            max_companies=request.max_companies,
        )

        processing_time = time.time() - start_time

        return PortfolioBuildResponse(
            action_plan=action_plan,
            budget=request.budget,
            risk_profile=request.risk_profile,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            data_collected=True,
        )

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la construction du portefeuille: {str(e)}"
        )


# ==========================================
# NOUVEAUX ENDPOINTS - GESTION DE PORTEFEUILLE
# ==========================================

@app.post("/portfolio/add", tags=["Portfolio"])
async def add_position(request: PositionAddRequest):
    """Ajoute une position au portefeuille"""
    db = PortfolioDatabase()
    success = db.add_position(
        request.ticker,
        request.company_name,
        request.quantity,
        request.price,
        user_id=request.user_id
    )

    if success:
        return {"message": f"Position {request.company_name} ajoutée avec succès", "ticker": request.ticker}
    else:
        raise HTTPException(status_code=500, detail="Erreur lors de l'ajout")


@app.post("/portfolio/sell", tags=["Portfolio"])
async def sell_position(request: PositionSellRequest):
    """Vend une position (partiellement ou totalement)"""
    db = PortfolioDatabase()
    success = db.sell_position(request.ticker, request.quantity, request.price, user_id=request.user_id)

    if success:
        return {"message": f"Vente de {request.quantity} actions {request.ticker} enregistrée"}
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de la vente")


@app.get("/portfolio", tags=["Portfolio"])
async def get_portfolio(user_id: str = "default_user"):
    """Récupère le portefeuille complet avec prix à jour"""
    db = PortfolioDatabase()
    db.update_current_prices(user_id)
    summary = db.get_portfolio_summary(user_id)
    return summary


@app.get("/portfolio/context", tags=["Portfolio"])
async def get_portfolio_context(user_id: str = "default_user"):
    """Contexte du portefeuille formaté pour l'IA"""
    manager = PortfolioManager()
    context = manager.get_portfolio_context_for_ai(user_id)
    return {"context": context}


@app.get("/portfolio/health", tags=["Portfolio"])
async def check_portfolio_health(user_id: str = "default_user"):
    """Analyse la santé du portefeuille (score 0-100)"""
    manager = PortfolioManager()
    health = manager.get_portfolio_health_score(user_id)
    return health


@app.get("/portfolio/rebalance", tags=["Portfolio"])
async def check_rebalance(user_id: str = "default_user"):
    """Vérifie si le portefeuille nécessite un rééquilibrage"""
    manager = PortfolioManager()
    result = manager.should_rebalance(user_id)
    return result


@app.get("/portfolio/position/{ticker}", tags=["Portfolio"])
async def get_position_details(ticker: str, user_id: str = "default_user"):
    """Récupère tous les détails d'une position"""
    manager = PortfolioManager()
    details = manager.get_position_details(ticker, user_id)
    return details


# ==========================================
# NOUVEAUX ENDPOINTS - TRÉSORERIE PEA
# ==========================================

@app.post("/portfolio/deposit", tags=["Portfolio - Treasury"])
async def deposit_cash_to_pea(amount: float, user_id: str = "default_user", notes: Optional[str] = None):
    """
    Dépose de l'argent sur le PEA

    Args:
        amount: Montant à déposer (euros)
        user_id: Identifiant utilisateur
        notes: Notes optionnelles sur le dépôt
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Le montant doit être positif")

    db = PortfolioDatabase()
    success = db.deposit_cash(amount, user_id=user_id, notes=notes)

    if success:
        treasury = db.get_treasury_status(user_id)
        return {
            "message": f"Dépôt de {amount:.2f}€ effectué avec succès",
            "new_cash_available": treasury['cash_available'],
            "total_deposits": treasury['total_deposits']
        }
    else:
        raise HTTPException(status_code=500, detail="Erreur lors du dépôt")


@app.get("/portfolio/treasury", tags=["Portfolio - Treasury"])
async def get_treasury_status(user_id: str = "default_user"):
    """
    Récupère l'état complet de la trésorerie PEA

    Returns:
        État détaillé de la trésorerie (dépôts, cash disponible, cash investi)
    """
    db = PortfolioDatabase()
    treasury = db.get_treasury_status(user_id)
    return treasury


@app.get("/portfolio/treasury/deposits", tags=["Portfolio - Treasury"])
async def get_deposit_history(user_id: str = "default_user", limit: int = 50):
    """Récupère l'historique des dépôts effectués sur le PEA"""
    db = PortfolioDatabase()
    deposits = db.get_deposit_history(user_id, limit=limit)
    return {
        "user_id": user_id,
        "total_deposits": len(deposits),
        "deposits": deposits
    }


@app.get("/portfolio/treasury/cashflow", tags=["Portfolio - Treasury"])
async def get_cash_flow(user_id: str = "default_user", event_type: Optional[str] = None, limit: int = 100):
    """
    Récupère l'historique des flux de trésorerie

    Args:
        event_type: Filter par type ('DEPOSIT', 'BUY', 'SELL') ou None pour tous
        limit: Nombre maximum d'événements à retourner
    """
    db = PortfolioDatabase()
    events = db.get_cash_flow_events(user_id, event_type=event_type, limit=limit)
    return {
        "user_id": user_id,
        "event_type_filter": event_type or "ALL",
        "total_events": len(events),
        "events": events
    }


# ==========================================
# NOUVEAUX ENDPOINTS - OPPORTUNITÉS D'INVESTISSEMENT
# ==========================================

@app.post("/portfolio/opportunities/analyze", tags=["Portfolio - Opportunities"])
async def analyze_investment_opportunities(user_id: str = "default_user"):
    """
    Analyse le cash disponible et suggère des opportunités d'investissement

    Args:
        user_id: Identifiant utilisateur

    Returns:
        Analyse complète avec opportunités détectées
    """
    try:
        manager = PortfolioManager()
        result = manager.analyze_cash_opportunities(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio/opportunities/pending", tags=["Portfolio - Opportunities"])
async def get_pending_opportunities(user_id: str = "default_user", include_expired: bool = False):
    """
    Récupère toutes les opportunités en attente de décision

    Args:
        user_id: Identifiant utilisateur
        include_expired: Inclure les opportunités expirées
    """
    try:
        manager = PortfolioManager()
        opportunities = manager.get_pending_opportunities(user_id, include_expired)
        return {
            "success": True,
            "count": len(opportunities),
            "opportunities": opportunities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/opportunities/create", tags=["Portfolio - Opportunities"])
async def create_opportunity(
    ticker: str,
    company_name: str,
    recommendation_type: str,
    suggested_amount: float,
    reasoning: str,
    user_id: str = "default_user",
    suggested_quantity: Optional[int] = None,
    target_price: Optional[float] = None,
    confidence_score: float = 0.7,
    risk_level: str = "MEDIUM",
    expires_in_days: int = 7
):
    """
    Crée une nouvelle opportunité d'investissement

    Args:
        ticker: Symbole boursier
        company_name: Nom de l'entreprise
        recommendation_type: Type ('NEW_POSITION', 'ADD_TO_EXISTING', 'DIVERSIFY')
        suggested_amount: Montant suggéré
        reasoning: Justification de l'opportunité
    """
    try:
        manager = PortfolioManager()
        success = manager.save_opportunity_to_db(
            ticker=ticker,
            company_name=company_name,
            recommendation_type=recommendation_type,
            suggested_amount=suggested_amount,
            reasoning=reasoning,
            user_id=user_id,
            suggested_quantity=suggested_quantity,
            target_price=target_price,
            confidence_score=confidence_score,
            risk_level=risk_level,
            expires_in_days=expires_in_days
        )

        if success:
            return {"success": True, "message": "Opportunité créée avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Échec de la création")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/opportunities/{opportunity_id}/accept", tags=["Portfolio - Opportunities"])
async def accept_opportunity(
    opportunity_id: int,
    user_id: str = "default_user",
    actual_quantity: Optional[int] = None,
    actual_price: Optional[float] = None
):
    """
    Accepte une opportunité et exécute la transaction

    Args:
        opportunity_id: ID de l'opportunité
        actual_quantity: Quantité réelle (optionnel, utilise suggested_quantity sinon)
        actual_price: Prix réel (optionnel, utilise prix du marché sinon)
    """
    try:
        manager = PortfolioManager()
        result = manager.accept_opportunity(
            opportunity_id=opportunity_id,
            user_id=user_id,
            actual_quantity=actual_quantity,
            actual_price=actual_price
        )

        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/portfolio/opportunities/{opportunity_id}/reject", tags=["Portfolio - Opportunities"])
async def reject_opportunity(
    opportunity_id: int,
    user_id: str = "default_user",
    reason: Optional[str] = None
):
    """
    Rejette une opportunité d'investissement

    Args:
        opportunity_id: ID de l'opportunité
        reason: Raison du rejet (optionnel)
    """
    try:
        manager = PortfolioManager()
        success = manager.reject_opportunity(
            opportunity_id=opportunity_id,
            user_id=user_id,
            reason=reason
        )

        if success:
            return {"success": True, "message": "Opportunité rejetée"}
        else:
            raise HTTPException(status_code=404, detail="Opportunité non trouvée")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio/opportunities/{opportunity_id}", tags=["Portfolio - Opportunities"])
async def get_opportunity_details(opportunity_id: int, user_id: str = "default_user"):
    """
    Récupère les détails d'une opportunité spécifique

    Args:
        opportunity_id: ID de l'opportunité
    """
    try:
        manager = PortfolioManager()
        opportunities = manager.get_pending_opportunities(user_id, include_expired=True)

        opportunity = next((o for o in opportunities if o['id'] == opportunity_id), None)

        if opportunity:
            return {"success": True, "opportunity": opportunity}
        else:
            raise HTTPException(status_code=404, detail="Opportunité non trouvée")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# NOUVEAUX ENDPOINTS - MARKET DATA
# ==========================================

@app.get("/market/stock/{ticker}", tags=["Market Data"])
async def get_stock_info(ticker: str):
    """Récupère les informations de marché d'une action"""
    service = YahooFinanceService()
    info = service.get_stock_info(ticker)

    if not info:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} non trouvé")

    return info


@app.get("/market/history/{ticker}", tags=["Market Data"])
async def get_stock_history(
    ticker: str,
    period: str = "1y",
    interval: str = "1d"
):
    """
    Récupère l'historique des cours

    Args:
        period: "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"
        interval: "1d", "1wk", "1mo"
    """
    service = YahooFinanceService()
    df = service.get_historical_data(ticker, period, interval)

    if df.empty:
        raise HTTPException(status_code=404, detail=f"Pas de données pour {ticker}")

    # Convertir en JSON
    data = df.reset_index().to_dict(orient='records')
    return {
        "ticker": ticker,
        "period": period,
        "interval": interval,
        "data_points": len(data),
        "data": data[:100]  # Limiter à 100 points par défaut
    }


# ==========================================
# NOUVEAUX ENDPOINTS - ANALYSE AVANCÉE
# ==========================================

@app.get("/analysis/news/{company_name}", tags=["Analysis"])
async def get_company_news(company_name: str, days_back: int = 7):
    """Récupère les actualités récentes d'une entreprise"""
    aggregator = NewsAggregator()
    news = aggregator.get_company_news(company_name, days_back=days_back)
    return {"company": company_name, "news_count": len(news), "articles": news}


@app.get("/analysis/sentiment/{company_name}", tags=["Analysis"])
async def analyze_sentiment(company_name: str, days_back: int = 7):
    """Analyse le sentiment des actualités pour une entreprise"""
    aggregator = NewsAggregator()
    analyzer = SentimentAnalyzer(provider="claude")

    news = aggregator.get_company_news(company_name, days_back=days_back)
    sentiment = analyzer.analyze_news_sentiment(company_name, news)

    return sentiment


@app.get("/analysis/technical/{ticker}", tags=["Analysis"])
async def analyze_technical(ticker: str, period: str = "6mo"):
    """Analyse technique complète d'une action"""
    yf_service = YahooFinanceService()
    analyzer = TechnicalAnalyzer()

    # Récupérer les données
    df = yf_service.get_historical_data(ticker, period=period)

    if df.empty:
        raise HTTPException(status_code=404, detail=f"Pas de données pour {ticker}")

    # Calculer les indicateurs
    df = analyzer.calculate_indicators(df)

    # Détecter les signaux
    signals = analyzer.detect_signals(df)

    # Support/Résistance
    levels = analyzer.calculate_support_resistance(df)

    # Tendance
    trend = analyzer.calculate_trend(df)

    return {
        "ticker": ticker,
        "signals": signals,
        "levels": levels,
        "trend": trend
    }


@app.get("/analysis/complete/{ticker}", tags=["Analysis"])
async def complete_analysis(ticker: str, company_name: str):
    """Analyse complète: Market Data + News + Sentiment + Technique"""
    yf_service = YahooFinanceService()
    aggregator = NewsAggregator()
    sentiment_analyzer = SentimentAnalyzer()
    technical_analyzer = TechnicalAnalyzer()

    try:
        # 1. Market Data
        market_info = yf_service.get_stock_info(ticker)

        # 2. News + Sentiment
        news = aggregator.get_company_news(company_name, days_back=7)
        sentiment = sentiment_analyzer.analyze_news_sentiment(company_name, news)

        # 3. Analyse Technique
        df = yf_service.get_historical_data(ticker, period="6mo")
        if not df.empty:
            df = technical_analyzer.calculate_indicators(df)
            signals = technical_analyzer.detect_signals(df)
            levels = technical_analyzer.calculate_support_resistance(df)
            trend = technical_analyzer.calculate_trend(df)
        else:
            signals = {}
            levels = {}
            trend = "UNKNOWN"

        return {
            "ticker": ticker,
            "company": company_name,
            "market_data": market_info,
            "news_sentiment": sentiment,
            "technical_analysis": {
                "signals": signals,
                "levels": levels,
                "trend": trend
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
