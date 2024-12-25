import argparse
import logging
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.utils import embedding_functions
import torch
from transformers import AutoTokenizer
from backend.chunkers import Chunk
from backend.workflows.pdf_workflow import PdfToChunksWorkflow
from backend.llm import FastMLXEndpoint

# Setup logging
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

# Constants
COLLECTION_NAME = "documents"
EMBEDDING_MODEL = "ibm-granite/granite-embedding-278m-multilingual"
CHUNK_SIZE = 512
MLX_MODEL = "mlx-community/Llama-3.2-3B-Instruct-4bit"
MLX_URL = "http://localhost:8000/v1"

class RAGApp:
    def __init__(self):
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_function
        )
        
        # Initialize PDF workflow
        self.pdf_workflow = PdfToChunksWorkflow(max_chunk_size=CHUNK_SIZE)
        
        # Initialize MLX endpoint
        self.llm = FastMLXEndpoint(
            api_key="test-key",  # Replace with actual key if needed
            url_base=MLX_URL
        )
        
        # Initialize tokenizer for chunking
        self.tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)

    def ingest_pdf(self, pdf_path: str | Path) -> None:
        """Ingest a PDF file into the vector database."""
        _log.info(f"Ingesting PDF: {pdf_path}")
        
        # Process PDF and get chunks
        chunks = self.pdf_workflow.process(pdf_path)
        
        # Add chunks to ChromaDB
        texts = [chunk.content for chunk in chunks]
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": str(pdf_path), "chunk_index": i} for i in range(len(chunks))]
        
        self.collection.add(
            documents=texts,
            ids=ids,
            metadatas=metadatas
        )
        _log.info(f"Added {len(chunks)} chunks to vector database")

    def query(self, question: str, n_results: int = 3) -> str:
        """Query the vector database and generate a response."""
        _log.info(f"Processing query: {question}")
        
        # Get relevant chunks from ChromaDB
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results
        )
        
        # Construct prompt with context
        context = "\n\n".join(results['documents'][0])
        prompt = f"""Use the following context to answer the question. If you cannot answer the question based on the context, say "I cannot answer this question based on the available context."

Context:
{context}

Question: {question}

Answer:"""
        
        # Generate response using MLX
        response = self.llm.generate(
            prompt=prompt,
            model_name=MLX_MODEL
        )
        
        return response

def interactive_mode(app: RAGApp):
    """Run the app in interactive mode."""
    print("\nEntering interactive mode. Type 'exit' to quit, 'help' for commands.")
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            
            elif user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("  help     - Show this help message")
                print("  ingest   - Ingest a PDF file (usage: ingest path/to/file.pdf)")
                print("  docs     - Show list of ingested documents")
                print("  exit     - Exit the application")
                print("  [query]  - Ask any other question about the documents")
                
            elif user_input.lower().startswith('ingest '):
                pdf_path = user_input[7:].strip()
                if pdf_path:
                    app.ingest_pdf(pdf_path)
                else:
                    print("Please provide a path to a PDF file")
                    
            elif user_input.lower() == 'docs':
                # Get unique document sources
                results = app.collection.get(include=['metadatas'])
                if results and results['metadatas']:
                    sources = {meta['source'] for meta in results['metadatas']}
                    print("\nIngested documents:")
                    for source in sources:
                        print(f"  - {source}")
                else:
                    print("No documents have been ingested yet")
                    
            elif user_input:
                response = app.query(user_input)
                print("\nAnswer:", response)
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="RAG CLI Application")
    parser.add_argument("--ingest", type=str, help="Path to PDF file to ingest")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    app = RAGApp()
    
    if args.ingest:
        app.ingest_pdf(args.ingest)
    
    if args.interactive:
        interactive_mode(app)
    elif not args.ingest:
        print("No action specified. Use --interactive for interactive mode or --ingest to add a document.")

if __name__ == "__main__":
    main()
