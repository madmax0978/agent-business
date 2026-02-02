#!/usr/bin/env python3
"""
Script rapide pour indexer quelques PDF pour les tests
"""

import sys
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

API_BASE_URL = "http://localhost:8000"

def check_api():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def index_pdf(pdf_path: Path, collection_name: str):
    print(f"\n📄 Indexation: {pdf_path.name} → {collection_name}")
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            # L'endpoint /upload attend seulement collection_name comme paramètre
            data = {
                'collection_name': collection_name
            }

            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                data=data,
                timeout=300
            )

            if response.status_code == 200:
                result = response.json()
                total_chunks = result.get('total_chunks', 0)
                print(f"   ✅ {total_chunks} chunks créés")
                print(f"      Tables: {result.get('table_chunks', 0)}, Texte: {result.get('text_chunks', 0)}")
                return True
            else:
                print(f"   ❌ Erreur {response.status_code}: {response.text[:200]}")
                return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def main():
    print("="*60)
    print("INDEXATION RAPIDE - 3 PDF pour tests")
    print("="*60)

    if not check_api():
        print("\n❌ API non accessible")
        print("Lancez: uvicorn api.main:app --reload")
        sys.exit(1)
    print("\n✅ API accessible")

    # Indexer 3 PDF légers pour les tests
    pdf_dir = Path(__file__).parent.parent / "data" / "context"

    pdfs_to_index = [
        ("hermes_20240209_cp_resultatsannuels2023_vf.pdf", "Hermes_2023"),
        ("lvmhDocuments financiers  - 31 décembre 2024.pdf", "LVMH_2024"),
        ("safranFY 2024 FR Vdef.pdf", "Safran_2024"),
    ]

    print(f"\n🚀 Indexation de {len(pdfs_to_index)} fichiers...")

    success = 0
    for filename, collection in pdfs_to_index:
        pdf_path = pdf_dir / filename
        if pdf_path.exists():
            if index_pdf(pdf_path, collection):
                success += 1
        else:
            print(f"\n⚠️  Fichier non trouvé: {filename}")

    print(f"\n{'='*60}")
    print(f"✅ {success}/{len(pdfs_to_index)} fichiers indexés")
    print("\n💡 Lancez maintenant: ./run_tests.sh")
    print("="*60)

if __name__ == "__main__":
    main()
