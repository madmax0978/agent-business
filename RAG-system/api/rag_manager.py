"""
Gestionnaire RAG pour l'indexation et la recherche multi-documents
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
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
import requests


class CustomSerializerProvider(ChunkingSerializerProvider):
    """Provider personnalisé pour le sérialiseur"""

    def get_serializer(self, doc):
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),
            params=MarkdownParams(image_placeholder="<!-- image -->"),
        )


class RAGManager:
    """Gestionnaire centralisé pour le système RAG"""

    def __init__(
        self,
        db_path: str = "../data/vector_db",
        embed_model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "mistral",
    ):
        self.db_path = db_path
        self.embed_model_id = embed_model_id
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model

        # Initialiser les composants
        self.chroma_client = self._init_chromadb()
        self.embed_model = self._init_embedding_model()

    def _init_chromadb(self) -> chromadb.Client:
        """Initialise le client ChromaDB"""
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(
            path=self.db_path, settings=Settings(anonymized_telemetry=False)
        )

    def _init_embedding_model(self) -> SentenceTransformer:
        """Initialise le modèle d'embedding"""
        return SentenceTransformer(self.embed_model_id)

    def check_ollama(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(self.ollama_model in m["name"] for m in models)
            return False
        except requests.exceptions.RequestException:
            return False

    def list_collections(self) -> List[str]:
        """Liste toutes les collections disponibles"""
        collections = self.chroma_client.list_collections()
        return [col.name for col in collections]

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Récupère les informations d'une collection"""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            count = collection.count()
            all_chunks = collection.get(include=["metadatas"])
            table_count = sum(
                1 for m in all_chunks["metadatas"] if m.get("is_table", False)
            )
            text_count = count - table_count

            return {
                "name": collection_name,
                "total_chunks": count,
                "table_chunks": table_count,
                "text_chunks": text_count,
                "table_percentage": round((table_count / count * 100), 2)
                if count > 0
                else 0,
            }
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' non trouvée: {e}")

    def index_document(
        self, file_path: str, collection_name: str
    ) -> Dict[str, Any]:
        """Indexe un document PDF complet"""
        start_time = time.time()

        # 1. Convertir le document
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Fichier non trouvé : {file_path}")

        converter = DocumentConverter()
        doc = converter.convert(source=file_path).document

        # 2. Initialiser le chunker
        tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(self.embed_model_id)
        )
        chunker = HybridChunker(
            tokenizer=tokenizer, serializer_provider=CustomSerializerProvider()
        )

        # 3. Générer les chunks
        chunk_iter = chunker.chunk(dl_doc=doc)
        chunks_list = list(chunk_iter)

        # 4. Traiter les chunks
        processed_chunks = []
        for i, chunk in enumerate(chunks_list):
            ctx_text = chunker.contextualize(chunk=chunk)
            num_tokens = tokenizer.count_tokens(text=ctx_text)
            doc_chunk = DocChunk.model_validate(chunk)
            doc_items_refs = [it.self_ref for it in doc_chunk.meta.doc_items]
            doc_items_labels = [it.label.value for it in doc_chunk.meta.doc_items]

            chunk_data = {
                "chunk_id": i,
                "text": ctx_text,
                "num_tokens": num_tokens,
                "doc_items_refs": doc_items_refs,
                "doc_items_labels": doc_items_labels,
                "metadata": {
                    "headings": doc_chunk.meta.headings
                    if hasattr(doc_chunk.meta, "headings")
                    else [],
                    "origin": str(doc_chunk.meta.origin)
                    if hasattr(doc_chunk.meta, "origin")
                    else None,
                },
            }
            processed_chunks.append(chunk_data)

        # 5. Générer les embeddings
        texts = [chunk["text"] for chunk in processed_chunks]
        embeddings = self.embed_model.encode(texts, show_progress_bar=False).tolist()

        # 6. Créer ou recréer la collection
        try:
            self.chroma_client.delete_collection(name=collection_name)
        except Exception:
            pass

        collection = self.chroma_client.create_collection(
            name=collection_name,
            metadata={"document_path": file_path, "indexed_at": str(time.time())},
        )

        # 7. Indexer dans ChromaDB (par batches pour gérer les gros documents)
        ids = []
        documents = []
        metadatas = []

        for chunk, embedding in zip(processed_chunks, embeddings):
            is_table = "table" in chunk["doc_items_labels"]
            ids.append(f"chunk_{chunk['chunk_id']}")
            documents.append(chunk["text"])
            metadatas.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "num_tokens": chunk["num_tokens"],
                    "doc_items_labels": ",".join(chunk["doc_items_labels"]),
                    "headings": ",".join(chunk["metadata"]["headings"])
                    if chunk["metadata"]["headings"]
                    else "",
                    "is_table": is_table,
                    "content_type": "table" if is_table else "text",
                }
            )

        # Insérer par batches de 5000 chunks max (limite ChromaDB)
        batch_size = 5000
        total_chunks = len(ids)

        for i in range(0, total_chunks, batch_size):
            batch_end = min(i + batch_size, total_chunks)
            batch_ids = ids[i:batch_end]
            batch_documents = documents[i:batch_end]
            batch_metadatas = metadatas[i:batch_end]
            batch_embeddings = embeddings[i:batch_end]

            collection.add(
                ids=batch_ids,
                documents=batch_documents,
                metadatas=batch_metadatas,
                embeddings=batch_embeddings
            )

        # 8. Statistiques
        table_count = sum(1 for m in metadatas if m["is_table"])
        text_count = len(metadatas) - table_count

        processing_time = time.time() - start_time

        return {
            "success": True,
            "collection_name": collection_name,
            "total_chunks": len(processed_chunks),
            "table_chunks": table_count,
            "text_chunks": text_count,
            "processing_time": processing_time,
        }

    def search(
        self,
        question: str,
        collection_name: str,
        n_results: int = 5,
        filter_tables: Optional[bool] = None,
    ) -> Tuple[List[str], List[Dict], List[float]]:
        """Recherche dans une collection"""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' non trouvée: {e}")

        # Générer l'embedding de la question
        query_embedding = self.embed_model.encode(question).tolist()

        # Filtrer si nécessaire
        where_filter = None
        if filter_tables is True:
            where_filter = {"is_table": True}
        elif filter_tables is False:
            where_filter = {"is_table": False}

        # Rechercher
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"],
        )

        return (
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )

    def generate_answer(
        self, question: str, chunks: List[str], metadatas: List[Dict]
    ) -> str:
        """Génère une réponse avec Ollama"""
        # Construire le contexte
        context_parts = []
        for i, (chunk, metadata) in enumerate(zip(chunks, metadatas), 1):
            content_type = metadata.get("content_type", "unknown")
            context_parts.append(f"[Extrait {i} - Type: {content_type}]\n{chunk}\n")

        context = "\n".join(context_parts)

        # Construire le prompt
        prompt = f"""Tu es un assistant expert en analyse de documents financiers et rapports d'entreprise.

Voici des extraits pertinents du document :

{context}

En utilisant UNIQUEMENT les informations fournies dans ces extraits, réponds à la question suivante de manière précise et concise. Si les extraits ne contiennent pas assez d'information pour répondre, dis-le clairement.

Question : {question}

Réponse :"""

        # Appeler Ollama
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "top_p": 0.9},
                },
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Erreur API Ollama: {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur de connexion à Ollama: {e}")
