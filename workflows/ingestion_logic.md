# Ingestion Workflow

This workflow visualizes how local documents are processed into the vector database.

```mermaid
flowchart LR
    Docs[data/*.md, data/*.pdf] --> Docling[IBM Docling Engine]
    Docling --> Parser[Structural Layout Parsing]
    Parser --> Chunker[Hybrid Chunker]
    Chunker --> Embed[GenAI: gemini-embedding-001]
    Embed --> Qdrant[(Qdrant In-Memory)]
```

## Strategy

- **Formats**: Supports `.md` (Markdown) and `.pdf`.
- **Parsing**: `Docling` is used for high-fidelity extraction of headings, lists, and tables.
- **Chunking**: `HybridChunker` ensures that semantic boundaries (like headings) are preserved across chunks.
- **Storage**: Chunks are stored in a volatile in-memory `Qdrant` collection, which is re-initialized on every script execution to ensure fresh data.
