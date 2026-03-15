# Testing the CRAG/SR-RAG Pipeline

I have updated `src/main.py` so that you can easily test any query by passing it as a command-line argument!

## How to Test

Run the pipeline from your terminal using `uv`:

```bash
PYTHONPATH=. uv run python src/main.py "Your query goes here"
```

The pipeline will automatically:
1. Initialize the Qdrant DB in-memory.
2. Ingest the document (if not already downloaded).
3. Run the complete routing, generation, and critique pipeline.
4. Output verbose logs showing exact reasoning and scores.

---

## Scenario Queries to Try

### 1. Pass CRAG without search
*These queries ask about the contents of the ingested repository. CRAG will evaluate the retrieved vector chunks as relevant and skip the Tavily/Serper search.*
- `PYTHONPATH=. uv run python src/main.py "What are the architectural modes in the Corrective Self-Reflective RAG repo?"`
- `PYTHONPATH=. uv run python src/main.py "Explain how the HybridChunker works in this project."`
- `PYTHONPATH=. uv run python src/main.py "What Vector Database is used in the reference repository architecture?"`

### 2. Require search in CRAG (Fallback to Web)
*These queries ask about current events or completely unrelated topics. CRAG will analyze the repo docs, realize they do not contain the answer, and route to Serper Web Search.*
- `PYTHONPATH=. uv run python src/main.py "Who won the Super Bowl in 2024?"`
- `PYTHONPATH=. uv run python src/main.py "What are the latest features released in Python 3.13?"`
- `PYTHONPATH=. uv run python src/main.py "What is the current stock price of Google?"`

### 3. Pass SR-RAG
*These queries allow the Generation Agent to draft a perfectly grounded answer on the first try. The Critic will score it >= 0.8, and it will immediately return.*
- `PYTHONPATH=. uv run python src/main.py "Summarize the overarching goal of the Corrective Self-Reflective RAG pipeline."`
- `PYTHONPATH=. uv run python src/main.py "Does the repository use Qdrant or ChromaDB?"`

### 4. FAIL SR-RAG (Trigger the Feedback Refinement Loop)
*To forcefully fail the Self-Reflective (SR-RAG) grounding metric, we have to trick the Generation agent into hallucinating or generating an ungrounded claim. If we instruct it to output excessive details about a nonexistent feature, the strict grounding critic will catch the hallucination, score it `< 0.8`, and force a regeneration.*
- `PYTHONPATH=. uv run python src/main.py "Explain the enterprise pricing tiers and the 24/7 support SLA detailed in the repository."`
*(Since this repo has no pricing, the LLM might hallucinate a standard pricing model, causing the Critic to catch the hallucination and force it to refine its answer to "The context does not contain pricing information.")*

---

## What Documents Are in the DB?

The pipeline currently ingests **a single document** directly from the reference GitHub repository.

- **Source URL**: `https://raw.githubusercontent.com/sourangshupal/corrective_self_reflective_rag/main/README.md`
- **Local Location**: It is downloaded and saved as `repo_README.md` in the root of your project directory (`/Users/mohit/Documents/GitHub/crag-srag-pipeline/repo_README.md`).
- **Storage**: The chunks are stored via `hybrid chunking` into an **in-memory** instance of Qdrant (which only lives as long as the python script is running).

If you want to add more documents, simply modify the `fetch_and_process_repo_docs()` function in `src/ingestion.py` to loop over additional URLs or local local files!
