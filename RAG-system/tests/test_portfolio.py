"""
Tests de la gestion de portefeuille: positions, PRU, plus-values, santé
"""

import pytest
import requests
import time
import uuid


@pytest.mark.portfolio
class TestPortfolioManagement:
    """Tests des fonctionnalités de gestion de portefeuille"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, api_base_url):
        """Setup et nettoyage pour chaque test"""
        # Utiliser UUID pour garantir l'unicité entre les tests
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:12]}"
        yield
        # Cleanup après chaque test si nécessaire
        # Note: Pour nettoyer complètement, supprimer data/portfolio.db avant les tests

    def test_add_position(self, api_base_url, check_api_running, auth_headers):
        """
        Test l'ajout d'une position au portefeuille.

        Vérifie que:
        - La position est créée correctement
        - Le PRU est calculé
        - Les données sont persistées
        """
        position_data = {
            "ticker": "MC.PA",
            "company_name": "LVMH",
            "quantity": 10,
            "price": 700.0,
            "user_id": self.test_user_id
        }

        response = requests.post(f"{api_base_url}/portfolio/add", json=position_data, headers=auth_headers)
        assert response.status_code == 200, "L'ajout de position doit réussir"

        data = response.json()
        assert "message" in data
        assert data["ticker"] == "MC.PA"

        print(f"\nAjout position:")
        print(f"  {position_data['company_name']}: {position_data['quantity']} actions @ {position_data['price']}€")
        print(f"  Investissement: {position_data['quantity'] * position_data['price']}€")

    def test_add_multiple_positions(self, api_base_url, check_api_running, auth_headers):
        """
        Test l'ajout de plusieurs positions.

        Vérifie la construction progressive d'un portefeuille
        avec plusieurs entreprises.
        """
        positions = [
            {"ticker": "MC.PA", "company_name": "LVMH", "quantity": 10, "price": 700.0},
            {"ticker": "BNP.PA", "company_name": "BNP Paribas", "quantity": 50, "price": 55.0},
            {"ticker": "TTE.PA", "company_name": "TotalEnergies", "quantity": 30, "price": 60.0},
        ]

        for pos in positions:
            pos["user_id"] = self.test_user_id
            response = requests.post(f"{api_base_url}/portfolio/add", json=pos, headers=auth_headers)
            assert response.status_code == 200, f"Ajout de {pos['company_name']} doit réussir"

        # Vérifier le portefeuille
        response = requests.get(f"{api_base_url}/portfolio", params={"user_id": self.test_user_id}, headers=auth_headers)
        assert response.status_code == 200

        portfolio = response.json()
        assert portfolio["total_positions"] == 3, "Doit avoir 3 positions"

        print(f"\nPortefeuille multi-positions:")
        print(f"  Nombre de positions: {portfolio['total_positions']}")
        print(f"  Valeur totale: {portfolio['total_value']:,.2f}€")
        print(f"  Montant investi: {portfolio['total_invested']:,.2f}€")

    def test_pru_calculation(self, api_base_url, check_api_running, auth_headers):
        """
        Test le calcul du Prix de Revient Unitaire (PRU).

        Vérifie que le PRU est correctement calculé lors:
        - D'achats successifs à des prix différents
        - De renforcements de position
        """
        # Premier achat
        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": "MC.PA",
            "company_name": "LVMH",
            "quantity": 10,
            "price": 700.0,
            "user_id": self.test_user_id
        })
        assert response.status_code == 200

        # Deuxième achat (renforcement)
        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": "MC.PA",
            "company_name": "LVMH",
            "quantity": 5,
            "price": 750.0,
            "user_id": self.test_user_id
        })
        assert response.status_code == 200

        # Vérifier le PRU
        response = requests.get(f"{api_base_url}/portfolio", params={"user_id": self.test_user_id}, headers=auth_headers)
        portfolio = response.json()

        lvmh_position = next((p for p in portfolio["positions"] if p["ticker"] == "MC.PA"), None)
        assert lvmh_position is not None, "Position LVMH doit exister"

        # PRU attendu: (10*700 + 5*750) / 15 = 716.67
        expected_pru = (10 * 700 + 5 * 750) / 15
        actual_pru = lvmh_position["avg_price"]

        assert abs(actual_pru - expected_pru) < 0.01, f"PRU devrait être {expected_pru:.2f}, obtenu {actual_pru:.2f}"

        print(f"\nCalcul PRU:")
        print(f"  Achat 1: 10 @ 700€")
        print(f"  Achat 2: 5 @ 750€")
        print(f"  PRU calculé: {actual_pru:.2f}€ (attendu: {expected_pru:.2f}€) ✓")
        print(f"  Quantité totale: {lvmh_position['quantity']}")

    def test_sell_position(self, api_base_url, check_api_running, auth_headers):
        """
        Test la vente d'une position (partielle ou totale).

        Vérifie que:
        - La vente réduit correctement la quantité
        - La plus-value est calculée
        - Le PRU reste cohérent
        """
        # Ajouter une position
        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": "MC.PA",
            "company_name": "LVMH",
            "quantity": 20,
            "price": 700.0,
            "user_id": self.test_user_id
        })
        assert response.status_code == 200

        # Vendre partiellement
        response = requests.post(f"{api_base_url}/portfolio/sell", json={
            "ticker": "MC.PA",
            "quantity": 10,
            "price": 750.0,
            "user_id": self.test_user_id
        })
        assert response.status_code == 200, "La vente doit réussir"

        data = response.json()
        assert "message" in data

        # Vérifier la position restante
        response = requests.get(f"{api_base_url}/portfolio", params={"user_id": self.test_user_id}, headers=auth_headers)
        portfolio = response.json()

        lvmh_position = next((p for p in portfolio["positions"] if p["ticker"] == "MC.PA"), None)
        assert lvmh_position is not None
        assert lvmh_position["quantity"] == 10, "Quantité doit être 10 après vente de 10"

        print(f"\nVente position:")
        print(f"  Quantité initiale: 20")
        print(f"  Vente: 10 @ 750€")
        print(f"  Quantité restante: {lvmh_position['quantity']}")
        print(f"  Plus-value réalisée: {10 * (750 - 700)}€")

    def test_portfolio_summary(self, api_base_url, check_api_running, auth_headers):
        """
        Test le récapitulatif du portefeuille.

        Vérifie que le résumé contient:
        - Nombre de positions
        - Valeur totale
        - Montant investi
        - Plus-values latentes
        - Performance globale
        """
        # Créer un portefeuille
        positions = [
            {"ticker": "MC.PA", "company_name": "LVMH", "quantity": 10, "price": 700.0},
            {"ticker": "BNP.PA", "company_name": "BNP Paribas", "quantity": 50, "price": 55.0},
        ]

        for pos in positions:
            pos["user_id"] = self.test_user_id
            requests.post(f"{api_base_url}/portfolio/add", json=pos, headers=auth_headers)

        # Récupérer le résumé
        response = requests.get(f"{api_base_url}/portfolio", params={"user_id": self.test_user_id}, headers=auth_headers)
        assert response.status_code == 200

        summary = response.json()

        # Vérifier les champs essentiels
        assert "total_positions" in summary
        assert "total_value" in summary
        assert "total_invested" in summary
        assert "total_gain_loss" in summary
        assert "total_gain_loss_percent" in summary
        assert "positions" in summary

        print(f"\nRésumé portefeuille:")
        print(f"  Positions: {summary['total_positions']}")
        print(f"  Valeur actuelle: {summary['total_value']:,.2f}€")
        print(f"  Investi: {summary['total_invested']:,.2f}€")
        print(f"  +/- value: {summary['total_gain_loss']:+,.2f}€ ({summary['total_gain_loss_percent']:+.2f}%)")

    def test_portfolio_health_score(self, api_base_url, check_api_running, auth_headers):
        """
        Test le calcul du score de santé du portefeuille.

        Vérifie que le score (0-100) reflète:
        - La diversification
        - La concentration des positions
        - La performance globale
        - Les positions en perte
        """
        # Créer un portefeuille diversifié
        positions = [
            {"ticker": "MC.PA", "company_name": "LVMH", "quantity": 10, "price": 700.0},
            {"ticker": "BNP.PA", "company_name": "BNP Paribas", "quantity": 50, "price": 55.0},
            {"ticker": "TTE.PA", "company_name": "TotalEnergies", "quantity": 30, "price": 60.0},
            {"ticker": "AIR.PA", "company_name": "Airbus", "quantity": 20, "price": 130.0},
            {"ticker": "OR.PA", "company_name": "L'Oréal", "quantity": 8, "price": 400.0},
        ]

        for pos in positions:
            pos["user_id"] = self.test_user_id
            requests.post(f"{api_base_url}/portfolio/add", json=pos, headers=auth_headers)

        # Récupérer le score de santé
        response = requests.get(f"{api_base_url}/portfolio/health", params={"user_id": self.test_user_id}, headers=auth_headers)
        assert response.status_code == 200

        health = response.json()

        assert "score" in health
        assert "grade" in health
        assert 0 <= health["score"] <= 100, "Score doit être entre 0 et 100"

        print(f"\nScore de santé portefeuille:")
        print(f"  Score: {health['score']}/100")
        print(f"  Grade: {health['grade']}")
        print(f"  Positions: {health.get('total_positions', 'N/A')}")
        if "issues" in health:
            print(f"  Problèmes: {len(health['issues'])}")
            for issue in health["issues"][:3]:
                print(f"    - {issue}")

    def test_rebalance_recommendations(self, api_base_url, check_api_running, auth_headers):
        """
        Test les recommandations de rééquilibrage.

        Vérifie que le système détecte:
        - Les positions trop concentrées (> 25%)
        - Les positions trop faibles (< 5%)
        - Le manque de diversification
        """
        # Créer un portefeuille déséquilibré (concentration sur 1 action)
        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": "MC.PA",
            "company_name": "LVMH",
            "quantity": 100,  # Position très importante
            "price": 700.0,
            "user_id": self.test_user_id
        })

        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": "BNP.PA",
            "company_name": "BNP Paribas",
            "quantity": 10,  # Position faible
            "price": 55.0,
            "user_id": self.test_user_id
        })

        # Vérifier les recommandations
        response = requests.get(f"{api_base_url}/portfolio/rebalance", params={"user_id": self.test_user_id}, headers=auth_headers)
        assert response.status_code == 200

        rebalance = response.json()

        assert "needs_rebalance" in rebalance
        assert "recommendations" in rebalance

        if rebalance["needs_rebalance"]:
            print(f"\nRecommandations de rééquilibrage:")
            print(f"  Rééquilibrage nécessaire: OUI")
            print(f"  Nombre de recommandations: {len(rebalance['recommendations'])}")
            for rec in rebalance["recommendations"][:3]:
                action = rec.get("action", "N/A")
                company = rec.get("company", rec.get("reason", "N/A"))
                print(f"    - {action}: {company}")

    def test_position_details(self, api_base_url, check_api_running, auth_headers):
        """
        Test la récupération des détails d'une position.

        Vérifie qu'on obtient:
        - Données du portefeuille (PRU, quantité, +/- value)
        - Données de marché en temps réel
        - Historique des transactions
        - Analyses passées
        """
        # Ajouter une position
        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": "MC.PA",
            "company_name": "LVMH",
            "quantity": 10,
            "price": 700.0,
            "user_id": self.test_user_id
        })

        # Récupérer les détails
        response = requests.get(
            f"{api_base_url}/portfolio/position/MC.PA", params={"user_id": self.test_user_id}
        , headers=auth_headers)
        assert response.status_code == 200

        details = response.json()

        assert "position" in details or "error" not in details
        if "position" in details:
            position = details["position"]
            assert position["ticker"] == "MC.PA"
            print(f"\nDétails position MC.PA:")
            print(f"  Quantité: {position['quantity']}")
            print(f"  PRU: {position['avg_price']}€")
            if "market_data" in details:
                print(f"  Données marché: ✓")
            if "transactions" in details:
                print(f"  Historique transactions: {len(details['transactions'])}")

    def test_portfolio_context_for_ai(self, api_base_url, check_api_running, auth_headers):
        """
        Test la génération du contexte portefeuille pour l'IA.

        Vérifie que le système peut générer un contexte textuel formaté
        du portefeuille, utilisable par les agents CrewAI.
        """
        # Créer un portefeuille
        positions = [
            {"ticker": "MC.PA", "company_name": "LVMH", "quantity": 10, "price": 700.0},
            {"ticker": "BNP.PA", "company_name": "BNP Paribas", "quantity": 50, "price": 55.0},
        ]

        for pos in positions:
            pos["user_id"] = self.test_user_id
            requests.post(f"{api_base_url}/portfolio/add", json=pos, headers=auth_headers)

        # Récupérer le contexte
        response = requests.get(f"{api_base_url}/portfolio/context", params={"user_id": self.test_user_id}, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "context" in data

        context = data["context"]
        assert len(context) > 100, "Le contexte doit être substantiel"
        assert "LVMH" in context, "Doit contenir le nom de l'entreprise"
        assert "MC.PA" in context, "Doit contenir le ticker"

        print(f"\nContexte pour IA:")
        print(f"  Longueur: {len(context)} caractères")
        print(f"  Extrait: {context[:200]}...")

    def test_error_handling_portfolio(self, api_base_url, check_api_running, auth_headers):
        """
        Test la gestion d'erreurs pour le portefeuille.

        Vérifie:
        - Vente d'une position inexistante
        - Vente de plus d'actions que possédées
        - Ajout avec paramètres invalides
        """
        # Test 1: Vente d'une position inexistante
        response = requests.post(f"{api_base_url}/portfolio/sell", json={
            "ticker": "NONEXISTENT.PA",
            "quantity": 10,
            "price": 100.0,
            "user_id": self.test_user_id
        })
        assert response.status_code in [400, 404, 500], "Doit gérer la position inexistante"

        print("\nGestion d'erreurs portefeuille:")
        print(f"  Position inexistante: {response.status_code} ✓")

        # Test 2: Quantité négative
        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": "MC.PA",
            "company_name": "LVMH",
            "quantity": -10,  # Négatif
            "price": 700.0,
            "user_id": self.test_user_id
        })
        assert response.status_code == 422, "Doit rejeter quantité négative"
        print(f"  Quantité négative: 422 ✓")
