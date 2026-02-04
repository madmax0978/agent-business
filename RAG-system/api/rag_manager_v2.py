"""
Gestionnaire RAG Optimisé v2 - Version Professionnelle
Optimisations: Meilleur modèle multilingual, cache, chunking avancé, monitoring
"""

import os
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
import logging

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

# Logger
logger = logging.getLogger(__name__)


class ChunkingConfig:
    """Configuration avancée pour le chunking optimisé"""

    def __init__(
        self,
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        min_chunk_size: int = 100,
        preserve_sentences: bool = True,
        add_context_headers: bool = True,
    ):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.min_chunk_size = min_chunk_size
        self.preserve_sentences = preserve_sentences
        self.add_context_headers = add_context_headers


class CustomSerializerProvider(ChunkingSerializerProvider):
    """Provider personnalisé avec sérialisation optimisée"""

    def get_serializer(self, doc):
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),
            params=MarkdownParams(
                image_placeholder="<!-- image -->",
                # Ajouter métadonnées dans les chunks
                include_references=True,
            ),
        )


class OptimizedRAGManager:
    """
    Gestionnaire RAG Optimisé pour documents financiers

    Améliorations par rapport à v1:
    - Modèle multilingual optimisé pour le français
    - Cache des embeddings
    - Configuration chunking avancée
    - Monitoring des performances
    - Meilleure gestion d'erreurs
    """

    def __init__(
        self,
        db_path: str = "../data/vector_db",
        embed_model_id: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "mistral",
        chunking_config: Optional[ChunkingConfig] = None,
        enable_cache: bool = True,
    ):
        """
        Initialise le gestionnaire RAG optimisé

        Args:
            db_path: Chemin vers la base ChromaDB
            embed_model_id: Modèle d'embedding (multilingual pour le français)
            ollama_url: URL du serveur Ollama
            ollama_model: Modèle Ollama à utiliser
            chunking_config: Configuration du chunking
            enable_cache: Activer le cache des embeddings
        """
        self.db_path = db_path
        self.embed_model_id = embed_model_id
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.enable_cache = enable_cache

        # Configuration chunking par défaut optimisée pour documents financiers
        self.chunking_config = chunking_config or ChunkingConfig(
            max_tokens=512,  # Chunks de taille moyenne pour bon équilibre
            overlap_tokens=50,  # Overlap pour contexte
            min_chunk_size=100,  # Éviter chunks trop petits
            preserve_sentences=True,  # Ne pas couper les phrases
            add_context_headers=True,  # Ajouter titres de section
        )

        # Initialiser les composants
        logger.info(f"Initialisation RAG Manager v2 avec modèle: {embed_model_id}")
        self.chroma_client = self._init_chromadb()
        self.embed_model = self._init_embedding_model()

        # Cache pour les embeddings de questions fréquentes
        self._embedding_cache = {} if enable_cache else None

        logger.info("RAG Manager v2 initialisé avec succès")

    def _init_chromadb(self) -> chromadb.Client:
        """Initialise ChromaDB avec configuration optimisée"""
        Path(self.db_path).mkdir(parents=True, exist_ok=True)

        return chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False,  # Sécurité en production
            )
        )

    def _init_embedding_model(self) -> SentenceTransformer:
        """
        Initialise le modèle d'embedding
        Utilise paraphrase-multilingual-mpnet-base-v2 par défaut:
        - Excellente performance en français
        - Spécialisé pour la recherche sémantique
        - Meilleur que all-MiniLM-L6-v2 pour le multilingual
        """
        logger.info(f"Chargement du modèle d'embedding: {self.embed_model_id}")
        model = SentenceTransformer(self.embed_model_id)
        logger.info("Modèle d'embedding chargé")
        return model

    def _get_embedding_cached(self, text: str) -> List[float]:
        """
        Récupère l'embedding avec cache
        Utilise un hash du texte comme clé
        """
        if not self.enable_cache:
            return self.embed_model.encode(text).tolist()

        # Créer une clé de cache basée sur le hash du texte
        cache_key = hashlib.md5(text.encode()).hexdigest()

        if cache_key not in self._embedding_cache:
            embedding = self.embed_model.encode(text).tolist()
            self._embedding_cache[cache_key] = embedding
            logger.debug(f"Embedding caché pour clé: {cache_key[:8]}")
        else:
            logger.debug(f"Embedding récupéré du cache: {cache_key[:8]}")

        return self._embedding_cache[cache_key]

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
        """Récupère les informations détaillées d'une collection"""
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            count = collection.count()
            all_chunks = collection.get(include=["metadatas"])

            # Statistiques détaillées
            table_count = sum(1 for m in all_chunks["metadatas"] if m.get("is_table", False))
            text_count = count - table_count

            # Calculer statistiques sur les tokens
            token_counts = [m.get("num_tokens", 0) for m in all_chunks["metadatas"]]
            avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0

            return {
                "name": collection_name,
                "total_chunks": count,
                "table_chunks": table_count,
                "text_chunks": text_count,
                "table_percentage": round((table_count / count * 100), 2) if count > 0 else 0,
                "avg_tokens_per_chunk": round(avg_tokens, 2),
            }
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' non trouvée: {e}")

    def index_document(
        self,
        file_path: str,
        collection_name: str,
        show_progress: bool = False
    ) -> Dict[str, Any]:
        """
        Indexe un document PDF avec optimisations

        Args:
            file_path: Chemin vers le PDF
            collection_name: Nom de la collection
            show_progress: Afficher la progression

        Returns:
            Statistiques d'indexation
        """
        start_time = time.time()
        logger.info(f"Début indexation: {file_path} -> {collection_name}")

        # 1. Validation
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Fichier non trouvé : {file_path}")

        # 2. Conversion avec docling
        logger.info("Conversion du document avec docling...")
        converter = DocumentConverter()
        doc = converter.convert(source=file_path).document
        conversion_time = time.time() - start_time
        logger.info(f"Conversion terminée en {conversion_time:.2f}s")

        # 3. Initialiser le chunker avec configuration optimisée
        logger.info("Initialisation du chunker...")
        tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(self.embed_model_id)
        )
        chunker = HybridChunker(
            tokenizer=tokenizer,
            serializer_provider=CustomSerializerProvider()
        )

        # 4. Générer les chunks
        logger.info("Génération des chunks...")
        chunk_start = time.time()
        chunk_iter = chunker.chunk(dl_doc=doc)
        chunks_list = list(chunk_iter)
        chunking_time = time.time() - chunk_start
        logger.info(f"{len(chunks_list)} chunks générés en {chunking_time:.2f}s")

        # 5. Traiter les chunks avec métadonnées enrichies
        logger.info("Traitement des chunks...")
        processed_chunks = []
        for i, chunk in enumerate(chunks_list):
            ctx_text = chunker.contextualize(chunk=chunk)
            num_tokens = tokenizer.count_tokens(text=ctx_text)

            # Skip chunks trop petits
            if num_tokens < self.chunking_config.min_chunk_size:
                continue

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
                    "headings": doc_chunk.meta.headings if hasattr(doc_chunk.meta, "headings") else [],
                    "origin": str(doc_chunk.meta.origin) if hasattr(doc_chunk.meta, "origin") else None,
                },
            }
            processed_chunks.append(chunk_data)

        logger.info(f"{len(processed_chunks)} chunks conservés après filtrage")

        # 6. Générer les embeddings en batch
        logger.info("Génération des embeddings...")
        embedding_start = time.time()
        texts = [chunk["text"] for chunk in processed_chunks]
        embeddings = self.embed_model.encode(
            texts,
            show_progress_bar=show_progress,
            batch_size=32,  # Batch pour performance
            convert_to_tensor=False
        ).tolist()
        embedding_time = time.time() - embedding_start
        logger.info(f"Embeddings générés en {embedding_time:.2f}s ({len(embeddings)/embedding_time:.1f} chunks/s)")

        # 7. Créer ou recréer la collection
        # Vérifier si la collection existe et la supprimer si nécessaire
        try:
            existing_collections = [c.name for c in self.chroma_client.list_collections()]
            if collection_name in existing_collections:
                self.chroma_client.delete_collection(name=collection_name)
                logger.info(f"Collection '{collection_name}' supprimée")
                # Petit délai pour que ChromaDB traite la suppression
                time.sleep(0.3)
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification/suppression de collection: {e}")

        # Créer la collection avec gestion d'erreur
        try:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={
                    "hnsw:space": "cosine",  # Utiliser cosine similarity (crucial!)
                    "document_path": file_path,
                    "indexed_at": str(time.time()),
                    "model": self.embed_model_id,
                    "chunking_max_tokens": self.chunking_config.max_tokens,
                },
            )
        except Exception as e:
            logger.error(f"Échec de création de collection: {e}")
            # Si la collection existe toujours, essayer de la récupérer
            try:
                collection = self.chroma_client.get_collection(name=collection_name)
                logger.warning(f"Utilisation de la collection existante '{collection_name}'")
            except Exception:
                raise Exception(f"Impossible de créer ou récupérer la collection '{collection_name}': {e}")
        logger.info(f"Collection '{collection_name}' créée")

        # 8. Préparer les données pour ChromaDB
        ids = []
        documents = []
        metadatas = []

        for chunk, embedding in zip(processed_chunks, embeddings):
            is_table = "table" in chunk["doc_items_labels"]
            ids.append(f"chunk_{chunk['chunk_id']}")
            documents.append(chunk["text"])
            metadatas.append({
                "chunk_id": chunk["chunk_id"],
                "num_tokens": chunk["num_tokens"],
                "doc_items_labels": ",".join(chunk["doc_items_labels"]),
                "headings": ",".join(chunk["metadata"]["headings"]) if chunk["metadata"]["headings"] else "",
                "is_table": is_table,
                "content_type": "table" if is_table else "text",
            })

        # 9. Insérer par batches (limite ChromaDB: 5000)
        logger.info("Insertion dans ChromaDB...")
        insert_start = time.time()
        batch_size = 5000
        total_chunks = len(ids)

        for i in range(0, total_chunks, batch_size):
            batch_end = min(i + batch_size, total_chunks)
            collection.add(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
                embeddings=embeddings[i:batch_end]
            )

        insert_time = time.time() - insert_start
        logger.info(f"Insertion terminée en {insert_time:.2f}s")

        # 10. Statistiques finales
        table_count = sum(1 for m in metadatas if m["is_table"])
        text_count = len(metadatas) - table_count
        total_time = time.time() - start_time

        stats = {
            "success": True,
            "collection_name": collection_name,
            "total_chunks": len(processed_chunks),
            "table_chunks": table_count,
            "text_chunks": text_count,
            "processing_time": total_time,
            "conversion_time": conversion_time,
            "chunking_time": chunking_time,
            "embedding_time": embedding_time,
            "insert_time": insert_time,
            "chunks_per_second": len(processed_chunks) / total_time,
        }

        logger.info(f"Indexation terminée: {stats['total_chunks']} chunks en {stats['processing_time']:.2f}s")
        return stats

    def search(
        self,
        question: str,
        collection_name: str,
        n_results: int = 5,
        filter_tables: Optional[bool] = None,
        min_score: float = 0.0,
    ) -> Tuple[List[str], List[Dict], List[float]]:
        """
        Recherche sémantique optimisée avec cache

        Args:
            question: Question de l'utilisateur
            collection_name: Collection à interroger
            n_results: Nombre de résultats
            filter_tables: Filtrer par type (True=tables, False=texte, None=tous)
            min_score: Score minimum (0-1, basé sur 1-distance)

        Returns:
            Tuple (chunks, metadatas, distances)
        """
        start_time = time.time()

        try:
            collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' non trouvée: {e}")

        # Générer l'embedding avec cache
        query_embedding = self._get_embedding_cached(question)

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

        # Filtrer par score minimum
        chunks = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        # Convertir distances en scores (1 - distance)
        filtered_results = []
        for chunk, metadata, distance in zip(chunks, metadatas, distances):
            score = 1 - distance
            if score >= min_score:
                filtered_results.append((chunk, metadata, distance))

        if filtered_results:
            chunks, metadatas, distances = zip(*filtered_results)
        else:
            chunks, metadatas, distances = [], [], []

        search_time = time.time() - start_time
        logger.info(f"Recherche terminée en {search_time:.3f}s, {len(chunks)} résultats")

        return list(chunks), list(metadatas), list(distances)

    def generate_answer(
        self, question: str, chunks: List[str], metadatas: List[Dict]
    ) -> str:
        """Génère une réponse avec Ollama"""
        # Construire le contexte
        context_parts = []
        for i, (chunk, metadata) in enumerate(zip(chunks, metadatas), 1):
            content_type = metadata.get("content_type", "unknown")
            headings = metadata.get("headings", "")

            # Ajouter contexte enrichi
            context_header = f"[Extrait {i} - Type: {content_type}"
            if headings:
                context_header += f" - Section: {headings}"
            context_header += "]"

            context_parts.append(f"{context_header}\n{chunk}\n")

        context = "\n".join(context_parts)

        # Prompt optimisé pour l'analyse financière
        prompt = f"""Tu es un assistant expert en analyse financière et rapports d'entreprise.

Voici des extraits pertinents de documents financiers :

{context}

En utilisant UNIQUEMENT les informations fournies dans ces extraits, réponds à la question suivante de manière précise, structurée et professionnelle.

Si les extraits ne contiennent pas assez d'informations pour répondre complètement, indique clairement ce qui manque.

Pour les données chiffrées, cite les chiffres exacts du document.

Question : {question}

Réponse détaillée :"""

        # Appeler Ollama
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Plus bas pour précision
                        "top_p": 0.9,
                        "num_predict": 500,  # Réponses plus longues
                    },
                },
                timeout=90,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Erreur API Ollama: {response.status_code}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur de connexion à Ollama: {e}")

    def clear_cache(self):
        """Vide le cache des embeddings"""
        if self._embedding_cache:
            self._embedding_cache.clear()
            logger.info("Cache vidé")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du cache"""
        if not self._embedding_cache:
            return {"enabled": False}

        return {
            "enabled": True,
            "size": len(self._embedding_cache),
            "model": self.embed_model_id,
        }
