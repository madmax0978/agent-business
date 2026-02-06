"""
Tests unitaires pour le système de backtesting
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ajouter le chemin vers le module backtesting
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from backtesting.engine import BacktestEngine
from backtesting.strategies.ma_crossover import MovingAverageCrossover
from backtesting.strategies.rsi_strategy import RSIMeanReversion
from backtesting.strategies.buy_and_hold import BuyAndHold
from backtesting.portfolio import BacktestPortfolio, Trade
from backtesting.metrics import PerformanceMetrics
from backtesting.strategies.base import Signal


# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture
def sample_data():
    """Génère des données de test OHLCV"""
    dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
    np.random.seed(42)

    # Générer des prix avec tendance
    prices = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
    prices = np.maximum(prices, 50)  # Éviter les prix négatifs

    data = pd.DataFrame({
        'Date': dates,
        'Open': prices + np.random.randn(len(dates)),
        'High': prices + abs(np.random.randn(len(dates))),
        'Low': prices - abs(np.random.randn(len(dates))),
        'Close': prices,
        'Volume': np.random.randint(100000, 1000000, len(dates))
    })

    return data


@pytest.fixture
def portfolio():
    """Crée un portfolio de test"""
    return BacktestPortfolio(initial_capital=10000.0, commission=0.001, slippage=0.0005)


# ==========================================
# TESTS PORTFOLIO
# ==========================================

def test_portfolio_initialization(portfolio):
    """Test l'initialisation du portfolio"""
    assert portfolio.initial_capital == 10000.0
    assert portfolio.cash == 10000.0
    assert portfolio.holdings == 0
    assert portfolio.commission == 0.001
    assert portfolio.slippage == 0.0005
    assert len(portfolio.trades) == 0


def test_portfolio_buy_success(portfolio):
    """Test un achat réussi"""
    date = datetime.now()
    result = portfolio.buy(date, 'TEST', 100.0, quantity=10)

    assert result is True
    assert portfolio.holdings == 10
    assert portfolio.cash < 10000.0  # Cash diminué
    assert len(portfolio.trades) == 1
    assert portfolio.trades[0].type == 'BUY'


def test_portfolio_buy_insufficient_cash(portfolio):
    """Test un achat avec cash insuffisant"""
    date = datetime.now()
    result = portfolio.buy(date, 'TEST', 5000.0, quantity=10)  # 50000€ nécessaires

    assert result is False
    assert portfolio.holdings == 0
    assert portfolio.cash == 10000.0  # Cash inchangé
    assert len(portfolio.trades) == 0


def test_portfolio_sell_success(portfolio):
    """Test une vente réussie"""
    date = datetime.now()

    # D'abord acheter
    portfolio.buy(date, 'TEST', 100.0, quantity=10)

    # Puis vendre
    result = portfolio.sell(date + timedelta(days=1), 'TEST', 110.0, quantity=5)

    assert result is True
    assert portfolio.holdings == 5
    assert portfolio.cash > 10000.0 - (100 * 10 * 1.001)  # Profit réalisé
    assert len(portfolio.trades) == 2
    assert portfolio.trades[1].type == 'SELL'
    assert portfolio.trades[1].profit is not None


def test_portfolio_sell_without_holdings(portfolio):
    """Test une vente sans holdings"""
    date = datetime.now()
    result = portfolio.sell(date, 'TEST', 100.0, quantity=10)

    assert result is False
    assert portfolio.holdings == 0
    assert len(portfolio.trades) == 0


def test_portfolio_equity_curve(portfolio, sample_data):
    """Test la mise à jour de l'equity curve"""
    for idx in range(10):
        date = sample_data.iloc[idx]['Date']
        price = sample_data.iloc[idx]['Close']
        portfolio.update_equity(date, price)

    assert len(portfolio.equity_curve) == 11  # Initial + 10 updates
    assert len(portfolio.dates) == 10


# ==========================================
# TESTS STRATEGIES
# ==========================================

def test_ma_crossover_strategy(sample_data):
    """Test la stratégie MA Crossover"""
    strategy = MovingAverageCrossover(fast_period=10, slow_period=20)

    # Test sur les premières barres (pas assez de données)
    signal = strategy.on_bar(sample_data, 15, holdings=0)
    assert signal in [Signal.BUY, Signal.SELL, Signal.HOLD]

    # Test sur les dernières barres (assez de données)
    signal = strategy.on_bar(sample_data, len(sample_data) - 1, holdings=0)
    assert signal in [Signal.BUY, Signal.SELL, Signal.HOLD]


def test_rsi_strategy(sample_data):
    """Test la stratégie RSI"""
    strategy = RSIMeanReversion(rsi_period=14, oversold=30, overbought=70)

    # Test avec holdings=0 (peut acheter)
    signal = strategy.on_bar(sample_data, 50, holdings=0)
    assert signal in [Signal.BUY, Signal.HOLD]

    # Test avec holdings>0 (peut vendre)
    signal = strategy.on_bar(sample_data, 50, holdings=10)
    assert signal in [Signal.SELL, Signal.HOLD]


def test_buy_and_hold_strategy(sample_data):
    """Test la stratégie Buy and Hold"""
    strategy = BuyAndHold()

    # Premier appel sans holdings -> BUY
    signal = strategy.on_bar(sample_data, 0, holdings=0)
    assert signal == Signal.BUY

    # Deuxième appel avec holdings -> HOLD
    signal = strategy.on_bar(sample_data, 1, holdings=10)
    assert signal == Signal.HOLD


def test_strategy_params():
    """Test la récupération des paramètres des stratégies"""
    strategy1 = MovingAverageCrossover(fast_period=50, slow_period=200)
    params1 = strategy1.get_params()

    assert 'fast_period' in params1
    assert 'slow_period' in params1
    assert params1['fast_period'] == 50
    assert params1['slow_period'] == 200

    strategy2 = RSIMeanReversion(rsi_period=14, oversold=25, overbought=75)
    params2 = strategy2.get_params()

    assert 'rsi_period' in params2
    assert params2['oversold'] == 25


# ==========================================
# TESTS METRICS
# ==========================================

def test_calculate_total_return():
    """Test le calcul du rendement total"""
    total_return = PerformanceMetrics.calculate_total_return(10000, 12000)
    assert total_return == pytest.approx(20.0, abs=0.1)

    total_return = PerformanceMetrics.calculate_total_return(10000, 8000)
    assert total_return == pytest.approx(-20.0, abs=0.1)


def test_calculate_sharpe_ratio():
    """Test le calcul du Sharpe Ratio"""
    # Rendements positifs constants
    returns = np.array([0.01] * 100)
    sharpe = PerformanceMetrics.calculate_sharpe_ratio(returns, risk_free_rate=0.02)
    assert sharpe > 0

    # Rendements volatils
    returns = np.random.randn(100) * 0.02
    sharpe = PerformanceMetrics.calculate_sharpe_ratio(returns)
    assert isinstance(sharpe, float)


def test_calculate_max_drawdown():
    """Test le calcul du max drawdown"""
    # Equity curve qui monte puis descend
    equity_curve = [100, 110, 120, 115, 100, 95, 105, 110]
    max_dd, peak_idx, trough_idx = PerformanceMetrics.calculate_max_drawdown(equity_curve)

    assert max_dd < 0  # Drawdown est négatif
    assert peak_idx <= trough_idx  # Le pic est avant le creux


def test_calculate_volatility():
    """Test le calcul de la volatilité"""
    returns = np.random.randn(252) * 0.01  # Rendements journaliers
    volatility = PerformanceMetrics.calculate_volatility(returns)

    assert volatility > 0
    assert volatility < 100  # Volatilité raisonnable


def test_calculate_trade_metrics():
    """Test le calcul des métriques de trading"""
    # Créer des trades de test
    trades = [
        Trade(datetime.now(), 'BUY', 'TEST', 100, 10, 0.1, 0.05, 1000),
        Trade(datetime.now(), 'SELL', 'TEST', 110, 10, 0.11, 0.055, 1100, profit=100, return_pct=10),
        Trade(datetime.now(), 'BUY', 'TEST', 110, 10, 0.11, 0.055, 1100),
        Trade(datetime.now(), 'SELL', 'TEST', 105, 10, 0.105, 0.0525, 1050, profit=-50, return_pct=-4.5),
    ]

    metrics = PerformanceMetrics.calculate_trade_metrics(trades)

    assert 'win_rate' in metrics
    assert 'profit_factor' in metrics
    assert 'num_trades' in metrics
    assert metrics['num_trades'] == 4
    assert 0 <= metrics['win_rate'] <= 100


# ==========================================
# TESTS ENGINE
# ==========================================

def test_engine_initialization():
    """Test l'initialisation du moteur"""
    engine = BacktestEngine(initial_capital=10000.0, commission=0.001, slippage=0.0005)

    assert engine.initial_capital == 10000.0
    assert engine.commission == 0.001
    assert engine.slippage == 0.0005
    assert len(engine.strategies) == 0


def test_engine_add_strategy():
    """Test l'ajout de stratégies"""
    engine = BacktestEngine()
    strategy1 = MovingAverageCrossover()
    strategy2 = RSIMeanReversion()

    engine.add_strategy(strategy1)
    engine.add_strategy(strategy2)

    assert len(engine.strategies) == 2


def test_engine_get_available_strategies():
    """Test la récupération des stratégies disponibles"""
    strategies = BacktestEngine.get_available_strategies()

    assert isinstance(strategies, list)
    assert 'ma_crossover' in strategies
    assert 'rsi' in strategies
    assert 'buy_and_hold' in strategies


def test_engine_create_strategy():
    """Test la création de stratégie à partir du nom"""
    strategy = BacktestEngine.create_strategy('ma_crossover', {'fast_period': 50, 'slow_period': 200})

    assert isinstance(strategy, MovingAverageCrossover)
    assert strategy.fast_period == 50
    assert strategy.slow_period == 200


def test_engine_create_strategy_invalid():
    """Test la création d'une stratégie invalide"""
    with pytest.raises(ValueError):
        BacktestEngine.create_strategy('invalid_strategy')


@pytest.mark.slow
def test_engine_run_backtest():
    """
    Test complet d'un backtest (lent car télécharge des données réelles)

    Note: Marqué comme 'slow' - exécuter avec: pytest -m "not slow"
    """
    engine = BacktestEngine(initial_capital=10000.0)
    strategy = BuyAndHold()

    # Utiliser une période courte pour le test
    result = engine.run(
        ticker='MC.PA',
        start_date='2023-01-01',
        end_date='2023-12-31',
        strategy=strategy
    )

    # Vérifier le résultat
    assert result.ticker == 'MC.PA'
    assert result.strategy_name == 'Buy and Hold'
    assert result.initial_capital == 10000.0
    assert isinstance(result.total_return, float)
    assert isinstance(result.sharpe_ratio, float)
    assert len(result.equity_curve) > 0


# ==========================================
# TESTS INTEGRATION
# ==========================================

def test_full_backtest_workflow(sample_data):
    """Test un workflow complet de backtest avec données de test"""
    # Créer le moteur
    engine = BacktestEngine(initial_capital=10000.0)

    # Créer la stratégie
    strategy = MovingAverageCrossover(fast_period=10, slow_period=20)

    # Simuler un backtest avec les données de test
    portfolio = BacktestPortfolio(initial_capital=10000.0)

    for idx in range(len(sample_data)):
        date = sample_data.iloc[idx]['Date']
        price = sample_data.iloc[idx]['Close']

        # Obtenir le signal
        signal = strategy.on_bar(sample_data, idx, portfolio.get_holdings())

        # Exécuter le trade
        if signal == Signal.BUY:
            portfolio.buy(date, 'TEST', price)
        elif signal == Signal.SELL:
            portfolio.sell(date, 'TEST', price)

        # Mettre à jour l'equity
        portfolio.update_equity(date, price)

    # Vérifier que le portfolio a été mis à jour
    assert len(portfolio.equity_curve) > 0
    assert len(portfolio.dates) > 0

    # Calculer les métriques
    final_value = portfolio.get_current_value(sample_data.iloc[-1]['Close'])
    total_return = PerformanceMetrics.calculate_total_return(10000.0, final_value)

    assert isinstance(total_return, float)


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v", "-m", "not slow"])
