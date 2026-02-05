"""
Configuration pytest et fixtures communes pour tous les tests
"""

import pytest
import requests
import sys
from pathlib import Path
from datetime import datetime
import time

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def api_base_url():
    """URL de base de l'API"""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def check_api_running(api_base_url):
    """Vérifie que l'API est accessible avant de lancer les tests"""
    try:
        response = requests.get(f"{api_base_url}/health", timeout=5)
        if response.status_code != 200:
            pytest.skip("API non accessible - démarrez l'API avec 'uvicorn api.main:app'")
    except requests.exceptions.RequestException:
        pytest.skip("API non accessible - démarrez l'API avec 'uvicorn api.main:app'")
    return True


@pytest.fixture(scope="session")
def auth_token(api_base_url):
    """
    Obtient un token JWT pour authentifier les requêtes de test.

    Utilise les credentials par défaut (admin/changeme) depuis .env
    Le token est valide 30 jours pour les tests.
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Credentials depuis .env
    username = os.getenv("API_USERNAME", "admin")
    password = os.getenv("API_PASSWORD", "changeme")

    try:
        response = requests.post(
            f"{api_base_url}/auth/login",
            json={"username": username, "password": password},
            timeout=5
        )

        if response.status_code == 200:
            token = response.json()["access_token"]
            return token
        else:
            pytest.skip(f"Authentification échouée: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        pytest.skip(f"Impossible de s'authentifier: {e}")


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """
    Headers d'authentification JWT pour les requêtes de test.

    Utilise le token obtenu via auth_token().
    À inclure dans toutes les requêtes protégées.

    Usage:
        requests.get(f"{api_base_url}/portfolio", headers=auth_headers)
    """
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="session")
def test_tickers():
    """Liste de tickers pour tests réels"""
    return {
        "lvmh": "MC.PA",          # LVMH - Luxe
        "bnp": "BNP.PA",          # BNP Paribas - Banque
        "total": "TTE.PA",        # TotalEnergies - Énergie
        "airbus": "AIR.PA",       # Airbus - Aéronautique
        "loreal": "OR.PA",        # L'Oréal - Cosmétiques
    }


@pytest.fixture(scope="session")
def test_companies():
    """Liste d'entreprises pour tests"""
    return {
        "MC.PA": "LVMH",
        "BNP.PA": "BNP Paribas",
        "TTE.PA": "TotalEnergies",
        "AIR.PA": "Airbus",
        "OR.PA": "L'Oréal",
    }


@pytest.fixture
def sample_portfolio():
    """Portefeuille de test"""
    return {
        "positions": [
            {
                "ticker": "MC.PA",
                "company_name": "LVMH",
                "quantity": 10,
                "avg_price": 700.0,
            },
            {
                "ticker": "BNP.PA",
                "company_name": "BNP Paribas",
                "quantity": 50,
                "avg_price": 55.0,
            },
        ],
        "total_invested": 9750.0,
    }


@pytest.fixture
def test_document_path():
    """Chemin vers un document PDF de test (si disponible)"""
    # Chercher un PDF de test dans le répertoire data
    data_dir = Path(__file__).parent.parent / "data" / "documents"
    if data_dir.exists():
        pdf_files = list(data_dir.glob("*.pdf"))
        if pdf_files:
            return str(pdf_files[0])
    return None


@pytest.fixture
def cleanup_test_collections(api_base_url):
    """Nettoie les collections de test après les tests"""
    test_collections = []

    yield test_collections

    # Cleanup après les tests
    for collection_name in test_collections:
        try:
            requests.delete(f"{api_base_url}/collections/{collection_name}")
        except:
            pass


def pytest_configure(config):
    """Configuration personnalisée de pytest"""
    print("\n" + "="*80)
    print("RAG-PEA SYSTEM - SUITE DE TESTS COMPLÈTE")
    print("="*80)
    print(f"Début des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")


def pytest_sessionfinish(session, exitstatus):
    """Affichage du résumé après tous les tests"""
    print("\n" + "="*80)
    print(f"Fin des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
