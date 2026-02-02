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
