#!/usr/bin/env python3
"""
Script pour indexer tous les PDF un par un
- Noms de collections validés (compatible ChromaDB)
- Anti-doublons fiable
- Indexation séquentielle (simple et fiable)
"""

import os
import sys
from pathlib import Path
import requests
import time
import re
import unicodedata

sys.path.insert(0, str(Path(__file__).parent.parent))

API_BASE_URL = "http://localhost:8000"
TIMEOUT = 1800  # 30 minutes par PDF

def sanitize_collection_name(name: str) -> str:
    """
    Nettoie le nom de collection pour respecter les règles ChromaDB.
    DOIT être identique à la fonction dans api/main.py !

    Règles ChromaDB:
    - 3-512 caractères
    - Seulement [a-zA-Z0-9._-]
    """
    # Enlever l'extension .pdf si présente
    if name.endswith('.pdf'):
        name = name[:-4]

    # Remplacer espaces par underscores
    name = name.replace(" ", "_")

    # Supprimer les accents: "décembre" → "decembre"
    name = unicodedata.normalize('NFKD', name)
    name = name.encode('ASCII', 'ignore').decode('ASCII')

    # Garder seulement [a-zA-Z0-9._-]
    name = re.sub(r'[^a-zA-Z0-9._-]', '', name)

    # Remplacer multiples _.- par un seul
    name = re.sub(r'[._-]+', '_', name)

    # Enlever _.- au début/fin
    name = name.strip('._-')

    # Assurer minimum 3 caractères
    if len(name) < 3:
        name = f"doc_{name}_001"

    # Maximum 512 caractères
    return name[:512].rstrip('._-')

def check_api():
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

def index_pdf(pdf_path: Path, collection_name: str, index: int, total: int):
    """
    Indexe un PDF dans une collection.

    Returns:
        tuple: (success: bool, status: str, collection_name: str)
    """
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            data = {'collection_name': collection_name}

            size_mb = pdf_path.stat().st_size / 1024 / 1024

            print(f"\n[{index}/{total}] 📄 {pdf_path.name}")
            print(f"   Collection: {collection_name}")
            print(f"   Taille: {size_mb:.1f} MB")
            print(f"   ⏳ Indexation en cours...")

            response = requests.post(
                f"{API_BASE_URL}/upload",
                files=files,
                data=data,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                total_chunks = result.get('total_chunks', 0)
                table_chunks = result.get('table_chunks', 0)
                text_chunks = result.get('text_chunks', 0)

                print(f"   ✅ Succès! {total_chunks} chunks")
                print(f"      Tables: {table_chunks}, Texte: {text_chunks}")

                return (True, "success", collection_name)
            else:
                error_msg = response.text[:200]
                print(f"   ❌ Erreur {response.status_code}: {error_msg}")

                return (False, f"HTTP {response.status_code}", collection_name)

    except Exception as e:
        print(f"   ❌ Exception: {str(e)[:200]}")

        return (False, str(e)[:50], collection_name)

def main():
    print("="*80)
    print("INDEXATION PDF - UN PAR UN")
    print("="*80)

    # 1. Vérifier l'API
    print("\n🔍 Vérification de l'API...")
    if not check_api():
        print("❌ L'API n'est pas accessible sur http://localhost:8000")
        print("   Lancez: cd api && python -m uvicorn main:app --reload")
        sys.exit(1)
    print("✅ API accessible")

    # 2. Trouver tous les PDF
    pdf_dir = Path(__file__).parent.parent / "data" / "context"
    if not pdf_dir.exists():
        print(f"❌ Dossier {pdf_dir} non trouvé")
        sys.exit(1)

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    print(f"\n📁 {len(pdf_files)} fichiers PDF trouvés")

    if not pdf_files:
        print("❌ Aucun PDF à indexer")
        sys.exit(0)

    # 3. Récupérer collections existantes
    print("\n📚 Vérification des collections existantes...")
    existing_collections = {c['name']: c for c in get_collections()}

    if existing_collections:
        print(f"   {len(existing_collections)} collections déjà indexées")
        print("   (seront skippées automatiquement)")
    else:
        print("   Aucune collection (départ à zéro)")

    # 4. Préparer la liste des PDFs à indexer
    pdfs_to_index = []
    skipped = []

    for pdf_path in pdf_files:
        # Générer le nom de collection (identique à l'API)
        collection_name = sanitize_collection_name(pdf_path.name)

        # Vérifier si déjà indexé
        if collection_name in existing_collections:
            skipped.append((pdf_path.name, collection_name))
        else:
            pdfs_to_index.append((pdf_path, collection_name))

    # Afficher résumé
    print(f"\n📊 RÉSUMÉ:")
    print(f"   Total PDFs: {len(pdf_files)}")
    print(f"   À indexer: {len(pdfs_to_index)}")
    print(f"   Déjà indexés: {len(skipped)}")

    if skipped:
        print(f"\n⏭️  Collections déjà indexées (skippées):")
        for pdf_name, col_name in skipped[:10]:  # Max 10 pour pas surcharger
            print(f"   - {pdf_name} → {col_name}")
        if len(skipped) > 10:
            print(f"   ... et {len(skipped) - 10} autres")

    if not pdfs_to_index:
        print("\n✅ Tous les PDFs sont déjà indexés!")
        sys.exit(0)

    # 5. Confirmation
    print(f"\n⚠️  L'indexation peut prendre du temps:")
    print(f"   - Petits PDFs: ~1-2 min chacun")
    print(f"   - Gros PDFs (600 pages): ~15-20 min chacun")
    print(f"   - Temps estimé: {len(pdfs_to_index) * 3}-{len(pdfs_to_index) * 10} minutes")

    response = input(f"\n❓ Indexer {len(pdfs_to_index)} PDFs? (o/N): ")
    if response.lower() not in ['o', 'oui', 'y', 'yes']:
        print("❌ Annulé")
        sys.exit(0)

    # 6. Indexation séquentielle
    print("\n🚀 Démarrage de l'indexation...")
    print("="*80)

    start_time = time.time()
    success_count = 0
    failed_count = 0

    # Traiter chaque PDF un par un
    for i, (pdf_path, collection_name) in enumerate(pdfs_to_index):
        try:
            success, status, col_name = index_pdf(
                pdf_path,
                collection_name,
                i + 1,
                len(pdfs_to_index)
            )

            if success:
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            print(f"\n❌ Erreur inattendue pour {pdf_path.name}: {e}")
            failed_count += 1

    # 7. Résumé final
    elapsed_time = time.time() - start_time

    print("\n" + "="*80)
    print("RÉSUMÉ FINAL")
    print("="*80)
    print(f"✅ Réussis:  {success_count}/{len(pdfs_to_index)}")
    print(f"❌ Échoués:  {failed_count}/{len(pdfs_to_index)}")
    print(f"⏭️  Ignorés:  {len(skipped)}/{len(pdf_files)} (déjà indexés)")
    print(f"⏱️  Temps total: {elapsed_time / 60:.1f} minutes")

    # 8. Collections finales
    print("\n📚 Collections finales:")
    final_collections = get_collections()
    print(f"   Total: {len(final_collections)} collections")

    if final_collections:
        total_chunks = sum(c.get('total_chunks', 0) for c in final_collections)
        print(f"   Chunks totaux: {total_chunks:,}")

    print("\n🎉 Indexation terminée!")

    if failed_count > 0:
        print(f"\n⚠️  {failed_count} fichiers ont échoué")
        print("   Relancez le script pour réessayer (les réussis seront skippés)")

    print("\n💡 Tests disponibles:")
    print("   ./run_tests.sh")

if __name__ == "__main__":
    main()
