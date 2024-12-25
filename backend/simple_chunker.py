from dataclasses import dataclass
from typing import List
from transformers import AutoTokenizer
import re

@dataclass
class Chunk:
    content: str
    start_index: int
    end_index: int
    tokens: int

class SimpleChunker:
    def __init__(self, max_chunk_size: int = 512, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.max_chunk_size = max_chunk_size
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.special_block_pattern = re.compile(
            r'(\|.*?\n\|[-|\s]+\n(?:\|.*?\n)+)|'  # Tables
            r'(?:([^\n]+)\n\n)?(!\[.*?\]\(.*?\).*?)(?:\n\n([^\n]+))?',  # Images
            re.MULTILINE | re.DOTALL
        )
        self.sentence_end = re.compile(r'[.!?]\s+')

    def get_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def is_table_block(self, text: str) -> bool:
        """Check if text is a table block."""
        return bool(re.match(r'\|.*?\n\|[-|\s]+\n(?:\|.*?\n)+', text))

    def chunk_text(self, text: str) -> List[Chunk]:
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
