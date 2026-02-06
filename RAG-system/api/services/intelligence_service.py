"""
Service Intelligence - Agrégation ML + Backtesting + Agents IA

Ce service combine tous les outils d'analyse (ML predictions, backtesting, agents CrewAI)
pour fournir une recommandation d'investissement complète et fiable.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

# Imports des modules d'analyse
from ..ml.price_predictor import PricePredictor
from ..backtesting.engine import BacktestEngine
from ..backtesting.strategies import AVAILABLE_STRATEGIES
from ..services.data_fetcher import DataFetcher
from ..services.portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Signal d'un composant d'analyse"""
    source: str  # ML, BACKTESTING, TECHNICAL, FUNDAMENTAL
    decision: str  # BUY, HOLD, SELL
    confidence: float  # 0.0 to 1.0
    reasoning: str
    metadata: Optional[Dict] = None


@dataclass
class IntelligenceReport:
    """Rapport complet d'intelligence d'investissement"""
    ticker: str
    timestamp: str
    current_price: float

    # Prédictions ML
    ml_prediction: Optional[Dict] = None

    # Backtesting
    backtesting: Optional[Dict] = None

    # Analyse technique
    technical_analysis: Optional[Dict] = None

    # Analyse fondamentale
    fundamental_analysis: Optional[Dict] = None

    # Décision agrégée finale
    aggregated_recommendation: Optional[Dict] = None

    # Reasoning complet
    reasoning: str = ""

    # Tous les signaux
    signals: List[Signal] = None

    def __post_init__(self):
        if self.signals is None:
            self.signals = []


class IntelligenceService:
    """
    Service qui agrège tous les outils d'analyse pour une recommandation complète

    Pipeline:
    1. Récupération données marché (prix, volume, historique)
    2. Prédiction ML (LSTM/Prophet) - prix futurs 30 jours
    3. Backtesting - test 3 meilleures stratégies sur historique
    4. Analyse technique - RSI, MACD, Bollinger, etc.
    5. Analyse fondamentale - agents CrewAI (optionnel, coûteux)
    6. Agrégation - fusion de tous les signaux
    7. Recommandation finale - BUY/HOLD/SELL avec confiance
    """

    def __init__(self):
        """Initialise tous les composants d'analyse"""
        self.ml_predictor = PricePredictor(model_type='ensemble')
        self.backtest_engine = BacktestEngine(initial_capital=10000.0)
        self.data_fetcher = DataFetcher()
        self.portfolio_manager = PortfolioManager()

        logger.info("IntelligenceService initialisé")


    async def analyze_ticker(
        self,
        ticker: str,
        include_ml: bool = True,
        include_backtesting: bool = True,
        include_technical: bool = True,
        include_fundamental: bool = False,  # Coûteux (agents IA)
        backtest_period: str = "5Y"
    ) -> IntelligenceReport:
        """
        Analyse complète d'un ticker avec tous les outils disponibles

        Args:
            ticker: Symbole boursier (ex: MC.PA)
            include_ml: Inclure prédictions ML
            include_backtesting: Inclure backtesting stratégies
            include_technical: Inclure analyse technique
            include_fundamental: Inclure analyse fondamentale (agents)
            backtest_period: Période pour backtesting (1Y, 2Y, 5Y)

        Returns:
            IntelligenceReport avec toutes les analyses et recommandation finale
        """
        logger.info(f"🔍 Analyse complète de {ticker}")

        report = IntelligenceReport(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            current_price=0.0
        )

        try:
            # 1. Récupérer données marché actuelles
            current_data = self.data_fetcher.get_current_price(ticker)
            report.current_price = current_data.get('price', 0.0)

            # 2. ML Predictions (si demandé)
            if include_ml:
                ml_signal = await self._get_ml_signal(ticker)
                if ml_signal:
                    report.ml_prediction = ml_signal['data']
                    report.signals.append(ml_signal['signal'])

            # 3. Backtesting (si demandé)
            if include_backtesting:
                backtest_signal = await self._get_backtest_signal(ticker, backtest_period)
                if backtest_signal:
                    report.backtesting = backtest_signal['data']
                    report.signals.append(backtest_signal['signal'])

            # 4. Analyse Technique (si demandé)
            if include_technical:
                technical_signal = await self._get_technical_signal(ticker)
                if technical_signal:
                    report.technical_analysis = technical_signal['data']
                    report.signals.append(technical_signal['signal'])

            # 5. Analyse Fondamentale avec agents (si demandé)
            if include_fundamental:
                fundamental_signal = await self._get_fundamental_signal(ticker)
                if fundamental_signal:
                    report.fundamental_analysis = fundamental_signal['data']
                    report.signals.append(fundamental_signal['signal'])

            # 6. Agrégation de tous les signaux
            report.aggregated_recommendation = self._aggregate_signals(report.signals, report.current_price)
            report.reasoning = self._generate_reasoning(report)

            logger.info(f"✅ Analyse terminée - Recommandation: {report.aggregated_recommendation['decision']}")

        except Exception as e:
            logger.error(f"❌ Erreur analyse {ticker}: {e}")
            raise

        return report


    async def _get_ml_signal(self, ticker: str) -> Optional[Dict]:
        """Obtenir signal ML (prédictions LSTM/Prophet)"""
        try:
            logger.info(f"  📊 ML Predictions pour {ticker}")

            # Vérifier si modèle existe, sinon entraîner rapidement
            if not self.ml_predictor.model_exists(ticker):
                logger.warning(f"  ⚠️ Modèle non entraîné pour {ticker}, entraînement rapide...")
                # Entraînement rapide sur 2 ans
                self.ml_predictor.train(
                    ticker=ticker,
                    period="2y",
                    epochs=50,
                    save_model=True
                )

            # Prédire 30 jours
            predictions = self.ml_predictor.predict(ticker=ticker, horizon=30)

            # Extraire signal
            expected_return = predictions.get('expected_return_30d', 0.0)
            confidence = predictions.get('confidence_avg', 0.5)
            trend = predictions.get('trend', 'NEUTRAL')

            # Décision basée sur rendement attendu
            if expected_return > 3.0:  # > 3% sur 30j
                decision = "BUY"
            elif expected_return < -3.0:  # < -3% sur 30j
                decision = "SELL"
            else:
                decision = "HOLD"

            signal = Signal(
                source="ML",
                decision=decision,
                confidence=confidence,
                reasoning=f"ML predicts {expected_return:+.1f}% over 30 days ({trend} trend)",
                metadata=predictions
            )

            return {
                'data': predictions,
                'signal': signal
            }

        except Exception as e:
            logger.error(f"  ❌ Erreur ML: {e}")
            return None


    async def _get_backtest_signal(self, ticker: str, period: str = "5Y") -> Optional[Dict]:
        """Obtenir signal Backtesting (test stratégies historiques)"""
        try:
            logger.info(f"  📈 Backtesting pour {ticker}")

            # Définir dates
            end_date = datetime.now()
            if period == "1Y":
                start_date = end_date - timedelta(days=365)
            elif period == "2Y":
                start_date = end_date - timedelta(days=730)
            else:  # 5Y par défaut
                start_date = end_date - timedelta(days=1825)

            # Tester 3 stratégies performantes
            strategies_to_test = ["ma_crossover", "rsi_strategy", "macd"]
            best_strategy = None
            best_sharpe = -999

            for strategy_name in strategies_to_test:
                try:
                    result = self.backtest_engine.run_backtest(
                        ticker=ticker,
                        strategy_name=strategy_name,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        commission=0.001,
                        slippage=0.0005
                    )

                    if result['sharpe_ratio'] > best_sharpe:
                        best_sharpe = result['sharpe_ratio']
                        best_strategy = result

                except Exception as e:
                    logger.warning(f"    ⚠️ {strategy_name} failed: {e}")
                    continue

            if not best_strategy:
                return None

            # Décision basée sur performance historique
            sharpe = best_strategy.get('sharpe_ratio', 0)
            total_return = best_strategy.get('total_return', 0)

            if sharpe > 1.0 and total_return > 10:
                decision = "BUY"
                confidence = min(0.9, 0.5 + sharpe * 0.2)
            elif sharpe < 0.5 or total_return < 0:
                decision = "SELL"
                confidence = 0.6
            else:
                decision = "HOLD"
                confidence = 0.5

            signal = Signal(
                source="BACKTESTING",
                decision=decision,
                confidence=confidence,
                reasoning=f"Best strategy: {best_strategy['strategy']} (Sharpe: {sharpe:.2f}, Return: {total_return:+.1f}%)",
                metadata=best_strategy
            )

            return {
                'data': {
                    'best_strategy': best_strategy['strategy'],
                    'sharpe_ratio': sharpe,
                    'total_return': total_return,
                    'max_drawdown': best_strategy.get('max_drawdown', 0),
                    'win_rate': best_strategy.get('win_rate', 0),
                    'signal': decision
                },
                'signal': signal
            }

        except Exception as e:
            logger.error(f"  ❌ Erreur Backtesting: {e}")
            return None


    async def _get_technical_signal(self, ticker: str) -> Optional[Dict]:
        """Obtenir signal Analyse Technique (RSI, MACD, Bollinger)"""
        try:
            logger.info(f"  📉 Analyse Technique pour {ticker}")

            # Récupérer indicateurs techniques
            indicators = self.data_fetcher.get_technical_indicators(ticker)

            # RSI
            rsi = indicators.get('rsi', 50)
            rsi_signal = "BUY" if rsi < 35 else ("SELL" if rsi > 65 else "HOLD")

            # MACD
            macd = indicators.get('macd', {})
            macd_signal = macd.get('signal', 'NEUTRAL')

            # Bollinger Bands
            bollinger = indicators.get('bollinger', {})
            bb_signal = bollinger.get('signal', 'NEUTRAL')

            # Agrégation technique
            signals = [rsi_signal, macd_signal, bb_signal]
            buy_count = signals.count("BUY")
            sell_count = signals.count("SELL")

            if buy_count >= 2:
                decision = "BUY"
                confidence = 0.7
            elif sell_count >= 2:
                decision = "SELL"
                confidence = 0.7
            else:
                decision = "HOLD"
                confidence = 0.5

            signal = Signal(
                source="TECHNICAL",
                decision=decision,
                confidence=confidence,
                reasoning=f"RSI: {rsi:.1f} ({rsi_signal}), MACD: {macd_signal}, Bollinger: {bb_signal}",
                metadata=indicators
            )

            return {
                'data': {
                    'rsi': rsi,
                    'macd': macd_signal,
                    'bollinger': bb_signal,
                    'signal': decision
                },
                'signal': signal
            }

        except Exception as e:
            logger.error(f"  ❌ Erreur Technical: {e}")
            return None


    async def _get_fundamental_signal(self, ticker: str) -> Optional[Dict]:
        """Obtenir signal Analyse Fondamentale (Agents CrewAI)"""
        try:
            logger.info(f"  🤖 Analyse Fondamentale pour {ticker}")

            # TODO: Intégration agents CrewAI
            # Pour l'instant, signal neutre

            signal = Signal(
                source="FUNDAMENTAL",
                decision="HOLD",
                confidence=0.5,
                reasoning="Fundamental analysis not yet implemented",
                metadata={}
            )

            return {
                'data': {
                    'score': 5.0,
                    'signal': "HOLD"
                },
                'signal': signal
            }

        except Exception as e:
            logger.error(f"  ❌ Erreur Fundamental: {e}")
            return None


    def _aggregate_signals(self, signals: List[Signal], current_price: float) -> Dict:
        """
        Agrège tous les signaux en une recommandation finale

        Méthode: Vote pondéré par confiance
        """
        if not signals:
            return {
                'decision': 'HOLD',
                'confidence': 0.0,
                'signals_count': {'BUY': 0, 'HOLD': 0, 'SELL': 0},
                'reasoning': "No signals available"
            }

        # Compter les votes pondérés
        votes = {'BUY': 0.0, 'HOLD': 0.0, 'SELL': 0.0}
        for signal in signals:
            votes[signal.decision] += signal.confidence

        # Décision = vote maximum
        decision = max(votes, key=votes.get)

        # Confiance = moyenne des confiances des signaux concordants
        concordant_signals = [s for s in signals if s.decision == decision]
        confidence = sum(s.confidence for s in concordant_signals) / len(concordant_signals) if concordant_signals else 0.0

        # Ajuster confiance selon consensus
        total_weight = sum(votes.values())
        decision_weight = votes[decision]
        consensus_ratio = decision_weight / total_weight if total_weight > 0 else 0
        confidence = confidence * consensus_ratio

        # Calcul target price et stop loss
        if decision == "BUY":
            target_price = current_price * 1.10  # +10%
            stop_loss = current_price * 0.95  # -5%
            expected_return = 10.0
        elif decision == "SELL":
            target_price = current_price * 0.90  # -10%
            stop_loss = current_price * 1.05  # +5%
            expected_return = -10.0
        else:
            target_price = current_price
            stop_loss = current_price * 0.95
            expected_return = 0.0

        # Risk level
        if confidence > 0.75:
            risk_level = "LOW"
        elif confidence > 0.60:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"

        return {
            'decision': decision,
            'confidence': round(confidence, 2),
            'signals_count': {
                'BUY': sum(1 for s in signals if s.decision == 'BUY'),
                'HOLD': sum(1 for s in signals if s.decision == 'HOLD'),
                'SELL': sum(1 for s in signals if s.decision == 'SELL')
            },
            'target_price': round(target_price, 2),
            'stop_loss': round(stop_loss, 2),
            'expected_return': round(expected_return, 1),
            'risk_level': risk_level,
            'time_horizon': '30_DAYS',
            'reasoning': self._generate_aggregation_reasoning(signals, decision, confidence)
        }


    def _generate_aggregation_reasoning(self, signals: List[Signal], decision: str, confidence: float) -> str:
        """Génère le raisonnement de l'agrégation"""
        reasons = [f"{s.source}: {s.reasoning}" for s in signals]
        return f"Decision: {decision} (confidence: {confidence:.2f}). " + " | ".join(reasons)


    def _generate_reasoning(self, report: IntelligenceReport) -> str:
        """Génère le raisonnement complet du rapport"""
        parts = []

        if report.ml_prediction:
            parts.append(f"ML predicts {report.ml_prediction.get('expected_return_30d', 0):+.1f}% in 30 days")

        if report.backtesting:
            parts.append(f"Best backtest strategy: {report.backtesting['best_strategy']} (Sharpe: {report.backtesting['sharpe_ratio']:.2f})")

        if report.technical_analysis:
            parts.append(f"Technical: RSI={report.technical_analysis['rsi']:.1f}")

        if report.aggregated_recommendation:
            agg = report.aggregated_recommendation
            parts.append(f"Final: {agg['decision']} (conf: {agg['confidence']:.2f})")

        return ". ".join(parts) + "."
