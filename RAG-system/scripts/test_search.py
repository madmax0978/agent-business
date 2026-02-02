#!/usr/bin/env python3
"""Script de test pour la recherche par type de contenu"""

import chromadb
from chromadb.config import Settings
from rich.console import Console
from rich.panel import Panel

console = Console(width=200)

# Charger la collection
chroma_client = chromadb.PersistentClient(
    path="../data/vector_db",
    settings=Settings(anonymized_telemetry=False)
)
collection = chroma_client.get_collection(name="lvmh_report")

# Test 1: Recherche de tableaux uniquement
console.print("\n[bold blue]Test 1: Recherche de tableaux financiers[/bold blue]\n")
results_tables = collection.query(
    query_texts=["ventes par région et chiffre d'affaires"],
    n_results=3,
    where={"is_table": True},
    include=["documents", "metadatas", "distances"]
)

for i, (doc, metadata, distance) in enumerate(zip(
    results_tables["documents"][0],
    results_tables["metadatas"][0],
    results_tables["distances"][0]
)):
    preview = doc[:300] + "..." if len(doc) > 300 else doc
    title = f"Table {i+1} | Score: {1-distance:.3f} | Type: {metadata['content_type']}"
    console.print(Panel(preview, title=title, border_style="green"))

# Test 2: Recherche de texte uniquement
console.print("\n[bold blue]Test 2: Recherche de texte narratif[/bold blue]\n")
results_text = collection.query(
    query_texts=["stratégie et objectifs de l'entreprise"],
    n_results=3,
    where={"is_table": False},
    include=["documents", "metadatas", "distances"]
)

for i, (doc, metadata, distance) in enumerate(zip(
    results_text["documents"][0],
    results_text["metadatas"][0],
    results_text["distances"][0]
)):
    preview = doc[:300] + "..." if len(doc) > 300 else doc
    title = f"Texte {i+1} | Score: {1-distance:.3f} | Type: {metadata['content_type']}"
    console.print(Panel(preview, title=title, border_style="cyan"))

# Test 3: Recherche tous types
console.print("\n[bold blue]Test 3: Recherche sans filtre[/bold blue]\n")
results_all = collection.query(
    query_texts=["résultats financiers"],
    n_results=3,
    include=["documents", "metadatas", "distances"]
)

for i, (doc, metadata, distance) in enumerate(zip(
    results_all["documents"][0],
    results_all["metadatas"][0],
    results_all["distances"][0]
)):
    preview = doc[:300] + "..." if len(doc) > 300 else doc
    title = f"Résultat {i+1} | Score: {1-distance:.3f} | Type: {metadata['content_type']}"
    console.print(Panel(preview, title=title, border_style="yellow"))

console.print("\n[bold green]✓ Tests terminés ![/bold green]")
