import logging
import time
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

from docling.document_converter import DocumentConverter, MarkdownFormatOption
from docling.datamodel.base_models import InputFormat
from docling.chunking import HybridChunker, Chunk
from transformers import AutoTokenizer

# Setup logging
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

# Constants
EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TOKENS = 256

@dataclass
class ChunkingResult:
    """
    Result of markdown chunking process.
    
    Attributes:
        chunks (List[Chunk]): List of document chunks
        conversion_time (float): Time taken for document conversion
        chunking_time (float): Time taken for chunking
        total_time (float): Total processing time
    """
    chunks: List[Chunk]
    conversion_time: float
    chunking_time: float
    total_time: float

class MarkdownToChunksWorkflow:
    def __init__(self, max_tokens: int = MAX_TOKENS, model_id: str = EMBED_MODEL_ID):
        """
        Initialize the workflow with configurable token limit and model.
        
        Args:
            max_tokens (int): Maximum tokens per chunk. Defaults to 256.
            model_id (str): Model ID for tokenization. 
                          Defaults to "sentence-transformers/all-MiniLM-L6-v2".
        """
        self.max_tokens = max_tokens
        self.model_id = model_id
        
        # Initialize document converter
        self.doc_converter = DocumentConverter(
            format_options={
                InputFormat.MD: MarkdownFormatOption()
            }
        )
        
        # Initialize tokenizer and chunker
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.chunker = HybridChunker(
            tokenizer=self.tokenizer,
            max_tokens=max_tokens,
        )

    def _convert_markdown(self, input_path: Path):
        """
        Convert markdown document using docling.
        
        Args:
            input_path (Path): Path to input markdown file
            
        Returns:
            Document: Converted document
        """
        _log.info(f"Converting Markdown: {input_path}")
        conv_res = self.doc_converter.convert(input_path)
        return conv_res.document

    def _chunk_document(self, doc) -> List[Chunk]:
        """
        Chunk the document using HybridChunker.
        
        Args:
            doc: Document to chunk
            
        Returns:
            List[Chunk]: List of document chunks
        """
        _log.info("Chunking document...")
        chunk_iter = self.chunker.chunk(dl_doc=doc)
        return list(chunk_iter)

    def save_chunks(self, chunks: List[Chunk], output_file: Path, timing_info: dict):
        """
        Save chunks to a text file with timing information.
        
        Args:
            chunks (List[Chunk]): List of document chunks
            output_file (Path): Path to output file
            timing_info (dict): Dictionary containing timing information
        """
        _log.info(f"Saving chunks to: {output_file}")
        with open(output_file, 'w') as f:
            # Write timing information
            f.write(f"Document conversion time: {timing_info['conversion_time']:.2f} seconds\n")
            f.write(f"Chunking time: {timing_info['chunking_time']:.2f} seconds\n")
            f.write(f"Total time: {timing_info['total_time']:.2f} seconds\n\n")
            
            # Write chunks
            for i, chunk in enumerate(chunks):
                f.write(f"=== Chunk {i} ===\n")
                txt_tokens = len(self.tokenizer.tokenize(chunk.text, max_length=None))
                f.write(f"Text ({txt_tokens} tokens):\n{chunk.text}\n")

                ser_txt = self.chunker.serialize(chunk=chunk)
                ser_tokens = len(self.tokenizer.tokenize(ser_txt, max_length=None))
                f.write(f"Serialized ({ser_tokens} tokens):\n{ser_txt}\n")
                f.write("\n")

    def process(self, input_path: str | Path, output_file: str | Path = None) -> ChunkingResult:
        """
        Process a markdown file and return chunks synchronously.
        
        Args:
            input_path: Path to the markdown file
            output_file: Optional path to save chunks to
            
        Returns:
            ChunkingResult: Result containing chunks and timing information
        """
        if isinstance(input_path, str):
            input_path = Path(input_path)
            
        if output_file and isinstance(output_file, str):
            output_file = Path(output_file)

        # Start timing
        total_start_time = time.time()
        
        # Convert markdown
        conversion_start_time = time.time()
        doc = self._convert_markdown(input_path)
        conversion_time = time.time() - conversion_start_time

        # Chunk the markdown
        chunking_start_time = time.time()
        chunks = self._chunk_document(doc)
        chunking_time = time.time() - chunking_start_time

        # Calculate total time
        total_time = time.time() - total_start_time

        # Save chunks if output file provided
        if output_file:
            timing_info = {
                'conversion_time': conversion_time,
                'chunking_time': chunking_time,
                'total_time': total_time
            }
            self.save_chunks(chunks, output_file, timing_info)
        
        return ChunkingResult(
            chunks=chunks,
            conversion_time=conversion_time,
            chunking_time=chunking_time,
            total_time=total_time
        )

    async def aprocess(self, input_path: str | Path, output_file: str | Path = None) -> ChunkingResult:
        """
        Process a markdown file and return chunks asynchronously.
        
        Args:
            input_path: Path to the markdown file
            output_file: Optional path to save chunks to
            
        Returns:
            ChunkingResult: Result containing chunks and timing information
        """
        # For now, we'll run synchronously since the underlying libraries don't support async
        # In the future, we could run the processing in a thread pool
        return self.process(input_path, output_file)
