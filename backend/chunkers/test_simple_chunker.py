import asyncio
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports from the backend package
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.chunkers import SimpleChunker

def test_sync_chunking():
    """Test synchronous text chunking"""
    chunker = SimpleChunker(max_chunk_size=512)
    
    # Test text with different block types
    test_text = """
# Test Document

This is a paragraph with a simple sentence. Here is another sentence that should be in the same chunk.

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
| Data 3   | Data 4   |

Here's an image:
![Test Image](path/to/image.png)
This is the image caption.

Another paragraph with multiple sentences. This should create a new chunk. And here's one more sentence.
"""
    
    try:
        chunks = chunker.chunk_text(test_text)
        print("\nSync Chunking Test:")
        print(f"Input text length: {len(test_text)}")
        print(f"Number of chunks: {len(chunks)}")
        
        # Print chunk details
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i}:")
            print(f"Start: {chunk.start_index}")
            print(f"End: {chunk.end_index}")
            print(f"Tokens: {chunk.tokens}")
            print("Content preview:")
            print(chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content)
        
        return True
    except Exception as e:
        print(f"Error in sync chunking: {str(e)}")
        return False

async def test_async_chunking():
    """Test asynchronous text chunking"""
    chunker = SimpleChunker(max_chunk_size=512)
    
    # Test text with different block types
    test_text = """
# Test Document

This is a paragraph with a simple sentence. Here is another sentence that should be in the same chunk.

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
| Data 3   | Data 4   |

Here's an image:
![Test Image](path/to/image.png)
This is the image caption.

Another paragraph with multiple sentences. This should create a new chunk. And here's one more sentence.
"""
    
    try:
        chunks = await chunker.achunk_text(test_text)
        print("\nAsync Chunking Test:")
        print(f"Input text length: {len(test_text)}")
        print(f"Number of chunks: {len(chunks)}")
        
        # Print chunk details
        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i}:")
            print(f"Start: {chunk.start_index}")
            print(f"End: {chunk.end_index}")
            print(f"Tokens: {chunk.tokens}")
            print("Content preview:")
            print(chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content)
        
        return True
    except Exception as e:
        print(f"Error in async chunking: {str(e)}")
        return False

def test_special_blocks():
    """Test handling of special blocks like tables and images"""
    chunker = SimpleChunker(max_chunk_size=512)
    
    # Test table
    table_text = """
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
"""
    
    # Test image
    image_text = """
Some text before the image.

![Image Title](path/to/image.jpg)
Image caption here.

Some text after the image.
"""
    
    try:
        print("\nSpecial Blocks Test:")
        
        # Test table chunking
        table_chunks = chunker.chunk_text(table_text)
        print("\nTable Chunking:")
        print(f"Number of chunks: {len(table_chunks)}")
        print("First chunk content:")
        print(table_chunks[0].content)
        
        # Test image chunking
        image_chunks = chunker.chunk_text(image_text)
        print("\nImage Chunking:")
        print(f"Number of chunks: {len(image_chunks)}")
        for chunk in image_chunks:
            print("\nChunk content:")
            print(chunk.content)
        
        return True
    except Exception as e:
        print(f"Error in special blocks test: {str(e)}")
        return False

def main():
    # Run synchronous test
    sync_success = test_sync_chunking()
    
    # Run async test
    async_success = asyncio.run(test_async_chunking())
    
    # Run special blocks test
    special_success = test_special_blocks()
    
    # Print overall results
    print("\nTest Results:")
    print(f"Synchronous Test: {'✓ Passed' if sync_success else '✗ Failed'}")
    print(f"Asynchronous Test: {'✓ Passed' if async_success else '✗ Failed'}")
    print(f"Special Blocks Test: {'✓ Passed' if special_success else '✗ Failed'}")

if __name__ == "__main__":
    main()
