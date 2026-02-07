"""
Routes FastAPI pour le backtesting
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import hashlib

from .engine import BacktestEngine
from .strategies import AVAILABLE_STRATEGIES
from .visualization import BacktestVisualizer
from auth import get_current_user  # Import absolu pour Docker

# Router pour les endpoints de backtesting
router = APIRouter(prefix="/backtesting", tags=["Backtesting"])

# Cache des résultats (en mémoire pour démo, à remplacer par Redis en prod)
results_cache: Dict[str, Any] = {}


# ==========================================
# MODÈLES PYDANTIC
# ==========================================

class BacktestRequest(BaseModel):
    """Modèle pour lancer un backtest"""
    ticker: str = Field(..., description="Symbole boursier (ex: 'MC.PA')")
    strategy: str = Field(..., description="Nom de la stratégie (ex: 'ma_crossover')")
    params: Optional[Dict[str, Any]] = Field(None, description="Paramètres de la stratégie")
    start_date: str = Field(..., description="Date de début (YYYY-MM-DD)")
    end_date: str = Field(..., description="Date de fin (YYYY-MM-DD)")
    initial_capital: float = Field(10000.0, description="Capital initial en euros", gt=0)
    commission: float = Field(0.001, description="Commission par trade (0.001 = 0.1%)", ge=0, le=0.1)
    slippage: float = Field(0.0005, description="Slippage moyen (0.0005 = 0.05%)", ge=0, le=0.1)


class BacktestResponse(BaseModel):
    """Modèle pour la réponse d'un backtest"""
    backtest_id: str
    strategy: str
    ticker: str
    period: str
    performance: Dict[str, Any]
    comparison_vs_buy_hold: Optional[Dict[str, Any]] = None
    trades: List[Dict[str, Any]]
    equity_curve_url: str


class CompareRequest(BaseModel):
    """Modèle pour comparer plusieurs stratégies"""
    ticker: str = Field(..., description="Symbole boursier")
    strategies: List[str] = Field(..., description="Liste des stratégies à comparer")
    params: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Paramètres par stratégie (optionnel)"
    )
    start_date: str = Field(..., description="Date de début")
    end_date: str = Field(..., description="Date de fin")
    initial_capital: float = Field(10000.0, description="Capital initial", gt=0)
    commission: float = Field(0.001, ge=0, le=0.1)
    slippage: float = Field(0.0005, ge=0, le=0.1)


class OptimizeRequest(BaseModel):
    """Modèle pour optimiser les paramètres d'une stratégie"""
    ticker: str = Field(..., description="Symbole boursier")
    strategy: str = Field(..., description="Nom de la stratégie")
    param_grid: Dict[str, List] = Field(
        ...,
        description="Grille de paramètres à tester"
    )
    start_date: str = Field(..., description="Date de début")
    end_date: str = Field(..., description="Date de fin")
    initial_capital: float = Field(10000.0, gt=0)
    commission: float = Field(0.001, ge=0, le=0.1)
    slippage: float = Field(0.0005, ge=0, le=0.1)


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, current_user: str = Depends(get_current_user)):
    """
    Lance un backtest pour une stratégie donnée

    Args:
        request: Paramètres du backtest

    Returns:
        Résultats du backtest avec toutes les métriques
    """
    try:
        # Créer le moteur de backtest
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage
        )

        # Créer la stratégie
        strategy = engine.create_strategy(request.strategy, request.params)

        # Lancer le backtest
        result = engine.run(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            strategy=strategy
        )

        # Générer un ID unique pour ce backtest
        backtest_id = hashlib.md5(
            f"{request.ticker}_{request.strategy}_{request.start_date}_{request.end_date}_{datetime.now()}".encode()
        ).hexdigest()[:12]

        # Stocker le résultat dans le cache
        results_cache[backtest_id] = result

        # Préparer la réponse
        response = BacktestResponse(
            backtest_id=backtest_id,
            strategy=result.strategy_name,
            ticker=result.ticker,
            period=f"{result.start_date} to {result.end_date}",
            performance={
                "total_return": result.total_return,
                "annualized_return": result.annualized_return,
                "sharpe_ratio": result.sharpe_ratio,
                "sortino_ratio": result.sortino_ratio,
                "max_drawdown": result.max_drawdown,
                "calmar_ratio": result.calmar_ratio,
                "win_rate": result.win_rate,
                "profit_factor": result.profit_factor,
                "num_trades": result.num_trades,
                "avg_trade": result.avg_trade,
                "volatility": result.volatility,
            },
            comparison_vs_buy_hold=None,  # TODO: implémenter
            trades=[t.to_dict() for t in result.trades[:50]],  # Limiter à 50 trades pour la réponse
            equity_curve_url=f"/backtesting/visualization/{backtest_id}"
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du backtest: {str(e)}")


@router.get("/strategies")
async def list_strategies(current_user: str = Depends(get_current_user)):
    """
    Liste toutes les stratégies disponibles avec leurs paramètres

    Returns:
        Liste des stratégies avec descriptions
    """
    strategies_info = []

    for name, strategy_class in AVAILABLE_STRATEGIES.items():
        # Créer une instance par défaut pour récupérer les paramètres
        instance = strategy_class()

        strategies_info.append({
            "name": name,
            "display_name": instance.get_name(),
            "default_params": instance.get_params(),
            "description": strategy_class.__doc__.strip() if strategy_class.__doc__ else "N/A"
        })

    return {
        "total": len(strategies_info),
        "strategies": strategies_info
    }


@router.post("/compare")
async def compare_strategies(request: CompareRequest, current_user: str = Depends(get_current_user)):
    """
    Compare plusieurs stratégies sur les mêmes données

    Args:
        request: Paramètres de comparaison

    Returns:
        Résultats comparatifs de toutes les stratégies
    """
    try:
        # Créer le moteur
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage
        )

        # Créer les stratégies
        strategies = []
        for strategy_name in request.strategies:
            params = request.params.get(strategy_name) if request.params else None
            strategy = engine.create_strategy(strategy_name, params)
            strategies.append(strategy)

        # Comparer les stratégies
        comparison = engine.compare_strategies(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            strategies=strategies
        )

        # Préparer la réponse
        response = {
            "ticker": comparison.ticker,
            "period": f"{comparison.start_date} to {comparison.end_date}",
            "best_strategy": comparison.best_strategy,
            "comparison_metrics": comparison.comparison_metrics,
            "strategies": [
                {
                    "name": r.strategy_name,
                    "total_return": r.total_return,
                    "sharpe_ratio": r.sharpe_ratio,
                    "max_drawdown": r.max_drawdown,
                    "win_rate": r.win_rate,
                    "num_trades": r.num_trades,
                }
                for r in comparison.strategies
            ]
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison: {str(e)}")


@router.post("/optimize")
async def optimize_strategy(request: OptimizeRequest, current_user: str = Depends(get_current_user)):
    """
    Optimise les paramètres d'une stratégie via Grid Search

    Args:
        request: Paramètres d'optimisation

    Returns:
        Meilleurs paramètres trouvés et résultats
    """
    try:
        # Créer le moteur
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            commission=request.commission,
            slippage=request.slippage
        )

        # Récupérer la classe de stratégie
        if request.strategy not in AVAILABLE_STRATEGIES:
            raise ValueError(f"Stratégie inconnue: {request.strategy}")

        strategy_class = AVAILABLE_STRATEGIES[request.strategy]

        # Optimiser
        optimization_result = engine.optimize_parameters(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date,
            strategy_class=strategy_class,
            param_grid=request.param_grid
        )

        # Préparer la réponse
        response = {
            "strategy": request.strategy,
            "ticker": request.ticker,
            "best_params": optimization_result['best_params'],
            "best_sharpe_ratio": optimization_result['best_sharpe_ratio'],
            "best_performance": {
                "total_return": optimization_result['best_result'].total_return,
                "sharpe_ratio": optimization_result['best_result'].sharpe_ratio,
                "max_drawdown": optimization_result['best_result'].max_drawdown,
            } if optimization_result['best_result'] else None,
            "all_results": optimization_result['all_results'][:20],  # Top 20
            "total_combinations_tested": len(optimization_result['all_results'])
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'optimisation: {str(e)}")


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str, current_user: str = Depends(get_current_user)):
    """
    Récupère les résultats complets d'un backtest

    Args:
        backtest_id: Identifiant du backtest

    Returns:
        Résultats détaillés
    """
    if backtest_id not in results_cache:
        raise HTTPException(status_code=404, detail="Backtest non trouvé")

    result = results_cache[backtest_id]

    return {
        "backtest_id": backtest_id,
        "result": result.to_dict()
    }


@router.get("/visualization/{backtest_id}")
async def get_visualization(backtest_id: str, chart_type: str = "equity", current_user: str = Depends(get_current_user)):
    """
    Génère une visualisation pour un backtest

    Args:
        backtest_id: Identifiant du backtest
        chart_type: Type de graphique ('equity', 'drawdown', 'returns')

    Returns:
        HTML du graphique Plotly
    """
    if backtest_id not in results_cache:
        raise HTTPException(status_code=404, detail="Backtest non trouvé")

    result = results_cache[backtest_id]
    visualizer = BacktestVisualizer()

    try:
        if chart_type == "equity":
            fig = visualizer.plot_equity_curve(result, show_trades=True, compare_with_buy_hold=True)
        elif chart_type == "drawdown":
            fig = visualizer.plot_drawdown(result)
        elif chart_type == "returns":
            fig = visualizer.plot_returns_distribution(result)
        else:
            raise ValueError(f"Type de graphique inconnu: {chart_type}")

        # Retourner le HTML du graphique
        return {"html": fig.to_html(full_html=False, include_plotlyjs='cdn')}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la visualisation: {str(e)}")


# Export du router
__all__ = ['router']
