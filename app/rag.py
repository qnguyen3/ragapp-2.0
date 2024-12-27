import logging
import hashlib
import pickle
from pathlib import Path
from typing import List, Set, Optional

import chromadb
from chromadb.utils import embedding_functions
from transformers import AutoTokenizer

from .config import settings
from backend.workflows.pdf_workflow import PdfToChunksWorkflow
from backend.llm import FastMLXEndpoint

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        """Initialize the RAG service with necessary components."""
        try:
            # Create cache directory if it doesn't exist
            Path(settings.CACHE_DIR).mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB
            self.chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_DB_PATH
            )
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=settings.EMBEDDING_MODEL
            )
            self.collection = self.chroma_client.get_or_create_collection(
                name=settings.COLLECTION_NAME,
                embedding_function=self.embedding_function
            )
            
            # Initialize PDF workflow
            self.pdf_workflow = PdfToChunksWorkflow(
                max_chunk_size=settings.CHUNK_SIZE
            )
            
            # Initialize MLX endpoint
            self.llm = FastMLXEndpoint(
                api_key="test-key",  # Replace with actual key if needed
                url_base=settings.MLX_URL
            )
            
            # Initialize tokenizer for chunking
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.EMBEDDING_MODEL
            )
            
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise

    def _get_document_hash(self, file_path: str | Path) -> str:
        """Get hash of document for caching."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _cache_chunks(self, doc_hash: str, chunks: List) -> None:
        """Cache processed chunks."""
        cache_path = Path(settings.CACHE_DIR) / f"{doc_hash}.pkl"
        with open(cache_path, 'wb') as f:
            pickle.dump(chunks, f)

    def _get_cached_chunks(self, doc_hash: str) -> Optional[List]:
        """Get cached chunks if they exist."""
        cache_path = Path(settings.CACHE_DIR) / f"{doc_hash}.pkl"
        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        return None

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Get all document IDs first
            results = self.collection.get()
            if results and results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Cleared {len(results['ids'])} documents from vector database")
            else:
                logger.info("No documents to clear from vector database")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise

    def ingest_pdf(self, pdf_path: str | Path) -> None:
        """
        Ingest a PDF file into the vector database.
        
        Args:
            pdf_path: Path to the PDF file
            
        Raises:
            Exception: If ingestion fails
        """
        logger.info(f"Ingesting PDF: {pdf_path}")
        try:
            # Check cache first
            doc_hash = self._get_document_hash(pdf_path)
            chunks = self._get_cached_chunks(doc_hash)
            
            if not chunks:
                logger.info("No cached chunks found, processing PDF...")
                # Process PDF and get chunks
                chunks = self.pdf_workflow.process(pdf_path)
                # Cache the chunks
                self._cache_chunks(doc_hash, chunks)
                logger.info("Cached processed chunks")
            else:
                logger.info("Using cached chunks")
            
            # Get IDs of existing chunks for this document
            existing_chunks = self.collection.get(
                where={"source": str(pdf_path)},
                include=['metadatas']
            )
            
            # Extract IDs from metadatas and delete if any exist
            if existing_chunks and existing_chunks['metadatas']:
                existing_ids = [
                    f"{Path(meta['source']).stem}_chunk_{meta['chunk_index']}"
                    for meta in existing_chunks['metadatas']
                ]
                if existing_ids:
                    self.collection.delete(ids=existing_ids)
                    logger.info(f"Deleted {len(existing_ids)} existing chunks for {pdf_path}")

            # Add new chunks to ChromaDB
            texts = [chunk.content for chunk in chunks]
            ids = [f"{Path(pdf_path).stem}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [{
                "source": str(pdf_path),
                "chunk_index": i
            } for i in range(len(chunks))]
            
            self.collection.add(
                documents=texts,
                ids=ids,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(chunks)} chunks to vector database")
            
        except Exception as e:
            logger.error(f"Failed to ingest PDF {pdf_path}: {e}")
            raise

    def query(self, question: str, n_results: int = 5, chat_history: str = "") -> str:
        """
        Query the vector database and generate a response.
        
        Args:
            question: The question to answer
            n_results: Number of relevant chunks to consider
            
        Returns:
            str: Generated answer
            
        Raises:
            Exception: If query processing fails
        """
        logger.info(f"Processing query: {question}")
        try:
            # Check if there are any documents in the collection
            all_docs = self.collection.get()
            doc_count = len(all_docs['ids']) if all_docs and 'ids' in all_docs else 0
            logger.info(f"Current document count in collection: {doc_count}")
            
            if doc_count == 0:
                return "No documents have been uploaded yet. Please upload a document first."
            
            # Get relevant chunks from ChromaDB with metadata
            results = self.collection.query(
                query_texts=[question],
                n_results=min(n_results, doc_count),  # Don't request more chunks than we have
                include=['documents', 'metadatas']
            )
            
            logger.info(f"Query results: {results}")  # Log full results for debugging
            
            if not results['documents'] or not results['documents'][0]:
                logger.warning("Query returned no relevant chunks")
                return "No relevant information found in the documents."
                
            logger.info(f"Found {len(results['documents'][0])} relevant chunks")
            
            # Construct context with all chunks and their sources
            context_parts = []
            for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                source = Path(meta['source']).stem
                context_parts.append(f"[Chunk {i+1} from {source}]:\n{doc}")
            
            context = "\n\n" + "\n\n".join(context_parts)
            prompt = f"""Use the following context and chat history to answer the question. If you cannot answer the question based on the context, say "I cannot answer this question based on the available context."

Context:
{context}

Chat History:
{chat_history}

Question: {question}

Answer the question based on the context above. If the chat history is relevant, you may reference it, but prioritize information from the context. Be clear and concise in your response."""
            
            # Generate response using MLX
            response = self.llm.generate(
                prompt=prompt,
                model_name=settings.MLX_MODEL
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise

    def list_documents(self) -> Set[str]:
        """
        Get a list of all ingested documents.
        
        Returns:
            Set[str]: Set of unique document sources
            
        Raises:
            Exception: If retrieval fails
        """
        try:
            results = self.collection.get(include=['metadatas'])
            if not results or not results['metadatas']:
                return set()
                
            return {
                meta['source'] 
                for meta in results['metadatas']
            }
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise
