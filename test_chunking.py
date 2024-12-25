from markdown_chunker import AcademicMarkdownChunker
import logging

def output_chunks_to_file(input_file: str, output_file: str):
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize chunker with appropriate chunk sizes for this document
    chunker = AcademicMarkdownChunker(
        max_chunk_size=2000,  # Increased to handle larger sections
        min_chunk_size=100,
        overlap_size=50
    )
    
    # Process the markdown file
    chunks = chunker.chunk_file(input_file)
    
    # Write chunks to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Processing file: {input_file}\n")
        f.write(f"Total chunks found: {len(chunks)}\n\n")
        
        for i, chunk in enumerate(chunks, 1):
            f.write(f"{'='*80}\n")
            f.write(f"CHUNK {i}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Type: {chunk.chunk_type}\n")
            f.write(f"Section: {chunk.section_title}\n")
            f.write(f"Start Index: {chunk.start_index}\n")
            f.write(f"End Index: {chunk.end_index}\n")
            f.write(f"Length: {len(chunk.content)} characters\n")
            f.write(f"Metadata: {chunk.metadata}\n")
            f.write("\nContent:\n")
            f.write(f"{'-'*80}\n")
            f.write(f"{chunk.content}\n")
            f.write(f"{'-'*80}\n\n")

if __name__ == "__main__":
    # Process the Tesla markdown file
    output_chunks_to_file("scratch_tesla/tesla_pdf-with-image-refs.md", "chunks_output_tesla_md.txt")
