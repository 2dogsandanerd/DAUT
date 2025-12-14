
from typing import List, Dict, Any, Optional
from pathlib import Path
import os
from src.core.service_config import ServiceConfig
from src.chroma.client import ChromaDBClient
from src.llm.client import OllamaClient

class RAGAccess:
    """
    Interface for the MCP server to access RAG capabilities.
    """
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.config = ServiceConfig()
        
        # Initialize Clients
        self.chroma_client = ChromaDBClient(
            host=self.config.chroma_host,
            port=self.config.chroma_port,
            timeout=self.config.chroma_timeout
        )
        
        # We need Ollama for embeddings
        ollama_host = "http://localhost:11434"
        if hasattr(self.config, 'ollama_host'):
            ollama_host = self.config.ollama_host
            
        self.ollama_client = OllamaClient(host=ollama_host)
        self.embedding_model = "nomic-embed-text"

    def health_check(self) -> Dict[str, bool]:
        """Check connection to backend services"""
        return {
            "chroma": self.chroma_client.health_check(),
            "ollama": self.ollama_client.health_check()
        }

    def search_documentation(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search in the documentation.
        """
        # 1. Generate Embedding
        embedding = self.ollama_client.create_embedding(self.embedding_model, query)
        if not embedding:
            print(f"Failed to generate embedding for query: {query}")
            return []

        # 2. Query ChromaDB
        # We search in both code and docs collections ?? 
        # For now let's prioritize docs or search both.
        # Based on updater logic: project_name + "_docs" / "_code"
        
        project_name = self.project_path.name
        collections_to_search = [f"{project_name}_docs", f"{project_name}_code"]
        
        all_results = []
        
        for col_name in collections_to_search:
            results = self.chroma_client.query_collection(
                collection_name=col_name,
                query_embeddings=[embedding],
                n_results=n_results,
                auto_create=False
            )
            
            if results and 'documents' in results and results['documents']:
                # Chroma returns list of lists
                docs = results['documents'][0]
                metadatas = results['metadatas'][0] if 'metadatas' in results else []
                ids = results['ids'][0] if 'ids' in results else []
                distances = results['distances'][0] if 'distances' in results else []
                
                for i, doc in enumerate(docs):
                    all_results.append({
                        "content": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "id": ids[i] if i < len(ids) else "",
                        "score": distances[i] if i < len(distances) else 0.0,
                        "source": col_name
                    })
        
        # Sort by score (distance) - lower is better for cosine distance in Chroma defaults usually,
        # but check metadata. default is l2? 
        # Chroma default is L2 (Euclidean), lower is better.
        # If created with cosine, lower is better (0=identical, 1=orthogonal, 2=opposite)
        all_results.sort(key=lambda x: x['score'])
        
        return all_results[:n_results]

    def list_files(self) -> List[str]:
        """List all markdown files in the auto_docs or docs folder"""
        # Simple implementation searching common doc folders
        doc_dirs = [
            self.project_path / "docs",
            self.project_path / "auto_docs"
        ]
        
        files = []
        for d in doc_dirs:
            if d.exists():
                for f in d.rglob("*.md"):
                    files.append(str(f.relative_to(self.project_path)))
        return sorted(list(set(files)))

    def get_file_content(self, file_path: str) -> Optional[str]:
        """Read content of a specific file"""
        full_path = self.project_path / file_path
        if full_path.exists() and full_path.is_file():
             # Basic security check: prevent going outside project
            try:
                full_path.relative_to(self.project_path)
            except ValueError:
                return None
                
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
