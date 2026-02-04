#!/usr/bin/env python3
"""
Script de test pour les handlers Telegram
Permet de tester tous les endpoints API avant de lancer le bot
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
USER_ID = "test_user"


def print_test(name: str, success: bool, details: str = ""):
    """Affiche le résultat d'un test"""
    icon = "✅" if success else "❌"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")


def test_api_health():
    """Test 1: Vérifier que l'API est en ligne"""
    print("\n🔍 Test 1: API Health Check")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        success = response.status_code == 200
        details = f"Status: {response.status_code}"
        print_test("API Health", success, details)
        return success
    except Exception as e:
        print_test("API Health", False, str(e))
        return False


def test_treasury_endpoints():
    """Test 2: Endpoints de trésorerie"""
    print("\n💰 Test 2: Trésorerie")

    # Test deposit
    try:
        response = requests.post(
            f"{API_BASE_URL}/portfolio/deposit",
            params={"amount": 10000, "user_id": USER_ID, "notes": "Test initial"}
        )
        success = response.status_code == 200
        print_test("POST /portfolio/deposit", success, f"Status: {response.status_code}")
    except Exception as e:
        print_test("POST /portfolio/deposit", False, str(e))

    # Test treasury status
    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/treasury",
            params={"user_id": USER_ID}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Cash: {data.get('cash_available', 0)}€"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /portfolio/treasury", success, details)
    except Exception as e:
        print_test("GET /portfolio/treasury", False, str(e))

    # Test deposit history
    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/treasury/deposits",
            params={"user_id": USER_ID, "limit": 5}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"{data.get('total_deposits', 0)} dépôts"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /portfolio/treasury/deposits", success, details)
    except Exception as e:
        print_test("GET /portfolio/treasury/deposits", False, str(e))

    # Test cashflow
    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/treasury/cashflow",
            params={"user_id": USER_ID, "limit": 10}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"{data.get('total_events', 0)} événements"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /portfolio/treasury/cashflow", success, details)
    except Exception as e:
        print_test("GET /portfolio/treasury/cashflow", False, str(e))


def test_portfolio_endpoints():
    """Test 3: Endpoints de portfolio"""
    print("\n📊 Test 3: Portfolio")

    # Test add position
    try:
        response = requests.post(
            f"{API_BASE_URL}/portfolio/add",
            json={
                "ticker": "MC.PA",
                "company_name": "LVMH",
                "quantity": 5,
                "price": 750.0,
                "user_id": USER_ID
            }
        )
        success = response.status_code == 200
        print_test("POST /portfolio/add", success, f"Status: {response.status_code}")
    except Exception as e:
        print_test("POST /portfolio/add", False, str(e))

    # Test get portfolio
    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio",
            params={"user_id": USER_ID}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"{data.get('total_positions', 0)} positions, Valeur: {data.get('total_value', 0)}€"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /portfolio", success, details)
    except Exception as e:
        print_test("GET /portfolio", False, str(e))

    # Test portfolio health
    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/health",
            params={"user_id": USER_ID}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Score: {data.get('score', 0)}/100, Grade: {data.get('grade', 'N/A')}"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /portfolio/health", success, details)
    except Exception as e:
        print_test("GET /portfolio/health", False, str(e))

    # Test rebalance
    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/rebalance",
            params={"user_id": USER_ID}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            needs = "Oui" if data.get('needs_rebalance') else "Non"
            details = f"Rééquilibrage nécessaire: {needs}"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /portfolio/rebalance", success, details)
    except Exception as e:
        print_test("GET /portfolio/rebalance", False, str(e))


def test_opportunities_endpoints():
    """Test 4: Endpoints d'opportunités"""
    print("\n💡 Test 4: Opportunités")

    # Test analyze opportunities
    try:
        response = requests.post(
            f"{API_BASE_URL}/portfolio/opportunities/analyze",
            params={"user_id": USER_ID}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            has_opp = "Oui" if data.get('has_opportunities') else "Non"
            count = len(data.get('opportunities', []))
            details = f"Opportunités: {has_opp} ({count} détectées)"
        else:
            details = f"Status: {response.status_code}"
        print_test("POST /portfolio/opportunities/analyze", success, details)
    except Exception as e:
        print_test("POST /portfolio/opportunities/analyze", False, str(e))

    # Test get pending opportunities
    try:
        response = requests.get(
            f"{API_BASE_URL}/portfolio/opportunities/pending",
            params={"user_id": USER_ID}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"{data.get('count', 0)} opportunités en attente"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /portfolio/opportunities/pending", success, details)
    except Exception as e:
        print_test("GET /portfolio/opportunities/pending", False, str(e))


def test_market_endpoints():
    """Test 5: Endpoints de market data"""
    print("\n📈 Test 5: Market Data")

    # Test stock info
    try:
        response = requests.get(f"{API_BASE_URL}/market/stock/MC.PA")
        success = response.status_code == 200
        if success:
            data = response.json()
            price = data.get('currentPrice', 0)
            details = f"Prix MC.PA: {price}€"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /market/stock/MC.PA", success, details)
    except Exception as e:
        print_test("GET /market/stock/MC.PA", False, str(e))

    # Test stock history
    try:
        response = requests.get(
            f"{API_BASE_URL}/market/history/MC.PA",
            params={"period": "1mo", "interval": "1d"}
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"{data.get('data_points', 0)} points de données"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /market/history/MC.PA", success, details)
    except Exception as e:
        print_test("GET /market/history/MC.PA", False, str(e))


def test_analysis_endpoints():
    """Test 6: Endpoints d'analyse"""
    print("\n🔍 Test 6: Analyses")

    # Test news
    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/news/LVMH",
            params={"days_back": 7},
            timeout=30
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"{data.get('news_count', 0)} articles"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /analysis/news/LVMH", success, details)
    except Exception as e:
        print_test("GET /analysis/news/LVMH", False, str(e))

    # Test technical analysis
    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/technical/MC.PA",
            params={"period": "6mo"},
            timeout=30
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Tendance: {data.get('trend', 'N/A')}"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /analysis/technical/MC.PA", success, details)
    except Exception as e:
        print_test("GET /analysis/technical/MC.PA", False, str(e))

    # Test complete analysis (peut être long)
    print("\n⏳ Analyse complète en cours (peut prendre 30-60s)...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/analysis/complete/MC.PA",
            params={"company_name": "LVMH"},
            timeout=120
        )
        success = response.status_code == 200
        if success:
            data = response.json()
            details = f"Ticker: {data.get('ticker', 'N/A')}"
        else:
            details = f"Status: {response.status_code}"
        print_test("GET /analysis/complete/MC.PA", success, details)
    except Exception as e:
        print_test("GET /analysis/complete/MC.PA", False, str(e))


def test_transactions():
    """Test 7: Transactions (vente)"""
    print("\n💰 Test 7: Transactions")

    # Test sell
    try:
        response = requests.post(
            f"{API_BASE_URL}/portfolio/sell",
            json={
                "ticker": "MC.PA",
                "quantity": 1,
                "price": 800.0,
                "user_id": USER_ID
            }
        )
        success = response.status_code == 200
        print_test("POST /portfolio/sell", success, f"Status: {response.status_code}")
    except Exception as e:
        print_test("POST /portfolio/sell", False, str(e))


def cleanup_test_data():
    """Nettoie les données de test"""
    print("\n🧹 Nettoyage des données de test...")
    # Note: Dans un vrai environnement, vous pourriez avoir un endpoint pour supprimer un utilisateur
    print("   (Les données de test restent en base pour inspection)")


def main():
    """Lance tous les tests"""
    print("=" * 60)
    print("🧪 TEST DES HANDLERS TELEGRAM - API ENDPOINTS")
    print("=" * 60)
    print(f"\n📡 API: {API_BASE_URL}")
    print(f"👤 Test User ID: {USER_ID}")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test 1: API Health
    if not test_api_health():
        print("\n❌ ERREUR: L'API n'est pas disponible!")
        print("   → Démarrez l'API avec: cd api && python main.py")
        return

    # Tests des endpoints
    test_treasury_endpoints()
    test_portfolio_endpoints()
    test_opportunities_endpoints()
    test_market_endpoints()
    test_analysis_endpoints()
    test_transactions()

    # Cleanup
    cleanup_test_data()

    print("\n" + "=" * 60)
    print("✅ TESTS TERMINÉS")
    print("=" * 60)
    print("\n💡 Prochaines étapes:")
    print("   1. Vérifier que tous les tests sont passés")
    print("   2. Lancer le bot Telegram: python telegram_bot_main.py")
    print("   3. Tester les commandes dans Telegram")
    print("\n📚 Documentation: TELEGRAM_HANDLERS_GUIDE.md")


if __name__ == "__main__":
    main()
