"""
Exemple d'intégration des nouvelles fonctionnalités dans main.py (FastAPI)

Ajouter ces endpoints dans votre fichier api/main.py
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.portfolio_manager import PortfolioManager

# Router pour les opportunités
opportunities_router = APIRouter(prefix="/portfolio/opportunities", tags=["Opportunities"])

# =============================================================================
# MODÈLES PYDANTIC
# =============================================================================

class OpportunityAnalysisResponse(BaseModel):
    """Réponse de l'analyse des opportunités"""
    has_opportunities: bool
    cash_available: float
    cash_ratio: float
    portfolio_size: int
    total_value: float
    opportunities: list

class OpportunityCreateRequest(BaseModel):
    """Requête de création d'opportunité"""
    ticker: str
    company_name: str
    recommendation_type: str
    suggested_amount: float
    reasoning: str
    suggested_quantity: Optional[int] = None
    target_price: Optional[float] = None
    confidence_score: float = 0.7
    risk_level: str = "MEDIUM"
    expires_in_days: int = 7

class OpportunityAcceptRequest(BaseModel):
    """Requête d'acceptation d'opportunité"""
    actual_quantity: Optional[int] = None
    actual_price: Optional[float] = None

class OpportunityRejectRequest(BaseModel):
    """Requête de rejet d'opportunité"""
    reason: Optional[str] = None

# =============================================================================
# ENDPOINTS
# =============================================================================

@opportunities_router.post("/analyze", response_model=OpportunityAnalysisResponse)
async def analyze_opportunities(user_id: str = "default_user"):
    """
    Analyse les opportunités d'investissement basées sur le cash disponible
    
    Returns:
        OpportunityAnalysisResponse avec toutes les opportunités détectées
    """
    try:
        pm = PortfolioManager()
        result = pm.analyze_cash_opportunities(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@opportunities_router.get("/pending")
async def get_pending_opportunities(
    user_id: str = "default_user",
    include_expired: bool = False
):
    """
    Récupère toutes les opportunités en attente
    
    Args:
        user_id: Identifiant utilisateur
        include_expired: Inclure les opportunités expirées
    
    Returns:
        Liste des opportunités en attente
    """
    try:
        pm = PortfolioManager()
        opportunities = pm.get_pending_opportunities(user_id, include_expired)
        return {
            "success": True,
            "count": len(opportunities),
            "opportunities": opportunities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@opportunities_router.post("/create")
async def create_opportunity(
    request: OpportunityCreateRequest,
    user_id: str = "default_user"
):
    """
    Crée une nouvelle opportunité d'investissement
    
    Body:
        OpportunityCreateRequest avec tous les détails
    
    Returns:
        Confirmation de création
    """
    try:
        pm = PortfolioManager()
        success = pm.save_opportunity_to_db(
            ticker=request.ticker,
            company_name=request.company_name,
            recommendation_type=request.recommendation_type,
            suggested_amount=request.suggested_amount,
            reasoning=request.reasoning,
            user_id=user_id,
            suggested_quantity=request.suggested_quantity,
            target_price=request.target_price,
            confidence_score=request.confidence_score,
            risk_level=request.risk_level,
            expires_in_days=request.expires_in_days
        )
        
        if success:
            return {
                "success": True,
                "message": "Opportunité créée avec succès"
            }
        else:
            raise HTTPException(status_code=500, detail="Échec de la création")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@opportunities_router.post("/{opportunity_id}/accept")
async def accept_opportunity(
    opportunity_id: int,
    request: OpportunityAcceptRequest = OpportunityAcceptRequest(),
    user_id: str = "default_user"
):
    """
    Accepte une opportunité et exécute la transaction
    
    Args:
        opportunity_id: ID de l'opportunité
        request: Paramètres optionnels (quantité, prix)
    
    Returns:
        Résultat de la transaction
    """
    try:
        pm = PortfolioManager()
        result = pm.accept_opportunity(
            opportunity_id=opportunity_id,
            user_id=user_id,
            actual_quantity=request.actual_quantity,
            actual_price=request.actual_price
        )
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error'))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@opportunities_router.post("/{opportunity_id}/reject")
async def reject_opportunity(
    opportunity_id: int,
    request: OpportunityRejectRequest = OpportunityRejectRequest(),
    user_id: str = "default_user"
):
    """
    Rejette une opportunité d'investissement
    
    Args:
        opportunity_id: ID de l'opportunité
        request: Raison du rejet (optionnel)
    
    Returns:
        Confirmation de rejet
    """
    try:
        pm = PortfolioManager()
        success = pm.reject_opportunity(
            opportunity_id=opportunity_id,
            user_id=user_id,
            reason=request.reason
        )
        
        if success:
            return {
                "success": True,
                "message": "Opportunité rejetée"
            }
        else:
            raise HTTPException(status_code=404, detail="Opportunité non trouvée")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@opportunities_router.get("/{opportunity_id}")
async def get_opportunity_details(
    opportunity_id: int,
    user_id: str = "default_user"
):
    """
    Récupère les détails d'une opportunité spécifique
    
    Args:
        opportunity_id: ID de l'opportunité
    
    Returns:
        Détails complets de l'opportunité
    """
    try:
        pm = PortfolioManager()
        opportunities = pm.get_pending_opportunities(user_id, include_expired=True)
        
        opportunity = next((o for o in opportunities if o['id'] == opportunity_id), None)
        
        if opportunity:
            return {
                "success": True,
                "opportunity": opportunity
            }
        else:
            raise HTTPException(status_code=404, detail="Opportunité non trouvée")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# INTÉGRATION DANS main.py
# =============================================================================

"""
Pour intégrer dans votre main.py:

1. Importer le router:
   from EXEMPLE_INTEGRATION_API import opportunities_router

2. Ajouter le router à l'app FastAPI:
   app.include_router(opportunities_router)

3. Optionnel: Ajouter dans le /portfolio/context existant pour afficher les opportunités
"""


# =============================================================================
# EXEMPLES DE REQUÊTES
# =============================================================================

"""
1. Analyser les opportunités:
   POST http://localhost:8000/portfolio/opportunities/analyze?user_id=default_user

2. Lister les opportunités en attente:
   GET http://localhost:8000/portfolio/opportunities/pending?user_id=default_user

3. Créer une opportunité manuellement:
   POST http://localhost:8000/portfolio/opportunities/create?user_id=default_user
   Body:
   {
     "ticker": "AAPL",
     "company_name": "Apple Inc.",
     "recommendation_type": "ADD_TO_EXISTING",
     "suggested_amount": 500.0,
     "reasoning": "Position performante à renforcer",
     "suggested_quantity": 2,
     "confidence_score": 0.8,
     "risk_level": "LOW",
     "expires_in_days": 7
   }

4. Accepter une opportunité:
   POST http://localhost:8000/portfolio/opportunities/123/accept?user_id=default_user
   Body:
   {
     "actual_quantity": 2,
     "actual_price": 225.50
   }

5. Rejeter une opportunité:
   POST http://localhost:8000/portfolio/opportunities/123/reject?user_id=default_user
   Body:
   {
     "reason": "Préfère attendre une baisse"
   }

6. Détails d'une opportunité:
   GET http://localhost:8000/portfolio/opportunities/123?user_id=default_user
"""

