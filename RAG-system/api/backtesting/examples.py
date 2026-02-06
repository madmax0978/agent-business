"""
Exemples d'utilisation du système de backtesting

Ce fichier contient des exemples pratiques pour utiliser le module de backtesting
"""

from engine import BacktestEngine
from strategies.ma_crossover import MovingAverageCrossover
from strategies.rsi_strategy import RSIMeanReversion
from strategies.bollinger import BollingerBandsBreakout
from strategies.macd import MACDCrossover
from strategies.momentum import MomentumStrategy
from strategies.buy_and_hold import BuyAndHold
from visualization import BacktestVisualizer


def example_1_simple_backtest():
    """
    Exemple 1: Backtest simple d'une stratégie MA Crossover sur LVMH
    """
    print("=" * 60)
    print("EXEMPLE 1: Backtest Simple - MA Crossover sur LVMH")
    print("=" * 60)

    # Créer le moteur
    engine = BacktestEngine(initial_capital=10000.0)

    # Créer la stratégie
    strategy = MovingAverageCrossover(fast_period=50, slow_period=200)

    # Lancer le backtest
    result = engine.run(
        ticker='MC.PA',  # LVMH
        start_date='2020-01-01',
        end_date='2024-12-31',
        strategy=strategy
    )

    # Afficher les résultats
    print(f"\nStratégie: {result.strategy_name}")
    print(f"Période: {result.start_date} to {result.end_date}")
    print(f"Capital Initial: {result.initial_capital:,.2f} €")
    print(f"Capital Final: {result.final_capital:,.2f} €")
    print(f"\nPerformance:")
    print(f"  - Rendement Total: {result.total_return:+.2f}%")
    print(f"  - Rendement Annualisé: {result.annualized_return:+.2f}%")
    print(f"  - Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"  - Sortino Ratio: {result.sortino_ratio:.2f}")
    print(f"  - Max Drawdown: {result.max_drawdown:.2f}%")
    print(f"  - Volatilité: {result.volatility:.2f}%")
    print(f"\nStatistiques de Trading:")
    print(f"  - Nombre de Trades: {result.num_trades}")
    print(f"  - Win Rate: {result.win_rate:.2f}%")
    print(f"  - Profit Factor: {result.profit_factor:.2f}")
    print(f"  - Trade Moyen: {result.avg_trade:+.2f}%")

    return result


def example_2_compare_strategies():
    """
    Exemple 2: Comparer plusieurs stratégies sur le même actif
    """
    print("\n" + "=" * 60)
    print("EXEMPLE 2: Comparaison de Stratégies sur Air Liquide")
    print("=" * 60)

    # Créer le moteur
    engine = BacktestEngine(initial_capital=10000.0)

    # Créer plusieurs stratégies
    strategies = [
        MovingAverageCrossover(fast_period=50, slow_period=200),
        RSIMeanReversion(rsi_period=14, oversold=30, overbought=70),
        BollingerBandsBreakout(period=20, std_dev=2.0),
        MACDCrossover(fast_period=12, slow_period=26, signal_period=9),
        MomentumStrategy(lookback_period=10, threshold=0.02),
        BuyAndHold(),
    ]

    # Comparer les stratégies
    comparison = engine.compare_strategies(
        ticker='AI.PA',  # Air Liquide
        start_date='2019-01-01',
        end_date='2024-12-31',
        strategies=strategies
    )

    # Afficher le classement
    print(f"\nMeilleure Stratégie: {comparison.best_strategy}")
    print(f"\nClassement par Sharpe Ratio:")
    for idx, rank in enumerate(comparison.comparison_metrics['ranking'], 1):
        print(f"  {idx}. {rank['strategy']}: "
              f"Sharpe={rank['sharpe']:.2f}, "
              f"Return={rank['return']:+.2f}%")

    return comparison


def example_3_optimize_parameters():
    """
    Exemple 3: Optimiser les paramètres d'une stratégie via Grid Search
    """
    print("\n" + "=" * 60)
    print("EXEMPLE 3: Optimisation de Paramètres - RSI Strategy")
    print("=" * 60)

    # Créer le moteur
    engine = BacktestEngine(initial_capital=10000.0)

    # Définir la grille de paramètres à tester
    param_grid = {
        'rsi_period': [10, 14, 20],
        'oversold': [20, 25, 30],
        'overbought': [70, 75, 80],
    }

    print(f"\nTest de {3 * 3 * 3} combinaisons de paramètres...")

    # Optimiser
    optimization = engine.optimize_parameters(
        ticker='OR.PA',  # L'Oréal
        start_date='2020-01-01',
        end_date='2024-12-31',
        strategy_class=RSIMeanReversion,
        param_grid=param_grid
    )

    # Afficher les résultats
    print(f"\nMeilleurs Paramètres:")
    for key, value in optimization['best_params'].items():
        print(f"  - {key}: {value}")

    print(f"\nPerformance avec meilleurs paramètres:")
    print(f"  - Sharpe Ratio: {optimization['best_sharpe_ratio']:.2f}")
    print(f"  - Rendement Total: {optimization['best_result'].total_return:+.2f}%")
    print(f"  - Max Drawdown: {optimization['best_result'].max_drawdown:.2f}%")

    print(f"\nTop 5 Combinaisons:")
    for idx, res in enumerate(optimization['all_results'][:5], 1):
        print(f"  {idx}. {res['params']} -> Sharpe: {res['sharpe_ratio']:.2f}")

    return optimization


def example_4_visualizations():
    """
    Exemple 4: Créer des visualisations des résultats
    """
    print("\n" + "=" * 60)
    print("EXEMPLE 4: Visualisations")
    print("=" * 60)

    # Lancer un backtest
    engine = BacktestEngine(initial_capital=10000.0)
    strategy = MovingAverageCrossover(fast_period=50, slow_period=200)

    result = engine.run(
        ticker='SAN.PA',  # Sanofi
        start_date='2020-01-01',
        end_date='2024-12-31',
        strategy=strategy
    )

    # Créer les visualisations
    visualizer = BacktestVisualizer()

    # 1. Equity Curve
    fig1 = visualizer.plot_equity_curve(result, show_trades=True)
    fig1.write_html('/tmp/equity_curve.html')
    print("\n1. Equity Curve sauvegardée: /tmp/equity_curve.html")

    # 2. Drawdown
    fig2 = visualizer.plot_drawdown(result)
    fig2.write_html('/tmp/drawdown.html')
    print("2. Drawdown sauvegardé: /tmp/drawdown.html")

    # 3. Distribution des rendements
    fig3 = visualizer.plot_returns_distribution(result)
    fig3.write_html('/tmp/returns_distribution.html')
    print("3. Distribution des rendements sauvegardée: /tmp/returns_distribution.html")

    print("\nOuvrez ces fichiers dans un navigateur pour voir les graphiques interactifs!")

    return result


def example_5_pea_portfolio_backtest():
    """
    Exemple 5: Backtest d'un portfolio PEA complet
    """
    print("\n" + "=" * 60)
    print("EXEMPLE 5: Backtest Portfolio PEA")
    print("=" * 60)

    # Actions PEA éligibles
    pea_stocks = {
        'MC.PA': 'LVMH',
        'OR.PA': 'L\'Oréal',
        'AI.PA': 'Air Liquide',
        'SAN.PA': 'Sanofi',
        'BNP.PA': 'BNP Paribas',
    }

    engine = BacktestEngine(initial_capital=10000.0)

    # Tester la même stratégie sur toutes les actions
    strategy_class = MovingAverageCrossover
    params = {'fast_period': 50, 'slow_period': 200}

    print("\nTest de MA Crossover sur 5 actions PEA:\n")

    results = {}
    for ticker, company in pea_stocks.items():
        strategy = strategy_class(**params)
        try:
            result = engine.run(
                ticker=ticker,
                start_date='2020-01-01',
                end_date='2024-12-31',
                strategy=strategy
            )
            results[company] = result

            print(f"{company} ({ticker}):")
            print(f"  Return: {result.total_return:+.2f}%")
            print(f"  Sharpe: {result.sharpe_ratio:.2f}")
            print(f"  Drawdown: {result.max_drawdown:.2f}%")
            print()

        except Exception as e:
            print(f"{company} ({ticker}): Erreur - {e}\n")

    # Trouver la meilleure action
    if results:
        best_stock = max(results.items(), key=lambda x: x[1].sharpe_ratio)
        print(f"Meilleure Action (Sharpe): {best_stock[0]} (Sharpe: {best_stock[1].sharpe_ratio:.2f})")

    return results


def example_6_api_usage():
    """
    Exemple 6: Utilisation via l'API REST (avec requests)
    """
    print("\n" + "=" * 60)
    print("EXEMPLE 6: Utilisation via API REST")
    print("=" * 60)

    import requests

    BASE_URL = "http://localhost:8000"
    TOKEN = "votre_token_jwt"  # Obtenu via /auth/login

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. Lister les stratégies disponibles
    print("\n1. Récupération des stratégies disponibles...")
    response = requests.get(f"{BASE_URL}/backtesting/strategies", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        strategies = response.json()
        print(f"Nombre de stratégies: {strategies['total']}")
        for s in strategies['strategies']:
            print(f"  - {s['name']}: {s['display_name']}")

    # 2. Lancer un backtest
    print("\n2. Lancement d'un backtest...")
    backtest_request = {
        "ticker": "MC.PA",
        "strategy": "ma_crossover",
        "params": {
            "fast_period": 50,
            "slow_period": 200
        },
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 10000.0,
        "commission": 0.001,
        "slippage": 0.0005
    }

    response = requests.post(
        f"{BASE_URL}/backtesting/run",
        json=backtest_request,
        headers=headers
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Backtest ID: {result['backtest_id']}")
        print(f"Return: {result['performance']['total_return']:+.2f}%")
        print(f"Sharpe: {result['performance']['sharpe_ratio']:.2f}")

    # 3. Comparer des stratégies
    print("\n3. Comparaison de stratégies...")
    compare_request = {
        "ticker": "MC.PA",
        "strategies": ["ma_crossover", "rsi", "buy_and_hold"],
        "start_date": "2020-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 10000.0
    }

    response = requests.post(
        f"{BASE_URL}/backtesting/compare",
        json=compare_request,
        headers=headers
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        comparison = response.json()
        print(f"Meilleure stratégie: {comparison['best_strategy']}")

    print("\nExemple terminé! (Note: Nécessite l'API en cours d'exécution)")


if __name__ == "__main__":
    # Exécuter tous les exemples
    print("SYSTÈME DE BACKTESTING RAG-PEA")
    print("Exemples d'utilisation\n")

    # Exemple 1: Backtest simple
    result1 = example_1_simple_backtest()

    # Exemple 2: Comparaison
    comparison = example_2_compare_strategies()

    # Exemple 3: Optimisation
    optimization = example_3_optimize_parameters()

    # Exemple 4: Visualisations
    result4 = example_4_visualizations()

    # Exemple 5: Portfolio PEA
    portfolio_results = example_5_pea_portfolio_backtest()

    # Exemple 6: API (nécessite l'API en cours d'exécution)
    # example_6_api_usage()

    print("\n" + "=" * 60)
    print("Tous les exemples terminés!")
    print("=" * 60)
