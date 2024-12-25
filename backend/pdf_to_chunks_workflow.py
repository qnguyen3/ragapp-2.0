import logging
import time
from pathlib import Path
from typing import List

from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from simple_chunker import SimpleChunker, Chunk

# Setup logging
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

IMAGE_RESOLUTION_SCALE = 2.0

class PdfToChunksWorkflow:
    def __init__(self, max_chunk_size: int = 512):
        """Initialize the workflow with configurable chunk size."""
        self.chunker = SimpleChunker(max_chunk_size=max_chunk_size)
        
        # Setup PDF converter with image options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True
        
        self.doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def process(self, pdf_path: str | Path, output_dir: str | Path = None) -> List[Chunk]:
        """
        Process a PDF file and return chunks of text.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save markdown and images (defaults to 'scratch_{pdf_name}')
            
        Returns:
            List of Chunk objects containing the chunked text
        """
        if isinstance(pdf_path, str):
            pdf_path = Path(pdf_path)
            
        # Setup output directory
        if output_dir is None:
            output_dir = Path(f"scratch_{pdf_path.stem}")
        elif isinstance(output_dir, str):
            output_dir = Path(output_dir)
            
        output_dir.mkdir(parents=True, exist_ok=True)
            
        _log.info(f"Processing PDF file: {pdf_path}")
        start_time = time.time()
        
        # Convert PDF
        _log.info("Converting PDF...")
        conv_result = self.doc_converter.convert(pdf_path)
        doc_filename = conv_result.input.file.stem
        
        # Save page images
        for page_no, page in conv_result.document.pages.items():
            page_image_filename = output_dir / f"{doc_filename}-{page_no}.png"
            with page_image_filename.open("wb") as fp:
                page.image.pil_image.save(fp, format="PNG")
                
        # Save markdown with externally referenced pictures
        md_filename = output_dir / f"{doc_filename}-with-image-refs.md"
        _log.info(f"Saving markdown to: {md_filename}")
        conv_result.document.save_as_markdown(md_filename, image_mode=ImageRefMode.REFERENCED)
        
        # Read markdown file
        _log.info("Reading markdown file...")
        with open(md_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chunk the content
        _log.info("Chunking content...")
        chunks = self.chunker.chunk_text(content)
        
        end_time = time.time() - start_time
        _log.info(f"Created {len(chunks)} chunks in {end_time:.2f} seconds")
        
        return chunks

def main():
    """Example usage"""
    # Initialize workflow
    workflow = PdfToChunksWorkflow(max_chunk_size=512)
    
    # Process a PDF file
    pdf_path = "backend/tesla_pdf.pdf"  # Example path
    chunks = workflow.process(pdf_path)
    
    # Save chunks to output file
    output_file = Path("test_chunks_output.txt")
    _log.info(f"Saving chunks to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(chunks):
            f.write(f"\n=== Chunk {i} ===\n")
            f.write(f"Start index: {chunk.start_index}\n")
            f.write(f"End index: {chunk.end_index}\n")
            f.write(f"Tokens: {chunk.tokens}\n")
            f.write("Content:\n")
            f.write(chunk.content)
            f.write("\n")

if __name__ == "__main__":
    main()
