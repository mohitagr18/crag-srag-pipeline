# Testing the CRAG/SR-RAG Pipeline

I have updated the pipeline architecture! Instead of fetching a single GitHub README online, the ingestion engine now natively supports dragging-and-dropping `.txt` or `.pdf` files straight into your `data/` directory.

## How to Test

Run the pipeline from your terminal using `uv`:

```bash
PYTHONPATH=. uv run python src/main.py "Your query goes here"
```

The pipeline will automatically:
1. Scan the `data/` directory for any `.txt` or `.pdf` documents.
2. Parse, chunk (*HybridChunker*), and embed (*gemini-embedding-001*) them into the localized Qdrant Vector DB.
3. Run the complete routing, generation, and critique pipeline.
4. Output verbose logs showing exact reasoning and scores.

---

## Scenario Queries to Try

*I have placed a sample capabilities document `data/orion_specs.txt` inside your folder so you can test immediately. To test your own data, drop it in the `data/` folder!*

### 1. Pass CRAG without search
*These queries ask about the contents of the ingested local documents. CRAG will evaluate the retrieved vector chunks as relevant and completely skip the Serper search.*
- `PYTHONPATH=. uv run python src/main.py "What materials make up the Orion spacecraft hull?"`
- `PYTHONPATH=. uv run python src/main.py "What temperature is the interior cabin regulated to?"`
- `PYTHONPATH=. uv run python src/main.py "How many Gs of acceleration can the framework support?"`

### 2. Require search in CRAG (Fallback to Web)
*These queries ask about current events or completely unrelated topics. CRAG will analyze the local documents, realize they do not contain the answer, and route to Serper Web Search.*
- `PYTHONPATH=. uv run python src/main.py "Who won the Super Bowl in 2024?"`
- `PYTHONPATH=. uv run python src/main.py "What are the latest features released in Python 3.13?"`
- `PYTHONPATH=. uv run python src/main.py "What is the current stock price of Google?"`

### 3. Pass SR-RAG
*These queries allow the Generation Agent to draft a perfectly grounded answer from the context on the first try. The Critic will score it >= 0.8, and it will immediately return.*
- `PYTHONPATH=. uv run python src/main.py "Summarize the upcoming changes planned for revision 2.0 of the Orion hull."`
- `PYTHONPATH=. uv run python src/main.py "Why is the inner shell polished with lead?"`

### 4. FAIL SR-RAG (Trigger the Feedback Refinement Loop)
*To forcefully fail the Self-Reflective (SR-RAG) grounding metric, we have to trick the Generation agent into hallucinating or generating an ungrounded claim. Since the prompt strictly instructs the agent to answer 'ONLY using the provided context', if we ask about something adjacent but explicitly missing, the critic will catch the hallucination.*
- `PYTHONPATH=. uv run python src/main.py "Explain the exact cost figures in USD associated with manufacturing the DuraWeave mesh."`
*(Since this document contains no pricing data, the strict Critic will catch any attempts to hallucinate a number out-of-context and force it to refine its answer to "The context does not contain cost figures.")*

---

## What Documents Are in the DB?

- **Location**: The engine reads all `.txt` and `.pdf` files dropped into the local `/Users/mohit/Documents/GitHub/crag-srag-pipeline/data/` folder.
- **Parsing**: `docling` automatically extracts the text layouts.
- **Storage**: The chunks are stored via `hybrid chunking` into an **in-memory** instance of Qdrant (which only lives as long as the python script is running).

> [!WARNING]
> Please note that if you place heavily formatted, multi-page PDFs inside the `data/` directory, the initial ingestion via the IBM `Docling` visual engine can take several minutes to completely process before the query pipeline asks for your prompt!
