#!/usr/bin/env python3
"""
Script de requête pour le système RAG
Permet d'interroger la base vectorielle en langage naturel
"""

import sys
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# Configuration
DB_PATH = "../data/vector_db"
COLLECTION_NAME = "lvmh_report"
EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_N_RESULTS = 3

# Console pour affichage
console = Console(width=200)


def load_database():
    """Charge la base de données ChromaDB"""
    console.print("[bold blue]Chargement de la base de données...[/bold blue]")

    chroma_client = chromadb.PersistentClient(
        path=DB_PATH,
        settings=Settings(anonymized_telemetry=False)
    )

    try:
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        count = collection.count()
        console.print(f"[bold green]✓[/bold green] Base chargée : {count} chunks disponibles\n")
        return collection
    except Exception as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] Collection '{COLLECTION_NAME}' non trouvée")
        console.print(f"[yellow]Exécutez d'abord indexing.py pour créer la base[/yellow]")
        sys.exit(1)


def load_model():
    """Charge le modèle d'embedding"""
    console.print(f"[bold blue]Chargement du modèle d'embedding...[/bold blue]")
    model = SentenceTransformer(EMBED_MODEL_ID)
    console.print(f"[bold green]✓[/bold green] Modèle chargé\n")
    return model


def search_query(collection, model, query: str, n_results: int = DEFAULT_N_RESULTS, filter_tables: bool = None):
    """
    Effectue une recherche dans la base vectorielle

    Args:
        collection: Collection ChromaDB
        model: Modèle d'embedding
        query: Question de l'utilisateur
        n_results: Nombre de résultats à retourner
        filter_tables: True pour tableaux uniquement, False pour texte uniquement, None pour tout

    Returns:
        Résultats de la recherche
    """
    # 1. Transformer la question en vecteur
    console.print("[bold blue]Transformation de la question en vecteur...[/bold blue]")
    query_embedding = model.encode(query).tolist()
    console.print(f"[bold green]✓[/bold green] Vecteur généré ({len(query_embedding)} dimensions)\n")

    # 2. Préparer le filtre si nécessaire
    where_filter = None
    if filter_tables is True:
        where_filter = {"is_table": True}
    elif filter_tables is False:
        where_filter = {"is_table": False}

    # 3. Rechercher dans la base
    console.print(f"[bold blue]Recherche des {n_results} chunks les plus pertinents...[/bold blue]")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter if where_filter else None,
        include=["documents", "metadatas", "distances"]
    )

    console.print(f"[bold green]✓[/bold green] Recherche terminée\n")
    return results


def display_results(results, query: str):
    """Affiche les résultats de la recherche de manière élégante"""
    console.print(f"[bold magenta]Question :[/bold magenta] {query}\n")

    if not results["documents"][0]:
        console.print("[yellow]Aucun résultat trouvé[/yellow]")
        return

    # Créer un tableau pour les statistiques
    stats_table = Table(title="Résultats de la recherche", show_header=True, header_style="bold cyan")
    stats_table.add_column("Rang", style="dim", width=6)
    stats_table.add_column("Score", justify="right", width=10)
    stats_table.add_column("Type", width=10)
    stats_table.add_column("Tokens", justify="right", width=10)

    for i, (doc, metadata, distance) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ), 1):
        score = 1 - distance  # Convertir la distance en score de similarité
        content_type = metadata.get("content_type", "unknown")
        num_tokens = metadata.get("num_tokens", "N/A")

        stats_table.add_row(
            f"#{i}",
            f"{score:.3f}",
            content_type,
            str(num_tokens)
        )

    console.print(stats_table)
    console.print()

    # Afficher chaque résultat dans un panel
    for i, (doc, metadata, distance) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ), 1):
        score = 1 - distance
        content_type = metadata.get("content_type", "unknown")
        num_tokens = metadata.get("num_tokens", "N/A")

        # Prévisualisation du texte
        preview = doc[:500] + "..." if len(doc) > 500 else doc

        # Titre du panel avec informations
        title = f"Résultat #{i} | Score: {score:.3f} | Type: {content_type} | Tokens: {num_tokens}"

        # Couleur en fonction du score
        if score > 0.7:
            border_style = "green"
        elif score > 0.5:
            border_style = "yellow"
        else:
            border_style = "red"

        console.print(Panel(preview, title=title, border_style=border_style))
        console.print()


def interactive_mode(collection, model):
    """Mode interactif pour poser des questions"""
    console.print(Panel(
        "[bold]Mode interactif[/bold]\n"
        "Posez vos questions sur le rapport LVMH.\n"
        "Tapez 'quit' ou 'exit' pour quitter.\n"
        "Tapez 'table' pour chercher uniquement dans les tableaux.\n"
        "Tapez 'text' pour chercher uniquement dans le texte.",
        title="Système de requête RAG",
        border_style="magenta"
    ))
    console.print()

    filter_mode = None  # None = tout, True = tableaux, False = texte

    while True:
        try:
            # Demander la question
            query = Prompt.ask("\n[bold cyan]Votre question[/bold cyan]")

            # Commandes spéciales
            if query.lower() in ["quit", "exit", "q"]:
                console.print("[bold green]Au revoir ![/bold green]")
                break

            if query.lower() == "table":
                filter_mode = True
                console.print("[yellow]Mode : recherche dans les tableaux uniquement[/yellow]")
                continue

            if query.lower() == "text":
                filter_mode = False
                console.print("[yellow]Mode : recherche dans le texte uniquement[/yellow]")
                continue

            if query.lower() == "all":
                filter_mode = None
                console.print("[yellow]Mode : recherche dans tout le contenu[/yellow]")
                continue

            if not query.strip():
                continue

            # Effectuer la recherche
            console.print()
            results = search_query(collection, model, query, filter_tables=filter_mode)

            # Afficher les résultats
            display_results(results, query)

        except KeyboardInterrupt:
            console.print("\n[bold green]Au revoir ![/bold green]")
            break
        except Exception as e:
            console.print(f"[bold red]Erreur:[/bold red] {e}")


def single_query_mode(collection, model, query: str, n_results: int = DEFAULT_N_RESULTS):
    """Mode requête unique (pour utilisation en ligne de commande)"""
    results = search_query(collection, model, query, n_results)
    display_results(results, query)


def main():
    """Fonction principale"""
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]     Système de requête RAG - LVMH      [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]\n")

    # 1. Charger la base de données
    collection = load_database()

    # 2. Charger le modèle
    model = load_model()

    # 3. Mode interactif ou requête unique
    if len(sys.argv) > 1:
        # Mode ligne de commande avec question fournie
        query = " ".join(sys.argv[1:])
        single_query_mode(collection, model, query)
    else:
        # Mode interactif
        interactive_mode(collection, model)


if __name__ == "__main__":
    main()
