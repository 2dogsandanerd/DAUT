# Changelog

## [1.1.0] - 2025-12-14

### 🚀 New Features
- **MCP Server Integration**: 
  - Added full Model Context Protocol (MCP) server support.
  - Runs as a background systemd service (`daut-mcp.service`).
  - Supports API Key authentication and RAG query tools (`query_rag`, `read_documentation_file`).
  - Added "System Status" sidebar in UI to show MCP health and active connections.

### 🧠 RAG Engine Improvements
- **Unified Collections**: Refactored `UpdaterEngine` to use a single, unified collection for the entire project (e.g., `daut_code`) instead of creating fragmented collections for each subfolder.
- **Full Content Embeddings**: Fixed a limitation where only the first 1000 characters of a document were indexed. Now uses the full content for semantic search.
- **Smart Scanning**: `auto_docs` and `docs` directories are now forcibly scanned even if excluded by `.gitignore`, ensuring generated documentation is always indexed.

### 💅 UI & Usability
- **ChromaDB Management**: 
  - Replaced text input with a Collection Dropdown for easier selection.
  - Fixed JSON serialization errors when viewing collection details.
- **Status Reporting**: Improved error handling in the sidebar (no more "Red Error" boxes without context).

### 🐛 Bug Fixes
- Fixed `AttributeError: 'DocElement' object has no attribute 'format'`.
- Fixed `TypeError` in MCP status widget when `active_connections` list was empty.
- Fixed context-blind updates for nested files by enforcing Root Project path propagation.

### 📚 Documentation
- Added **Best Practices** section to README advising on `auto_docs` prioritization vs. legacy `docs/`.
