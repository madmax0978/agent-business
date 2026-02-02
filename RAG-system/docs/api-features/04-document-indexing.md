# Document Indexing - `/index`

## Vue d'ensemble

Indexe un document PDF existant depuis un chemin de fichier local, sans avoir besoin de l'uploader. Utile pour les scripts batch et l'indexation de documents déjà présents sur le serveur.

## Comment ça marche

### Flux de traitement

```
Client
  │
  ▼
POST /index
  {
    "file_path": "/path/to/document.pdf",
    "document_name": "document.pdf",
    "collection_name": "custom_collection"
  }
  │
  ├─> Validation du chemin
  ├─> Vérification existence fichier
  │
  ▼
RAGManager.index_document()
  │
  ├─> Extraction PDF (PyPDF2)
  ├─> Détection tableaux (camelot)
  ├─> Chunking intelligent (par page)
  ├─> Génération embeddings (OpenAI)
  │
  ▼
ChromaDB (stockage vectoriel)
  │
  ▼
Réponse avec statistiques
```

### Code concerné (main.py:149-173)

```python
@app.post("/index", response_model=IndexingResponse)
async def index_existing_document(doc: DocumentUpload):
    # Générer un nom de collection si non fourni
    collection_name = doc.collection_name or Path(doc.file_path).stem.lower().replace(" ", "_")

    try:
        # Indexer le document
        result = rag_manager.index_document(doc.file_path, collection_name)

        return IndexingResponse(
            success=result["success"],
            collection_name=result["collection_name"],
            total_chunks=result["total_chunks"],
            table_chunks=result["table_chunks"],
            text_chunks=result["text_chunks"],
            message=f"Document '{doc.document_name}' indexé avec succès",
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'indexation: {str(e)}")
```

## Fichiers impliqués

| Fichier | Rôle |
|---------|------|
| `api/main.py` | Endpoint d'indexation |
| `api/models.py` | Modèles `DocumentUpload`, `IndexingResponse` |
| `api/rag_manager.py` | Logique d'indexation complète |
| `api/document_processor.py` | Extraction PDF et tableaux |

## Comment bien tester

### Test 1 : Indexation simple

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/Users/user/documents/airbus_report.pdf",
    "document_name": "Airbus Financial Report 2024",
    "collection_name": "airbus_2024"
  }'
```

**Résultat attendu** :
```json
{
  "success": true,
  "collection_name": "airbus_2024",
  "total_chunks": 156,
  "table_chunks": 28,
  "text_chunks": 128,
  "message": "Document 'Airbus Financial Report 2024' indexé avec succès"
}
```

### Test 2 : Sans nom de collection (auto-généré)

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/data/reports/lvmh_2023.pdf",
    "document_name": "LVMH Report"
  }'
```

**Résultat** : Collection nommée automatiquement `lvmh_2023`

### Test 3 : Fichier inexistant

```bash
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/invalid/document.pdf",
    "document_name": "Test"
  }'
```

**Résultat attendu** :
```json
{
  "detail": "File not found: /path/invalid/document.pdf"
}
```
Status code: **404**

### Test 4 : Script Python pour indexation batch

```python
import requests
from pathlib import Path

API_URL = "http://localhost:8000"

def index_document(file_path: str, collection_name: str = None):
    """Indexe un document depuis son chemin"""
    url = f"{API_URL}/index"

    payload = {
        "file_path": file_path,
        "document_name": Path(file_path).name,
        "collection_name": collection_name
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['collection_name']}: {result['total_chunks']} chunks")
        return result
    else:
        print(f"❌ Erreur: {response.json()}")
        return None

# Utilisation
index_document("/data/reports/airbus_2024.pdf", "airbus_2024")
```

### Test 5 : Indexation batch d'un dossier

```python
def index_directory(directory: str, pattern: str = "*.pdf"):
    """Indexe tous les PDFs d'un dossier"""
    from pathlib import Path

    pdf_files = list(Path(directory).glob(pattern))
    print(f"📂 {len(pdf_files)} fichiers trouvés\n")

    results = {"success": 0, "failed": 0, "total_chunks": 0}

    for pdf_file in pdf_files:
        print(f"Indexation: {pdf_file.name}")

        # Générer nom de collection depuis le nom de fichier
        collection_name = pdf_file.stem.lower().replace(" ", "_").replace("-", "_")

        result = index_document(str(pdf_file), collection_name)

        if result:
            results["success"] += 1
            results["total_chunks"] += result["total_chunks"]
        else:
            results["failed"] += 1

    print(f"\n📊 Résumé:")
    print(f"   ✅ Succès: {results['success']}")
    print(f"   ❌ Échecs: {results['failed']}")
    print(f"   📝 Chunks totaux: {results['total_chunks']}")

# Indexer tous les PDFs du dossier
index_directory("/data/financial-reports/")
```

### Test 6 : Validation avant indexation

```python
def validate_and_index(file_path: str):
    """Valide puis indexe un document"""
    from pathlib import Path
    import PyPDF2

    path = Path(file_path)

    # Vérifier que le fichier existe
    if not path.exists():
        print(f"❌ Fichier introuvable: {file_path}")
        return None

    # Vérifier que c'est un PDF
    if path.suffix.lower() != '.pdf':
        print(f"❌ Pas un PDF: {file_path}")
        return None

    # Vérifier que le PDF est lisible
    try:
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            num_pages = len(pdf.pages)
            print(f"✅ PDF valide: {num_pages} pages")
    except:
        print(f"❌ PDF corrompu: {file_path}")
        return None

    # Indexer
    return index_document(file_path)

validate_and_index("/data/reports/airbus_2024.pdf")
```

### Test 7 : Monitoring de l'indexation

```python
import time

def index_with_monitoring(file_path: str):
    """Indexe avec monitoring du temps"""
    start = time.time()

    print(f"⏱️  Démarrage indexation: {Path(file_path).name}")

    result = index_document(file_path)

    elapsed = time.time() - start

    if result:
        print(f"✅ Terminé en {elapsed:.1f}s")
        print(f"   Chunks: {result['total_chunks']}")
        print(f"   Tables: {result['table_chunks']}")
        print(f"   Vitesse: {result['total_chunks']/elapsed:.1f} chunks/s")
    else:
        print(f"❌ Échec après {elapsed:.1f}s")

    return result

index_with_monitoring("/data/large_report.pdf")
```

## Comment l'améliorer

### Amélioration 1 : Support des chemins relatifs

```python
from pathlib import Path
import os

@app.post("/index")
async def index_existing_document(doc: DocumentUpload):
    # Résoudre le chemin absolu
    file_path = Path(doc.file_path)
    if not file_path.is_absolute():
        # Si chemin relatif, chercher depuis plusieurs emplacements
        search_paths = [
            Path("../data/documents"),
            Path("../data/uploads"),
            Path.cwd()
        ]

        for search_path in search_paths:
            full_path = search_path / file_path
            if full_path.exists():
                file_path = full_path
                break

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {doc.file_path}")

    # Indexer
    result = rag_manager.index_document(str(file_path), collection_name)
    ...
```

### Amélioration 2 : Réindexation intelligente

```python
@app.post("/index")
async def index_existing_document(doc: DocumentUpload, force: bool = False):
    """Indexe avec vérification des doublons"""

    # Vérifier si déjà indexé
    if not force:
        existing_collections = rag_manager.list_collections()
        if collection_name in existing_collections:
            return {
                "success": False,
                "message": f"Collection '{collection_name}' existe déjà. Utilisez force=true pour réindexer",
                "collection_name": collection_name
            }

    # Indexer
    result = rag_manager.index_document(str(file_path), collection_name)
    ...
```

### Amélioration 3 : Indexation partielle (pages spécifiques)

```python
class DocumentUploadPartial(BaseModel):
    file_path: str
    document_name: str
    collection_name: Optional[str] = None
    start_page: Optional[int] = None  # NOUVEAU
    end_page: Optional[int] = None     # NOUVEAU

@app.post("/index")
async def index_existing_document(doc: DocumentUploadPartial):
    # Indexer seulement certaines pages
    result = rag_manager.index_document(
        doc.file_path,
        collection_name,
        start_page=doc.start_page,
        end_page=doc.end_page
    )
    ...
```

### Amélioration 4 : Métadonnées enrichies

```python
class DocumentUploadEnriched(BaseModel):
    file_path: str
    document_name: str
    collection_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # NOUVEAU

@app.post("/index")
async def index_existing_document(doc: DocumentUploadEnriched):
    # Ajouter métadonnées personnalisées
    extra_metadata = doc.metadata or {}
    extra_metadata.update({
        "indexed_at": datetime.now().isoformat(),
        "indexed_by": "api",
        "file_size": Path(doc.file_path).stat().st_size
    })

    result = rag_manager.index_document(
        doc.file_path,
        collection_name,
        extra_metadata=extra_metadata
    )
    ...
```

### Amélioration 5 : Indexation avec webhook de progression

```python
from fastapi.background import BackgroundTasks

@app.post("/index/async")
async def index_async(
    background_tasks: BackgroundTasks,
    doc: DocumentUpload,
    webhook_url: Optional[str] = None
):
    """Indexation asynchrone avec notifications"""
    job_id = str(uuid.uuid4())

    background_tasks.add_task(
        index_with_progress,
        job_id,
        doc.file_path,
        doc.collection_name,
        webhook_url
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "check_status": f"/index/status/{job_id}"
    }

async def index_with_progress(job_id, file_path, collection_name, webhook_url):
    """Indexe avec notifications de progression"""
    # Notification 0%
    if webhook_url:
        requests.post(webhook_url, json={"job_id": job_id, "progress": 0})

    # Indexation
    result = rag_manager.index_document(file_path, collection_name)

    # Notification 100%
    if webhook_url:
        requests.post(webhook_url, json={
            "job_id": job_id,
            "progress": 100,
            "result": result
        })
```

### Amélioration 6 : Chunking strategies personnalisables

```python
class DocumentUploadAdvanced(BaseModel):
    file_path: str
    document_name: str
    collection_name: Optional[str] = None
    chunking_strategy: str = "by_page"  # NOUVEAU: by_page, by_paragraph, by_tokens

@app.post("/index")
async def index_existing_document(doc: DocumentUploadAdvanced):
    result = rag_manager.index_document(
        doc.file_path,
        collection_name,
        chunking_strategy=doc.chunking_strategy
    )
    ...
```

## Cas d'usage

### 1. Script d'indexation automatique (cron)

```bash
#!/bin/bash
# index_new_reports.sh

REPORTS_DIR="/data/financial-reports"
API_URL="http://localhost:8000"

# Indexer tous les nouveaux PDFs
for file in $REPORTS_DIR/*.pdf; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        collection=$(echo "$filename" | sed 's/.pdf$//' | tr '[:upper:]' '[:lower:]' | tr ' ' '_')

        echo "Indexing: $filename -> $collection"

        curl -X POST "$API_URL/index" \
          -H "Content-Type: application/json" \
          -d "{
            \"file_path\": \"$file\",
            \"document_name\": \"$filename\",
            \"collection_name\": \"$collection\"
          }"

        echo ""
    fi
done
```

### 2. Intégration avec watchdog (surveillance de dossier)

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PDFIndexHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.pdf'):
            print(f"Nouveau PDF détecté: {event.src_path}")
            time.sleep(2)  # Attendre que le fichier soit complètement écrit
            index_document(event.src_path)

# Surveillance automatique
observer = Observer()
observer.schedule(PDFIndexHandler(), path="/data/reports/", recursive=False)
observer.start()
print("🔍 Surveillance active...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
```

### 3. Réindexation après mise à jour

```python
def reindex_collection(collection_name: str, file_path: str):
    """Supprime puis réindexe une collection"""

    # 1. Supprimer l'ancienne collection
    print(f"🗑️  Suppression: {collection_name}")
    requests.delete(f"{API_URL}/collections/{collection_name}")

    # 2. Réindexer
    print(f"📝 Réindexation: {file_path}")
    result = index_document(file_path, collection_name)

    if result:
        print(f"✅ Mise à jour terminée: {result['total_chunks']} chunks")
    else:
        print(f"❌ Échec de la réindexation")

reindex_collection("airbus_2024", "/data/reports/airbus_2024_updated.pdf")
```

## Métriques à surveiller

| Métrique | Valeur normale | Action si anormale |
|----------|----------------|-------------------|
| Temps d'indexation | 30-60s pour 10MB | Optimiser extraction |
| Chunks extraits | > 50 par document | Vérifier PDF |
| Tables détectées | 5-20% des chunks | Calibrer camelot |
| Taux d'erreur | < 5% | Investiguer logs |

## Debugging

### Problème : FileNotFoundError malgré chemin valide

**Cause** : Permissions ou chemin relatif mal résolu

**Solution** :
```python
# Vérifier les permissions
import os
file_path = "/data/reports/doc.pdf"
print(f"Existe: {os.path.exists(file_path)}")
print(f"Lisible: {os.access(file_path, os.R_OK)}")

# Essayer chemin absolu
file_path = os.path.abspath(file_path)
```

### Problème : PDF corrompu ou protégé

**Cause** : PDF chiffré ou endommagé

**Solution** :
```bash
# Réparer avec ghostscript
gs -o output.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress input.pdf

# Décrypter si protégé
qpdf --decrypt --password=PASSWORD input.pdf output.pdf
```

### Problème : Timeout sur gros fichiers

**Cause** : Document trop volumineux

**Solution** :
```python
# Indexer page par page
def index_large_document_chunked(file_path: str, pages_per_batch: int = 50):
    import PyPDF2

    with open(file_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        total_pages = len(pdf.pages)

    for start_page in range(0, total_pages, pages_per_batch):
        end_page = min(start_page + pages_per_batch, total_pages)
        collection = f"{Path(file_path).stem}_part{start_page//pages_per_batch}"

        print(f"Indexing pages {start_page}-{end_page}")
        index_document(file_path, collection)  # Avec start_page/end_page si supporté
```

## Bonnes pratiques

1. **Toujours vérifier l'existence du fichier avant**
   ```python
   if not Path(file_path).exists():
       raise FileNotFoundError(file_path)
   ```

2. **Utiliser des chemins absolus**
   ```python
   file_path = str(Path(file_path).resolve())
   ```

3. **Logger chaque indexation**
   ```python
   logger.info(f"Indexing: {file_path} -> {collection_name}")
   ```

4. **Gérer les doublons**
   ```python
   if collection_exists(collection_name):
       raise HTTPException(400, "Collection already exists")
   ```

5. **Nettoyer après échec**
   ```python
   try:
       result = index_document(...)
   except Exception as e:
       # Nettoyer collection partielle
       delete_collection(collection_name)
       raise
   ```

## Conclusion

L'endpoint `/index` est idéal pour :
- ✅ Indexation batch de documents locaux
- ✅ Scripts d'automatisation
- ✅ Pipelines CI/CD
- ✅ Surveillance de dossiers

**Différence avec `/upload`** :
- `/upload` : Upload + indexation (pour fichiers externes)
- `/index` : Indexation uniquement (pour fichiers déjà sur serveur)

**Prochaine amélioration recommandée** : Indexation asynchrone avec file d'attente pour gérer de gros volumes.
