#!/usr/bin/env python3
"""
Script d'indexation pour le système RAG
Charge les chunks et les indexe dans ChromaDB avec leurs embeddings
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Configuration
CHUNKS_FILE = "../data/chunks/chunks.json"
DB_PATH = "../data/vector_db"
COLLECTION_NAME = "lvmh_report"
EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

# Console pour affichage
console = Console(width=200)


def load_chunks(chunks_file: str) -> List[Dict[str, Any]]:
    """Charge les chunks depuis le fichier JSON"""
    console.print(f"[bold blue]Chargement des chunks depuis:[/bold blue] {chunks_file}")

    if not os.path.exists(chunks_file):
        raise FileNotFoundError(f"Le fichier de chunks n'existe pas : {chunks_file}")

    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    console.print(f"[bold green]✓[/bold green] {len(chunks)} chunks chargés")
    return chunks


def initialize_model(model_id: str) -> SentenceTransformer:
    """Initialise le modèle d'embedding"""
    console.print(f"[bold blue]Chargement du modèle d'embedding:[/bold blue] {model_id}")
    model = SentenceTransformer(model_id)
    console.print("[bold green]✓[/bold green] Modèle chargé")
    return model


def initialize_chromadb(db_path: str, collection_name: str) -> chromadb.Collection:
    """Initialise ChromaDB et crée/récupère la collection"""
    console.print(f"[bold blue]Initialisation de ChromaDB:[/bold blue] {db_path}")

    # Créer le répertoire si nécessaire
    Path(db_path).mkdir(parents=True, exist_ok=True)

    # Initialiser le client ChromaDB
    chroma_client = chromadb.PersistentClient(
        path=db_path,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )

    # Supprimer la collection si elle existe déjà (pour réindexer)
    try:
        chroma_client.delete_collection(name=collection_name)
        console.print(f"[yellow]Collection existante '{collection_name}' supprimée[/yellow]")
    except Exception:
        pass

    # Créer la collection
    collection = chroma_client.create_collection(
        name=collection_name,
        metadata={"description": "LVMH Financial Report Chunks"}
    )

    console.print(f"[bold green]✓[/bold green] Collection '{collection_name}' créée")
    return collection


def generate_embeddings(
    chunks: List[Dict[str, Any]],
    model: SentenceTransformer
) -> List[List[float]]:
    """Génère les embeddings pour tous les chunks"""
    console.print("[bold blue]Génération des embeddings...[/bold blue]")

    texts = [chunk["text"] for chunk in chunks]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Génération des embeddings...", total=len(texts))

        # Traiter par lots pour optimiser
        batch_size = 32
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = model.encode(batch, show_progress_bar=False)
            all_embeddings.extend(embeddings.tolist())
            progress.update(task, advance=len(batch))

    console.print(f"[bold green]✓[/bold green] {len(all_embeddings)} embeddings générés")
    return all_embeddings


def index_chunks(
    collection: chromadb.Collection,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]]
) -> None:
    """Indexe les chunks dans ChromaDB"""
    console.print("[bold blue]Indexation dans ChromaDB...[/bold blue]")

    ids = []
    documents = []
    metadatas = []
    embeddings_list = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Indexation des chunks...", total=len(chunks))

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # ID unique pour chaque chunk
            chunk_id = f"chunk_{chunk['chunk_id']}"

            # Document (le texte du chunk)
            document = chunk["text"]

            # Métadonnées
            is_table = "table" in chunk["doc_items_labels"]
            metadata = {
                "chunk_id": chunk["chunk_id"],
                "num_tokens": chunk["num_tokens"],
                "doc_items_labels": ",".join(chunk["doc_items_labels"]),
                "headings": ",".join(chunk["metadata"]["headings"]) if chunk["metadata"]["headings"] else "",
                "is_table": is_table,  # Flag booléen pour faciliter le filtrage
                "content_type": "table" if is_table else "text",  # Type de contenu
            }

            ids.append(chunk_id)
            documents.append(document)
            metadatas.append(metadata)
            embeddings_list.append(embedding)

            progress.update(task, advance=1)

        # Ajouter tous les documents à la collection
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings_list
        )

    console.print(f"[bold green]✓[/bold green] {len(chunks)} chunks indexés")


def verify_index(collection: chromadb.Collection, num_samples: int = 3) -> None:
    """Vérifie l'indexation en affichant quelques exemples"""
    console.print(f"\n[bold blue]Vérification de l'index (échantillon de {num_samples}):[/bold blue]\n")

    # Récupérer les premiers chunks
    results = collection.get(
        limit=num_samples,
        include=["documents", "metadatas"]
    )

    for i, (doc_id, document, metadata) in enumerate(zip(
        results["ids"],
        results["documents"],
        results["metadatas"]
    )):
        text_preview = document[:300] + "..." if len(document) > 300 else document
        title = f"ID: {doc_id} | Tokens: {metadata['num_tokens']} | Labels: {metadata['doc_items_labels']}"
        console.print(Panel(text_preview, title=title, border_style="cyan"))


def get_collection_stats(collection: chromadb.Collection) -> Dict[str, Any]:
    """Récupère les statistiques de la collection"""
    count = collection.count()

    # Récupérer tous les chunks pour analyser les types
    all_chunks = collection.get(include=["metadatas"])

    # Compter les tableaux vs texte
    table_count = sum(1 for m in all_chunks["metadatas"] if m.get("is_table", False))
    text_count = count - table_count

    return {
        "total_chunks": count,
        "table_chunks": table_count,
        "text_chunks": text_count,
        "table_percentage": round((table_count / count * 100), 2) if count > 0 else 0
    }


def search_by_content_type(
    collection: chromadb.Collection,
    query: str,
    content_type: str = "all",
    n_results: int = 5
) -> Dict[str, Any]:
    """
    Recherche des chunks par type de contenu

    Args:
        collection: Collection ChromaDB
        query: Texte de la requête
        content_type: "table", "text", ou "all"
        n_results: Nombre de résultats à retourner

    Returns:
        Résultats de la recherche
    """
    where_filter = None
    if content_type == "table":
        where_filter = {"is_table": True}
    elif content_type == "text":
        where_filter = {"is_table": False}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter if where_filter else None,
        include=["documents", "metadatas", "distances"]
    )

    return results


def main():
    """Fonction principale"""
    try:
        console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]")
        console.print("[bold magenta]  Système d'indexation RAG - LVMH Report  [/bold magenta]")
        console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]\n")

        # 1. Charger les chunks
        chunks = load_chunks(CHUNKS_FILE)

        # 2. Initialiser le modèle d'embedding
        model = initialize_model(EMBED_MODEL_ID)

        # 3. Initialiser ChromaDB
        collection = initialize_chromadb(DB_PATH, COLLECTION_NAME)

        # 4. Générer les embeddings
        embeddings = generate_embeddings(chunks, model)

        # 5. Indexer les chunks
        index_chunks(collection, chunks, embeddings)

        # 6. Vérifier l'indexation
        verify_index(collection)

        # 7. Afficher les statistiques
        stats = get_collection_stats(collection)
        console.print(Panel(
            f"[bold]Statistiques de l'index:[/bold]\n"
            f"• Nombre total de chunks indexés : {stats['total_chunks']}\n"
            f"• Chunks avec tableaux : {stats['table_chunks']} ({stats['table_percentage']}%)\n"
            f"• Chunks texte simple : {stats['text_chunks']}\n"
            f"• Collection : {COLLECTION_NAME}\n"
            f"• Base de données : {DB_PATH}\n"
            f"• Modèle d'embedding : {EMBED_MODEL_ID}",
            title="Résumé de l'indexation",
            border_style="green"
        ))

        console.print("\n[bold green]✓ Indexation terminée avec succès ![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]✗ Erreur fatale:[/bold red] {e}")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        raise


if __name__ == "__main__":
    main()
