import re
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Union
import logging
from pathlib import Path
from transformers import AutoTokenizer

@dataclass
class Chunk:
    """Represents a chunk of markdown content with metadata."""
    content: str
    section_title: str
    chunk_type: str  # 'text', 'figure', 'table', 'references'
    start_index: int
    end_index: int
    metadata: dict

class AcademicMarkdownChunker:
    def __init__(self, 
                 max_chunk_size: int = 512,
                 overlap_size: int = 64,
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the chunker with configuration parameters.
        
        Args:
            max_chunk_size: Maximum size of a chunk in tokens
            overlap_size: Number of tokens to overlap between chunks
            model_name: Name of the HuggingFace model to use for tokenization
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.section_pattern = re.compile(r'^#{2,3}\s+(.+)$', re.MULTILINE)
        self.figure_pattern = re.compile(r'(?:([^\n]+)\n\n)?(!\[.*?\]\(.*?\).*?)(?:\n\n([^\n]+))?(?=\n\n|$)', re.DOTALL)
        self.table_pattern = re.compile(r'(\|.*?\n\|[-|\s]+\n(?:\|.*?\n)+)', re.MULTILINE)
        self.sentence_end_pattern = re.compile(r'[.!?]\s+')
        
    def _get_current_section(self, text: str, position: int) -> str:
        """Find the current section title based on position in text."""
        matches = list(self.section_pattern.finditer(text[:position]))
        if not matches:
            return "Unknown Section"
        return matches[-1].group(1).strip()

    def _is_special_block(self, text: str, start_pos: int) -> Optional[tuple]:
        """Check if position starts a special block (figure/table)."""
        # Check for figures
        figure_match = self.figure_pattern.match(text[start_pos:])
        if figure_match:
            return ('figure', figure_match.group(0))
            
        # Check for tables
        table_match = self.table_pattern.match(text[start_pos:])
        if table_match:
            return ('table', table_match.group(1))
            
        return None

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences at punctuation marks."""
        return [s.strip() for s in self.sentence_end_pattern.split(text) if s.strip()]

    def _get_token_length(self, text: str) -> int:
        """Get the number of tokens in a text string."""
        return len(self.tokenizer.encode(text))

    def _find_overlap_start(self, text: str, target_tokens: int) -> int:
        """Find the start position that gives approximately target_tokens when tokenized."""
        if not text:
            return 0
            
        # Find all sentence breaks
        sentence_breaks = list(self.sentence_end_pattern.finditer(text))
        if not sentence_breaks:
            return 0
            
        # Try each break point from the end until we find one that gives us close to target_tokens
        for match in reversed(sentence_breaks):
            overlap_text = text[match.end():]
            if self._get_token_length(overlap_text) <= target_tokens:
                return match.end()
                
        return 0

    def create_chunks(self, text: str) -> List[Chunk]:
        """
        Create chunks from the markdown text, trying to reach max_chunk_size at punctuation marks.
        
        Args:
            text: Input markdown text
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        current_pos = 0
        current_chunk = []
        current_chunk_tokens = 0
        last_chunk_end = 0  # Track where the last chunk ended for overlap
        
        while current_pos < len(text):
            # Check if we're at a section header
            section_match = self.section_pattern.match(text[current_pos:])
            if section_match:
                # If we have content in current chunk, save it
                if current_chunk:
                    chunk_content = ''.join(current_chunk)
                    chunks.append(Chunk(
                        content=chunk_content,
                        section_title=self._get_current_section(text, current_pos),
                        chunk_type='text',
                        start_index=current_pos - len(chunk_content),
                        end_index=current_pos,
                        metadata={'token_count': self._get_token_length(chunk_content)}
                    ))
                    last_chunk_end = current_pos
                    current_chunk = []
                    current_chunk_tokens = 0
                    
                current_pos += len(section_match.group(0))
                continue
                
            # Check for special blocks
            special_block = self._is_special_block(text, current_pos)
            if special_block:
                block_type, block_content = special_block
                
                # Save current chunk if exists
                if current_chunk:
                    chunk_content = ''.join(current_chunk)
                    chunks.append(Chunk(
                        content=chunk_content,
                        section_title=self._get_current_section(text, current_pos),
                        chunk_type='text',
                        start_index=current_pos - len(chunk_content),
                        end_index=current_pos,
                        metadata={'token_count': self._get_token_length(chunk_content)}
                    ))
                    last_chunk_end = current_pos
                    current_chunk = []
                    current_chunk_tokens = 0
                
                if block_type == 'figure':
                    citation_match = re.search(r'!\[(.*?)\]\((.*?)\)', block_content)
                    citation_text = citation_match.group(0) if citation_match else ''
                    content_without_citation = block_content.replace(citation_text, '')
                    total_tokens = self._get_token_length(block_content)
                    actual_tokens = self._get_token_length(content_without_citation)
                else:
                    total_tokens = actual_tokens = self._get_token_length(block_content)
                
                chunks.append(Chunk(
                    content=block_content,
                    section_title=self._get_current_section(text, current_pos),
                    chunk_type=block_type,
                    start_index=current_pos,
                    end_index=current_pos + len(block_content),
                    metadata={
                        'is_special_block': True,
                        'total_tokens': total_tokens,
                        'actual_tokens': actual_tokens
                    }
                ))
                last_chunk_end = current_pos + len(block_content)
                current_pos += len(block_content)
                continue
            
            # Regular text processing
            next_char = text[current_pos]
            temp_chunk = ''.join(current_chunk) + next_char
            temp_tokens = self._get_token_length(temp_chunk)
            
            # Check if adding this character would exceed max tokens
            if temp_tokens >= self.max_chunk_size:
                chunk_text = ''.join(current_chunk)
                
                # Look for the last sentence break
                last_sentence_break = max(
                    (i.end() for i in self.sentence_end_pattern.finditer(chunk_text)), 
                    default=None
                )
                
                if last_sentence_break:
                    # Split at the last sentence break
                    first_part = chunk_text[:last_sentence_break].strip()
                    remainder = chunk_text[last_sentence_break:].strip()
                else:
                    # If no sentence break found, use all content
                    first_part = chunk_text
                    remainder = ""
                
                if first_part:
                    chunks.append(Chunk(
                        content=first_part,
                        section_title=self._get_current_section(text, current_pos),
                        chunk_type='text',
                        start_index=current_pos - len(chunk_text),
                        end_index=current_pos - len(chunk_text) + len(first_part),
                        metadata={'token_count': self._get_token_length(first_part)}
                    ))
                    last_chunk_end = current_pos - len(chunk_text) + len(first_part)
                
                # Start new chunk with remainder and overlap from previous chunk
                if self.overlap_size > 0:
                    overlap_start = self._find_overlap_start(first_part, self.overlap_size)
                    overlap_text = first_part[overlap_start:]
                    current_chunk = [overlap_text, remainder] if remainder else [overlap_text]
                    current_chunk_tokens = self._get_token_length(''.join(current_chunk))
                else:
                    current_chunk = [remainder] if remainder else []
                    current_chunk_tokens = self._get_token_length(remainder) if remainder else 0
            
            # Add current character to chunk
            current_chunk.append(next_char)
            current_chunk_tokens = temp_tokens
            current_pos += 1
        
        # Add final chunk if exists
        if current_chunk:
            chunk_content = ''.join(current_chunk)
            chunks.append(Chunk(
                content=chunk_content,
                section_title=self._get_current_section(text, current_pos),
                chunk_type='text',
                start_index=current_pos - len(chunk_content),
                end_index=current_pos,
                metadata={'token_count': self._get_token_length(chunk_content)}
            ))
            
        return chunks

    def chunk_file(self, file_path: str) -> List[Chunk]:
        """
        Process a markdown file and return chunks.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            List of Chunk objects
        
        Raises:
            FileNotFoundError: If the file doesn't exist
            UnicodeDecodeError: If there's an encoding issue
            ValueError: If the file is empty or invalid
        """
        if not file_path.endswith('.md'):
            raise ValueError("File must be a markdown file with .md extension")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if not content.strip():
                raise ValueError(f"File is empty: {file_path}")
                
            # Basic markdown validation
            if not re.search(r'^#', content, re.MULTILINE):
                logging.warning(f"File {file_path} may not be properly formatted markdown (no headers found)")
                
            return self.create_chunks(content)
            
        except UnicodeDecodeError:
            # Try with different encodings
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    logging.warning(f"File {file_path} was read using {encoding} encoding")
                    return self.create_chunks(content)
                except UnicodeDecodeError:
                    continue
            raise UnicodeDecodeError(f"Could not decode file {file_path} with any known encoding")
            
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {str(e)}")
            raise

# Example usage:
if __name__ == "__main__":
    chunker = AcademicMarkdownChunker(
        max_chunk_size=512,
        overlap_size=64,
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Example using a file
    try:
        # Get the path to your markdown file
        current_dir = Path(__file__).parent
        markdown_file = "backend/tesla_pdf.pdf"
        
        # Process the file
        chunks = chunker.chunk_file(str(markdown_file))
        
        # Print chunks with formatting
        print(f"\nProcessed {markdown_file.name}")
        print(f"Found {len(chunks)} chunks\n")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"Chunk {i}:")
            print(f"Type: {chunk.chunk_type}")
            print(f"Section: {chunk.section_title}")
            print(f"Length: {len(chunk.content)} characters")
            print("Content:")
            
            print("-" * 50)
            print(chunk.content)
            print("-" * 50 + "\n")
            
    except Exception as e:
        logging.error(f"Error processing markdown file: {str(e)}")
        raise