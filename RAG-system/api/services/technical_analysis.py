"""
Analyse technique complète avec indicateurs
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class TechnicalAnalyzer:
    """Analyseur technique avec calcul d'indicateurs"""

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule tous les indicateurs techniques

        Args:
            df: DataFrame avec colonnes Open, High, Low, Close, Volume

        Returns:
            DataFrame enrichi avec tous les indicateurs
        """
        try:
            import pandas_ta as ta

            # Moyennes mobiles
            df['SMA_50'] = ta.sma(df['Close'], length=50)
            df['SMA_200'] = ta.sma(df['Close'], length=200)
            df['EMA_20'] = ta.ema(df['Close'], length=20)

            # RSI
            df['RSI'] = ta.rsi(df['Close'], length=14)

            # MACD
            macd = ta.macd(df['Close'])
            if macd is not None and not macd.empty:
                df['MACD'] = macd['MACD_12_26_9']
                df['MACD_signal'] = macd['MACDs_12_26_9']
                df['MACD_histogram'] = macd['MACDh_12_26_9']

            # Bandes de Bollinger
            bbands = ta.bbands(df['Close'], length=20)
            if bbands is not None and not bbands.empty:
                # Les noms de colonnes peuvent varier selon la version de pandas_ta
                bb_cols = bbands.columns.tolist()
                bb_upper = [col for col in bb_cols if col.startswith('BBU_')]
                bb_middle = [col for col in bb_cols if col.startswith('BBM_')]
                bb_lower = [col for col in bb_cols if col.startswith('BBL_')]

                if bb_upper:
                    df['BB_upper'] = bbands[bb_upper[0]]
                if bb_middle:
                    df['BB_middle'] = bbands[bb_middle[0]]
                if bb_lower:
                    df['BB_lower'] = bbands[bb_lower[0]]

            # Volume
            df['Volume_SMA'] = ta.sma(df['Volume'], length=20)

        except ImportError:
            print("⚠️ pandas-ta non disponible, utilisation de calculs manuels")
            df = TechnicalAnalyzer._calculate_indicators_manual(df)

        return df

    @staticmethod
    def _calculate_indicators_manual(df: pd.DataFrame) -> pd.DataFrame:
        """Calcul manuel des indicateurs si pandas-ta n'est pas disponible"""
        # SMA
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']

        # Bandes de Bollinger
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (std * 2)
        df['BB_lower'] = df['BB_middle'] - (std * 2)

        # Volume
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()

        return df

    @staticmethod
    def detect_signals(df: pd.DataFrame) -> Dict:
        """
        Détecte les signaux d'achat/vente

        Returns:
            Dict avec les signaux et leur force
        """
        latest = df.iloc[-1]
        signals = []
        score = 0  # Score global de -100 (très baissier) à +100 (très haussier)

        # Signal 1: Position par rapport aux MA
        if pd.notna(latest.get('SMA_50')) and pd.notna(latest.get('SMA_200')):
            if latest['Close'] > latest['SMA_50'] > latest['SMA_200']:
                signals.append("✅ Prix au-dessus des MA 50 et 200 (haussier)")
                score += 20
            elif latest['Close'] < latest['SMA_50'] < latest['SMA_200']:
                signals.append("⚠️ Prix en-dessous des MA 50 et 200 (baissier)")
                score -= 20

            # Golden Cross / Death Cross
            if len(df) >= 2:
                if latest['SMA_50'] > latest['SMA_200']:
                    prev_50 = df.iloc[-2].get('SMA_50')
                    prev_200 = df.iloc[-2].get('SMA_200')
                    if pd.notna(prev_50) and pd.notna(prev_200):
                        if prev_50 <= prev_200:
                            signals.append("🌟 GOLDEN CROSS: MA50 croise MA200 à la hausse (TRÈS HAUSSIER)")
                            score += 30

        # Signal 2: RSI
        if pd.notna(latest.get('RSI')):
            if latest['RSI'] < 30:
                signals.append(f"🔵 RSI à {latest['RSI']:.1f} - Zone de survente (opportunité d'achat)")
                score += 15
            elif latest['RSI'] > 70:
                signals.append(f"🔴 RSI à {latest['RSI']:.1f} - Zone de surachat (risque de correction)")
                score -= 15
            elif 40 <= latest['RSI'] <= 60:
                signals.append(f"⚪ RSI à {latest['RSI']:.1f} - Zone neutre")

        # Signal 3: MACD
        if pd.notna(latest.get('MACD')) and pd.notna(latest.get('MACD_signal')):
            if latest['MACD'] > latest['MACD_signal']:
                signals.append("📈 MACD au-dessus du signal (momentum haussier)")
                score += 10
            else:
                signals.append("📉 MACD en-dessous du signal (momentum baissier)")
                score -= 10

        # Signal 4: Bandes de Bollinger
        if pd.notna(latest.get('BB_upper')) and pd.notna(latest.get('BB_lower')):
            if latest['BB_upper'] != latest['BB_lower']:
                bb_position = (latest['Close'] - latest['BB_lower']) / (latest['BB_upper'] - latest['BB_lower'])

                if bb_position < 0.2:
                    signals.append("💎 Prix proche de la bande basse de Bollinger (opportunité)")
                    score += 15
                elif bb_position > 0.8:
                    signals.append("⚡ Prix proche de la bande haute de Bollinger (prudence)")
                    score -= 10

        # Signal 5: Volume
        if pd.notna(latest.get('Volume')) and pd.notna(latest.get('Volume_SMA')):
            if latest['Volume'] > latest['Volume_SMA'] * 1.5:
                signals.append("🔊 Volume élevé (confirmation du mouvement)")
                score += 5

        # Déterminer la recommandation
        if score >= 50:
            recommendation = "ACHETER FORT"
        elif score >= 25:
            recommendation = "ACHETER"
        elif score >= 10:
            recommendation = "ACCUMULER"
        elif score >= -10:
            recommendation = "CONSERVER"
        elif score >= -25:
            recommendation = "ALLÉGER"
        else:
            recommendation = "VENDRE"

        return {
            "score": score,
            "recommendation": recommendation,
            "signals": signals,
            "current_price": latest['Close'],
            "sma_50": latest.get('SMA_50'),
            "sma_200": latest.get('SMA_200'),
            "rsi": latest.get('RSI'),
            "macd": latest.get('MACD')
        }

    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict:
        """Calcule les niveaux de support et résistance"""
        # Support = minimum local
        df['local_min'] = df['Low'].rolling(window=window, center=True).min()
        supports = df[df['Low'] == df['local_min']]['Low'].unique()

        # Résistance = maximum local
        df['local_max'] = df['High'].rolling(window=window, center=True).max()
        resistances = df[df['High'] == df['local_max']]['High'].unique()

        # Garder les 3 niveaux les plus proches du prix actuel
        current_price = df.iloc[-1]['Close']

        supports_sorted = sorted([s for s in supports if s < current_price], reverse=True)[:3]
        resistances_sorted = sorted([r for r in resistances if r > current_price])[:3]

        return {
            "supports": [float(s) for s in supports_sorted],
            "resistances": [float(r) for r in resistances_sorted],
            "current_price": float(current_price)
        }

    @staticmethod
    def calculate_trend(df: pd.DataFrame, period: int = 50) -> str:
        """
        Détermine la tendance actuelle

        Returns:
            "HAUSSIER", "BAISSIER", ou "NEUTRE"
        """
        if len(df) < period:
            return "NEUTRE"

        # Calculer la pente de la SMA
        sma = df['Close'].rolling(window=period).mean()

        if pd.notna(sma.iloc[-1]) and pd.notna(sma.iloc[-period]):
            slope = (sma.iloc[-1] - sma.iloc[-period]) / sma.iloc[-period]

            if slope > 0.05:  # +5%
                return "HAUSSIER"
            elif slope < -0.05:  # -5%
                return "BAISSIER"
            else:
                return "NEUTRE"

        return "NEUTRE"
