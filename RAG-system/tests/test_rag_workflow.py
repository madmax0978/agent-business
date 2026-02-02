"""
Tests du workflow RAG complet: indexation, recherche, génération
"""

import pytest
import requests
from pathlib import Path


@pytest.mark.rag
class TestRAGWorkflow:
    """Tests du workflow RAG de bout en bout"""

    def test_health_check(self, api_base_url, check_api_running):
        """
        Test que l'API répond correctement au health check.

        Vérifie que l'API est opérationnelle et que les services essentiels
        (Ollama, ChromaDB) sont accessibles.
        """
        response = requests.get(f"{api_base_url}/health")

        assert response.status_code == 200, "API doit retourner 200 OK"

        data = response.json()
        assert data["status"] == "healthy", "Status doit être 'healthy'"
        assert "version" in data, "Version doit être présente"
        assert "collections" in data, "Liste des collections doit être présente"

        print(f"\nAPI Health Check: OK")
        print(f"  Status: {data['status']}")
        print(f"  Version: {data['version']}")
        print(f"  Ollama disponible: {data.get('ollama_available', False)}")
        print(f"  Collections existantes: {len(data['collections'])}")

    def test_list_collections(self, api_base_url, check_api_running):
        """
        Test la récupération de la liste des collections.

        Vérifie que l'endpoint /collections retourne bien une liste
        avec les métadonnées de chaque collection.
        """
        response = requests.get(f"{api_base_url}/collections")

        assert response.status_code == 200, "Doit retourner 200 OK"

        collections = response.json()
        assert isinstance(collections, list), "Doit retourner une liste"

        print(f"\nCollections disponibles: {len(collections)}")
        for col in collections[:5]:  # Afficher max 5
            print(f"  - {col['name']}: {col['total_chunks']} chunks "
                  f"({col['text_chunks']} text, {col['table_chunks']} tables)")

    def test_get_collection_info(self, api_base_url, check_api_running):
        """
        Test la récupération d'informations sur une collection spécifique.

        Vérifie qu'on peut obtenir les détails d'une collection existante
        (nombre de chunks, répartition texte/tableaux, etc.)
        """
        # D'abord, récupérer la liste des collections
        response = requests.get(f"{api_base_url}/collections")
        collections = response.json()

        if not collections:
            pytest.skip("Aucune collection disponible pour ce test")

        # Tester avec la première collection
        collection_name = collections[0]["name"]

        response = requests.get(f"{api_base_url}/collections/{collection_name}")
        assert response.status_code == 200, f"Collection '{collection_name}' doit exister"

        info = response.json()
        assert info["name"] == collection_name
        assert "total_chunks" in info
        assert "table_chunks" in info
        assert "text_chunks" in info

        print(f"\nInfo collection '{collection_name}':")
        print(f"  Total chunks: {info['total_chunks']}")
        print(f"  Text chunks: {info['text_chunks']}")
        print(f"  Table chunks: {info['table_chunks']}")
        print(f"  Table percentage: {info['table_percentage']}%")

    def test_rag_search_semantic(self, api_base_url, check_api_running):
        """
        Test la recherche sémantique dans une collection.

        Vérifie que le système RAG peut effectuer une recherche sémantique
        et retourner des chunks pertinents avec leurs scores de similarité.
        """
        # Récupérer une collection existante
        response = requests.get(f"{api_base_url}/collections")
        collections = response.json()

        if not collections:
            pytest.skip("Aucune collection disponible pour la recherche")

        collection_name = collections[0]["name"]

        # Effectuer une recherche sémantique
        query_data = {
            "question": "Quel est le chiffre d'affaires de l'entreprise?",
            "collection_name": collection_name,
            "n_results": 3,
            "generate_answer": False  # Pas de génération pour ce test
        }

        response = requests.post(f"{api_base_url}/query", json=query_data)
        assert response.status_code == 200, "La recherche doit réussir"

        result = response.json()
        assert result["question"] == query_data["question"]
        assert result["collection_name"] == collection_name
        assert "chunks" in result
        assert len(result["chunks"]) > 0, "Doit retourner au moins un chunk"

        # Vérifier la structure des chunks
        first_chunk = result["chunks"][0]
        assert "chunk_id" in first_chunk
        assert "text" in first_chunk
        assert "score" in first_chunk
        assert 0 <= first_chunk["score"] <= 1, "Score doit être entre 0 et 1"

        print(f"\nRecherche sémantique dans '{collection_name}':")
        print(f"  Question: {query_data['question']}")
        print(f"  Chunks trouvés: {len(result['chunks'])}")
        print(f"  Meilleur score: {result['chunks'][0]['score']:.4f}")
        print(f"  Temps de traitement: {result['processing_time']:.2f}s")

    def test_rag_search_with_generation(self, api_base_url, check_api_running):
        """
        Test la recherche RAG avec génération de réponse.

        Vérifie que le système peut non seulement trouver des chunks pertinents,
        mais aussi générer une réponse synthétique en utilisant Ollama.
        """
        # Vérifier d'abord si Ollama est disponible
        health_response = requests.get(f"{api_base_url}/health")
        health_data = health_response.json()

        if not health_data.get("ollama_available", False):
            pytest.skip("Ollama n'est pas disponible - lancez 'ollama serve'")

        # Récupérer une collection
        response = requests.get(f"{api_base_url}/collections")
        collections = response.json()

        if not collections:
            pytest.skip("Aucune collection disponible")

        collection_name = collections[0]["name"]

        # Recherche avec génération
        query_data = {
            "question": "Résume les principaux résultats financiers de cette entreprise",
            "collection_name": collection_name,
            "n_results": 5,
            "generate_answer": True
        }

        response = requests.post(f"{api_base_url}/query", json=query_data)
        assert response.status_code == 200, "La recherche doit réussir"

        result = response.json()
        assert result["answer"] is not None, "Une réponse doit être générée"
        assert len(result["answer"]) > 50, "La réponse doit être substantielle"

        print(f"\nRecherche avec génération:")
        print(f"  Question: {query_data['question']}")
        print(f"  Chunks utilisés: {len(result['chunks'])}")
        print(f"  Longueur de la réponse: {len(result['answer'])} caractères")
        print(f"  Réponse (extrait): {result['answer'][:200]}...")

    def test_rag_filter_tables(self, api_base_url, check_api_running):
        """
        Test le filtrage des tableaux vs texte dans la recherche.

        Vérifie que le système peut filtrer spécifiquement les tableaux
        ou le texte lors des recherches (utile pour extraire des données chiffrées).
        """
        response = requests.get(f"{api_base_url}/collections")
        collections = response.json()

        if not collections:
            pytest.skip("Aucune collection disponible")

        # Trouver une collection avec des tableaux
        collection_with_tables = None
        for col in collections:
            if col["table_chunks"] > 0:
                collection_with_tables = col["name"]
                break

        if not collection_with_tables:
            pytest.skip("Aucune collection avec des tableaux trouvée")

        # Rechercher uniquement dans les tableaux
        query_data = {
            "question": "données financières chiffrées",
            "collection_name": collection_with_tables,
            "n_results": 3,
            "filter_tables": True,  # Uniquement les tableaux
            "generate_answer": False
        }

        response = requests.post(f"{api_base_url}/query", json=query_data)
        assert response.status_code == 200

        result = response.json()

        # Vérifier que tous les chunks sont des tableaux
        for chunk in result["chunks"]:
            assert chunk["content_type"] == "table", "Tous les chunks doivent être des tableaux"

        print(f"\nFiltre tableaux activé:")
        print(f"  Collection: {collection_with_tables}")
        print(f"  Tableaux trouvés: {len(result['chunks'])}")

    def test_rag_quality_of_results(self, api_base_url, check_api_running):
        """
        Test la qualité des résultats RAG.

        Vérifie que les résultats retournés sont bien pertinents par rapport
        à la question posée (scores de similarité suffisamment élevés).
        """
        response = requests.get(f"{api_base_url}/collections")
        collections = response.json()

        if not collections:
            pytest.skip("Aucune collection disponible")

        collection_name = collections[0]["name"]

        # Questions de différents types
        test_queries = [
            "résultats financiers",
            "chiffre d'affaires",
            "stratégie d'entreprise",
        ]

        for question in test_queries:
            query_data = {
                "question": question,
                "collection_name": collection_name,
                "n_results": 5,
                "generate_answer": False
            }

            response = requests.post(f"{api_base_url}/query", json=query_data)
            result = response.json()

            # Vérifier que le meilleur résultat a un score raisonnable
            if result["chunks"]:
                best_score = result["chunks"][0]["score"]
                assert best_score > 0.3, f"Le meilleur score ({best_score}) devrait être > 0.3 pour '{question}'"

                print(f"\nQualité pour '{question}': Score={best_score:.4f} ✓")

    def test_rag_error_handling(self, api_base_url, check_api_running):
        """
        Test la gestion d'erreurs du système RAG.

        Vérifie que le système gère correctement les cas d'erreur:
        - Collection inexistante
        - Paramètres invalides
        - Requêtes malformées
        """
        # Test 1: Collection inexistante
        query_data = {
            "question": "test",
            "collection_name": "collection_inexistante_xyz",
            "n_results": 5
        }

        response = requests.post(f"{api_base_url}/query", json=query_data)
        assert response.status_code == 404, "Doit retourner 404 pour collection inexistante"

        print("\nGestion d'erreurs:")
        print("  Collection inexistante: 404 ✓")

        # Test 2: n_results invalide (> 20)
        collections = requests.get(f"{api_base_url}/collections").json()
        if collections:
            query_data = {
                "question": "test",
                "collection_name": collections[0]["name"],
                "n_results": 100  # Au-dessus de la limite
            }

            response = requests.post(f"{api_base_url}/query", json=query_data)
            assert response.status_code == 422, "Doit retourner 422 pour n_results invalide"

            print("  n_results invalide: 422 ✓")
