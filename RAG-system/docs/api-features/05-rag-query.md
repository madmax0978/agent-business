# RAG Query - `/query`

## Vue d'ensemble

Endpoint central du système RAG qui effectue une recherche vectorielle dans une collection ChromaDB et peut générer une réponse contextuelle avec Ollama.

## Comment ça marche

### Flux de traitement

```
Client
  │
  ▼
POST /query
  {
    "question": "Quel est le CA de LVMH en 2023?",
    "collection_name": "lvmh_2023",
    "n_results": 5,
    "generate_answer": true
  }
  │
  ▼
RAGManager.search()
  │
  ├─> Génération embedding de la question (OpenAI)
  ├─> Recherche vectorielle (ChromaDB)
  ├─> Récupération des top N chunks similaires
  │
  ▼
Si generate_answer = true
  │
  ▼
RAGManager.generate_answer()
  │
  ├─> Construction du prompt avec contexte
  ├─> Génération avec Ollama (llama2/mistral)
  │
  ▼
Réponse avec chunks + answer (optionnel)
```

### Code concerné (main.py:176-230)

```python
@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    start_time = time.time()

    # Rechercher les chunks pertinents
    chunks, metadatas, distances = rag_manager.search(
        question=request.question,
        collection_name=request.collection_name,
        n_results=request.n_results,
        filter_tables=request.filter_tables,
    )

    # Préparer les chunks
    chunk_responses = []
    for chunk, metadata, distance in zip(chunks, metadatas, distances):
        chunk_responses.append(
            ChunkResponse(
                chunk_id=metadata["chunk_id"],
                text=chunk,
                score=1 - distance,  # Convertir distance en score similarité
                content_type=metadata.get("content_type", "unknown"),
                num_tokens=metadata["num_tokens"],
                metadata=metadata,
            )
        )

    # Générer une réponse si demandé
    answer = None
    if request.generate_answer:
        if not rag_manager.check_ollama():
            raise HTTPException(503, "Ollama n'est pas disponible")

        answer = rag_manager.generate_answer(request.question, chunks, metadatas)

    processing_time = time.time() - start_time

    return QueryResponse(
        question=request.question,
        answer=answer,
        chunks=chunk_responses,
        collection_name=request.collection_name,
        processing_time=processing_time,
    )
```

## Fichiers impliqués

| Fichier | Rôle |
|---------|------|
| `api/main.py` | Endpoint query |
| `api/models.py` | QueryRequest, QueryResponse, ChunkResponse |
| `api/rag_manager.py` | search(), generate_answer() |
| ChromaDB | Recherche vectorielle |
| Ollama | Génération de réponse |

## Comment bien tester

### Test 1 : Recherche simple (sans génération)

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quel est le chiffre d affaires de LVMH?",
    "collection_name": "lvmh_2023",
    "n_results": 5,
    "generate_answer": false
  }'
```

**Résultat attendu** :
```json
{
  "question": "Quel est le chiffre d'affaires de LVMH?",
  "answer": null,
  "chunks": [
    {
      "chunk_id": "lvmh_2023_page_12_chunk_1",
      "text": "Le chiffre d'affaires du Groupe LVMH s'établit à 79,2 milliards d'euros en 2023...",
      "score": 0.89,
      "content_type": "text",
      "num_tokens": 450,
      "metadata": {
        "source": "lvmh_annual_report_2023.pdf",
        "page": 12
      }
    }
  ],
  "collection_name": "lvmh_2023",
  "processing_time": 0.42
}
```

### Test 2 : Recherche avec génération de réponse

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelle est la stratégie de croissance de LVMH?",
    "collection_name": "lvmh_2023",
    "n_results": 3,
    "generate_answer": true
  }'
```

**Résultat attendu** :
```json
{
  "question": "Quelle est la stratégie de croissance de LVMH?",
  "answer": "D'après les documents analysés, la stratégie de croissance de LVMH repose sur trois piliers principaux:\n\n1. Innovation constante dans les métiers du luxe\n2. Expansion géographique, notamment en Asie\n3. Acquisitions ciblées de marques prestigieuses\n\nLe Groupe mise également sur la digitalisation et l'expérience client.",
  "chunks": [...],
  "collection_name": "lvmh_2023",
  "processing_time": 2.15
}
```

### Test 3 : Filtrer uniquement les tableaux

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Résultats financiers",
    "collection_name": "lvmh_2023",
    "n_results": 5,
    "filter_tables": true,
    "generate_answer": false
  }'
```

**Résultat** : Seulement les chunks de type "table"

### Test 4 : Script Python pour recherche interactive

```python
import requests

API_URL = "http://localhost:8000"

def query_rag(question: str, collection: str, generate_answer: bool = True):
    """Effectue une requête RAG"""
    url = f"{API_URL}/query"

    payload = {
        "question": question,
        "collection_name": collection,
        "n_results": 5,
        "generate_answer": generate_answer
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        result = response.json()

        print(f"\n📄 Question: {result['question']}")
        print(f"⏱️  Temps: {result['processing_time']:.2f}s")
        print(f"📚 Chunks trouvés: {len(result['chunks'])}\n")

        if result['answer']:
            print("💬 Réponse:")
            print(result['answer'])
            print()

        print("📋 Chunks pertinents:")
        for i, chunk in enumerate(result['chunks'], 1):
            print(f"\n{i}. Score: {chunk['score']:.2f} | Page: {chunk['metadata'].get('page', '?')}")
            print(f"   {chunk['text'][:200]}...")

        return result
    else:
        print(f"❌ Erreur: {response.json()}")
        return None

# Utilisation
query_rag(
    "Quel est le résultat net de LVMH?",
    "lvmh_2023",
    generate_answer=True
)
```

### Test 5 : Chatbot avec historique

```python
class RAGChatbot:
    def __init__(self, collection_name: str):
        self.collection = collection_name
        self.history = []

    def ask(self, question: str):
        """Pose une question avec contexte historique"""
        # Ajouter historique au prompt
        context = "\n".join([
            f"Q: {q}\nR: {a}"
            for q, a in self.history[-3:]  # 3 derniers échanges
        ])

        full_question = f"{context}\n\nQ: {question}" if context else question

        result = query_rag(full_question, self.collection, generate_answer=True)

        if result and result['answer']:
            self.history.append((question, result['answer']))
            return result['answer']

        return None

# Utilisation
chatbot = RAGChatbot("lvmh_2023")
chatbot.ask("Quel est le CA de LVMH?")
chatbot.ask("Et le résultat net?")  # Contexte: on parle de LVMH
chatbot.ask("Comment a-t-il évolué?")  # Contexte: on parle du résultat net
```

### Test 6 : Comparaison multi-collections

```python
def compare_across_collections(question: str, collections: list):
    """Compare la réponse à travers plusieurs collections"""
    print(f"\n🔍 Question: {question}\n")

    for collection in collections:
        print(f"📚 Collection: {collection}")
        result = query_rag(question, collection, generate_answer=True)

        if result and result['answer']:
            print(f"   {result['answer'][:200]}...")
        print()

# Comparer LVMH sur 3 années
compare_across_collections(
    "Quel est le chiffre d'affaires?",
    ["lvmh_2021", "lvmh_2022", "lvmh_2023"]
)
```

## Comment l'améliorer

### Amélioration 1 : Reranking des résultats

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

@app.post("/query")
async def query_rag(request: QueryRequest):
    # Recherche initiale (plus de résultats)
    chunks, metadatas, distances = rag_manager.search(
        question=request.question,
        collection_name=request.collection_name,
        n_results=request.n_results * 3,  # 3x plus
    )

    # Reranking avec cross-encoder
    pairs = [[request.question, chunk] for chunk in chunks]
    scores = reranker.predict(pairs)

    # Trier par nouveau score
    reranked = sorted(
        zip(chunks, metadatas, scores),
        key=lambda x: x[2],
        reverse=True
    )[:request.n_results]

    # Continuer avec les meilleurs...
```

### Amélioration 2 : Streaming de la réponse

```python
from fastapi.responses import StreamingResponse

@app.post("/query/stream")
async def query_rag_stream(request: QueryRequest):
    """Streaming de la réponse pour UX temps réel"""

    async def generate():
        # Recherche chunks
        chunks, metadatas, _ = rag_manager.search(...)

        # Générer réponse en streaming
        for token in rag_manager.generate_answer_stream(request.question, chunks):
            yield f"data: {json.dumps({'token': token})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Amélioration 3 : Cache des résultats

```python
from functools import lru_cache
import hashlib

def cache_key(question: str, collection: str) -> str:
    """Génère une clé de cache"""
    return hashlib.md5(f"{question}:{collection}".encode()).hexdigest()

@lru_cache(maxsize=1000)
def cached_search(question: str, collection: str, n_results: int):
    """Recherche avec cache"""
    return rag_manager.search(question, collection, n_results)

@app.post("/query")
async def query_rag(request: QueryRequest):
    # Utiliser le cache
    chunks, metadatas, distances = cached_search(
        request.question,
        request.collection_name,
        request.n_results
    )
    ...
```

### Amélioration 4 : Filtres avancés par métadonnées

```python
class QueryRequestAdvanced(QueryRequest):
    metadata_filters: Optional[Dict[str, Any]] = None  # NOUVEAU

@app.post("/query")
async def query_rag(request: QueryRequestAdvanced):
    # Filtrer par métadonnées
    chunks, metadatas, distances = rag_manager.search(
        question=request.question,
        collection_name=request.collection_name,
        n_results=request.n_results,
        where=request.metadata_filters  # {"page": {"$gte": 10, "$lte": 20}}
    )
    ...
```

### Amélioration 5 : Explication des chunks choisis

```python
@app.post("/query")
async def query_rag(request: QueryRequest):
    # ... recherche ...

    # Expliquer pourquoi chaque chunk a été choisi
    explanations = []
    for chunk, metadata, distance in zip(chunks, metadatas, distances):
        # Analyser les mots-clés communs
        question_words = set(request.question.lower().split())
        chunk_words = set(chunk.lower().split())
        common_words = question_words & chunk_words

        explanations.append({
            "chunk_id": metadata["chunk_id"],
            "score": 1 - distance,
            "common_keywords": list(common_words),
            "relevance_reason": f"Contient {len(common_words)} mots-clés de la question"
        })

    return QueryResponse(
        ...
        explanations=explanations  # NOUVEAU
    )
```

### Amélioration 6 : Fusion de réponses multi-modèles

```python
@app.post("/query/ensemble")
async def query_with_ensemble(request: QueryRequest):
    """Génère réponses avec plusieurs modèles et fusionne"""

    # Recherche chunks
    chunks, metadatas, _ = rag_manager.search(...)

    # Générer avec plusieurs modèles
    models = ["llama2", "mistral", "phi"]
    answers = []

    for model in models:
        answer = rag_manager.generate_answer(
            request.question,
            chunks,
            metadatas,
            model=model
        )
        answers.append(answer)

    # Fusionner (prendre le plus long, ou voter, etc.)
    final_answer = max(answers, key=len)

    return QueryResponse(
        answer=final_answer,
        alternative_answers=answers,  # NOUVEAU
        ...
    )
```

## Cas d'usage

### 1. Q&A interactif

```python
def interactive_qa(collection: str):
    """Session Q&A interactive"""
    print(f"💬 Session Q&A sur {collection}")
    print("Tapez 'exit' pour quitter\n")

    while True:
        question = input("❓ Votre question: ")

        if question.lower() == 'exit':
            break

        result = query_rag(question, collection, generate_answer=True)

        if result and result['answer']:
            print(f"\n✅ Réponse:\n{result['answer']}\n")
        else:
            print("\n❌ Aucune réponse trouvée\n")

interactive_qa("lvmh_2023")
```

### 2. Analyse comparative

```python
def compare_financial_metrics(metric: str, companies: list, year: str):
    """Compare une métrique entre plusieurs entreprises"""
    question = f"Quel est le {metric}?"

    results = {}
    for company in companies:
        collection = f"{company.lower()}_{year}"
        result = query_rag(question, collection, generate_answer=True)

        if result and result['answer']:
            results[company] = result['answer']

    print(f"\n📊 Comparaison: {metric} ({year})\n")
    for company, answer in results.items():
        print(f"{company}:")
        print(f"  {answer}\n")

compare_financial_metrics(
    "chiffre d'affaires",
    ["LVMH", "Airbus", "TotalEnergies"],
    "2023"
)
```

### 3. Génération de rapport

```python
def generate_report(company: str, year: str):
    """Génère un rapport financier complet"""
    collection = f"{company.lower()}_{year}"

    questions = [
        "Quel est le chiffre d'affaires?",
        "Quel est le résultat net?",
        "Quels sont les principaux risques?",
        "Quelle est la stratégie de croissance?",
        "Quels sont les dividendes?"
    ]

    print(f"\n📄 RAPPORT FINANCIER - {company} {year}\n")
    print("=" * 60)

    for question in questions:
        print(f"\n❓ {question}")
        result = query_rag(question, collection, generate_answer=True)

        if result and result['answer']:
            print(f"   {result['answer']}")

    print("\n" + "=" * 60)

generate_report("LVMH", "2023")
```

## Métriques à surveiller

| Métrique | Valeur normale | Action si anormale |
|----------|----------------|-------------------|
| Temps de réponse (sans génération) | < 1s | Optimiser embeddings |
| Temps de génération Ollama | 2-5s | Utiliser modèle plus rapide |
| Score des chunks | > 0.7 | Améliorer embeddings |
| Pertinence réponse | > 80% | Améliorer prompt |

## Debugging

### Problème : Résultats non pertinents

**Cause** : Embeddings de mauvaise qualité

**Solution** :
```python
# Tester les embeddings
from openai import OpenAI

client = OpenAI()

question = "Quel est le CA?"
embedding = client.embeddings.create(
    input=question,
    model="text-embedding-ada-002"
).data[0].embedding

print(f"Embedding size: {len(embedding)}")  # Doit être 1536
```

### Problème : Ollama timeout

**Cause** : Modèle trop lent ou contexte trop grand

**Solution** :
```python
# Limiter le contexte
chunks_limited = chunks[:3]  # Seulement 3 chunks
# Ou utiliser un modèle plus rapide
rag_manager.generate_answer(..., model="phi")  # Au lieu de llama2
```

## Bonnes pratiques

1. **Limiter le nombre de chunks**
   ```python
   n_results = min(request.n_results, 10)  # Max 10
   ```

2. **Timeout raisonnable**
   ```python
   timeout = 30  # secondes max pour génération
   ```

3. **Valider la collection**
   ```python
   if collection not in rag_manager.list_collections():
       raise HTTPException(404, "Collection not found")
   ```

4. **Logger les requêtes**
   ```python
   logger.info(f"Query: {question} on {collection}")
   ```

## Conclusion

Le endpoint `/query` est le cœur du système RAG :
- ✅ Recherche vectorielle performante
- ✅ Génération de réponses contextuelles
- ✅ Flexible et extensible

**Prochaine amélioration recommandée** : Reranking avec cross-encoder pour améliorer la pertinence.
