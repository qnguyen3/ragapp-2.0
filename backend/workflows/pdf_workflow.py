import logging
import time
from pathlib import Path
from typing import List

from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from backend.chunkers import SimpleChunker, Chunk

# Setup logging
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

IMAGE_RESOLUTION_SCALE = 2.0

class PdfToChunksWorkflow:
    def __init__(self, max_chunk_size: int = 512):
        """
        Initialize the workflow with configurable chunk size.
        
        Args:
            max_chunk_size (int): Maximum size for each text chunk. Defaults to 512.
        """
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

    async def _save_page_images(self, conv_result, output_dir: Path, doc_filename: str):
        """
        Save page images from conversion result.
        
        Args:
            conv_result: The conversion result containing page images
            output_dir (Path): Directory to save images
            doc_filename (str): Base filename for the document
        """
        for page_no, page in conv_result.document.pages.items():
            page_image_filename = output_dir / f"{doc_filename}-{page_no}.png"
            with page_image_filename.open("wb") as fp:
                page.image.pil_image.save(fp, format="PNG")

    async def _save_markdown(self, conv_result, output_dir: Path, doc_filename: str) -> Path:
        """
        Save markdown with externally referenced pictures.
        
        Args:
            conv_result: The conversion result
            output_dir (Path): Directory to save markdown
            doc_filename (str): Base filename for the document
            
        Returns:
            Path: Path to the saved markdown file
        """
        md_filename = output_dir / f"{doc_filename}-with-image-refs.md"
        _log.info(f"Saving markdown to: {md_filename}")
        conv_result.document.save_as_markdown(md_filename, image_mode=ImageRefMode.REFERENCED)
        return md_filename

    async def aprocess(self, pdf_path: str | Path, output_dir: str | Path = None) -> List[Chunk]:
        """
        Process a PDF file and return chunks of text asynchronously.
        
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
        await self._save_page_images(conv_result, output_dir, doc_filename)
                
        # Save markdown with externally referenced pictures
        md_filename = await self._save_markdown(conv_result, output_dir, doc_filename)
        
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

    def process(self, pdf_path: str | Path, output_dir: str | Path = None) -> List[Chunk]:
        """
        Process a PDF file and return chunks of text synchronously.
        
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
