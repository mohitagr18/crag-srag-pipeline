# Advanced Corrective and Self-Reflective RAG (CRAG/SR-RAG) Pipeline

A production-grade, agentic RAG system that combines **Corrective Retrieval** (web-augmentation) with **Self-Reflective Generation** (iterative refinement) and **Full-Loop Adaptive Retrieval**.

## 🚀 Key Features

- **3-State Corrective RAG (CRAG)**: Dynamically routes queries between Local Vector DB (Qdrant), Hybrid Search, and Web Fallback (Serper) based on context relevance.
- **Utility-Aware SR-RAG**: Evaluates not just if an answer is truthful (**Grounding**), but if it actually addresses the user's intent (**Utility**).
- **Full-Loop Adaptive Retrieval**: If an answer lacks utility or grounding, the **Query Rewriter** optimizes the search term and re-triggers the entire retrieval/ranking process.
- **Best-Effort Delivery**: Prioritizes grounded, truthful "Partial Success" answers over generic error messages if information remains missing after retries.
- **Query Decoupling**: Maintains your original multi-part question intent while using surgical, rewritten queries for back-end search optimization.
- **Observability**: Built-in production logging with `loguru` and full trace visibility via `Opik`.

## 🏗️ Architecture

The pipeline follows a recursive, agentic flow:

1.  **Ingestion**: `docling` parses local PDFs/MDs into a `Qdrant` in-memory vector store.
2.  **Retrieval & CRAG**: A Gemini-powered evaluator decides if local context is sufficient or if web search is needed.
3.  **SR-RAG Iteration**: A generator-critic loop refines the draft up to 3 times for groundedness.
4.  **Adaptive Loop**: If the critic signals low utility (truthful but unhelpful), the orchestrator rewrites the query and re-starts from the retrieval phase.

> [!TIP]
> View the complete visual diagrams in the **[Workflows Directory](./workflows/overall_architecture.md)**.

## 🛠️ Setup & Usage

### 1. Prerequisites
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Google GenAI API Key](https://aistudio.google.com/)
- [Serper API Key](https://serper.dev/) (for web fallback)
- [Opik API Key](https://www.comet.com/opik/) (optional, for tracing)

### 2. Configuration
Copy `.env.example` to `.env` and fill in your keys:
```bash
GEMINI_API_KEY=your_key
SERPER_API_KEY=your_key
OPIK_API_KEY=your_key
OPIK_PROJECT_NAME=crag_srag_pipeline
```

### 3. Run the Pipeline
```bash
uv run python src/main.py "Your question here"
```

## 📖 Documentation

- **[Project Walkthrough](./walkthrough.md)**: A deep dive into the design decisions and implementation details.
- **[Technical Issues Log](./ISSUES.md)**: Documentation of hurdles like "Truthful Ignorance" and "Query Drift."
- **[Mermaid Workflows](./workflows/)**: Detailed visual diagrams of the ingestion, CRAG, and SR-RAG logic.

## 🧪 Testing

Test the pipeline's robustness with multi-part or "trick" queries:
- *"Summarize Orion specs and compare with Starship's payload thresholds."* (Tests hybrid search and utility).
- *"Detail the secret lizard colony in the fuel tanks."* (Tests hallucination recovery and utility resets).