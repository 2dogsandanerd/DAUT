
from mcp.server.fastmcp import FastMCP
from src.mcp.access import RAGAccess
import json

def create_mcp_server(name: str = "daut-rag-server", project_path: str = ".") -> FastMCP:
    """
    Creates and configures the FastMCP server with RAG tools.
    """
    mcp = FastMCP(name)
    rag = RAGAccess(project_path=project_path)

    @mcp.tool()
    def query_rag(query: str, n_results: int = 5) -> str:
        """
        Semantically search the project documentation and code using the RAG system.
        
        Args:
            query: The question or query to search for.
            n_results: Number of results to return (default: 5).
        """
        results = rag.search_documentation(query, n_results)
        
        if not results:
            return "No relevant results found."
            
        formatted_text = f"Found {len(results)} relevant results for '{query}':\n\n"
        for i, res in enumerate(results, 1):
            metadata = res.get('metadata', {})
            source = metadata.get('file_path', 'unknown')
            score = res.get('score', 0)
            content = res.get('content', '')
            
            formatted_text += f"--- Result {i} (Source: {source}, Score: {score:.4f}) ---\n"
            formatted_text += f"{content}\n\n"
            
        return formatted_text

    @mcp.tool()
    def read_documentation_file(file_path: str) -> str:
        """
        Read the full content of a specific documentation file.
        
        Args:
            file_path: Relative path to the file (e.g. 'docs/my_doc.md').
        """
        content = rag.get_file_content(file_path)
        if content:
            return content
        else:
            return f"Error: File '{file_path}' not found or could not be read. Please check the path using list_documentation_files."

    @mcp.tool()
    def list_documentation_files() -> str:
        """
        List all available documentation files in the project.
        """
        files = rag.list_files()
        if not files:
            return "No documentation files found."
        return "Available documentation files:\n" + "\n".join([f"- {f}" for f in files])

    return mcp
