#!/usr/bin/env python3
"""
Script d'indexation batch pour traiter de nombreux documents PDF
avec suivi de progression et reprise automatique
"""

import requests
import json
from pathlib import Path
from datetime import datetime
import time
import sys
import unicodedata
import re


class BatchIndexer:
    """Indexeur batch avec suivi de progression"""

    def __init__(self, documents_dir: str, api_url: str = "http://localhost:8000"):
        self.documents_dir = Path(documents_dir)
        self.api_url = api_url
        self.progress_file = Path("indexing_progress.json")
        self.log_file = Path("indexing_log.txt")
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None,
        }

    def load_progress(self):
        """Charge la progression sauvegardée"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"processed": [], "failed": []}

    def save_progress(self, progress):
        """Sauvegarde la progression"""
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)

    def log(self, message, level="INFO"):
        """Log un message dans le fichier et la console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"

        print(log_line)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")

    def get_file_size_mb(self, file_path):
        """Retourne la taille du fichier en MB"""
        return file_path.stat().st_size / (1024 * 1024)

    def estimate_processing_time(self, file_size_mb):
        """Estime le temps de traitement (environ 240 secondes par MB)"""
        return int(file_size_mb * 240)

    def sanitize_collection_name(self, name: str) -> str:
        """
        Nettoie le nom de collection pour respecter le format requis:
        - 3-512 caractères
        - Uniquement [a-zA-Z0-9._-]
        - Commence et finit par [a-zA-Z0-9]
        """
        # Remplacer espaces et tirets par underscore
        name = name.lower().replace(" ", "_").replace("-", "_")

        # Supprimer tous les caractères non autorisés (garder seulement a-z, 0-9, ., _, -)
        name = re.sub(r'[^a-z0-9._-]', '', name)

        # Supprimer les underscores multiples consécutifs
        name = re.sub(r'_+', '_', name)

        # S'assurer que le nom commence et finit par [a-zA-Z0-9]
        name = name.strip('._-')

        # S'assurer que le nom fait au moins 3 caractères
        if len(name) < 3:
            name = f"doc_{name}_001"

        # Limiter à 512 caractères
        if len(name) > 512:
            name = name[:512].rstrip('._-')

        return name

    def index_document(self, file_path: Path, timeout: int = None, retry: int = 0, max_retries: int = 2):
        """Indexe un document avec timeout adapté et système de retry"""

        size_mb = self.get_file_size_mb(file_path)

        # Timeout adapté à la taille
        # Formule : 240 secondes par MB (4 min/MB), minimum 15 minutes, maximum 4 heures
        # Pour les retry, on augmente le timeout de 50% à chaque tentative
        if timeout is None:
            base_timeout = max(900, min(14400, int(size_mb * 240)))
            timeout = int(base_timeout * (1 + retry * 0.5))  # +50% par retry

        # Nettoyer le nom de collection pour respecter le format requis
        collection_name = self.sanitize_collection_name(file_path.stem)

        retry_msg = f" (Tentative {retry + 1}/{max_retries + 1})" if retry > 0 else ""
        self.log(f"📄 Indexation: {file_path.name}{retry_msg}")
        self.log(f"   Taille: {size_mb:.1f} MB")
        self.log(f"   Timeout: {timeout}s (~{timeout//60}min)")
        self.log(f"   Collection: {collection_name}")

        try:
            response = requests.post(
                f"{self.api_url}/index",
                json={
                    "file_path": str(file_path.resolve()),
                    "document_name": file_path.name,
                    "collection_name": collection_name,
                },
                timeout=timeout
            )

            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Succès! Chunks: {data['total_chunks']} (Tables: {data['table_chunks']}, Texte: {data['text_chunks']})", "SUCCESS")
                return True, data
            else:
                self.log(f"❌ Erreur API: {response.status_code} - {response.text}", "ERROR")
                return False, None

        except requests.exceptions.Timeout:
            self.log(f"⏱️  Timeout après {timeout}s ({timeout//60}min)", "ERROR")

            # Retry automatique avec timeout augmenté
            if retry < max_retries:
                self.log(f"🔄 Nouvelle tentative avec timeout augmenté...", "WARNING")
                time.sleep(5)  # Pause de 5 secondes avant retry
                return self.index_document(file_path, timeout=None, retry=retry + 1, max_retries=max_retries)
            else:
                self.log(f"❌ Échec définitif après {max_retries + 1} tentatives", "ERROR")
                return False, None

        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}", "ERROR")
            return False, None

    def run(self, skip_existing=True, max_documents=None, retry_failed=False):
        """Lance l'indexation batch"""

        self.log("=" * 80)
        self.log("🚀 INDEXATION BATCH DE DOCUMENTS")
        self.log("=" * 80)

        # Vérifier que l'API est accessible
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code != 200:
                self.log("❌ L'API ne répond pas correctement", "ERROR")
                self.log("⚠️  Lancez d'abord l'API: cd api && python -m uvicorn main:app --reload", "ERROR")
                return
        except Exception as e:
            self.log(f"❌ Impossible de joindre l'API: {e}", "ERROR")
            self.log("⚠️  Lancez d'abord l'API: cd api && python -m uvicorn main:app --reload", "ERROR")
            return

        # Charger la progression
        progress = self.load_progress()

        # Trouver tous les PDFs
        pdf_files = sorted(self.documents_dir.glob("*.pdf"))

        if not pdf_files:
            self.log(f"❌ Aucun fichier PDF trouvé dans {self.documents_dir}", "ERROR")
            return

        self.stats["total"] = len(pdf_files)
        self.stats["start_time"] = datetime.now().isoformat()

        # Filtrer les fichiers selon le mode
        if retry_failed:
            # Mode retry : traiter uniquement les fichiers qui ont échoué
            failed_names = [f["file"] for f in progress.get("failed", [])]
            pdf_files = [f for f in pdf_files if f.name in failed_names]
            self.log(f"🔄 MODE RETRY : Réessayer les fichiers ayant échoué")
            self.stats["skipped"] = self.stats["total"] - len(pdf_files)
        elif skip_existing:
            # Mode normal : ignorer les fichiers déjà traités
            processed_names = [p["file"] for p in progress.get("processed", [])]
            pdf_files = [f for f in pdf_files if f.name not in processed_names]
            self.stats["skipped"] = self.stats["total"] - len(pdf_files)

        if max_documents:
            pdf_files = pdf_files[:max_documents]

        self.log(f"\n📊 STATISTIQUES:")
        self.log(f"   Total de documents: {self.stats['total']}")
        self.log(f"   Déjà traités: {self.stats['skipped']}")
        self.log(f"   À traiter: {len(pdf_files)}")

        # Calculer la taille totale
        total_size = sum(self.get_file_size_mb(f) for f in pdf_files)
        estimated_time = total_size * 240 / 60  # minutes (240 secondes par MB)

        self.log(f"   Taille totale: {total_size:.1f} MB")
        self.log(f"   Temps estimé: {estimated_time:.0f} minutes (~{estimated_time/60:.1f}h)")
        self.log("")

        if len(pdf_files) == 0:
            self.log("✅ Tous les documents sont déjà indexés!", "SUCCESS")
            return

        # Demander confirmation
        self.log("⚠️  IMPORTANT: Ce processus va prendre du temps.")
        self.log("   Vous pouvez l'interrompre avec Ctrl+C et le relancer plus tard.")
        self.log("   La progression sera sauvegardée automatiquement.")
        self.log("")

        response = input("Continuer? (y/n): ")
        if response.lower() != 'y':
            self.log("❌ Annulé par l'utilisateur")
            return

        self.log("\n🏃 Démarrage de l'indexation...\n")

        # Traiter chaque document
        for i, pdf_file in enumerate(pdf_files, 1):
            self.log("=" * 80)
            self.log(f"📄 Document {i}/{len(pdf_files)} ({i/len(pdf_files)*100:.1f}%)")
            self.log("=" * 80)

            start_time = time.time()
            success, data = self.index_document(pdf_file)
            elapsed = time.time() - start_time

            if success:
                self.stats["success"] += 1
                progress["processed"].append({
                    "file": pdf_file.name,
                    "collection": data["collection_name"],
                    "chunks": data["total_chunks"],
                    "timestamp": datetime.now().isoformat(),
                    "processing_time": elapsed
                })
                # Retirer de la liste des échecs si c'était un retry réussi
                progress["failed"] = [f for f in progress.get("failed", []) if f["file"] != pdf_file.name]
            else:
                self.stats["failed"] += 1
                # Ajouter à la liste des échecs seulement s'il n'y est pas déjà
                if pdf_file.name not in [f["file"] for f in progress.get("failed", [])]:
                    progress["failed"].append({
                        "file": pdf_file.name,
                        "timestamp": datetime.now().isoformat()
                    })

            # Sauvegarder la progression après chaque document
            self.save_progress(progress)

            # Afficher les stats intermédiaires
            success_rate = (self.stats["success"] / i) * 100
            remaining = len(pdf_files) - i

            self.log(f"\n📊 Progression: {i}/{len(pdf_files)} documents")
            self.log(f"   ✅ Succès: {self.stats['success']}")
            self.log(f"   ❌ Échecs: {self.stats['failed']}")
            self.log(f"   📈 Taux de réussite: {success_rate:.1f}%")
            self.log(f"   ⏱️  Temps écoulé: {elapsed:.1f}s")
            self.log(f"   🔄 Restants: {remaining} documents\n")

            # Pause entre documents pour ne pas surcharger l'API
            if i < len(pdf_files):
                self.log("⏸️  Pause de 2 secondes...\n")
                time.sleep(2)

        # Stats finales
        self.stats["end_time"] = datetime.now().isoformat()
        total_time = (datetime.fromisoformat(self.stats["end_time"]) -
                     datetime.fromisoformat(self.stats["start_time"])).total_seconds()

        self.log("=" * 80)
        self.log("🎉 INDEXATION TERMINÉE")
        self.log("=" * 80)
        self.log(f"\n📊 STATISTIQUES FINALES:")
        self.log(f"   Documents traités: {len(pdf_files)}")
        self.log(f"   ✅ Succès: {self.stats['success']}")
        self.log(f"   ❌ Échecs: {self.stats['failed']}")
        self.log(f"   Taux de réussite: {(self.stats['success']/len(pdf_files))*100:.1f}%")
        self.log(f"   ⏱️  Temps total: {total_time/60:.1f} minutes ({total_time/3600:.1f}h)")
        self.log(f"\n📁 Logs sauvegardés: {self.log_file}")
        self.log(f"📁 Progression sauvegardée: {self.progress_file}")

        if self.stats["failed"] > 0:
            self.log(f"\n⚠️  {self.stats['failed']} document(s) ont échoué")
            self.log("   Consultez le fichier de log pour les détails")


def main():
    """Point d'entrée"""

    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    INDEXATION BATCH DE DOCUMENTS                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage:
    python batch_index_documents.py <dossier_pdfs> [options]

Options:
    --force          Réindexer même les documents déjà traités
    --retry          Réessayer uniquement les documents ayant échoué
    --max N          Traiter seulement les N premiers documents
    --api-url URL    URL de l'API (défaut: http://localhost:8000)

Exemples:

    # Indexer tous les PDFs du dossier data/context/
    python batch_index_documents.py data/context/

    # Forcer la réindexation de tous les documents
    python batch_index_documents.py data/context/ --force

    # Réessayer les documents ayant échoué (avec timeouts augmentés)
    python batch_index_documents.py data/context/ --retry

    # Traiter seulement les 10 premiers (pour tester)
    python batch_index_documents.py data/context/ --max 10

💡 CONSEILS:

    • L'API doit être lancée: cd api && python -m uvicorn main:app --reload
    • Le processus peut prendre plusieurs heures pour 79 documents
    • Vous pouvez interrompre avec Ctrl+C et relancer plus tard
    • La progression est sauvegardée automatiquement
    • Timeouts adaptatifs: 15 min minimum, jusqu'à 4 heures pour gros docs
    • Retry automatique: 3 tentatives avec timeout augmenté
    • Un document de 1 MB ≈ 4 minutes, 15 MB ≈ 1 heure

📊 PROGRESSION:

    La progression est sauvegardée dans:
    • indexing_progress.json : Documents traités et à traiter
    • indexing_log.txt : Log complet de l'opération

🔄 REPRISE APRÈS INTERRUPTION:

    Relancez simplement la même commande, les documents déjà
    traités seront automatiquement ignorés.
""")
        return

    documents_dir = sys.argv[1]
    skip_existing = "--force" not in sys.argv
    retry_failed = "--retry" in sys.argv
    api_url = "http://localhost:8000"
    max_documents = None

    # Parser les options
    if "--api-url" in sys.argv:
        idx = sys.argv.index("--api-url")
        api_url = sys.argv[idx + 1]

    if "--max" in sys.argv:
        idx = sys.argv.index("--max")
        max_documents = int(sys.argv[idx + 1])

    # Lancer l'indexation
    indexer = BatchIndexer(documents_dir, api_url)

    try:
        indexer.run(skip_existing=skip_existing, max_documents=max_documents, retry_failed=retry_failed)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur (Ctrl+C)")
        print("💾 Progression sauvegardée!")
        print("🔄 Relancez la même commande pour reprendre l'indexation\n")


if __name__ == "__main__":
    main()
