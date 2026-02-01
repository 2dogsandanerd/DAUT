import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from loguru import logger

try:
    from llama_index.core.schema import Document
except ImportError:
    # Fallback for non-LlamaIndex users
    class Document:
        def __init__(self, text: str, metadata: dict):
            self.text = text
            self.metadata = metadata
        def __repr__(self):
            return f"Document(text={self.text[:50]}..., metadata={self.metadata})"

# --- Configuration & Heuristics ---

class ChunkConfig(BaseModel):
    """Heuristic defaults for chunking per document type"""
    chunk_size: int  # Size in characters
    overlap: int  # Overlap in characters
    splitter_type: str  # "semantic", "fixed", "code", "row_based"

class IngestHeuristics(BaseModel):
    """Document type specific heuristics - The 'Secret Sauce'"""
    pdf: ChunkConfig = ChunkConfig(chunk_size=800, overlap=120, splitter_type="semantic")
    docx: ChunkConfig = ChunkConfig(chunk_size=600, overlap=100, splitter_type="semantic")
    html: ChunkConfig = ChunkConfig(chunk_size=500, overlap=80, splitter_type="semantic")
    markdown: ChunkConfig = ChunkConfig(chunk_size=400, overlap=60, splitter_type="semantic")
    csv: ChunkConfig = ChunkConfig(chunk_size=500, overlap=50, splitter_type="row_based")
    email: ChunkConfig = ChunkConfig(chunk_size=512, overlap=80, splitter_type="semantic")
    code: ChunkConfig = ChunkConfig(chunk_size=256, overlap=40, splitter_type="code")
    default: ChunkConfig = ChunkConfig(chunk_size=800, overlap=120, splitter_type="semantic")

    @classmethod
    def get_config_for_file(cls, filename: str) -> ChunkConfig:
        ext = Path(filename).suffix.lower().replace('.', '')
        heuristics = cls()
        if hasattr(heuristics, ext):
            return getattr(heuristics, ext)
        return heuristics.default

# --- The Smart Loader ---

class SmartDoclingLoader:
    """
    Smart Document Loader using Docling.
    
    Features:
    - Layout-aware parsing (tables, headers)
    - Auto-format detection
    - Returns Markdown-formatted text (preserving structure)
    """

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.pptx', '.xlsx', '.html', '.md'}

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

    def load(self) -> List[Document]:
        """Load and parse the document using Docling."""
        try:
            from docling.document_converter import DocumentConverter
            
            logger.info(f"🚀 Processing with Docling: {self.file_path.name}")
            
            # 1. Convert
            converter = DocumentConverter()
            result = converter.convert(str(self.file_path))
            
            # 2. Export to Markdown (The key to preserving layout!)
            markdown_content = result.document.export_to_markdown()
            
            # 3. Get Optimal Settings (Heuristics)
            config = IngestHeuristics.get_config_for_file(self.file_path.name)
            logger.info(f"🧠 Applied Heuristics for {self.file_path.suffix}: Size={config.chunk_size}, Overlap={config.overlap}")

            # 4. Create Document
            doc = Document(
                text=markdown_content,
                metadata={
                    'source': str(self.file_path),
                    'file_name': self.file_path.name,
                    'file_type': self.file_path.suffix.lower(),
                    'loader': 'smart_docling',
                    'optimal_chunk_size': config.chunk_size,
                    'optimal_overlap': config.overlap
                }
            )
            
            return [doc]

        except ImportError:
            logger.error("Docling not installed. Run: pip install docling")
            raise
        except Exception as e:
            logger.error(f"Failed to process {self.file_path.name}: {e}")
            raise

# --- Demo Function ---

def ingest_file(file_path: str):
    loader = SmartDoclingLoader(file_path)
    docs = loader.load()
    return docs
