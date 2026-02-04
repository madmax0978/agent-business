#!/usr/bin/env python3
"""
Script pour vérifier quelle version du RAG est utilisée
"""

import requests
import json

API_URL = "http://localhost:8000"

def check_rag_version():
    print("=" * 80)
    print("🔍 VÉRIFICATION VERSION RAG")
    print("=" * 80)

    # 1. Vérifier l'API
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ L'API ne répond pas correctement")
            print("   Lancez: cd api && python -m uvicorn main:app --reload")
            return
    except:
        print("\n❌ Impossible de joindre l'API")
        print("   Lancez: cd api && python -m uvicorn main:app --reload")
        return

    print("\n✅ API accessible\n")

    # 2. Vérifier la version RAG
    try:
        response = requests.get(f"{API_URL}/rag-info", timeout=5)
        if response.status_code == 200:
            info = response.json()

            print("📊 INFORMATIONS RAG:")
            print(f"  Version: {info.get('rag_version', 'unknown')}")
            print(f"  Modèle embedding: {info.get('embedding_model', 'unknown')}")
            print(f"  Cache activé: {info.get('cache_enabled', False)}")
            print(f"  Utilise v2: {'✅ OUI' if info.get('is_v2') else '❌ NON'}")
            print(f"\n  ℹ️  {info.get('info', '')}")

            if info.get('is_v2'):
                print("\n🎉 EXCELLENT! Vous utilisez RAG v2 (optimisé)")
                print("   → Meilleur modèle multilingual")
                print("   → Cache des embeddings")
                print("   → Performances optimales")
            else:
                print("\n⚠️  Vous utilisez RAG v1 (non optimisé)")
                print("   → Considérez passer à v2 pour +1500% de performance")

        else:
            print(f"❌ Erreur endpoint /rag-info: {response.status_code}")
            print("   L'endpoint n'existe peut-être pas encore")

    except Exception as e:
        print(f"❌ Erreur: {e}")

    # 3. Vérifier les collections
    try:
        response = requests.get(f"{API_URL}/collections", timeout=5)
        if response.status_code == 200:
            collections = response.json()
            print(f"\n📚 COLLECTIONS: {len(collections)}")

            if collections:
                for col in collections[:3]:  # Afficher les 3 premières
                    print(f"  • {col['name']}: {col['total_chunks']} chunks")

                # Vérifier si indexées avec v1 ou v2
                print("\n💡 NOTE:")
                print("   Si les collections ont été indexées avec v1,")
                print("   réindexez-les avec: rm -rf data/vector_db && python scripts/quick_index.py")
            else:
                print("   Aucune collection. Indexez avec: python scripts/quick_index.py")

        else:
            print(f"\n❌ Erreur récupération collections: {response.status_code}")

    except Exception as e:
        print(f"\n❌ Erreur collections: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_rag_version()
