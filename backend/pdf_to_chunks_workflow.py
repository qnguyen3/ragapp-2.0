import logging
import time
from pathlib import Path

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.chunking import HybridChunker
from transformers import AutoTokenizer

# Setup logging
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

# Constants
EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MAX_TOKENS = 256
IMAGE_RESOLUTION_SCALE = 2.0

def process_pdf(input_pdf_path):
    """Process PDF using docling."""
    # Configure PDF pipeline options
    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    # Initialize document converter
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Convert document
    _log.info(f"Processing PDF: {input_pdf_path}")
    conv_res = doc_converter.convert(input_pdf_path)
    return conv_res.document

def chunk_document(doc):
    """Chunk the document using HybridChunker."""
    # Initialize tokenizer and chunker
    tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL_ID)
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=MAX_TOKENS,
    )
    
    _log.info("Chunking document...")
    # Process chunks
    chunk_iter = chunker.chunk(dl_doc=doc)
    return list(chunk_iter), chunker, tokenizer

def save_chunks_to_file(chunks, chunker, tokenizer, output_file, timing_info):
    """Save chunks to a text file with timing information."""
    _log.info(f"Saving chunks to: {output_file}")
    with open(output_file, 'w') as f:
        # Write timing information
        f.write(f"Document processing time: {timing_info['processing_time']:.2f} seconds\n")
        f.write(f"Chunking time: {timing_info['chunking_time']:.2f} seconds\n")
        f.write(f"Total time: {timing_info['total_time']:.2f} seconds\n\n")
        
        # Write chunks
        for i, chunk in enumerate(chunks):
            f.write(f"=== Chunk {i} ===\n")
            txt_tokens = len(tokenizer.tokenize(chunk.text, max_length=None))
            f.write(f"Text ({txt_tokens} tokens):\n{chunk.text}\n")

            ser_txt = chunker.serialize(chunk=chunk)
            ser_tokens = len(tokenizer.tokenize(ser_txt, max_length=None))
            f.write(f"Serialized ({ser_tokens} tokens):\n{ser_txt}\n")
            f.write("\n")

def main():
    # File paths
    input_pdf_path = Path("backend/tesla_pdf.pdf")  # Using tesla_pdf.pdf as example
    output_file = Path("chunks_output.txt")

    # Start timing
    total_start_time = time.time()
    
    # Step 1: Process PDF
    processing_start_time = time.time()
    doc = process_pdf(input_pdf_path)
    processing_time = time.time() - processing_start_time

    # Step 2: Chunk the document
    chunking_start_time = time.time()
    chunks, chunker, tokenizer = chunk_document(doc)
    chunking_time = time.time() - chunking_start_time

    # Calculate total time
    total_time = time.time() - total_start_time

    # Step 3: Save chunks to file
    timing_info = {
        'processing_time': processing_time,
        'chunking_time': chunking_time,
        'total_time': total_time
    }
    save_chunks_to_file(chunks, chunker, tokenizer, output_file, timing_info)
    
    _log.info("Process completed successfully!")

if __name__ == "__main__":
    main()
