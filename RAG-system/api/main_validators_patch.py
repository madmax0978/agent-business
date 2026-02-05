"""
PATCH MANUEL pour api/main.py

Ajouter les imports suivants après la ligne 65:

# Import des validateurs
from validators import ValidationError, validate_financial_amount

Ensuite, remplacer les 3 endpoints suivants:
"""

# ==========================================
# 1. ENDPOINT /portfolio/add (ligne 533-548)
# ==========================================
"""
REMPLACER:

@app.post("/portfolio/add", tags=["Portfolio"])
async def add_position(request: PositionAddRequest, current_user: str = Depends(get_current_user)):
    \"\"\"Ajoute une position au portefeuille\"\"\"
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

PAR:
"""

@app.post("/portfolio/add", tags=["Portfolio"])
async def add_position(request: PositionAddRequest, current_user: str = Depends(get_current_user)):
    """
    Ajoute une position au portefeuille avec validation Decimal stricte

    Raises:
        HTTPException 400: Si les paramètres sont invalides (montant, prix, quantité)
        HTTPException 409: Si le cash est insuffisant
        HTTPException 500: Si erreur serveur
    """
    try:
        db = PortfolioDatabase()
        success = db.add_position(
            request.ticker,
            request.company_name,
            request.quantity,
            request.price,
            user_id=request.user_id
        )

        if success:
            return {
                "message": f"Position {request.company_name} ajoutée avec succès",
                "ticker": request.ticker
            }
        else:
            raise HTTPException(status_code=500, detail="Erreur lors de l'ajout")

    except ValidationError as e:
        # Erreur de validation des paramètres (montant invalide, etc.)
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        # Erreur métier (cash insuffisant, etc.)
        error_msg = str(e)
        if "insuffisant" in error_msg.lower():
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        # Erreur inattendue
        logger.error(f"Erreur add_position: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors de l'ajout de position")


# ==========================================
# 2. ENDPOINT /portfolio/sell (ligne 551-560)
# ==========================================
"""
REMPLACER:

@app.post("/portfolio/sell", tags=["Portfolio"])
async def sell_position(request: PositionSellRequest, current_user: str = Depends(get_current_user)):
    \"\"\"Vend une position (partiellement ou totalement)\"\"\"
    db = PortfolioDatabase()
    success = db.sell_position(request.ticker, request.quantity, request.price, user_id=request.user_id)

    if success:
        return {"message": f"Vente de {request.quantity} actions {request.ticker} enregistrée"}
    else:
        raise HTTPException(status_code=400, detail="Erreur lors de la vente")

PAR:
"""

@app.post("/portfolio/sell", tags=["Portfolio"])
async def sell_position(request: PositionSellRequest, current_user: str = Depends(get_current_user)):
    """
    Vend une position (partiellement ou totalement) avec validation Decimal stricte

    Raises:
        HTTPException 400: Si les paramètres sont invalides
        HTTPException 404: Si la position n'existe pas
        HTTPException 500: Si erreur serveur
    """
    try:
        db = PortfolioDatabase()
        success = db.sell_position(
            request.ticker,
            request.quantity,
            request.price,
            user_id=request.user_id
        )

        if success:
            return {
                "message": f"Vente de {request.quantity} actions {request.ticker} enregistrée"
            }
        else:
            raise HTTPException(status_code=400, detail="Erreur lors de la vente")

    except ValidationError as e:
        # Erreur de validation des paramètres
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        # Erreur métier (quantité > disponible, position inexistante, etc.)
        error_msg = str(e)
        if "non trouvée" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        # Erreur inattendue
        logger.error(f"Erreur sell_position: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors de la vente")


# ==========================================
# 3. ENDPOINT /portfolio/deposit (ligne 608-637)
# ==========================================
"""
REMPLACER:

@app.post("/portfolio/deposit", tags=["Portfolio - Treasury"])
async def deposit_cash_to_pea(
    amount: float,
    user_id: str = "default_user",
    notes: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    \"\"\"
    Dépose de l'argent sur le PEA

    Args:
        amount: Montant à déposer (euros)
        user_id: Identifiant utilisateur
        notes: Notes optionnelles sur le dépôt
    \"\"\"
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

PAR:
"""

@app.post("/portfolio/deposit", tags=["Portfolio - Treasury"])
async def deposit_cash_to_pea(
    amount: float,
    user_id: str = "default_user",
    notes: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """
    Dépose de l'argent sur le PEA avec validation Decimal stricte

    Args:
        amount: Montant à déposer (euros, min: 0.01€, max: 150 000€)
        user_id: Identifiant utilisateur
        notes: Notes optionnelles sur le dépôt

    Raises:
        HTTPException 400: Si le montant est invalide (négatif, trop grand, etc.)
        HTTPException 500: Si erreur serveur
    """
    try:
        # Validation Decimal stricte (lever ValidationError si invalide)
        validate_financial_amount(
            amount,
            min_value=0.01,
            max_value=150_000.0,
            field_name="Montant du dépôt"
        )

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

    except ValidationError as e:
        # Erreur de validation (montant invalide)
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        # Erreur métier
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Erreur inattendue
        logger.error(f"Erreur deposit_cash: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur lors du dépôt")
