import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports from the backend package
sys.path.append(str(Path(__file__).parent.parent.parent))
from backend.workflows import PdfToChunksWorkflow

def test_sync_processing():
    """Test synchronous PDF processing"""
    workflow = PdfToChunksWorkflow(max_chunk_size=512)
    
    # Process a PDF file
    pdf_path = "backend/tesla_pdf.pdf"  # Example path
    output_dir = "test_output"
    
    try:
        chunks = workflow.process(pdf_path, output_dir)
        print("\nSync Processing Test:")
        print(f"PDF Path: {pdf_path}")
        print(f"Number of chunks: {len(chunks)}")
        
        # Print first chunk as example
        if chunks:
            print("\nFirst chunk preview:")
            print(f"Start index: {chunks[0].start_index}")
            print(f"End index: {chunks[0].end_index}")
            print(f"Tokens: {chunks[0].tokens}")
            print("Content preview (first 100 chars):")
            print(chunks[0].content[:100] + "...")
        
        return True
    except Exception as e:
        print(f"Error in sync processing: {str(e)}")
        return False

async def test_async_processing():
    """Test asynchronous PDF processing"""
    workflow = PdfToChunksWorkflow(max_chunk_size=512)
    
    # Process a PDF file
    pdf_path = "backend/tesla_pdf.pdf"  # Example path
    output_dir = "test_output_async"
    
    try:
        chunks = await workflow.aprocess(pdf_path, output_dir)
        print("\nAsync Processing Test:")
        print(f"PDF Path: {pdf_path}")
        print(f"Number of chunks: {len(chunks)}")
        
        # Print first chunk as example
        if chunks:
            print("\nFirst chunk preview:")
            print(f"Start index: {chunks[0].start_index}")
            print(f"End index: {chunks[0].end_index}")
            print(f"Tokens: {chunks[0].tokens}")
            print("Content preview (first 100 chars):")
            print(chunks[0].content[:100] + "...")
        
        return True
    except Exception as e:
        print(f"Error in async processing: {str(e)}")
        return False

def main():
    # Run synchronous test
    sync_success = test_sync_processing()
    
    # Run async test
    async_success = asyncio.run(test_async_processing())
    
    # Print overall results
    print("\nTest Results:")
    print(f"Synchronous Test: {'✓ Passed' if sync_success else '✗ Failed'}")
    print(f"Asynchronous Test: {'✓ Passed' if async_success else '✗ Failed'}")

if __name__ == "__main__":
    main()
