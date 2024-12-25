import logging
from pathlib import Path
from simple_chunker import SimpleChunker

# Setup logging
logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

def main():
    # Initialize chunker
    chunker = SimpleChunker(max_chunk_size=512)
    
    # Read test file
    input_file = Path("scratch_tesla/tesla_pdf-with-image-refs.md")
    _log.info(f"Reading file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chunk the content
    _log.info("Chunking content...")
    chunks = chunker.chunk_text(content)
    
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
            
            # # Add extra info for special blocks
            # if "|" in chunk.content and "\n|" in chunk.content:
            #     f.write("(Table block)\n")
            # if "![" in chunk.content and "](" in chunk.content:
            #     f.write("(Image block)\n")
    
    _log.info(f"Total chunks created: {len(chunks)}")
    _log.info("Done!")

if __name__ == "__main__":
    main()
