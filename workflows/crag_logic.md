# CRAG Decision Flow

This workflow illustrates the Corrective Retrieval-Augmented Generation (CRAG) logic used to determine if retrieved context is sufficient or needs web augmentation.

```mermaid
flowchart TD
    Start[Retrieve from Qdrant] --> Eval[Gemini Relevance Evaluator]
    
    Eval --> Logic{Status?}
    
    Logic -- "correct" --> UseLocal[Use Qdrant Chunks Only]
    Logic -- "ambiguous" --> Merge[Merge Local + Serper Web Context]
    Logic -- "incorrect" --> Fallback[Serper Web Search Only]
    
    UseLocal --> Done[Proceed to Generation]
    Merge --> Done
    Fallback --> Done
```

## Logic States

- **Correct**: The local vector database contained a definitive answer. No external API calls are made to Serper.
- **Ambiguous**: The local docs are related but incomplete. The pipeline merges local snippets with real-time web results to maximize grounding.
- **Incorrect**: The local docs are irrelevant to the query (e.g., asking about current events). The system discards the local context to prevent hallucinations.
