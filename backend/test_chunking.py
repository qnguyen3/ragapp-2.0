import os
from markdown_chunker import AcademicMarkdownChunker

# Source document to process
DOC_SOURCE = 'scratch/arena_learning-with-image-refs.md'

# Get path for output file in current directory
output_path = os.path.join(os.getcwd(), "chunks_output_arena_3.txt")

print(f"Processing markdown file: {DOC_SOURCE}")
print(f"Output will be written to: {output_path}")
print("-" * 80)

# Initialize the markdown chunker with token-based limits
chunker = AcademicMarkdownChunker(
    max_chunk_size=512,  # Maximum tokens per chunk
    overlap_size=64,     # Token overlap between chunks
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Process the markdown file
try:
    chunks = chunker.chunk_file(DOC_SOURCE)
    
    # Write chunks to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Total chunks: {len(chunks)}\n")
        f.write("-" * 80 + "\n\n")
        
        for i, chunk in enumerate(chunks, 1):
            f.write(f"Chunk {i}:\n")
            f.write(f"Type: {chunk.chunk_type}\n")
            f.write(f"Section: {chunk.section_title}\n")
            
            # Write token information
            if chunk.chunk_type == 'figure':
                f.write(f"Total Tokens: {chunk.metadata.get('total_tokens', 0)}\n")
                f.write(f"Content Tokens (excluding citations): {chunk.metadata.get('actual_tokens', 0)}\n")
            else:
                f.write(f"Token Count: {chunk.metadata.get('token_count', 0)}\n")
            
            f.write("\nContent:\n")
            f.write(chunk.content)
            f.write("\n" + "-" * 80 + "\n\n")
            
        # Write summary statistics
        total_tokens = sum(
            chunk.metadata.get('token_count', 0) if chunk.chunk_type != 'figure' 
            else chunk.metadata.get('actual_tokens', 0) 
            for chunk in chunks
        )
        f.write(f"\nSummary Statistics:\n")
        f.write(f"Total Chunks: {len(chunks)}\n")
        f.write(f"Total Tokens (excluding citations): {total_tokens}\n")
        f.write(f"Average Tokens per Chunk: {total_tokens / len(chunks):.1f}\n")
        
    print(f"Successfully processed {len(chunks)} chunks!")
    print(f"Output written to: {output_path}")
    
except Exception as e:
    print(f"Error processing file: {e}")
