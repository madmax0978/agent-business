#!/usr/bin/env python3
"""
Script pour indexer automatiquement tous les PDF du dossier data/context/
dans des collections ChromaDB pour les tests.
"""

import os
import sys
from pathlib import Path
import requests
import time

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# URL de l'API
API_BASE_URL = "http://localhost:8000"

def get_company_from_filename(filename: str) -> str:
    """Extrait le nom de l'entreprise du nom de fichier"""
    filename_lower = filename.lower()

    # Mapping des entreprises
    companies = {
        'lvmh': 'LVMH',
        'hermes': 'Hermès',
        'loreal': "L'Oréal",
        'sanofi': 'Sanofi',
        'totalenergies': 'TotalEnergies',
        'total': 'TotalEnergies',
        'bnp': 'BNP Paribas',
        'axa': 'AXA',
        'airbus': 'Airbus',
        'airliquid': 'Air Liquide',
        'schneider': 'Schneider Electric',
        'danone': 'Danone',
        'renault': 'Renault',
        'orange': 'Orange',
        'capgemini': 'Capgemini',
        'kering': 'Kering',
        'pernod': 'Pernod Ricard',
        'engie': 'Engie',
        'saint-gobain': 'Saint-Gobain',
        'vinci': 'Vinci',
        'bouygues': 'Bouygues',
        'carrefour': 'Carrefour',
        'safran': 'Safran',
        'stm': 'STMicroelectronics',
        '3ds': 'Dassault Systèmes',
    }

    for key, company in companies.items():
        if key in filename_lower:
            return company

    return "Entreprise"

def get_year_from_filename(filename: str) -> str:
    """Extrait l'année du nom de fichier"""
    # Chercher 2021, 2022, 2023, 2024, 2025
    for year in ['2025', '2024', '2023', '2022', '2021']:
        if year in filename:
            return year
    return "N/A"

def check_api_health():
    """Vérifie que l'API est accessible"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_collections():
    """Récupère la liste des collections existantes"""
    try:
        response = requests.get(f"{API_BASE_URL}/collections", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def index_pdf(pdf_path: Path, collection_name: str):
    """Indexe un PDF dans une collection"""
    print(f"\n📄 Indexation: {pdf_path.name}")
    print(f"   Collection: {collection_name}")

    try:
        # Upload du fichier
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            # L'endpoint /upload attend seulement collection_name
            data = {
                'collection_name': collection_name
            }

            print(f"   Upload en cours... (taille: {pdf_path.stat().st_size / 1024 / 1024:.1f} MB)")
            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                data=data,
                timeout=300  # 5 minutes max
            )

            if response.status_code == 200:
                result = response.json()
                total_chunks = result.get('total_chunks', 0)
                print(f"   ✅ Succès! {total_chunks} chunks créés")
                print(f"      Tables: {result.get('table_chunks', 0)}, Texte: {result.get('text_chunks', 0)}")
                return True
            else:
                print(f"   ❌ Erreur {response.status_code}: {response.text[:200]}")
                return False

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False

def main():
    print("="*80)
    print("INDEXATION AUTOMATIQUE DES PDF - RAG-PEA")
    print("="*80)

    # 1. Vérifier l'API
    print("\n🔍 Vérification de l'API...")
    if not check_api_health():
        print("❌ L'API n'est pas accessible sur http://localhost:8000")
        print("   Lancez l'API avec: uvicorn api.main:app --reload")
        sys.exit(1)
    print("✅ API accessible")

    # 2. Lister les collections existantes
    print("\n📚 Collections existantes:")
    collections = get_collections()
    if collections:
        for col in collections:
            print(f"   - {col['name']} ({col.get('count', 0)} documents)")
    else:
        print("   Aucune collection")

    # 3. Trouver tous les PDF
    pdf_dir = Path(__file__).parent.parent / "data" / "context"
    if not pdf_dir.exists():
        print(f"❌ Dossier {pdf_dir} non trouvé")
        sys.exit(1)

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    print(f"\n📁 {len(pdf_files)} fichiers PDF trouvés dans {pdf_dir}")

    if not pdf_files:
        print("❌ Aucun PDF à indexer")
        sys.exit(0)

    # 4. Demander confirmation
    print("\n⚠️  L'indexation peut prendre du temps (plusieurs minutes par fichier)")
    print(f"   Total estimé: {len(pdf_files) * 2:.0f}-{len(pdf_files) * 5:.0f} minutes")

    response = input("\n❓ Voulez-vous indexer tous les PDF? (o/N): ")
    if response.lower() not in ['o', 'oui', 'y', 'yes']:
        print("❌ Annulé")
        sys.exit(0)

    # 5. Indexer tous les PDF
    print("\n🚀 Démarrage de l'indexation...")
    print("="*80)

    success_count = 0
    failed_count = 0
    skipped_count = 0

    start_time = time.time()

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] {pdf_path.name}")

        # Déterminer le nom de la collection
        company = get_company_from_filename(pdf_path.name)
        year = get_year_from_filename(pdf_path.name)

        # Créer un nom de collection descriptif
        if "rapport" in pdf_path.name.lower() or "annual" in pdf_path.name.lower():
            doc_type = "Rapport Annuel"
        elif "semestriel" in pdf_path.name.lower() or "half" in pdf_path.name.lower():
            doc_type = "Rapport Semestriel"
        elif "financier" in pdf_path.name.lower():
            doc_type = "Documents Financiers"
        else:
            doc_type = "Document"

        collection_name = f"{company}_{year}".replace(" ", "_").replace("'", "")

        # Vérifier si déjà indexé
        existing_collections = [c['name'] for c in get_collections()]
        if collection_name in existing_collections:
            print(f"   ⏭️  Collection '{collection_name}' existe déjà, passage au suivant")
            skipped_count += 1
            continue

        # Indexer
        if index_pdf(pdf_path, collection_name):
            success_count += 1
            print(f"   📊 Progression: {success_count} réussis, {failed_count} échoués, {skipped_count} ignorés")
        else:
            failed_count += 1

        # Pause entre fichiers pour ne pas surcharger
        if i < len(pdf_files):
            time.sleep(2)

    # 6. Résumé
    elapsed_time = time.time() - start_time
    print("\n" + "="*80)
    print("RÉSUMÉ DE L'INDEXATION")
    print("="*80)
    print(f"✅ Réussis:  {success_count}/{len(pdf_files)}")
    print(f"❌ Échoués:  {failed_count}/{len(pdf_files)}")
    print(f"⏭️  Ignorés:  {skipped_count}/{len(pdf_files)}")
    print(f"⏱️  Temps total: {elapsed_time / 60:.1f} minutes")

    # 7. Afficher les collections finales
    print("\n📚 Collections finales:")
    final_collections = get_collections()
    if final_collections:
        for col in final_collections:
            print(f"   - {col['name']} ({col.get('count', 0)} documents)")

    print("\n🎉 Indexation terminée!")
    print("\n💡 Vous pouvez maintenant exécuter les tests:")
    print("   ./run_tests.sh")

if __name__ == "__main__":
    main()
