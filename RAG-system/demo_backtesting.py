#!/usr/bin/env python3
"""
Script de démonstration du système de backtesting RAG-PEA

Teste rapidement plusieurs stratégies sur une action PEA
"""

import sys
sys.path.insert(0, 'api')

from backtesting.engine import BacktestEngine
from backtesting.strategies.ma_crossover import MovingAverageCrossover
from backtesting.strategies.rsi_strategy import RSIMeanReversion
from backtesting.strategies.buy_and_hold import BuyAndHold
from backtesting.strategies.momentum import MomentumStrategy
from backtesting.visualization import BacktestVisualizer
import warnings
warnings.filterwarnings('ignore')


def print_separator():
    print("\n" + "=" * 80 + "\n")


def demo_simple_backtest():
    """Démonstration 1: Backtest simple"""
    print_separator()
    print("DÉMONSTRATION 1: Backtest Simple - LVMH (MC.PA)")
    print_separator()

    # Créer le moteur
    engine = BacktestEngine(
        initial_capital=10000.0,
        commission=0.001,  # 0.1%
        slippage=0.0005    # 0.05%
    )

    # Créer la stratégie
    strategy = MovingAverageCrossover(fast_period=50, slow_period=200)

    print(f"📊 Stratégie: {strategy.get_name()}")
    print(f"⚙️  Paramètres: {strategy.get_params()}")
    print(f"💰 Capital Initial: 10,000.00 €")
    print(f"📅 Période: 2022-01-01 à 2024-12-31\n")

    print("⏳ Téléchargement des données et exécution du backtest...")

    # Lancer le backtest
    result = engine.run(
        ticker='MC.PA',
        start_date='2022-01-01',
        end_date='2024-12-31',
        strategy=strategy
    )

    # Afficher les résultats
    print("\n✅ Backtest terminé!\n")
    print("📈 PERFORMANCE:")
    print(f"   • Capital Final: {result.final_capital:,.2f} €")
    print(f"   • Rendement Total: {result.total_return:+.2f}%")
    print(f"   • Rendement Annualisé: {result.annualized_return:+.2f}%")
    print(f"   • Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"   • Sortino Ratio: {result.sortino_ratio:.2f}")
    print(f"   • Max Drawdown: {result.max_drawdown:.2f}%")
    print(f"   • Volatilité: {result.volatility:.2f}%")

    print("\n📊 TRADING:")
    print(f"   • Nombre de Trades: {result.num_trades}")
    print(f"   • Win Rate: {result.win_rate:.2f}%")
    print(f"   • Profit Factor: {result.profit_factor:.2f}")
    print(f"   • Trade Moyen: {result.avg_trade:+.2f}%")

    if result.num_trades > 0:
        print(f"   • Meilleur Gain: {result.max_win:+.2f}%")
        print(f"   • Pire Perte: {result.max_loss:+.2f}%")

    return result


def demo_compare_strategies():
    """Démonstration 2: Comparaison de stratégies"""
    print_separator()
    print("DÉMONSTRATION 2: Comparaison de 4 Stratégies sur Air Liquide (AI.PA)")
    print_separator()

    # Créer le moteur
    engine = BacktestEngine(initial_capital=10000.0)

    # Créer les stratégies
    strategies = [
        MovingAverageCrossover(fast_period=50, slow_period=200),
        RSIMeanReversion(rsi_period=14, oversold=30, overbought=70),
        MomentumStrategy(lookback_period=10, threshold=0.02),
        BuyAndHold(),
    ]

    print("📊 Stratégies testées:")
    for s in strategies:
        print(f"   • {s.get_name()}")

    print(f"\n📅 Période: 2022-01-01 à 2024-12-31")
    print("⏳ Exécution de 4 backtests...\n")

    # Comparer
    comparison = engine.compare_strategies(
        ticker='AI.PA',
        start_date='2022-01-01',
        end_date='2024-12-31',
        strategies=strategies
    )

    # Afficher le classement
    print("✅ Comparaison terminée!\n")
    print("🏆 CLASSEMENT PAR SHARPE RATIO:\n")

    for idx, rank in enumerate(comparison.comparison_metrics['ranking'], 1):
        emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "  "
        print(f"{emoji} {idx}. {rank['strategy']}")
        print(f"      • Rendement: {rank['return']:+.2f}%")
        print(f"      • Sharpe: {rank['sharpe']:.2f}\n")

    print(f"🎯 Meilleure Stratégie: {comparison.best_strategy}")

    return comparison


def demo_optimization():
    """Démonstration 3: Optimisation de paramètres"""
    print_separator()
    print("DÉMONSTRATION 3: Optimisation RSI sur Sanofi (SAN.PA)")
    print_separator()

    # Créer le moteur
    engine = BacktestEngine(initial_capital=10000.0)

    # Grille de paramètres (réduite pour la démo)
    param_grid = {
        'rsi_period': [10, 14, 20],
        'oversold': [25, 30],
        'overbought': [70, 75],
    }

    total_combinations = 3 * 2 * 2
    print(f"🔍 Grid Search: {total_combinations} combinaisons de paramètres")
    print(f"⚙️  Paramètres testés:")
    for param, values in param_grid.items():
        print(f"   • {param}: {values}")

    print(f"\n📅 Période: 2022-01-01 à 2024-12-31")
    print("⏳ Optimisation en cours...\n")

    # Optimiser
    optimization = engine.optimize_parameters(
        ticker='SAN.PA',
        start_date='2022-01-01',
        end_date='2024-12-31',
        strategy_class=RSIMeanReversion,
        param_grid=param_grid
    )

    # Afficher les résultats
    print("✅ Optimisation terminée!\n")
    print("🎯 MEILLEURS PARAMÈTRES:")
    for param, value in optimization['best_params'].items():
        print(f"   • {param}: {value}")

    print(f"\n📈 PERFORMANCE AVEC MEILLEURS PARAMÈTRES:")
    best_result = optimization['best_result']
    print(f"   • Rendement Total: {best_result.total_return:+.2f}%")
    print(f"   • Sharpe Ratio: {best_result.sharpe_ratio:.2f}")
    print(f"   • Max Drawdown: {best_result.max_drawdown:.2f}%")
    print(f"   • Win Rate: {best_result.win_rate:.2f}%")

    print(f"\n📊 TOP 3 COMBINAISONS:")
    for idx, res in enumerate(optimization['all_results'][:3], 1):
        print(f"   {idx}. {res['params']}")
        print(f"      Sharpe: {res['sharpe_ratio']:.2f}, Return: {res['total_return']:+.2f}%")

    return optimization


def demo_visualization(result):
    """Démonstration 4: Visualisations"""
    print_separator()
    print("DÉMONSTRATION 4: Génération de Visualisations")
    print_separator()

    visualizer = BacktestVisualizer()

    print("📊 Création des graphiques interactifs...\n")

    # 1. Equity Curve
    fig1 = visualizer.plot_equity_curve(result, show_trades=True, compare_with_buy_hold=True)
    fig1.write_html('/tmp/backtesting_equity_curve.html')
    print("✅ 1. Equity Curve: /tmp/backtesting_equity_curve.html")

    # 2. Drawdown
    fig2 = visualizer.plot_drawdown(result)
    fig2.write_html('/tmp/backtesting_drawdown.html')
    print("✅ 2. Drawdown: /tmp/backtesting_drawdown.html")

    # 3. Distribution des rendements
    fig3 = visualizer.plot_returns_distribution(result)
    fig3.write_html('/tmp/backtesting_returns.html')
    print("✅ 3. Distribution des rendements: /tmp/backtesting_returns.html")

    print("\n💡 Ouvrez ces fichiers dans votre navigateur pour voir les graphiques interactifs!")


def main():
    """Fonction principale"""
    print("\n" + "🚀 " * 20)
    print("SYSTÈME DE BACKTESTING RAG-PEA")
    print("Démonstration Complète")
    print("🚀 " * 20)

    try:
        # Démo 1: Backtest simple
        result1 = demo_simple_backtest()

        # Démo 2: Comparaison
        comparison = demo_compare_strategies()

        # Démo 3: Optimisation
        optimization = demo_optimization()

        # Démo 4: Visualisations
        demo_visualization(result1)

        # Résumé final
        print_separator()
        print("🎉 DÉMONSTRATION TERMINÉE AVEC SUCCÈS!")
        print_separator()

        print("\n📚 PROCHAINES ÉTAPES:\n")
        print("1. Consultez la documentation: api/backtesting/README.md")
        print("2. Explorez les exemples: api/backtesting/examples.py")
        print("3. Lancez les tests: pytest tests/test_backtesting.py")
        print("4. Utilisez l'API REST: POST /backtesting/run")
        print("\n💡 Conseil: Commencez par Buy & Hold pour avoir une baseline!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Démonstration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        print("\nNote: Ce script nécessite une connexion internet pour télécharger les données.")
        print("Si l'erreur persiste, vérifiez que yfinance est bien installé:")
        print("  pip install yfinance")


if __name__ == "__main__":
    main()
