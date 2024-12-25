import asyncio
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports from the backend package
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.workflows import MarkdownToChunksWorkflow

def test_sync_processing():
    """Test synchronous markdown processing"""
    workflow = MarkdownToChunksWorkflow(max_tokens=256)
    
    # Process a markdown file
    input_path = "test.md"  # Example path
    output_file = "test_output_md.txt"
    
    try:
        result = workflow.process(input_path, output_file)
        print("\nSync Processing Test:")
        print(f"Input file: {input_path}")
        print(f"Number of chunks: {len(result.chunks)}")
        print(f"Conversion time: {result.conversion_time:.2f} seconds")
        print(f"Chunking time: {result.chunking_time:.2f} seconds")
        print(f"Total time: {result.total_time:.2f} seconds")
        
        # Print first chunk as example
        if result.chunks:
            print("\nFirst chunk preview:")
            print(f"Text tokens: {len(workflow.tokenizer.tokenize(result.chunks[0].text))}")
            print("Content preview (first 100 chars):")
            print(result.chunks[0].text[:100] + "...")
        
        return True
    except Exception as e:
        print(f"Error in sync processing: {str(e)}")
        return False

async def test_async_processing():
    """Test asynchronous markdown processing"""
    workflow = MarkdownToChunksWorkflow(max_tokens=256)
    
    # Process a markdown file
    input_path = "test.md"  # Example path
    output_file = "test_output_md_async.txt"
    
    try:
        result = await workflow.aprocess(input_path, output_file)
        print("\nAsync Processing Test:")
        print(f"Input file: {input_path}")
        print(f"Number of chunks: {len(result.chunks)}")
        print(f"Conversion time: {result.conversion_time:.2f} seconds")
        print(f"Chunking time: {result.chunking_time:.2f} seconds")
        print(f"Total time: {result.total_time:.2f} seconds")
        
        # Print first chunk as example
        if result.chunks:
            print("\nFirst chunk preview:")
            print(f"Text tokens: {len(workflow.tokenizer.tokenize(result.chunks[0].text))}")
            print("Content preview (first 100 chars):")
            print(result.chunks[0].text[:100] + "...")
        
        return True
    except Exception as e:
        print(f"Error in async processing: {str(e)}")
        return False

def test_chunk_saving():
    """Test chunk saving functionality"""
    workflow = MarkdownToChunksWorkflow(max_tokens=256)
    
    # Process without saving first
    input_path = "test.md"  # Example path
    
    try:
        print("\nChunk Saving Test:")
        
        # Test processing without output file
        result1 = workflow.process(input_path)
        print("Processing without output file: Success")
        
        # Test processing with output file
        result2 = workflow.process(input_path, "test_output_save.txt")
        print("Processing with output file: Success")
        print(f"Chunks saved to: test_output_save.txt")
        
        return True
    except Exception as e:
        print(f"Error in chunk saving test: {str(e)}")
        return False

def main():
    # Run synchronous test
    sync_success = test_sync_processing()
    
    # Run async test
    async_success = asyncio.run(test_async_processing())
    
    # Run chunk saving test
    save_success = test_chunk_saving()
    
    # Print overall results
    print("\nTest Results:")
    print(f"Synchronous Test: {'✓ Passed' if sync_success else '✗ Failed'}")
    print(f"Asynchronous Test: {'✓ Passed' if async_success else '✗ Failed'}")
    print(f"Chunk Saving Test: {'✓ Passed' if save_success else '✗ Failed'}")

if __name__ == "__main__":
    main()
