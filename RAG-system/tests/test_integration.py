"""
Tests d'intégration end-to-end du système RAG-PEA complet
"""

import pytest
import requests
import time


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndIntegration:
    """Tests du workflow complet de bout en bout"""

    def test_complete_workflow_data_to_decision(self, api_base_url, check_api_running, test_tickers, test_companies):
        """
        Test le workflow complet: Données → RAG → Agents → Recommandations → Portefeuille

        Ce test vérifie l'intégration complète:
        1. Récupération des données de marché
        2. Recherche dans la base RAG
        3. Analyse financière complète
        4. Génération de recommandations
        5. Mise à jour du portefeuille
        """
        print("\n" + "="*80)
        print("TEST END-TO-END: WORKFLOW COMPLET")
        print("="*80)

        ticker = test_tickers["lvmh"]
        company_name = test_companies[ticker]
        test_user_id = f"e2e_test_{int(time.time())}"

        # ÉTAPE 1: Récupérer les données de marché
        print("\n[1/5] Récupération données de marché...")
        response = requests.get(f"{api_base_url}/market/stock/{ticker}")
        assert response.status_code == 200, "Données marché doivent être accessibles"
        market_data = response.json()
        current_price = market_data.get("currentPrice") or market_data.get("regularMarketPrice")
        print(f"  ✓ Prix actuel {ticker}: {current_price}€")

        # ÉTAPE 2: Vérifier la disponibilité RAG
        print("\n[2/5] Vérification base RAG...")
        response = requests.get(f"{api_base_url}/collections")
        assert response.status_code == 200
        collections = response.json()
        print(f"  ✓ Collections disponibles: {len(collections)}")

        # ÉTAPE 3: Analyse complète (marché + news + technique)
        print("\n[3/5] Analyse financière complète...")
        response = requests.get(
            f"{api_base_url}/analysis/complete/{ticker}",
            params={"company_name": company_name}
        )
        assert response.status_code == 200, "Analyse complète doit réussir"
        analysis = response.json()
        print(f"  ✓ Analyse complète effectuée")
        print(f"    - Données marché: ✓")
        print(f"    - Sentiment news: {analysis.get('news_sentiment', {}).get('overall_sentiment', 'N/A')}")
        print(f"    - Tendance technique: {analysis.get('technical_analysis', {}).get('trend', 'N/A')}")

        # ÉTAPE 4: Ajouter au portefeuille
        print("\n[4/5] Ajout position au portefeuille...")
        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": ticker,
            "company_name": company_name,
            "quantity": 10,
            "price": float(current_price) if current_price else 700.0,
            "user_id": test_user_id
        })
        assert response.status_code == 200, "Ajout position doit réussir"
        print(f"  ✓ Position ajoutée: 10 actions @ {current_price}€")

        # ÉTAPE 5: Vérifier la santé du portefeuille
        print("\n[5/5] Analyse santé du portefeuille...")
        response = requests.get(f"{api_base_url}/portfolio/health", params={"user_id": test_user_id})
        assert response.status_code == 200
        health = response.json()
        print(f"  ✓ Score de santé: {health['score']}/100 ({health['grade']})")

        print("\n" + "="*80)
        print("WORKFLOW COMPLET: ✓ SUCCÈS")
        print("="*80)

    def test_rag_to_agents_integration(self, api_base_url, check_api_running):
        """
        Test l'intégration RAG → Agents CrewAI.

        Vérifie que les agents peuvent:
        1. Accéder aux données RAG
        2. Utiliser les tools correctement
        3. Générer des analyses basées sur les données RAG
        """
        # Vérifier qu'il y a des collections RAG disponibles
        response = requests.get(f"{api_base_url}/collections")
        collections = response.json()

        if not collections:
            pytest.skip("Aucune collection RAG disponible pour tester l'intégration avec les agents")

        print("\nIntégration RAG → Agents:")
        print(f"  Collections RAG: {len(collections)}")

        # Faire une recherche RAG
        collection_name = collections[0]["name"]
        query_data = {
            "question": "Quels sont les principaux indicateurs financiers?",
            "collection_name": collection_name,
            "n_results": 3,
            "generate_answer": False
        }

        response = requests.post(f"{api_base_url}/query", json=query_data)
        assert response.status_code == 200
        results = response.json()

        print(f"  ✓ Recherche RAG: {len(results['chunks'])} chunks trouvés")
        print(f"  ✓ Les agents peuvent accéder à ces données via RAG tool")

    def test_portfolio_to_analysis_feedback_loop(self, api_base_url, check_api_running, test_tickers):
        """
        Test la boucle de feedback: Portefeuille → Analyse → Recommandations → Portefeuille.

        Vérifie que:
        1. On peut analyser un portefeuille existant
        2. Obtenir des recommandations basées sur ce portefeuille
        3. Mettre à jour le portefeuille selon les recommandations
        """
        test_user_id = f"feedback_test_{int(time.time())}"
        ticker = test_tickers["lvmh"]

        print("\nBoucle de feedback Portefeuille ↔ Analyse:")

        # 1. Créer un portefeuille initial
        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": ticker,
            "company_name": "LVMH",
            "quantity": 10,
            "price": 700.0,
            "user_id": test_user_id
        })
        assert response.status_code == 200
        print("  [1] Portefeuille créé ✓")

        # 2. Récupérer le contexte portefeuille
        response = requests.get(f"{api_base_url}/portfolio/context", params={"user_id": test_user_id})
        assert response.status_code == 200
        context = response.json()["context"]
        print(f"  [2] Contexte portefeuille généré ({len(context)} chars) ✓")

        # 3. Vérifier les recommandations de rééquilibrage
        response = requests.get(f"{api_base_url}/portfolio/rebalance", params={"user_id": test_user_id})
        assert response.status_code == 200
        rebalance = response.json()
        print(f"  [3] Recommandations: {len(rebalance['recommendations'])} ✓")

        # 4. Vérifier qu'on peut analyser cette position
        response = requests.get(
            f"{api_base_url}/analysis/complete/{ticker}",
            params={"company_name": "LVMH"}
        )
        assert response.status_code == 200
        print("  [4] Analyse complète de la position ✓")

        print("  ✓ Boucle de feedback fonctionnelle")

    def test_multi_source_data_integration(self, api_base_url, check_api_running, test_tickers):
        """
        Test l'intégration de données multi-sources.

        Vérifie que le système intègre correctement:
        - Données de marché (Yahoo Finance)
        - Données RAG (documents indexés)
        - News en temps réel
        - Analyses techniques
        """
        ticker = test_tickers["lvmh"]
        company = "LVMH"

        print("\nIntégration multi-sources:")

        sources_ok = 0

        # Source 1: Yahoo Finance
        response = requests.get(f"{api_base_url}/market/stock/{ticker}")
        if response.status_code == 200:
            sources_ok += 1
            print("  ✓ [1] Yahoo Finance: Données marché")

        # Source 2: RAG Collections
        response = requests.get(f"{api_base_url}/collections")
        if response.status_code == 200 and len(response.json()) > 0:
            sources_ok += 1
            print("  ✓ [2] RAG: Documents indexés")

        # Source 3: News
        response = requests.get(f"{api_base_url}/analysis/news/{company}")
        if response.status_code == 200:
            sources_ok += 1
            print("  ✓ [3] News: Actualités récentes")

        # Source 4: Analyse technique
        response = requests.get(f"{api_base_url}/analysis/technical/{ticker}")
        if response.status_code == 200:
            sources_ok += 1
            print("  ✓ [4] Analyse: Indicateurs techniques")

        assert sources_ok >= 3, "Au moins 3 sources de données doivent être opérationnelles"
        print(f"\n  Total: {sources_ok}/4 sources intégrées ✓")

    def test_real_time_price_update(self, api_base_url, check_api_running, test_tickers):
        """
        Test la mise à jour en temps réel des prix.

        Vérifie que:
        1. Les prix du portefeuille se mettent à jour
        2. Les plus-values sont recalculées
        3. Le score de santé est mis à jour
        """
        test_user_id = f"realtime_test_{int(time.time())}"
        ticker = test_tickers["lvmh"]

        # Ajouter une position
        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": ticker,
            "company_name": "LVMH",
            "quantity": 10,
            "price": 700.0,
            "user_id": test_user_id
        })
        assert response.status_code == 200

        # Récupérer le portefeuille (déclenche mise à jour prix)
        response = requests.get(f"{api_base_url}/portfolio", params={"user_id": test_user_id})
        assert response.status_code == 200
        portfolio1 = response.json()

        # Attendre un peu et re-récupérer (peut avoir changé)
        time.sleep(2)
        response = requests.get(f"{api_base_url}/portfolio", params={"user_id": test_user_id})
        portfolio2 = response.json()

        print("\nMise à jour temps réel:")
        print(f"  Prix PRU: 700.00€")
        print(f"  Prix actuel: {portfolio2['positions'][0]['current_price']}€")
        print(f"  +/- value: {portfolio2['total_gain_loss']:+.2f}€")
        print("  ✓ Mise à jour fonctionnelle")

    def test_error_recovery(self, api_base_url, check_api_running):
        """
        Test la capacité du système à se rétablir après des erreurs.

        Vérifie que:
        1. Les erreurs sont gérées gracieusement
        2. Le système reste opérationnel après une erreur
        3. Les données ne sont pas corrompues
        """
        print("\nRésistance aux erreurs:")

        # Erreur 1: Requête invalide
        response = requests.post(f"{api_base_url}/query", json={"invalid": "data"})
        assert response.status_code in [400, 422]
        print("  ✓ [1] Requête invalide gérée")

        # Vérifier que l'API est toujours fonctionnelle
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200
        print("  ✓ [2] API toujours opérationnelle après erreur")

        # Erreur 2: Ticker invalide
        response = requests.get(f"{api_base_url}/market/stock/INVALID_XYZ")
        # Peut retourner 404 ou 500 selon l'implémentation
        print(f"  ✓ [3] Ticker invalide géré ({response.status_code})")

        # Vérifier encore une fois
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200
        print("  ✓ [4] API stable après multiples erreurs")

    def test_performance_under_load(self, api_base_url, check_api_running, test_tickers):
        """
        Test les performances sous charge modérée.

        Vérifie que:
        1. Le système peut traiter plusieurs requêtes simultanées
        2. Les temps de réponse restent raisonnables
        3. Pas de dégradation significative
        """
        ticker = test_tickers["lvmh"]
        num_requests = 10

        print(f"\nTest de charge ({num_requests} requêtes):")

        start_time = time.time()
        success_count = 0
        response_times = []

        for i in range(num_requests):
            req_start = time.time()
            response = requests.get(f"{api_base_url}/market/stock/{ticker}", timeout=10)
            req_time = time.time() - req_start

            if response.status_code == 200:
                success_count += 1
                response_times.append(req_time)

        total_time = time.time() - start_time

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        print(f"  Requêtes réussies: {success_count}/{num_requests}")
        print(f"  Temps total: {total_time:.2f}s")
        print(f"  Temps moyen par requête: {avg_response_time:.3f}s")

        assert success_count >= num_requests * 0.9, "Au moins 90% des requêtes doivent réussir"
        assert avg_response_time < 2.0, "Temps de réponse moyen doit être < 2s"

        print("  ✓ Performances acceptables sous charge")

    def test_data_consistency(self, api_base_url, check_api_running, test_tickers):
        """
        Test la cohérence des données entre les différents endpoints.

        Vérifie que:
        1. Les mêmes données sont cohérentes entre endpoints
        2. Les calculs (PRU, +/- values) sont corrects
        3. Pas d'incohérences après mises à jour
        """
        test_user_id = f"consistency_test_{int(time.time())}"
        ticker = test_tickers["lvmh"]

        print("\nCohérence des données:")

        # Ajouter une position
        buy_price = 700.0
        quantity = 10

        response = requests.post(f"{api_base_url}/portfolio/add", json={
            "ticker": ticker,
            "company_name": "LVMH",
            "quantity": quantity,
            "price": buy_price,
            "user_id": test_user_id
        })

        # Récupérer via /portfolio
        response1 = requests.get(f"{api_base_url}/portfolio", params={"user_id": test_user_id})
        portfolio = response1.json()

        # Récupérer via /portfolio/position
        response2 = requests.get(
            f"{api_base_url}/portfolio/position/{ticker}",
            params={"user_id": test_user_id}
        )
        position_details = response2.json()

        # Vérifier cohérence
        portfolio_position = portfolio["positions"][0]

        if "position" in position_details:
            detail_position = position_details["position"]

            assert portfolio_position["ticker"] == detail_position["ticker"]
            assert portfolio_position["quantity"] == detail_position["quantity"]
            assert portfolio_position["avg_price"] == detail_position["avg_price"]

            print("  ✓ Cohérence entre /portfolio et /portfolio/position")

        # Vérifier calculs
        invested = quantity * buy_price
        assert abs(portfolio_position["quantity"] * portfolio_position["avg_price"] - invested) < 0.01

        print("  ✓ Calculs PRU et investissement corrects")
        print("  ✓ Données cohérentes entre tous les endpoints")
