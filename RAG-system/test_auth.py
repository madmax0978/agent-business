"""
Script de test pour l'authentification JWT
"""

import requests
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

# Credentials par défaut (à adapter selon votre .env)
USERNAME = "admin"
PASSWORD = "changeme"


def print_section(title):
    """Affiche un titre de section"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_login_success():
    """Test 1: Login avec bonnes credentials"""
    print_section("TEST 1: Login avec bonnes credentials")

    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"\n✅ SUCCESS: Token obtenu")
        print(f"Token (premiers 50 chars): {token[:50]}...")
        return token
    else:
        print(f"\n❌ FAILED: Login échoué")
        return None


def test_login_failure():
    """Test 2: Login avec mauvaises credentials"""
    print_section("TEST 2: Login avec mauvaises credentials")

    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": "wrong", "password": "wrong"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 401:
        print(f"\n✅ SUCCESS: Login correctement refusé (401)")
        return True
    else:
        print(f"\n❌ FAILED: Devrait retourner 401")
        return False


def test_verify_token(token):
    """Test 3: Vérification du token"""
    print_section("TEST 3: Vérification du token")

    response = requests.get(
        f"{API_BASE_URL}/auth/verify",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    if response.status_code == 200:
        data = response.json()
        if data.get("valid"):
            print(f"\n✅ SUCCESS: Token valide")
            print(f"Username: {data.get('username')}")
            print(f"Expire: {data.get('expires_at')}")
            return True

    print(f"\n❌ FAILED: Token devrait être valide")
    return False


def test_endpoint_without_token():
    """Test 4: Accès endpoint protégé sans token"""
    print_section("TEST 4: Endpoint protégé sans token")

    response = requests.get(f"{API_BASE_URL}/collections")

    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response: {response.text}")

    if response.status_code == 403:
        print(f"\n✅ SUCCESS: Accès correctement refusé (403)")
        return True
    else:
        print(f"\n❌ FAILED: Devrait retourner 403 Forbidden")
        return False


def test_endpoint_with_valid_token(token):
    """Test 5: Accès endpoint protégé avec token valide"""
    print_section("TEST 5: Endpoint protégé avec token valide")

    response = requests.get(
        f"{API_BASE_URL}/collections",
        headers={"Authorization": f"Bearer {token}"}
    )

    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response: {response.text[:200]}")

    if response.status_code == 200:
        print(f"\n✅ SUCCESS: Accès autorisé avec token valide")
        return True
    else:
        print(f"\n❌ FAILED: Devrait retourner 200 OK")
        return False


def test_endpoint_with_invalid_token():
    """Test 6: Accès endpoint protégé avec token invalide"""
    print_section("TEST 6: Endpoint protégé avec token invalide")

    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake.token"

    response = requests.get(
        f"{API_BASE_URL}/collections",
        headers={"Authorization": f"Bearer {fake_token}"}
    )

    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response: {response.text}")

    if response.status_code == 401:
        print(f"\n✅ SUCCESS: Accès correctement refusé (401)")
        return True
    else:
        print(f"\n❌ FAILED: Devrait retourner 401 Unauthorized")
        return False


def test_health_endpoint_public():
    """Test 7: Endpoint /health doit rester public"""
    print_section("TEST 7: Endpoint /health (doit rester public)")

    response = requests.get(f"{API_BASE_URL}/health")

    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}")
    except:
        print(f"Response: {response.text}")

    if response.status_code == 200:
        print(f"\n✅ SUCCESS: /health accessible sans token")
        return True
    else:
        print(f"\n❌ FAILED: /health devrait être accessible sans token")
        return False


def main():
    """Execute tous les tests"""
    print("\n" + "="*60)
    print("  TEST SUITE - AUTHENTIFICATION JWT")
    print("="*60)
    print(f"\nAPI URL: {API_BASE_URL}")
    print(f"Username: {USERNAME}")
    print(f"Password: {PASSWORD}")

    results = []

    # Test 1: Login success
    token = test_login_success()
    results.append(("Login avec bonnes credentials", token is not None))

    if not token:
        print("\n❌ ERREUR: Impossible d'obtenir un token. Tests suivants annulés.")
        sys.exit(1)

    # Test 2: Login failure
    results.append(("Login avec mauvaises credentials", test_login_failure()))

    # Test 3: Verify token
    results.append(("Vérification du token", test_verify_token(token)))

    # Test 4: Endpoint without token
    results.append(("Endpoint protégé sans token", test_endpoint_without_token()))

    # Test 5: Endpoint with valid token
    results.append(("Endpoint protégé avec token valide", test_endpoint_with_valid_token(token)))

    # Test 6: Endpoint with invalid token
    results.append(("Endpoint protégé avec token invalide", test_endpoint_with_invalid_token()))

    # Test 7: Health endpoint public
    results.append(("Endpoint /health public", test_health_endpoint_public()))

    # Résumé
    print_section("RÉSUMÉ DES TESTS")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n{'='*60}")
    print(f"  RÉSULTAT: {passed}/{total} tests passés")
    print(f"{'='*60}\n")

    if passed == total:
        print("✅ Tous les tests ont réussi!")
        sys.exit(0)
    else:
        print(f"❌ {total - passed} test(s) ont échoué")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter à l'API")
        print(f"Vérifiez que l'API est lancée sur {API_BASE_URL}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nTests interrompus par l'utilisateur")
        sys.exit(1)
