"""
Service pour récupérer les données financières via Yahoo Finance

Ce module fournit :
- Accès aux données Yahoo Finance avec cache LRU
- TTL de 5 minutes pour les données temps réel
- Type hints complets
- Gestion d'erreurs robuste
"""

from __future__ import annotations

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import time
from threading import Lock

from api.logging_config import get_logger


logger = get_logger(__name__)


class YahooFinanceService:
    """
    Service pour interagir avec Yahoo Finance API avec cache intelligent

    Le cache utilise une stratégie LRU avec TTL :
    - Les données de marché sont mises en cache 5 minutes
    - Les données historiques peuvent être cachées plus longtemps
    - Cache thread-safe pour usage concurrent
    """

    def __init__(self):
        """Initialise le service avec un cache vide"""
        self._cache: Dict[str, tuple[float, any]] = {}
        self._cache_lock = Lock()
        self._cache_ttl = 300  # 5 minutes en secondes
        logger.info("YahooFinanceService initialized with cache TTL of 5 minutes")

    def _is_cache_valid(self, key: str) -> bool:
        """
        Vérifie si une entrée du cache est encore valide

        Args:
            key: Clé du cache

        Returns:
            True si le cache est valide, False sinon
        """
        if key not in self._cache:
            return False

        timestamp, _ = self._cache[key]
        age = time.time() - timestamp
        return age < self._cache_ttl

    def _get_from_cache(self, key: str) -> Optional[any]:
        """
        Récupère une valeur du cache si valide

        Args:
            key: Clé du cache

        Returns:
            Valeur cachée ou None si expiré/absent
        """
        with self._cache_lock:
            if self._is_cache_valid(key):
                _, value = self._cache[key]
                logger.debug(f"Cache HIT for key: {key}")
                return value
            logger.debug(f"Cache MISS for key: {key}")
            return None

    def _set_cache(self, key: str, value: any) -> None:
        """
        Stocke une valeur dans le cache

        Args:
            key: Clé du cache
            value: Valeur à cacher
        """
        with self._cache_lock:
            self._cache[key] = (time.time(), value)
            logger.debug(f"Cache SET for key: {key}")

    def clear_cache(self, ticker: Optional[str] = None) -> None:
        """
        Nettoie le cache

        Args:
            ticker: Si spécifié, nettoie uniquement les entrées de ce ticker
                   Sinon, nettoie tout le cache
        """
        with self._cache_lock:
            if ticker:
                keys_to_delete = [k for k in self._cache.keys() if ticker in k]
                for key in keys_to_delete:
                    del self._cache[key]
                logger.info(f"Cache cleared for ticker: {ticker}")
            else:
                self._cache.clear()
                logger.info("Entire cache cleared")

    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """
        Récupère les informations complètes d'une action avec cache

        Args:
            ticker: Ticker Yahoo Finance (ex: "MC.PA" pour LVMH)

        Returns:
            Dict avec toutes les infos (prix, P/E, dividendes, etc.)
            None si le ticker n'est pas trouvé

        Example:
            >>> service = YahooFinanceService()
            >>> info = service.get_stock_info("MC.PA")
            >>> print(f"Prix: {info['current_price']} EUR")
        """
        cache_key = f"info_{ticker}"

        # Vérifier le cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            logger.debug(f"Fetching stock info for {ticker}")
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or len(info) < 5:
                logger.warning(f"No data found for ticker: {ticker}")
                return None

            result = {
                "ticker": ticker,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "current_price": info.get("currentPrice", 0),
                "previous_close": info.get("previousClose", 0),
                "day_change_percent": (
                    (info.get("currentPrice", 0) - info.get("previousClose", 0))
                    / info.get("previousClose", 1) * 100
                ),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", None),
                "forward_pe": info.get("forwardPE", None),
                "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
                "payout_ratio": info.get("payoutRatio", 0) * 100 if info.get("payoutRatio") else 0,
                "52w_high": info.get("fiftyTwoWeekHigh", 0),
                "52w_low": info.get("fiftyTwoWeekLow", 0),
                "avg_volume": info.get("averageVolume", 0),
                "beta": info.get("beta", None),
                "profit_margin": info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0,
                "debt_to_equity": info.get("debtToEquity", None),
                "return_on_equity": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else 0,
            }

            # Mettre en cache
            self._set_cache(cache_key, result)
            logger.debug(f"Stock info fetched and cached for {ticker}")

            return result

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {ticker}: {e}")
            return None

    def get_historical_data(
        self,
        ticker: str,
        period: str = "5y",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Récupère l'historique des cours

        Args:
            ticker: Ticker Yahoo Finance
            period: "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"
            interval: "1d", "1wk", "1mo"

        Returns:
            DataFrame avec colonnes: Date, Open, High, Low, Close, Volume
            DataFrame vide en cas d'erreur

        Example:
            >>> service = YahooFinanceService()
            >>> df = service.get_historical_data("MC.PA", period="1y")
            >>> print(df.tail())
        """
        cache_key = f"history_{ticker}_{period}_{interval}"

        # Vérifier le cache (historique peut être caché plus longtemps)
        cached = self._get_from_cache(cache_key)
        if cached is not None and isinstance(cached, pd.DataFrame):
            return cached

        try:
            logger.debug(f"Fetching historical data for {ticker} (period={period}, interval={interval})")
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if not df.empty:
                # Mettre en cache
                self._set_cache(cache_key, df)
                logger.debug(f"Historical data fetched and cached for {ticker}: {len(df)} rows")

            return df

        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {e}")
            return pd.DataFrame()

    def get_financials(self, ticker: str) -> Optional[Dict]:
        """
        Récupère les données financières fondamentales

        Args:
            ticker: Ticker Yahoo Finance

        Returns:
            Dict avec bilans, comptes de résultat, flux de trésorerie
            None en cas d'erreur

        Example:
            >>> service = YahooFinanceService()
            >>> financials = service.get_financials("MC.PA")
            >>> balance_sheet = financials['balance_sheet']
        """
        cache_key = f"financials_{ticker}"

        # Vérifier le cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            logger.debug(f"Fetching financials for {ticker}")
            stock = yf.Ticker(ticker)

            result = {
                "balance_sheet": stock.balance_sheet,
                "income_statement": stock.financials,
                "cash_flow": stock.cashflow,
                "earnings": stock.earnings,
                "quarterly_earnings": stock.quarterly_earnings,
            }

            # Mettre en cache
            self._set_cache(cache_key, result)
            logger.debug(f"Financials fetched and cached for {ticker}")

            return result

        except Exception as e:
            logger.error(f"Error fetching financials for {ticker}: {e}")
            return None

    def get_recommendations(self, ticker: str) -> pd.DataFrame:
        """
        Récupère les recommandations d'analystes

        Args:
            ticker: Ticker Yahoo Finance

        Returns:
            DataFrame avec les recommandations (Buy/Hold/Sell)
            DataFrame vide en cas d'erreur
        """
        cache_key = f"recommendations_{ticker}"

        # Vérifier le cache
        cached = self._get_from_cache(cache_key)
        if cached is not None and isinstance(cached, pd.DataFrame):
            return cached

        try:
            logger.debug(f"Fetching recommendations for {ticker}")
            stock = yf.Ticker(ticker)
            recommendations = stock.recommendations

            if recommendations is not None and not recommendations.empty:
                # Mettre en cache
                self._set_cache(cache_key, recommendations)
                logger.debug(f"Recommendations fetched and cached for {ticker}")

            return recommendations if recommendations is not None else pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching recommendations for {ticker}: {e}")
            return pd.DataFrame()

    def get_realtime_quote(self, ticker: str) -> Optional[Dict]:
        """
        Récupère le prix en temps réel (ou quasi-réel)

        Note: Le cache TTL est plus court pour les quotes temps réel

        Args:
            ticker: Ticker Yahoo Finance

        Returns:
            Dict avec prix actuel, volume, variation, etc.
            None en cas d'erreur
        """
        cache_key = f"quote_{ticker}"

        # Pour les quotes temps réel, on utilise un cache plus court
        # Vérifier le cache (2 minutes au lieu de 5)
        with self._cache_lock:
            if cache_key in self._cache:
                timestamp, value = self._cache[cache_key]
                if time.time() - timestamp < 120:  # 2 minutes
                    logger.debug(f"Cache HIT for realtime quote: {ticker}")
                    return value

        try:
            logger.debug(f"Fetching realtime quote for {ticker}")
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d", interval="1m")

            if not data.empty:
                latest = data.iloc[-1]
                result = {
                    "ticker": ticker,
                    "price": float(latest['Close']),
                    "volume": int(latest['Volume']),
                    "timestamp": latest.name.isoformat(),
                    "open": float(data.iloc[0]['Open']),
                    "high": float(data['High'].max()),
                    "low": float(data['Low'].min()),
                    "change_percent": float(((latest['Close'] - data.iloc[0]['Open']) / data.iloc[0]['Open']) * 100)
                }
            else:
                # Fallback sur données journalières
                info = stock.info
                result = {
                    "ticker": ticker,
                    "price": info.get('currentPrice', 0),
                    "volume": info.get('volume', 0),
                    "timestamp": datetime.now().isoformat(),
                }

            # Mettre en cache
            self._set_cache(cache_key, result)
            logger.debug(f"Realtime quote fetched and cached for {ticker}")

            return result

        except Exception as e:
            logger.error(f"Error fetching realtime quote for {ticker}: {e}")
            return None


# Dictionnaire des tickers français pour le PEA
FRENCH_TICKERS = {
    "LVMH": "MC.PA",
    "L'Oréal": "OR.PA",
    "Hermès": "RMS.PA",
    "Sanofi": "SAN.PA",
    "TotalEnergies": "TTE.PA",
    "Air Liquide": "AI.PA",
    "Schneider Electric": "SU.PA",
    "BNP Paribas": "BNP.PA",
    "AXA": "CS.PA",
    "Danone": "BN.PA",
    "Pernod Ricard": "RI.PA",
    "Kering": "KER.PA",
    "STMicroelectronics": "STM.PA",
    "Capgemini": "CAP.PA",
    "Dassault Systèmes": "DSY.PA",
    "Orange": "ORA.PA",
    "Engie": "ENGI.PA",
    "Saint-Gobain": "SGO.PA",
    "Société Générale": "GLE.PA",
    "Renault": "RNO.PA",
    "Vinci": "DG.PA",
    "Airbus": "AIR.PA",
    "Safran": "SAF.PA",
    "Carrefour": "CA.PA",
    "Bouygues": "EN.PA",
}


def get_ticker(company_name: str) -> Optional[str]:
    """Helper pour obtenir le ticker Yahoo Finance depuis le nom"""
    return FRENCH_TICKERS.get(company_name)


def get_company_name(ticker: str) -> Optional[str]:
    """Helper pour obtenir le nom depuis le ticker"""
    for name, tick in FRENCH_TICKERS.items():
        if tick == ticker:
            return name
    return None
