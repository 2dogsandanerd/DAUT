# Documentation Auto-Update Tool (DAUT) - QWEN Context

## Project Overview

The Documentation Auto-Update Tool (DAUT) is a standalone Python application that automatically compares code and documentation, identifying discrepancies and updating documentation accordingly. The tool is designed to work with various project types and supports multiple programming languages.

The application implements a complete 4-phase architecture:
1. **Phase 1**: Core functionality (scanning, project analysis, discrepancy detection)
2. **Phase 2**: ChromaDB integration for semantic search
3. **Phase 3**: Ollama integration for AI-assisted documentation generation
4. **Phase 4**: Update functionality with backup system and ChromaDB updates

## Key Features

- **Universal Code Scanner**: Detects functions, classes, API endpoints in multiple languages (Python, JavaScript, TypeScript)
- **Documentation Scanner**: Analyzes documentation files in various formats (Markdown, reStructuredText, Text)
- **Discrepancy Analysis**: Finds gaps between code and documentation
- **User-friendly Interface**: Streamlit-based GUI and CLI
- **Intelligent File Filtering**: Respects .gitignore and ignores unwanted directories like venv, node_modules, __pycache__
- **ChromaDB Integration**: Updates vector database for semantic search capabilities
- **LLM Integration**: Ollama integration for AI-assisted documentation generation

## Architecture

The application is organized into several modules:
- `core/`: Core components like configuration management and project analysis
- `scanner/`: Components for scanning code and documentation files
- `models/`: Data models for code and documentation elements
- `ui/`: User interface based on Streamlit
- `matcher.py`: Matching algorithm for discrepancy detection
- `llm/`: Ollama integration for AI-assisted generation
- `chroma/`: ChromaDB integration for semantic search
- `updater/`: Update functionality with backup system

## Dependencies

The project uses:
- Python 3.9+
- Streamlit (>=1.28.0) for the UI
- ChromaDB (>=0.4.0) for vector search
- LangChain and langchain-ollama for LLM integration
- Ollama client library for LLM communication
- Pydantic for data validation
- GitPython for .gitignore functionality

## Building and Running

### Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

#### CLI Mode
```bash
# Scan project
python -m src.docs_updater /path/to/project

# Scan without further analysis
python -m src.docs_updater /path/to/project --mode scan --output ./results

# With specific service configuration
python -m src.docs_updater /path/to/project --service-config /path/to/service_config.json
```

#### GUI Mode
```bash
streamlit run src/ui/main.py
```

## Configuration

Service connections (Ollama, ChromaDB) can be configured via the `service_config.json` file. If this file is not found, a default configuration is automatically created with:
- Ollama Host: `http://localhost:11434`
- ChromaDB Host: `localhost:8000`

## File Format Support

- **Code**: `.py`, `.js`, `.ts`, `.tsx`, `.jsx`
- **Documentation**: `.md`, `.rst`, `.txt`
- **Configuration**: `.env`, `.json`, `.yaml`, `.yml`, `.toml`

## File Filtering

The tool automatically considers:
- `.gitignore` entries (when in a Git repository)
- Exclusion patterns from configuration (e.g., `venv/`, `node_modules/`, `__pycache__/`)
- File type filters based on configuration

## Development Conventions

- The project uses Pydantic for data validation and configuration management
- Classes follow a modular design with clear single responsibilities
- Error handling is implemented with try-catch blocks and appropriate logging
- The scanner intelligently detects project types and structures, including monorepos
- ChromaDB collections are created automatically when needed

## Open Implementation Points

1. **AI Documentation Generation**: The `generate_documentation_for_code` function is implemented, but currently uses placeholder implementations for embedding generation. The integration with a real embedding service (e.g., Sentence Transformers) is not fully implemented.

2. **Semantic Search Functions**: While ChromaDB is implemented, semantic search functions (e.g., for similarity matching between code and documentation) are still expandable.

3. **Update Workflows**: The actual documentation update function is implemented as a placeholder - the actual updating of documentation files based on LLM results is not fully implemented.

## Connection Parameters

- By default connected to `Ollama` on port 11434
- By default connected to `ChromaDB` on port 8000
- These values are configurable in the `service_config.json`
- On first start, necessary ChromaDB collections are created automatically