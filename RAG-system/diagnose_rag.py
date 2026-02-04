#!/usr/bin/env python3
"""
Script de diagnostic pour analyser la qualité du RAG
"""

import requests
import json
from pathlib import Path

API_URL = "http://localhost:8000"


def check_collections():
    """Vérifie les collections disponibles"""
    print("=" * 80)
    print("📚 COLLECTIONS DISPONIBLES")
    print("=" * 80)

    response = requests.get(f"{API_URL}/collections")
    if response.status_code != 200:
        print(f"❌ Erreur: {response.status_code}")
        return []

    collections = response.json()
    if not collections:
        print("❌ Aucune collection trouvée")
        return []

    print(f"\n✅ {len(collections)} collection(s) trouvée(s):\n")
    for col in collections:
        print(f"  • {col['name']}")
        print(f"    - Total chunks: {col['total_chunks']}")
        print(f"    - Tables: {col['table_chunks']}")
        print(f"    - Texte: {col['text_chunks']}")
        print()

    return collections


def test_query(collection_name, question):
    """Teste une requête et affiche les résultats détaillés"""
    print("=" * 80)
    print(f"🔍 TEST REQUÊTE: '{question}'")
    print(f"   Collection: {collection_name}")
    print("=" * 80)

    query_data = {
        "question": question,
        "collection_name": collection_name,
        "n_results": 5,
        "generate_answer": False
    }

    response = requests.post(f"{API_URL}/query", json=query_data)
    if response.status_code != 200:
        print(f"❌ Erreur {response.status_code}: {response.text}")
        return None

    result = response.json()

    if not result["chunks"]:
        print("❌ Aucun résultat trouvé")
        return None

    print(f"\n✅ {len(result['chunks'])} résultats trouvés:\n")

    for i, chunk in enumerate(result["chunks"], 1):
        score = chunk["score"]
        print(f"  [{i}] Score: {score:.4f} (distance: {1-score:.4f})")
        print(f"      Type: {chunk['content_type']}")
        print(f"      Tokens: {chunk['num_tokens']}")
        print(f"      Texte: {chunk['text'][:150]}...")
        print()

    best_score = result["chunks"][0]["score"]
    print(f"📊 ANALYSE:")
    print(f"   Meilleur score: {best_score:.4f}")
    print(f"   Seuil attendu: 0.3")

    if best_score < 0.3:
        print(f"   ❌ Score trop bas ({best_score:.4f} < 0.3)")
        print(f"\n💡 Causes possibles:")
        print(f"   - Question trop vague")
        print(f"   - Vocabulaire différent entre question et documents")
        print(f"   - Chunks ne contiennent pas assez de contexte")
        print(f"   - Modèle d'embedding pas optimal pour le français")
    else:
        print(f"   ✅ Score suffisant ({best_score:.4f} >= 0.3)")

    return result


def suggest_better_questions(collection_name):
    """Suggère des questions plus spécifiques"""
    print("\n" + "=" * 80)
    print("💡 SUGGESTIONS DE QUESTIONS PLUS SPÉCIFIQUES")
    print("=" * 80)

    # Tester avec des questions plus spécifiques
    specific_questions = [
        "Quel est le chiffre d'affaires en 2024?",
        "Quelle est la croissance du chiffre d'affaires?",
        "Quels sont les résultats du premier semestre?",
        "Quel est le résultat net de l'exercice?",
        "Quelles sont les perspectives pour 2025?",
    ]

    best_results = []

    for question in specific_questions:
        query_data = {
            "question": question,
            "collection_name": collection_name,
            "n_results": 1,
            "generate_answer": False
        }

        response = requests.post(f"{API_URL}/query", json=query_data)
        if response.status_code == 200:
            result = response.json()
            if result["chunks"]:
                score = result["chunks"][0]["score"]
                best_results.append((question, score))
                print(f"\n  • \"{question}\"")
                print(f"    Score: {score:.4f} {'✅' if score >= 0.3 else '❌'}")

    if best_results:
        best_results.sort(key=lambda x: x[1], reverse=True)
        best_q, best_s = best_results[0]
        print(f"\n🏆 Meilleure question: \"{best_q}\" (score: {best_s:.4f})")


def sample_chunks(collection_name):
    """Affiche des exemples de chunks pour voir le contenu"""
    print("\n" + "=" * 80)
    print(f"📄 EXEMPLES DE CHUNKS (Collection: {collection_name})")
    print("=" * 80)

    # Utiliser une requête très générique pour obtenir n'importe quel chunk
    query_data = {
        "question": "document",
        "collection_name": collection_name,
        "n_results": 3,
        "generate_answer": False
    }

    response = requests.post(f"{API_URL}/query", json=query_data)
    if response.status_code == 200:
        result = response.json()
        if result["chunks"]:
            print(f"\n✅ Voici quelques chunks de la collection:\n")
            for i, chunk in enumerate(result["chunks"][:3], 1):
                print(f"  Chunk #{i}:")
                print(f"  Type: {chunk['content_type']}")
                print(f"  Texte: {chunk['text'][:300]}...")
                print()


def main():
    print("\n" + "=" * 80)
    print("🔬 DIAGNOSTIC SYSTÈME RAG")
    print("=" * 80 + "\n")

    # 1. Vérifier l'API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ L'API ne répond pas correctement")
            print("   Lancez: cd api && python -m uvicorn main:app --reload")
            return
    except:
        print("❌ Impossible de joindre l'API")
        print("   Lancez: cd api && python -m uvicorn main:app --reload")
        return

    print("✅ API accessible\n")

    # 2. Lister les collections
    collections = check_collections()
    if not collections:
        print("\n❌ Impossible de continuer sans collections")
        print("   Lancez: python3 scripts/quick_index.py")
        return

    # 3. Prendre la première collection pour les tests
    collection_name = collections[0]["name"]

    # 4. Afficher des exemples de chunks
    sample_chunks(collection_name)

    # 5. Tester les questions génériques du test
    print("\n" + "=" * 80)
    print("🧪 TEST DES QUESTIONS GÉNÉRIQUES")
    print("=" * 80)

    generic_questions = [
        "résultats financiers",
        "chiffre d'affaires",
        "stratégie d'entreprise",
    ]

    scores = []
    for question in generic_questions:
        result = test_query(collection_name, question)
        if result and result["chunks"]:
            scores.append(result["chunks"][0]["score"])
        print()

    # 6. Suggérer de meilleures questions
    suggest_better_questions(collection_name)

    # 7. Analyse finale
    print("\n" + "=" * 80)
    print("📊 ANALYSE FINALE")
    print("=" * 80)

    if scores:
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        print(f"\nScores des questions génériques:")
        print(f"  Moyenne: {avg_score:.4f}")
        print(f"  Maximum: {max_score:.4f}")
        print(f"  Seuil test: 0.3")

        if max_score < 0.3:
            print(f"\n❌ PROBLÈME DÉTECTÉ:")
            print(f"   Les questions génériques obtiennent des scores trop bas.")
            print(f"\n🔧 SOLUTIONS RECOMMANDÉES:")
            print(f"   1. Utiliser des questions plus spécifiques dans le test")
            print(f"   2. OU baisser le seuil de 0.3 à 0.15-0.2")
            print(f"   3. OU améliorer le chunking pour plus de contexte")
            print(f"   4. OU utiliser un meilleur modèle d'embedding")
        else:
            print(f"\n✅ Les scores sont satisfaisants pour le test")

    print("\n" + "=" * 80)
    print("FIN DU DIAGNOSTIC")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
