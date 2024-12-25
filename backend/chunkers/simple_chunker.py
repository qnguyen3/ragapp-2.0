from dataclasses import dataclass
from typing import List
from transformers import AutoTokenizer
import re
import asyncio

@dataclass
class Chunk:
    """
    Represents a chunk of text with metadata.
    
    Attributes:
        content (str): The actual text content of the chunk
        start_index (int): Starting position in the original text
        end_index (int): Ending position in the original text
        tokens (int): Number of tokens in the chunk
    """
    content: str
    start_index: int
    end_index: int
    tokens: int

class SimpleChunker:
    def __init__(self, max_chunk_size: int = 512, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the chunker with configurable size and model.
        
        Args:
            max_chunk_size (int): Maximum number of tokens per chunk. Defaults to 512.
            model_name (str): Name of the model to use for tokenization. 
                            Defaults to "sentence-transformers/all-MiniLM-L6-v2".
        """
        self.max_chunk_size = max_chunk_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Regex patterns for special blocks
        self.special_block_pattern = re.compile(
            r'(\|.*?\n\|[-|\s]+\n(?:\|.*?\n)+)|'  # Tables
            r'(?:([^\n]+)\n\n)?(!\[.*?\]\(.*?\).*?)(?:\n\n([^\n]+))?',  # Images
            re.MULTILINE | re.DOTALL
        )
        self.sentence_end = re.compile(r'[.!?]\s+')

    def get_tokens(self, text: str) -> int:
        """
        Get the number of tokens in a text string.
        
        Args:
            text (str): Text to tokenize
            
        Returns:
            int: Number of tokens
        """
        return len(self.tokenizer.encode(text))

    async def aget_tokens(self, text: str) -> int:
        """
        Get the number of tokens in a text string asynchronously.
        
        Args:
            text (str): Text to tokenize
            
        Returns:
            int: Number of tokens
        """
        # Run tokenization in a thread pool since HuggingFace tokenizers are not async
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_tokens, text)

    def is_table_block(self, text: str) -> bool:
        """
        Check if text is a table block.
        
        Args:
            text (str): Text to check
            
        Returns:
            bool: True if text is a table block, False otherwise
        """
        return bool(re.match(r'\|.*?\n\|[-|\s]+\n(?:\|.*?\n)+', text))

    async def _process_special_block(self, text: str, current_pos: int) -> tuple[Chunk | None, int]:
        """
        Process special blocks like tables and images.
        
        Args:
            text (str): Full text being processed
            current_pos (int): Current position in text
            
        Returns:
            tuple: (Chunk if special block found or None, new position)
        """
        # Look for table blocks
        table_match = re.match(r'(\|.*?\n\|[-|\s]+\n(?:\|.*?\n)+)', text[current_pos:], re.MULTILINE)
        if table_match:
            table = table_match.group(0)
            tokens = await self.aget_tokens(table)
            return (Chunk(
                content=table,
                start_index=current_pos,
                end_index=current_pos + len(table),
                tokens=tokens
            ), current_pos + len(table))
            
        # Look for image blocks
        image_match = re.match(r'(?:([^\n]+)\n\n)?(!\[.*?\]\(.*?\).*?)(?:\n\n([^\n]+))?', text[current_pos:])
        if image_match:
            block = image_match.group(0)
            tokens = await self.aget_tokens(block)
            return (Chunk(
                content=block,
                start_index=current_pos,
                end_index=current_pos + len(block),
                tokens=tokens
            ), current_pos + len(block))
            
        return None, current_pos

    async def _process_text_block(self, text: str, current_pos: int) -> tuple[Chunk | None, int]:
        """
        Process regular text blocks.
        
        Args:
            text (str): Full text being processed
            current_pos (int): Current position in text
            
        Returns:
            tuple: (Chunk if text block processed or None, new position)
        """
        chunk_text = ""
        chunk_start = current_pos
        
        while current_pos < len(text):
            next_sentence_match = self.sentence_end.search(text[current_pos:])
            if not next_sentence_match:
                break
                
            sentence_end = current_pos + next_sentence_match.end()
            potential_chunk = text[chunk_start:sentence_end]
            
            # Skip token limit check for tables
            if not self.is_table_block(potential_chunk):
                tokens = await self.aget_tokens(potential_chunk)
                if tokens > self.max_chunk_size:
                    break
                
            chunk_text = potential_chunk
            current_pos = sentence_end

        # Handle remaining text
        if not chunk_text:
            remaining = text[current_pos:current_pos + 1000]  # Limit size for safety
            if self.is_table_block(remaining):
                # Keep entire table
                chunk_text = remaining
                current_pos += len(remaining)
            else:
                tokens = await self.aget_tokens(remaining)
                if tokens <= self.max_chunk_size:
                    chunk_text = remaining
                    current_pos += len(remaining)
                else:
                    chunk_text = text[current_pos:current_pos + 100]  # Fallback
                    current_pos += 100

        if chunk_text:
            tokens = await self.aget_tokens(chunk_text)
            return (Chunk(
                content=chunk_text,
                start_index=chunk_start,
                end_index=current_pos,
                tokens=tokens
            ), current_pos)
            
        return None, current_pos

    async def achunk_text(self, text: str) -> List[Chunk]:
        """
        Split text into chunks asynchronously, preserving special blocks.
        
        Args:
            text (str): Text to split into chunks
            
        Returns:
            List[Chunk]: List of text chunks with metadata
        """
        chunks = []
        current_pos = 0
        
        while current_pos < len(text):
            # Try processing special blocks first
            chunk, new_pos = await self._process_special_block(text, current_pos)
            if chunk:
                chunks.append(chunk)
                current_pos = new_pos
                continue
                
            # Process regular text
            chunk, new_pos = await self._process_text_block(text, current_pos)
            if chunk:
                chunks.append(chunk)
            current_pos = new_pos

        return chunks

    def chunk_text(self, text: str) -> List[Chunk]:
        """
        Split text into chunks synchronously, preserving special blocks.
        
        Args:
            text (str): Text to split into chunks
            
        Returns:
            List[Chunk]: List of text chunks with metadata
        """
        chunks = []
        current_pos = 0
        
        while current_pos < len(text):
            # Look ahead for table blocks
            table_match = re.match(r'(\|.*?\n\|[-|\s]+\n(?:\|.*?\n)+)', text[current_pos:], re.MULTILINE)
            if table_match:
                # Add table as a single chunk regardless of size
                table = table_match.group(0)
                chunks.append(Chunk(
                    content=table,
                    start_index=current_pos,
                    end_index=current_pos + len(table),
                    tokens=self.get_tokens(table)
                ))
                current_pos += len(table)
                continue
            
            # Check for image blocks
            image_match = re.match(r'(?:([^\n]+)\n\n)?(!\[.*?\]\(.*?\).*?)(?:\n\n([^\n]+))?', text[current_pos:])
            if image_match:
                block = image_match.group(0)
                chunks.append(Chunk(
                    content=block,
                    start_index=current_pos,
                    end_index=current_pos + len(block),
                    tokens=self.get_tokens(block)
                ))
                current_pos += len(block)
                continue

            # Regular text processing
            chunk_text = ""
            chunk_start = current_pos
            
            while current_pos < len(text):
                next_sentence_match = self.sentence_end.search(text[current_pos:])
                if not next_sentence_match:
                    break
                    
                sentence_end = current_pos + next_sentence_match.end()
                potential_chunk = text[chunk_start:sentence_end]
                
                # Skip token limit check for tables
                if not self.is_table_block(potential_chunk) and self.get_tokens(potential_chunk) > self.max_chunk_size:
                    break
                    
                chunk_text = potential_chunk
                current_pos = sentence_end

            # Handle remaining text
            if not chunk_text:
                remaining = text[current_pos:current_pos + 1000]  # Limit size for safety
                if self.is_table_block(remaining):
                    # Keep entire table
                    chunk_text = remaining
                    current_pos += len(remaining)
                else:
                    tokens = self.get_tokens(remaining)
                    if tokens <= self.max_chunk_size:
                        chunk_text = remaining
                        current_pos += len(remaining)
                    else:
                        chunk_text = text[current_pos:current_pos + 100]  # Fallback
                        current_pos += 100

            if chunk_text:
                chunks.append(Chunk(
                    content=chunk_text,
                    start_index=chunk_start,
                    end_index=current_pos,
                    tokens=self.get_tokens(chunk_text)
                ))

        return chunks
