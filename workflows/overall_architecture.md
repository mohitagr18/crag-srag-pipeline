# Overall Project Architecture

This document visualizes the complete end-to-end flow of the Corrective and Self-Reflective RAG (CRAG/SR-RAG) pipeline.

```mermaid
graph TD
    User([User Query]) --> Decouple{Decouple Queries}
    Decouple --> |"Search Query"| Retrieval[Retrieve from Qdrant]
    Decouple --> |"Original Intent"| Draft
    
    Retrieval --> CRAG{CRAG Evaluator}
    
    CRAG -- status: correct --> Grounding[Active Context]
    CRAG -- status: ambiguous --> Hybrid[Merge: Local + Web]
    CRAG -- status: incorrect --> Web[Serper Web Search]
    
    Hybrid --> Grounding
    Web --> Grounding
    
    Grounding --> Draft[Generator: Draft Answer]
    Draft --> Critique{Critic: Score & Utility}
    
    Critique -- "score >= 0.8 AND utility: true" --> Success([Final Answer])
    Critique -- "0.4 <= score < 0.8" --> Refine[Feedback: Refine Draft]
    Critique -- "Utility: False OR score < 0.4" --> LoopCheck{Loop Count?}
    
    Refine --> Draft
    
    LoopCheck -- "Loops < Max" --> Rewriter[Query Rewriter]
    Rewriter --> |"New Search Query"| Retrieval
    
    LoopCheck -- "Loops Exhausted" --> BestEffort{Best Effort?}
    BestEffort -- "score >= 0.8" --> Success
    BestEffort -- "score < 0.8" --> Failure([Generic Disclaimer])

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
    end
```

## Key Components

1.  **Query Decoupling**: The orchestrator maintains the original user intent for generation while refined/surgical search queries are used for adaptive retrieval loops.
2.  **CRAG Evaluator**: Classifies context relevance into three states (Correct, Ambiguous, Incorrect) to determine if web search is needed.
3.  **Utility-Aware Critique**: The system evaluates not just if an answer is truthful (Grounding), but also if it actually addresses the user's intent (Utility).
4.  **Adaptive Retrieval**: If utility or grounding is low, the **Query Rewriter** optimizes the search query to re-trigger the CRAG/Retrieval process.
5.  **Best-Effort Delivery**: If search loops are exhausted, the system prioritizes grounded truths over generic errors, delivering partial answers if they are factually correct.
