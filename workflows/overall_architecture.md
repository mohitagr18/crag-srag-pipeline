# Overall Project Architecture

This document visualizes the complete end-to-end flow of the Corrective and Self-Reflective RAG (CRAG/SR-RAG) pipeline.

```mermaid
graph TD
    User([User Query]) --> Ingestion[Ingestion Pipeline]
    Ingestion --> Qdrant[(Qdrant In-Memory)]
    
    User --> Retrieval[Retrieve from Qdrant]
    Retrieval --> CRAG{CRAG Evaluator}
    
    CRAG -- status: correct --> Grounding[Active Context]
    CRAG -- status: ambiguous --> Hybrid[Merge: Local + Web]
    CRAG -- status: incorrect --> Web[Serper Web Search]
    
    Hybrid --> Grounding
    Web --> Grounding
    
    Grounding --> Draft[Generator: Draft Answer]
    Draft --> Critique{Critic: Score Grounding}
    
    Critique -- "score >= 0.8" --> Success([Final Answer])
    Critique -- "0.4 <= score < 0.8" --> Refine[Feedback: Refine Draft]
    Critique -- "score < 0.4" --> Reset[Hallucination: Hard Reset]
    
    Refine --> Draft
    Reset --> Rewriter[Query Rewriter]
    Rewriter --> Retrieval
    
    Success --> Output([Final Answer])

    subgraph "Knowledge Discovery"
    Ingestion
    Qdrant
    end

    subgraph "Corrective Routing (CRAG)"
    Retrieval
    CRAG
    Hybrid
    Web
    end

    subgraph "Self-Reflection (SR-RAG)"
    Draft
    Critique
    Refine
    Reset
    end
```

## Key Components

1.  **Ingestion Engine**: Uses `docling` to parse local PDF/MD files and `Qdrant` for storage.
2.  **CRAG Evaluator**: Classifies context relevance into three states (Correct, Ambiguous, Incorrect) to determine if web search is needed.
3.  **SR-RAG Engine**: An iterative loop that generates drafts and critiques them for grounding.
4.  **Adaptive Retrieval**: If grounding fails severely, the **Query Rewriter** generates a new search query to re-trigger the CRAG/Retrieval process.
