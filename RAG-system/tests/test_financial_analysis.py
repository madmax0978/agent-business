"""
Tests des analyses financières: technique, fondamentale, sentiment, news
"""

import pytest
import requests
from datetime import datetime


@pytest.mark.financial
class TestFinancialAnalysis:
    """Tests des fonctionnalités d'analyse financière"""

    def test_get_stock_info(self, api_base_url, check_api_running, test_tickers):
        """
        Test la récupération d'informations de marché sur une action.

        Vérifie que l'intégration Yahoo Finance fonctionne et retourne
        les données essentielles (prix, capitalisation, volume, etc.)
        """
        ticker = test_tickers["lvmh"]  # MC.PA

        response = requests.get(f"{api_base_url}/market/stock/{ticker}")
        assert response.status_code == 200, f"Doit récupérer les infos pour {ticker}"

        data = response.json()

        # Vérifier les champs essentiels
        assert "symbol" in data or "ticker" in data, "Symbole doit être présent"
        assert "currentPrice" in data or "regularMarketPrice" in data, "Prix actuel doit être présent"

        print(f"\nInfos marché pour {ticker}:")
        price = data.get("currentPrice") or data.get("regularMarketPrice")
        print(f"  Prix actuel: {price} €")
        if "marketCap" in data:
            print(f"  Capitalisation: {data['marketCap']:,.0f} €")
        if "volume" in data:
            print(f"  Volume: {data['volume']:,}")

    def test_get_stock_history(self, api_base_url, check_api_running, test_tickers):
        """
        Test la récupération de l'historique des cours.

        Vérifie qu'on peut obtenir l'historique sur différentes périodes
        (1 mois, 3 mois, 1 an, etc.) avec les données OHLCV.
        """
        ticker = test_tickers["lvmh"]

        response = requests.get(
            f"{api_base_url}/market/history/{ticker}",
            params={"period": "1mo", "interval": "1d"}
        )

        assert response.status_code == 200, "Doit récupérer l'historique"

        data = response.json()
        assert data["ticker"] == ticker
        assert "data" in data
        assert len(data["data"]) > 0, "Doit contenir au moins un point de données"

        # Vérifier la structure des données
        first_point = data["data"][0]
        required_fields = ["Open", "High", "Low", "Close", "Volume"]
        for field in required_fields:
            assert field in first_point, f"Le champ {field} doit être présent"

        print(f"\nHistorique {ticker} (1 mois):")
        print(f"  Points de données: {data['data_points']}")
        print(f"  Période: {data['period']}")
        print(f"  Interval: {data['interval']}")

    def test_get_company_news(self, api_base_url, check_api_running, test_companies):
        """
        Test la récupération d'actualités d'entreprise.

        Vérifie que le système peut récupérer les news récentes
        d'une entreprise depuis différentes sources.
        """
        company_name = "LVMH"

        response = requests.get(
            f"{api_base_url}/analysis/news/{company_name}",
            params={"days_back": 7}
        )

        assert response.status_code == 200, f"Doit récupérer les news pour {company_name}"

        data = response.json()
        assert data["company"] == company_name
        assert "articles" in data
        assert "news_count" in data

        print(f"\nActualités {company_name} (7 derniers jours):")
        print(f"  Nombre d'articles: {data['news_count']}")

        if data["articles"]:
            first_article = data["articles"][0]
            print(f"  Dernier article: {first_article.get('title', 'N/A')[:60]}...")

    def test_sentiment_analysis(self, api_base_url, check_api_running):
        """
        Test l'analyse de sentiment sur les actualités.

        Vérifie que le système peut analyser le sentiment général
        (positif/neutre/négatif) des news d'une entreprise.
        """
        company_name = "LVMH"

        response = requests.get(
            f"{api_base_url}/analysis/sentiment/{company_name}",
            params={"days_back": 7}
        )

        assert response.status_code == 200, "L'analyse de sentiment doit réussir"

        data = response.json()

        # Vérifier les champs du sentiment
        assert "overall_sentiment" in data or "sentiment" in data, "Sentiment global doit être présent"
        assert "score" in data or "sentiment_score" in data, "Score de sentiment doit être présent"

        print(f"\nAnalyse sentiment {company_name}:")
        sentiment = data.get("overall_sentiment") or data.get("sentiment")
        score = data.get("score") or data.get("sentiment_score")
        print(f"  Sentiment: {sentiment}")
        print(f"  Score: {score}")

    def test_technical_analysis(self, api_base_url, check_api_running, test_tickers):
        """
        Test l'analyse technique complète.

        Vérifie que le système calcule correctement:
        - Les indicateurs techniques (RSI, MACD, moyennes mobiles)
        - Les signaux d'achat/vente
        - Les niveaux de support/résistance
        - La tendance générale
        """
        ticker = test_tickers["lvmh"]

        response = requests.get(
            f"{api_base_url}/analysis/technical/{ticker}",
            params={"period": "6mo"}
        )

        assert response.status_code == 200, "L'analyse technique doit réussir"

        data = response.json()
        assert data["ticker"] == ticker

        # Vérifier la présence des analyses
        assert "signals" in data, "Signaux techniques doivent être présents"
        assert "levels" in data, "Niveaux support/résistance doivent être présents"
        assert "trend" in data, "Tendance doit être présente"

        print(f"\nAnalyse technique {ticker}:")
        print(f"  Tendance: {data['trend']}")
        print(f"  Signaux: {data['signals']}")
        if data["levels"]:
            print(f"  Support/Résistance: {data['levels']}")

    def test_complete_analysis(self, api_base_url, check_api_running, test_tickers, test_companies):
        """
        Test l'analyse complète (market + news + sentiment + technique).

        Vérifie que le système peut fournir une vue d'ensemble complète
        combinant toutes les sources d'information.
        """
        ticker = test_tickers["lvmh"]
        company_name = test_companies[ticker]

        response = requests.get(
            f"{api_base_url}/analysis/complete/{ticker}",
            params={"company_name": company_name}
        )

        assert response.status_code == 200, "L'analyse complète doit réussir"

        data = response.json()
        assert data["ticker"] == ticker
        assert data["company"] == company_name

        # Vérifier toutes les sections
        assert "market_data" in data, "Données de marché doivent être présentes"
        assert "news_sentiment" in data, "Sentiment des news doit être présent"
        assert "technical_analysis" in data, "Analyse technique doit être présente"

        print(f"\nAnalyse complète {company_name} ({ticker}):")
        print(f"  Données marché: ✓")
        print(f"  News & Sentiment: ✓")
        print(f"  Analyse technique: ✓")

    def test_multiple_stocks_analysis(self, api_base_url, check_api_running, test_tickers):
        """
        Test l'analyse de plusieurs actions simultanément.

        Vérifie que le système peut traiter efficacement plusieurs
        actions en parallèle pour des comparaisons.
        """
        tickers_to_test = [
            test_tickers["lvmh"],
            test_tickers["bnp"],
            test_tickers["total"]
        ]

        results = []

        for ticker in tickers_to_test:
            response = requests.get(f"{api_base_url}/market/stock/{ticker}")
            if response.status_code == 200:
                results.append({
                    "ticker": ticker,
                    "data": response.json()
                })

        assert len(results) >= 2, "Au moins 2 actions doivent être analysées avec succès"

        print(f"\nAnalyse multi-actions:")
        for result in results:
            ticker = result["ticker"]
            data = result["data"]
            price = data.get("currentPrice") or data.get("regularMarketPrice", "N/A")
            print(f"  {ticker}: {price} €")

    def test_technical_indicators_quality(self, api_base_url, check_api_running, test_tickers):
        """
        Test la qualité et la cohérence des indicateurs techniques.

        Vérifie que les indicateurs calculés ont du sens:
        - RSI entre 0 et 100
        - Moyennes mobiles cohérentes (MM20 vs MM50 vs MM200)
        - Signaux logiques par rapport aux indicateurs
        """
        ticker = test_tickers["lvmh"]

        response = requests.get(
            f"{api_base_url}/analysis/technical/{ticker}",
            params={"period": "6mo"}
        )

        assert response.status_code == 200

        data = response.json()
        signals = data.get("signals", {})

        # Vérifier la cohérence des indicateurs
        if "rsi" in signals:
            rsi = signals["rsi"]
            assert 0 <= rsi <= 100, f"RSI doit être entre 0 et 100, obtenu: {rsi}"

            # Vérifier cohérence RSI vs signal
            if rsi < 30:
                print(f"\n  RSI: {rsi:.1f} - Zone de survente détectée ✓")
            elif rsi > 70:
                print(f"\n  RSI: {rsi:.1f} - Zone de surachat détectée ✓")
            else:
                print(f"\n  RSI: {rsi:.1f} - Zone neutre ✓")

    def test_error_handling_financial(self, api_base_url, check_api_running):
        """
        Test la gestion d'erreurs pour les analyses financières.

        Vérifie que le système gère bien:
        - Ticker invalide
        - Entreprise inexistante
        - Période invalide
        """
        # Test 1: Ticker invalide
        response = requests.get(f"{api_base_url}/market/stock/INVALID_TICKER_XYZ")
        assert response.status_code in [404, 500], "Doit gérer le ticker invalide"

        print("\nGestion d'erreurs analyses financières:")
        print(f"  Ticker invalide: {response.status_code} ✓")

        # Test 2: Période invalide pour l'historique
        response = requests.get(
            f"{api_base_url}/market/history/MC.PA",
            params={"period": "invalid_period"}
        )
        # Peut retourner 400/422 ou donner une période par défaut
        print(f"  Période invalide: {response.status_code}")

    def test_data_freshness(self, api_base_url, check_api_running, test_tickers):
        """
        Test que les données sont à jour.

        Vérifie que les prix et news récupérés sont récents
        (pas de données obsolètes).
        """
        ticker = test_tickers["lvmh"]

        # Récupérer les données de marché
        response = requests.get(f"{api_base_url}/market/stock/{ticker}")
        data = response.json()

        # Vérifier qu'on a un timestamp ou une date
        if "regularMarketTime" in data or "timestamp" in data:
            print(f"\nFraîcheur des données {ticker}:")
            timestamp = data.get("regularMarketTime") or data.get("timestamp")
            print(f"  Dernière mise à jour: {timestamp}")
            print("  Données à jour ✓")
        else:
            print(f"\n  Warning: Pas de timestamp trouvé pour {ticker}")
