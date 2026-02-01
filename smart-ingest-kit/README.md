# 🧠 Smart Ingest Kit

> **"Stop using static chunk sizes."**

This is a lightweight extraction from a production RAG platform. It solves the "Garbage In, Garbage Out" problem by applying intelligent parsing and heuristics *before* your data hits the vector database.

## 🚀 Features

1.  **Layout-Aware Parsing:** Uses [Docling](https://github.com/DS4SD/docling) to preserve document structure (headers, tables, lists) as Markdown. No more "soup of text".
2.  **Smart Heuristics:** Automatically applies optimal chunking strategies based on file type.
    *   **PDFs:** Larger chunks (800 chars) with semantic splitting.
    *   **Code:** Small chunks (256 chars) to preserve logic.
    *   **Markdown:** Medium chunks (400 chars).
3.  **Metadata Enrichment:** Tags your documents with the optimal settings, so your RAG pipeline knows how to handle them.

## 📦 Installation

```bash
pip install -r requirements.txt
```

## ⚡ Usage

```python
from smart_ingestor import ingest_file

# Just pass a file. The system handles the rest.
docs = ingest_file("my_complex_contract.pdf")

print(docs[0].text)  # Clean Markdown
print(docs[0].metadata['optimal_chunk_size'])  # e.g., 800
```

## ❓ Why this exists?

Most RAG tutorials tell you to use `RecursiveCharacterTextSplitter(chunk_size=1000)`.
That's fine for demos, but bad for production.
*   A 1000-char chunk might cut a Python function in half.
*   A PDF table needs to be understood as a table, not a stream of words.

This kit gives you the **"Ingestion Logic"** of a professional system, without the bloat.

## 🤝 Credits

Extracted from the **Mail Modul Alpha** RAG Platform.
Powered by [Docling](https://github.com/DS4SD/docling).
