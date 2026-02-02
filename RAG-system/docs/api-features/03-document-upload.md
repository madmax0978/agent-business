# Document Upload - `/upload`

## Vue d'ensemble

Permet d'uploader un fichier PDF directement via l'API et de l'indexer automatiquement dans ChromaDB pour la recherche RAG.

## Comment ça marche

### Flux de traitement

```
Client
  │
  ▼
POST /upload (multipart/form-data)
  │
  ├─> Validation (PDF uniquement)
  ├─> Sauvegarde dans data/uploads/
  │
  ▼
RAGManager.index_document()
  │
  ├─> Extraction PDF (PyPDF2)
  ├─> Détection tableaux (camelot)
  ├─> Chunking intelligent
  ├─> Génération embeddings (OpenAI)
  │
  ▼
ChromaDB (stockage vectoriel)
  │
  ▼
Réponse avec statistiques
```

### Code concerné (main.py:114-146)

```python
@app.post("/upload", response_model=IndexingResponse)
async def upload_document(file: UploadFile = File(...), collection_name: str = None):
    # Vérifier que c'est un PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")

    # Générer un nom de collection si non fourni
    if not collection_name:
        collection_name = Path(file.filename).stem.lower().replace(" ", "_")

    # Sauvegarder le fichier
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Indexer le document
    result = rag_manager.index_document(str(file_path), collection_name)

    return IndexingResponse(
        success=result["success"],
        collection_name=result["collection_name"],
        total_chunks=result["total_chunks"],
        table_chunks=result["table_chunks"],
        text_chunks=result["text_chunks"],
        message=f"Document indexé avec succès en {result['processing_time']:.2f}s",
    )
```

## Fichiers impliqués

| Fichier | Rôle |
|---------|------|
| `api/main.py` | Endpoint upload |
| `api/models.py` | Modèle `IndexingResponse` |
| `api/rag_manager.py` | Logique d'indexation |
| `api/document_processor.py` | Extraction PDF et tableaux |
| `data/uploads/` | Dossier de stockage des uploads |

## Comment bien tester

### Test 1 : Upload simple via curl

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/document.pdf"
```

**Résultat attendu** :
```json
{
  "success": true,
  "collection_name": "document",
  "total_chunks": 145,
  "table_chunks": 23,
  "text_chunks": 122,
  "message": "Document indexé avec succès en 45.32s"
}
```

### Test 2 : Upload avec nom de collection personnalisé

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@lvmh_report_2024.pdf" \
  -F "collection_name=lvmh_2024_q4"
```

**Résultat attendu** :
```json
{
  "success": true,
  "collection_name": "lvmh_2024_q4",
  "total_chunks": 89,
  "table_chunks": 15,
  "text_chunks": 74,
  "message": "Document indexé avec succès en 32.18s"
}
```

### Test 3 : Tester avec un fichier non-PDF

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.docx"
```

**Résultat attendu** :
```json
{
  "detail": "Seuls les fichiers PDF sont acceptés"
}
```
Status code: **400**

### Test 4 : Upload via Python

```python
import requests

def upload_pdf(file_path: str, collection_name: str = None):
    """Upload un PDF vers l'API"""
    url = "http://localhost:8000/upload"

    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {}
        if collection_name:
            data['collection_name'] = collection_name

        response = requests.post(url, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload réussi!")
        print(f"   Collection: {result['collection_name']}")
        print(f"   Chunks: {result['total_chunks']}")
        print(f"   Tables: {result['table_chunks']}")
        print(f"   Temps: {result['message']}")
        return result
    else:
        print(f"❌ Erreur: {response.json()}")
        return None

# Utilisation
upload_pdf("documents/airbus_report.pdf", "airbus_2024")
```

### Test 5 : Upload batch de plusieurs fichiers

```python
import os
from pathlib import Path

def upload_directory(directory: str):
    """Upload tous les PDFs d'un dossier"""
    pdf_files = list(Path(directory).glob("*.pdf"))

    print(f"📂 {len(pdf_files)} fichiers PDF trouvés\n")

    results = []
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"[{i}/{len(pdf_files)}] Upload: {pdf_file.name}")

        result = upload_pdf(str(pdf_file))
        if result:
            results.append(result)
            print(f"  ✅ {result['total_chunks']} chunks indexés\n")
        else:
            print(f"  ❌ Échec\n")

    print(f"\n📊 Résumé:")
    print(f"   Total uploadé: {len(results)}/{len(pdf_files)}")
    print(f"   Chunks totaux: {sum(r['total_chunks'] for r in results)}")

upload_directory("documents/reports/")
```

### Test 6 : Upload avec validation de taille

```python
def upload_pdf_with_validation(file_path: str, max_size_mb: int = 50):
    """Upload avec validation de taille"""
    file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)

    if file_size_mb > max_size_mb:
        print(f"❌ Fichier trop gros: {file_size_mb:.1f} MB (max: {max_size_mb} MB)")
        return None

    print(f"📄 Taille: {file_size_mb:.1f} MB")
    print(f"⏱️  Temps estimé: {file_size_mb * 60:.0f} secondes")

    return upload_pdf(file_path)

upload_pdf_with_validation("huge_document.pdf", max_size_mb=100)
```

### Test 7 : Monitoring de l'upload avec progress bar

```python
import requests
from tqdm import tqdm

def upload_pdf_with_progress(file_path: str):
    """Upload avec barre de progression"""
    url = "http://localhost:8000/upload"
    file_size = Path(file_path).stat().st_size

    with open(file_path, 'rb') as f:
        with tqdm(total=file_size, unit='B', unit_scale=True, desc="Upload") as pbar:
            def callback(monitor):
                pbar.update(monitor.bytes_read - pbar.n)

            # Upload avec monitoring
            files = {'file': f}
            response = requests.post(url, files=files)

    return response.json()
```

## Comment l'améliorer

### Amélioration 1 : Support de formats multiples

**Ajouter DOCX, TXT, etc.** :
```python
SUPPORTED_FORMATS = [".pdf", ".docx", ".txt", ".md"]

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Vérifier le format
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté. Formats acceptés: {SUPPORTED_FORMATS}"
        )

    # Convertir en PDF si nécessaire
    if file_extension == ".docx":
        file_path = convert_docx_to_pdf(file_path)
    elif file_extension == ".txt":
        file_path = convert_txt_to_pdf(file_path)

    # Indexer
    result = rag_manager.index_document(str(file_path), collection_name)
    ...
```

### Amélioration 2 : Validation avancée

**Vérifier le contenu du PDF** :
```python
import PyPDF2

def validate_pdf(file_path: str):
    """Valide qu'un PDF est lisible et contient du texte"""
    try:
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)

            # Vérifier qu'il y a des pages
            if len(pdf.pages) == 0:
                return False, "PDF vide (0 pages)"

            # Vérifier qu'on peut extraire du texte
            first_page_text = pdf.pages[0].extract_text()
            if len(first_page_text.strip()) < 50:
                return False, "PDF semble être une image (pas de texte extractible)"

            return True, f"PDF valide ({len(pdf.pages)} pages)"

    except Exception as e:
        return False, f"PDF corrompu: {str(e)}"

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # ... sauvegarder le fichier ...

    # Valider
    valid, message = validate_pdf(str(file_path))
    if not valid:
        file_path.unlink()  # Supprimer le fichier invalide
        raise HTTPException(status_code=400, detail=message)

    # Indexer
    ...
```

### Amélioration 3 : Upload asynchrone avec webhook

**Pour les gros fichiers** :
```python
from fastapi.background import BackgroundTasks
import uuid

processing_jobs = {}

@app.post("/upload/async")
async def upload_document_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    webhook_url: str = None
):
    """Upload asynchrone pour gros fichiers"""
    # Générer un job ID
    job_id = str(uuid.uuid4())

    # Sauvegarder le fichier
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Lancer le traitement en arrière-plan
    processing_jobs[job_id] = {"status": "processing", "progress": 0}

    background_tasks.add_task(
        process_document_async,
        job_id,
        str(file_path),
        collection_name,
        webhook_url
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "check_status": f"/upload/status/{job_id}"
    }

async def process_document_async(job_id, file_path, collection_name, webhook_url):
    """Traite le document en arrière-plan"""
    try:
        result = rag_manager.index_document(file_path, collection_name)
        processing_jobs[job_id] = {"status": "completed", "result": result}

        # Notifier via webhook
        if webhook_url:
            requests.post(webhook_url, json=result)

    except Exception as e:
        processing_jobs[job_id] = {"status": "failed", "error": str(e)}

@app.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str):
    """Vérifie le statut d'un upload asynchrone"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job non trouvé")

    return processing_jobs[job_id]
```

### Amélioration 4 : Extraction de métadonnées

**Détecter automatiquement les infos du document** :
```python
def extract_document_metadata(file_path: str):
    """Extrait les métadonnées d'un PDF"""
    with open(file_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        metadata = pdf.metadata

        return {
            "title": metadata.get('/Title', ''),
            "author": metadata.get('/Author', ''),
            "subject": metadata.get('/Subject', ''),
            "creation_date": metadata.get('/CreationDate', ''),
            "num_pages": len(pdf.pages)
        }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # ... upload ...

    # Extraire métadonnées
    metadata = extract_document_metadata(str(file_path))

    # Ajouter aux métadonnées ChromaDB
    result = rag_manager.index_document(
        str(file_path),
        collection_name,
        extra_metadata=metadata  # NOUVEAU
    )
    ...
```

### Amélioration 5 : Compression et optimisation

**Compresser les PDFs avant indexation** :
```python
def optimize_pdf(file_path: str):
    """Optimise un PDF (compression, suppression images)"""
    from PyPDF2 import PdfReader, PdfWriter

    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        # Supprimer les images (garder seulement le texte)
        page.compress_content_streams()
        writer.add_page(page)

    # Sauvegarder optimisé
    optimized_path = file_path.replace('.pdf', '_optimized.pdf')
    with open(optimized_path, 'wb') as f:
        writer.write(f)

    return optimized_path

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), optimize: bool = True):
    # ... upload ...

    if optimize:
        file_path = optimize_pdf(str(file_path))

    # Indexer
    ...
```

### Amélioration 6 : Détection de doublons

**Éviter d'indexer deux fois le même document** :
```python
import hashlib

def calculate_file_hash(file_path: str):
    """Calcule le hash MD5 d'un fichier"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Base de données des documents uploadés
uploaded_documents = {}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # ... sauvegarder ...

    # Calculer hash
    file_hash = calculate_file_hash(str(file_path))

    # Vérifier si déjà uploadé
    if file_hash in uploaded_documents:
        existing = uploaded_documents[file_hash]
        return {
            "success": False,
            "message": f"Document déjà uploadé: {existing['collection_name']}",
            "duplicate_of": existing
        }

    # Indexer
    result = rag_manager.index_document(str(file_path), collection_name)

    # Sauvegarder le hash
    uploaded_documents[file_hash] = {
        "collection_name": collection_name,
        "filename": file.filename,
        "upload_date": datetime.now().isoformat()
    }

    return result
```

## Cas d'usage

### 1. Interface de drag & drop web

```javascript
// Frontend React
function FileUploader() {
  const handleDrop = async (files) => {
    const formData = new FormData();
    formData.append('file', files[0]);

    const response = await fetch('http://localhost:8000/upload', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    console.log('Upload réussi:', result);
  };

  return (
    <Dropzone onDrop={handleDrop}>
      Glissez vos PDFs ici
    </Dropzone>
  );
}
```

### 2. Surveillance de dossier (auto-upload)

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PDFUploadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('.pdf'):
            print(f"Nouveau PDF détecté: {event.src_path}")
            upload_pdf(event.src_path)

# Surveillance
observer = Observer()
observer.schedule(PDFUploadHandler(), path="./watch_folder/", recursive=False)
observer.start()
```

### 3. Upload depuis URL

```python
@app.post("/upload/from-url")
async def upload_from_url(url: str, collection_name: str = None):
    """Télécharge et indexe un PDF depuis une URL"""
    import requests

    # Télécharger
    response = requests.get(url)
    filename = url.split('/')[-1]

    # Sauvegarder
    file_path = UPLOAD_DIR / filename
    with open(file_path, 'wb') as f:
        f.write(response.content)

    # Indexer
    result = rag_manager.index_document(str(file_path), collection_name)
    return result
```

## Métriques à surveiller

| Métrique | Valeur normale | Action si anormale |
|----------|----------------|-------------------|
| Temps d'upload | < 60s pour 10MB | Vérifier réseau |
| Taux de succès | > 95% | Investiguer erreurs |
| Taille moyenne | 5-20 MB | Optimiser si > 50MB |
| Chunks extraits | > 50 par document | Vérifier extraction |

## Debugging

### Problème : Upload timeout

**Solution** :
```python
# Augmenter le timeout FastAPI
from fastapi import Request
import asyncio

@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=300.0)
    except asyncio.TimeoutError:
        return JSONResponse({"detail": "Request timeout"}, status_code=504)
```

### Problème : PDF avec images seulement

**Solution** : Utiliser OCR
```python
# Ajouter pytesseract pour OCR
import pytesseract
from pdf2image import convert_from_path

def extract_text_with_ocr(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text
```

## Bonnes pratiques

1. **Limiter la taille des uploads**
   ```python
   MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
   ```

2. **Nettoyer les fichiers temporaires**
   ```python
   # Supprimer après indexation
   file_path.unlink()
   ```

3. **Logs détaillés**
   ```python
   logger.info(f"Upload: {file.filename} ({file_size_mb:.1f} MB)")
   ```

4. **Rate limiting**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)

   @app.post("/upload")
   @limiter.limit("10/minute")  # Max 10 uploads/minute
   async def upload_document(...):
       ...
   ```

## Conclusion

L'upload de documents est la porte d'entrée du système RAG. Une bonne implémentation permet :
- ✅ Indexation simple et rapide
- ✅ Support de gros fichiers
- ✅ Validation robuste
- ✅ Gestion des erreurs

**Prochaine amélioration recommandée** : Upload asynchrone avec file d'attente pour gérer les gros volumes.
