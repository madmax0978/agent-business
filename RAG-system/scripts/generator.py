#!/usr/bin/env python3
"""
Script de génération de réponses avec RAG
Combine la recherche vectorielle avec Ollama/Mistral pour générer des réponses
"""

import sys
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
import requests
import json

# Configuration
DB_PATH = "../data/vector_db"
COLLECTION_NAME = "lvmh_report"
EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"
N_RESULTS = 5  # Nombre de chunks à récupérer pour le contexte

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
        console.print(f"[bold green]✓[/bold green] Base chargée : {count} chunks disponibles")
        return collection
    except Exception as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] Collection '{COLLECTION_NAME}' non trouvée")
        console.print(f"[yellow]Exécutez d'abord indexing.py pour créer la base[/yellow]")
        sys.exit(1)


def load_model():
    """Charge le modèle d'embedding"""
    console.print(f"[bold blue]Chargement du modèle d'embedding...[/bold blue]")
    model = SentenceTransformer(EMBED_MODEL_ID)
    console.print(f"[bold green]✓[/bold green] Modèle chargé")
    return model


def check_ollama():
    """Vérifie si Ollama est disponible"""
    console.print(f"[bold blue]Vérification d'Ollama...[/bold blue]")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            if any(OLLAMA_MODEL in name for name in model_names):
                console.print(f"[bold green]✓[/bold green] Ollama est actif et le modèle {OLLAMA_MODEL} est disponible")
                return True
            else:
                console.print(f"[bold yellow]⚠[/bold yellow] Ollama est actif mais le modèle {OLLAMA_MODEL} n'est pas trouvé")
                console.print(f"[yellow]Modèles disponibles : {', '.join(model_names)}[/yellow]")
                console.print(f"[yellow]Installez le modèle avec : ollama pull {OLLAMA_MODEL}[/yellow]")
                return False
    except requests.exceptions.RequestException:
        console.print(f"[bold red]✗[/bold red] Ollama n'est pas accessible")
        console.print(f"[yellow]Lancez Ollama avec : ollama serve[/yellow]")
        return False


def search_context(collection, model, query: str, n_results: int = N_RESULTS):
    """Recherche les chunks pertinents pour la question"""
    console.print(f"[bold blue]Recherche de contexte pertinent...[/bold blue]")

    # Transformer la question en vecteur
    query_embedding = model.encode(query).tolist()

    # Rechercher dans la base
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    console.print(f"[bold green]✓[/bold green] {len(results['documents'][0])} chunks récupérés")
    return results


def build_prompt(question: str, chunks: list, metadatas: list) -> str:
    """Construit le prompt pour Ollama avec le contexte"""

    # Construire le contexte à partir des chunks
    context_parts = []
    for i, (chunk, metadata) in enumerate(zip(chunks, metadatas), 1):
        content_type = metadata.get("content_type", "unknown")
        context_parts.append(f"[Extrait {i} - Type: {content_type}]\n{chunk}\n")

    context = "\n".join(context_parts)

    # Construire le prompt
    prompt = f"""Tu es un assistant financier expert spécialisé dans l'analyse de rapports d'entreprise.

Voici des extraits du rapport financier semestriel de LVMH pour le premier semestre 2025 :

{context}

En utilisant UNIQUEMENT les informations fournies dans ces extraits, réponds à la question suivante de manière précise et concise. Si les extraits ne contiennent pas assez d'information pour répondre, dis-le clairement.

Question : {question}

Réponse :"""

    return prompt


def generate_response(prompt: str) -> str:
    """Génère une réponse avec Ollama"""
    console.print(f"[bold blue]Génération de la réponse avec {OLLAMA_MODEL}...[/bold blue]")

    try:
        # Appeler l'API Ollama
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Réponses plus déterministes
                    "top_p": 0.9,
                }
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "")
            console.print(f"[bold green]✓[/bold green] Réponse générée")
            return answer
        else:
            console.print(f"[bold red]✗[/bold red] Erreur API Ollama : {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]✗[/bold red] Erreur de connexion à Ollama : {e}")
        return None


def display_result(question: str, answer: str, chunks: list, metadatas: list, distances: list):
    """Affiche la réponse et les sources"""

    # Afficher la question
    console.print(f"\n[bold magenta]Question :[/bold magenta]")
    console.print(Panel(question, border_style="magenta"))

    # Afficher la réponse
    console.print(f"\n[bold cyan]Réponse :[/bold cyan]")
    console.print(Panel(Markdown(answer), border_style="cyan", title="Assistant IA"))

    # Afficher les sources utilisées
    console.print(f"\n[bold yellow]Sources utilisées :[/bold yellow]")
    for i, (chunk, metadata, distance) in enumerate(zip(chunks, metadatas, distances), 1):
        score = 1 - distance
        content_type = metadata.get("content_type", "unknown")

        # Prévisualisation courte
        preview = chunk[:200] + "..." if len(chunk) > 200 else chunk

        title = f"Source {i} | Score: {score:.3f} | Type: {content_type}"
        console.print(Panel(preview, title=title, border_style="dim"))


def interactive_mode(collection, model):
    """Mode interactif pour poser des questions"""
    console.print(Panel(
        "[bold]Mode RAG Interactif[/bold]\n"
        "Posez vos questions sur le rapport LVMH.\n"
        "L'IA générera des réponses basées sur le contenu du rapport.\n"
        "Tapez 'quit' ou 'exit' pour quitter.",
        title="Générateur de réponses RAG - LVMH",
        border_style="magenta"
    ))
    console.print()

    while True:
        try:
            # Demander la question
            question = Prompt.ask("\n[bold cyan]Votre question[/bold cyan]")

            # Commandes spéciales
            if question.lower() in ["quit", "exit", "q"]:
                console.print("[bold green]Au revoir ![/bold green]")
                break

            if not question.strip():
                continue

            console.print()

            # 1. Rechercher le contexte
            results = search_context(collection, model, question)

            if not results["documents"][0]:
                console.print("[yellow]Aucun contexte pertinent trouvé[/yellow]")
                continue

            # 2. Construire le prompt
            prompt = build_prompt(
                question,
                results["documents"][0],
                results["metadatas"][0]
            )

            # 3. Générer la réponse
            answer = generate_response(prompt)

            if answer:
                # 4. Afficher le résultat
                display_result(
                    question,
                    answer,
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )
            else:
                console.print("[bold red]Impossible de générer une réponse[/bold red]")

        except KeyboardInterrupt:
            console.print("\n[bold green]Au revoir ![/bold green]")
            break
        except Exception as e:
            console.print(f"[bold red]Erreur:[/bold red] {e}")


def single_query_mode(collection, model, question: str):
    """Mode requête unique"""
    # 1. Rechercher le contexte
    results = search_context(collection, model, question)

    if not results["documents"][0]:
        console.print("[yellow]Aucun contexte pertinent trouvé[/yellow]")
        return

    # 2. Construire le prompt
    prompt = build_prompt(
        question,
        results["documents"][0],
        results["metadatas"][0]
    )

    # 3. Générer la réponse
    answer = generate_response(prompt)

    if answer:
        # 4. Afficher le résultat
        display_result(
            question,
            answer,
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )
    else:
        console.print("[bold red]Impossible de générer une réponse[/bold red]")


def main():
    """Fonction principale"""
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]    Générateur RAG - Ollama + Mistral    [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]\n")

    # 1. Vérifier Ollama
    if not check_ollama():
        console.print("\n[bold red]Ollama doit être actif pour continuer[/bold red]")
        sys.exit(1)

    # 2. Charger la base de données
    collection = load_database()

    # 3. Charger le modèle d'embedding
    model = load_model()

    console.print()

    # 4. Mode interactif ou requête unique
    if len(sys.argv) > 1:
        # Mode ligne de commande avec question fournie
        question = " ".join(sys.argv[1:])
        single_query_mode(collection, model, question)
    else:
        # Mode interactif
        interactive_mode(collection, model)


if __name__ == "__main__":
    main()
