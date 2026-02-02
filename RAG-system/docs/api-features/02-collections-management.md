# Collections Management - `/collections`

## Vue d'ensemble

Gestion des collections ChromaDB qui contiennent les documents indexés. Permet de lister, consulter et supprimer les collections.

## Comment ça marche

### Flux de traitement

```
Client
  │
  ├─> GET /collections              → Liste toutes les collections
  ├─> GET /collections/{name}       → Détails d'une collection
  └─> DELETE /collections/{name}    → Supprime une collection
           │
           ▼
    RAGManager (rag_manager.py)
           │
           ▼
    ChromaDB (data/chroma_db/)
```

### Code concerné

**Liste des collections** (main.py:88-101):
```python
@app.get("/collections", response_model=List[CollectionInfo])
async def list_collections():
    collections = rag_manager.list_collections()
    collection_infos = []

    for col_name in collections:
        try:
            info = rag_manager.get_collection_info(col_name)
            collection_infos.append(CollectionInfo(**info))
        except Exception as e:
            continue

    return collection_infos
```

**Détails d'une collection** (main.py:104-111):
```python
@app.get("/collections/{collection_name}", response_model=CollectionInfo)
async def get_collection(collection_name: str):
    try:
        info = rag_manager.get_collection_info(collection_name)
        return CollectionInfo(**info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Suppression** (main.py:233-240):
```python
@app.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    try:
        rag_manager.chroma_client.delete_collection(name=collection_name)
        return {"message": f"Collection '{collection_name}' supprimée"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
```

## Fichiers impliqués

| Fichier | Rôle |
|---------|------|
| `api/main.py` | Définition des endpoints |
| `api/models.py` | Modèle `CollectionInfo` |
| `api/rag_manager.py` | Méthodes `list_collections()`, `get_collection_info()` |
| `data/chroma_db/` | Stockage physique des collections |

## Comment bien tester

### Test 1 : Lister toutes les collections

```bash
curl http://localhost:8000/collections
```

**Résultat attendu** :
```json
[
  {
    "name": "lvmh_annual_report_2023",
    "document_count": 1,
    "chunk_count": 145,
    "total_tokens": 52340,
    "table_chunks": 23,
    "text_chunks": 122,
    "created_at": "2024-01-15T10:30:00"
  },
  {
    "name": "airbus_financial_statements_2024",
    "document_count": 1,
    "chunk_count": 89,
    "total_tokens": 31200,
    "table_chunks": 15,
    "text_chunks": 74,
    "created_at": "2024-01-16T14:22:00"
  }
]
```

### Test 2 : Détails d'une collection spécifique

```bash
curl http://localhost:8000/collections/lvmh_annual_report_2023
```

**Résultat attendu** :
```json
{
  "name": "lvmh_annual_report_2023",
  "document_count": 1,
  "chunk_count": 145,
  "total_tokens": 52340,
  "table_chunks": 23,
  "text_chunks": 122,
  "created_at": "2024-01-15T10:30:00",
  "metadata": {
    "source": "/path/to/lvmh_annual_report_2023.pdf",
    "indexed_at": "2024-01-15T10:30:00"
  }
}
```

### Test 3 : Tester avec une collection inexistante

```bash
curl http://localhost:8000/collections/collection_qui_nexiste_pas
```

**Résultat attendu** :
```json
{
  "detail": "Collection 'collection_qui_nexiste_pas' not found"
}
```
Status code: **404**

### Test 4 : Supprimer une collection

```bash
curl -X DELETE http://localhost:8000/collections/old_collection
```

**Résultat attendu** :
```json
{
  "message": "Collection 'old_collection' supprimée avec succès"
}
```

### Test 5 : Script Python pour gérer les collections

```python
import requests

API_URL = "http://localhost:8000"

def list_all_collections():
    """Liste toutes les collections"""
    response = requests.get(f"{API_URL}/collections")
    collections = response.json()

    print(f"\n📚 {len(collections)} collections trouvées:\n")
    for col in collections:
        print(f"  • {col['name']}")
        print(f"    Chunks: {col['chunk_count']} | Tokens: {col['total_tokens']}")
        print(f"    Tables: {col['table_chunks']} | Texte: {col['text_chunks']}\n")

def get_collection_details(name):
    """Détails d'une collection"""
    response = requests.get(f"{API_URL}/collections/{name}")
    if response.status_code == 200:
        details = response.json()
        print(f"\n📄 {details['name']}")
        print(f"   Documents: {details['document_count']}")
        print(f"   Chunks: {details['chunk_count']}")
        print(f"   Tokens: {details['total_tokens']}")
    else:
        print(f"❌ Collection '{name}' non trouvée")

def delete_old_collections(days=30):
    """Supprime les collections de plus de X jours"""
    from datetime import datetime, timedelta

    collections = requests.get(f"{API_URL}/collections").json()
    cutoff_date = datetime.now() - timedelta(days=days)

    for col in collections:
        created = datetime.fromisoformat(col['created_at'])
        if created < cutoff_date:
            print(f"🗑️  Suppression: {col['name']} (créée le {created.date()})")
            requests.delete(f"{API_URL}/collections/{col['name']}")

# Utilisation
list_all_collections()
get_collection_details("lvmh_annual_report_2023")
```

### Test 6 : Vérifier l'intégrité des collections

```python
def check_collections_integrity():
    """Vérifie que toutes les collections sont accessibles"""
    collections = requests.get(f"{API_URL}/collections").json()

    issues = []
    for col in collections:
        # Vérifier qu'on peut récupérer les détails
        response = requests.get(f"{API_URL}/collections/{col['name']}")
        if response.status_code != 200:
            issues.append(f"❌ {col['name']}: Inaccessible")
            continue

        # Vérifier qu'il y a des chunks
        if col['chunk_count'] == 0:
            issues.append(f"⚠️  {col['name']}: Aucun chunk")

    if issues:
        print("\n🚨 Problèmes détectés:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ Toutes les collections sont OK")

check_collections_integrity()
```

## Comment l'améliorer

### Amélioration 1 : Statistiques agrégées

**Ajouter un endpoint pour les stats globales** :
```python
@app.get("/collections/stats/summary")
async def get_collections_summary():
    """Statistiques globales de toutes les collections"""
    collections = rag_manager.list_collections()

    total_chunks = 0
    total_tokens = 0
    total_tables = 0
    total_docs = 0

    for col_name in collections:
        info = rag_manager.get_collection_info(col_name)
        total_chunks += info['chunk_count']
        total_tokens += info['total_tokens']
        total_tables += info['table_chunks']
        total_docs += info['document_count']

    return {
        "total_collections": len(collections),
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "total_tokens": total_tokens,
        "total_tables": total_tables,
        "average_chunks_per_collection": total_chunks / len(collections) if collections else 0
    }
```

### Amélioration 2 : Recherche de collections

**Filtrer par nom ou métadonnées** :
```python
@app.get("/collections/search")
async def search_collections(query: str = ""):
    """Recherche de collections par nom"""
    all_collections = rag_manager.list_collections()

    # Filtrer par query
    matching = [col for col in all_collections if query.lower() in col.lower()]

    return {
        "query": query,
        "total_matches": len(matching),
        "collections": matching
    }
```

### Amélioration 3 : Export de collection

**Exporter une collection en JSON** :
```python
@app.get("/collections/{collection_name}/export")
async def export_collection(collection_name: str):
    """Exporte une collection au format JSON"""
    collection = rag_manager.chroma_client.get_collection(collection_name)

    # Récupérer tous les chunks
    results = collection.get(include=['documents', 'metadatas', 'embeddings'])

    return {
        "collection_name": collection_name,
        "chunk_count": len(results['documents']),
        "chunks": [
            {
                "id": results['ids'][i],
                "text": results['documents'][i],
                "metadata": results['metadatas'][i],
                "embedding": results['embeddings'][i] if results['embeddings'] else None
            }
            for i in range(len(results['documents']))
        ]
    }
```

### Amélioration 4 : Merge de collections

**Fusionner plusieurs collections** :
```python
@app.post("/collections/merge")
async def merge_collections(
    source_collections: List[str],
    target_collection: str
):
    """Fusionne plusieurs collections en une seule"""
    target = rag_manager.chroma_client.get_or_create_collection(target_collection)

    total_merged = 0
    for source_name in source_collections:
        source = rag_manager.chroma_client.get_collection(source_name)
        data = source.get(include=['documents', 'metadatas', 'embeddings'])

        # Ajouter à la collection cible
        target.add(
            documents=data['documents'],
            metadatas=data['metadatas'],
            embeddings=data['embeddings'],
            ids=[f"{source_name}_{id}" for id in data['ids']]
        )
        total_merged += len(data['documents'])

    return {
        "message": f"{len(source_collections)} collections fusionnées",
        "target_collection": target_collection,
        "total_chunks": total_merged
    }
```

### Amélioration 5 : Backup/Restore

**Sauvegarder et restaurer des collections** :
```python
@app.post("/collections/{collection_name}/backup")
async def backup_collection(collection_name: str, backup_path: str):
    """Crée une sauvegarde d'une collection"""
    import json
    from pathlib import Path

    collection = rag_manager.chroma_client.get_collection(collection_name)
    data = collection.get(include=['documents', 'metadatas'])

    backup_file = Path(backup_path) / f"{collection_name}_backup.json"
    with open(backup_file, 'w') as f:
        json.dump(data, f, indent=2)

    return {
        "message": "Backup créé",
        "backup_file": str(backup_file),
        "chunks_backed_up": len(data['documents'])
    }

@app.post("/collections/restore")
async def restore_collection(backup_file: str):
    """Restaure une collection depuis un backup"""
    import json

    with open(backup_file, 'r') as f:
        data = json.load(f)

    collection_name = Path(backup_file).stem.replace('_backup', '')
    collection = rag_manager.chroma_client.get_or_create_collection(collection_name)

    collection.add(
        documents=data['documents'],
        metadatas=data['metadatas'],
        ids=data['ids']
    )

    return {
        "message": "Collection restaurée",
        "collection_name": collection_name,
        "chunks_restored": len(data['documents'])
    }
```

### Amélioration 6 : Métadonnées enrichies

**Ajouter plus d'informations sur chaque collection** :
```python
def get_collection_info(self, collection_name: str):
    """Informations enrichies sur une collection"""
    collection = self.chroma_client.get_collection(collection_name)
    data = collection.get(include=['metadatas'])

    # Analyser les métadonnées
    companies = set()
    sources = set()
    date_range = {"min": None, "max": None}

    for metadata in data['metadatas']:
        if 'company' in metadata:
            companies.add(metadata['company'])
        if 'source' in metadata:
            sources.add(metadata['source'])
        if 'date' in metadata:
            # Calculer plage de dates
            pass

    return {
        "name": collection_name,
        "chunk_count": len(data['metadatas']),
        "companies": list(companies),
        "sources": list(sources),
        "date_range": date_range,
        # ... autres infos
    }
```

## Cas d'usage

### 1. Dashboard de monitoring

```python
def display_collections_dashboard():
    """Affiche un tableau de bord des collections"""
    collections = requests.get(f"{API_URL}/collections").json()

    print("=" * 80)
    print("📚 COLLECTIONS DASHBOARD")
    print("=" * 80)

    for col in sorted(collections, key=lambda x: x['chunk_count'], reverse=True):
        print(f"\n{col['name']}")
        print(f"  📄 Documents: {col['document_count']}")
        print(f"  📝 Chunks: {col['chunk_count']}")
        print(f"  🔢 Tokens: {col['total_tokens']:,}")
        print(f"  📊 Tables: {col['table_chunks']} | Texte: {col['text_chunks']}")

        # Barre de progression
        ratio = col['table_chunks'] / col['chunk_count'] if col['chunk_count'] > 0 else 0
        bar_length = int(ratio * 20)
        print(f"  Tables: [{'█' * bar_length}{'░' * (20 - bar_length)}] {ratio:.1%}")

display_collections_dashboard()
```

### 2. Nettoyage automatique

```bash
#!/bin/bash
# cleanup_collections.sh

# Supprimer les collections vides
for collection in $(curl -s http://localhost:8000/collections | jq -r '.[] | select(.chunk_count == 0) | .name'); do
    echo "Suppression de $collection (vide)"
    curl -X DELETE "http://localhost:8000/collections/$collection"
done
```

### 3. Validation avant analyse

```python
def validate_collection_before_query(collection_name: str, company: str):
    """Valide qu'une collection est appropriée pour analyser une entreprise"""
    try:
        col_info = requests.get(f"{API_URL}/collections/{collection_name}").json()

        # Vérifications
        if col_info['chunk_count'] < 10:
            return False, "Collection trop petite (< 10 chunks)"

        if col_info['table_chunks'] == 0:
            return False, "Aucun tableau détecté (données financières manquantes?)"

        if company.lower() not in collection_name.lower():
            return False, f"Collection '{collection_name}' ne correspond pas à '{company}'"

        return True, "Collection valide"

    except:
        return False, "Collection introuvable"

# Utilisation
valid, message = validate_collection_before_query("lvmh_2023", "LVMH")
if not valid:
    print(f"❌ {message}")
```

## Métriques à surveiller

| Métrique | Valeur normale | Action si anormale |
|----------|----------------|-------------------|
| Nombre de collections | Croissant | Nettoyer si > 100 |
| Chunks par collection | > 50 | Vérifier l'indexation |
| Tables par collection | > 5 | Vérifier extraction |
| Taille collection | Proportionnelle au PDF | Investiguer si trop petit/grand |

## Debugging

### Problème : Collections listées mais inaccessibles

**Cause** : Base ChromaDB corrompue

**Solution** :
```bash
# Supprimer et réindexer
rm -rf data/chroma_db/
python batch_index_documents.py data/context/
```

### Problème : Collection supprimée mais toujours listée

**Cause** : Cache ChromaDB

**Solution** :
```python
# Forcer le refresh
rag_manager.chroma_client = chromadb.PersistentClient(path="data/chroma_db")
```

## Bonnes pratiques

1. **Nommer les collections de manière cohérente**
   ```
   {company}_{document_type}_{year}
   Exemple: lvmh_annual_report_2023
   ```

2. **Sauvegarder régulièrement**
   ```bash
   # Backup hebdomadaire
   0 2 * * 0 /path/to/backup_collections.sh
   ```

3. **Limiter la taille des collections**
   - Maximum 1000 chunks par collection
   - Si plus grand, split en plusieurs collections

4. **Documenter les collections**
   - Ajouter des métadonnées riches
   - Inclure source, date, type de document

## Conclusion

Les collections sont au cœur du système RAG. Une bonne gestion permet :
- ✅ Organisation claire des documents
- ✅ Recherche efficace
- ✅ Maintenance simplifiée
- ✅ Performances optimales

**Prochaine amélioration recommandée** : Ajouter un système de tags/catégories pour mieux organiser les collections.
