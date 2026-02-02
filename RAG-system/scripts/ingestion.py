#!/usr/bin/env python3
"""
Script d'ingestion de documents pour le système RAG
Ce script convertit un PDF en chunks optimisés pour le retrieval
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.base import BaseTokenizer
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling_core.transforms.chunker.hierarchical_chunker import (
    DocChunk,
    ChunkingDocSerializer,
    ChunkingSerializerProvider,
)
from docling_core.transforms.serializer.markdown import (
    MarkdownTableSerializer,
    MarkdownParams,
)
from transformers import AutoTokenizer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Configuration
DOC_SOURCE = "../data/context/LVMH_Rapport financier semestriel 2025.pdf"
OUTPUT_DIR = "../data/chunks"
EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"

# Console pour affichage
console = Console(width=200)


class CustomSerializerProvider(ChunkingSerializerProvider):
    """Provider personnalisé pour le sérialiseur avec tables Markdown et placeholders pour images"""

    def get_serializer(self, doc):
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),
            params=MarkdownParams(
                image_placeholder="<!-- image -->",
            ),
        )


def convert_document(source_path: str) -> Any:
    """Convertit le document PDF en format Docling"""
    console.print(f"[bold blue]Conversion du document:[/bold blue] {source_path}")

    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Le fichier source n'existe pas : {source_path}")

    converter = DocumentConverter()
    result = converter.convert(source=source_path)

    console.print("[bold green]✓[/bold green] Document converti avec succès")
    return result.document


def initialize_chunker(tokenizer: BaseTokenizer) -> HybridChunker:
    """Initialise le chunker avec la configuration optimale"""
    console.print("[bold blue]Initialisation du chunker...[/bold blue]")

    chunker = HybridChunker(
        tokenizer=tokenizer,
        serializer_provider=CustomSerializerProvider(),
    )

    console.print("[bold green]✓[/bold green] Chunker initialisé")
    return chunker


def process_chunks(chunker: HybridChunker, doc: Any, tokenizer: BaseTokenizer) -> List[Dict[str, Any]]:
    """Traite tous les chunks du document"""
    console.print("[bold blue]Génération des chunks...[/bold blue]")

    chunk_iter = chunker.chunk(dl_doc=doc)
    chunks_list = list(chunk_iter)

    console.print(f"[bold green]✓[/bold green] {len(chunks_list)} chunks générés")

    # Conversion des chunks en format sérialisable
    processed_chunks = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Traitement des chunks...", total=len(chunks_list))

        for i, chunk in enumerate(chunks_list):
            try:
                # Contextualisation du chunk
                ctx_text = chunker.contextualize(chunk=chunk)
                num_tokens = tokenizer.count_tokens(text=ctx_text)

                # Extraction des métadonnées
                doc_chunk = DocChunk.model_validate(chunk)
                doc_items_refs = [it.self_ref for it in doc_chunk.meta.doc_items]
                doc_items_labels = [it.label.value for it in doc_chunk.meta.doc_items]

                # Création de l'objet chunk sérialisable
                chunk_data = {
                    "chunk_id": i,
                    "text": ctx_text,
                    "num_tokens": num_tokens,
                    "doc_items_refs": doc_items_refs,
                    "doc_items_labels": doc_items_labels,
                    "metadata": {
                        "headings": doc_chunk.meta.headings if hasattr(doc_chunk.meta, "headings") else [],
                        "origin": str(doc_chunk.meta.origin) if hasattr(doc_chunk.meta, "origin") else None,
                    }
                }

                processed_chunks.append(chunk_data)
                progress.update(task, advance=1)

            except Exception as e:
                console.print(f"[bold yellow]⚠[/bold yellow] Erreur lors du traitement du chunk {i}: {e}")
                continue

    return processed_chunks


def save_chunks(chunks: List[Dict[str, Any]], output_dir: str):
    """Sauvegarde les chunks dans un fichier JSON"""
    console.print(f"[bold blue]Sauvegarde des chunks...[/bold blue]")

    # Création du répertoire de sortie si nécessaire
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    output_file = os.path.join(output_dir, "chunks.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    console.print(f"[bold green]✓[/bold green] Chunks sauvegardés dans : {output_file}")

    # Statistiques
    total_tokens = sum(chunk["num_tokens"] for chunk in chunks)
    avg_tokens = total_tokens / len(chunks) if chunks else 0

    console.print(Panel(
        f"[bold]Statistiques:[/bold]\n"
        f"• Nombre de chunks : {len(chunks)}\n"
        f"• Tokens totaux : {total_tokens}\n"
        f"• Tokens moyens par chunk : {avg_tokens:.2f}",
        title="Résumé de l'ingestion",
        border_style="green"
    ))


def print_sample_chunks(chunks: List[Dict[str, Any]], num_samples: int = 3):
    """Affiche quelques exemples de chunks"""
    console.print(f"\n[bold blue]Exemples de chunks (premiers {num_samples}):[/bold blue]\n")

    for chunk in chunks[:num_samples]:
        title = f"Chunk {chunk['chunk_id']} | Tokens: {chunk['num_tokens']} | Labels: {', '.join(chunk['doc_items_labels'])}"
        text_preview = chunk['text'][:500] + "..." if len(chunk['text']) > 500 else chunk['text']
        console.print(Panel(text_preview, title=title, border_style="cyan"))


def main():
    """Fonction principale"""
    try:
        console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]")
        console.print("[bold magenta]  Système d'ingestion RAG - LVMH Report  [/bold magenta]")
        console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]\n")

        # 1. Conversion du document
        doc = convert_document(DOC_SOURCE)

        # 2. Initialisation du tokenizer
        console.print(f"[bold blue]Chargement du modèle de tokenization:[/bold blue] {EMBED_MODEL_ID}")
        tokenizer: BaseTokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),
        )
        console.print("[bold green]✓[/bold green] Tokenizer chargé\n")

        # 3. Initialisation du chunker
        chunker = initialize_chunker(tokenizer)

        # 4. Génération et traitement des chunks
        chunks = process_chunks(chunker, doc, tokenizer)

        if not chunks:
            console.print("[bold red]✗[/bold red] Aucun chunk généré !")
            return

        # 5. Sauvegarde des chunks
        save_chunks(chunks, OUTPUT_DIR)

        # 6. Affichage d'exemples
        print_sample_chunks(chunks)

        console.print("\n[bold green]✓ Ingestion terminée avec succès ![/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]✗ Erreur fatale:[/bold red] {e}")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        raise


if __name__ == "__main__":
    main()
