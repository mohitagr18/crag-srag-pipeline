# SR-RAG Refinement Loop

This workflow details the Self-Reflective (SR-RAG) iteration loop, which handles grounded generation and hallucination prevention.

```mermaid
flowchart TD
    Start[Handoff from CRAG] --> Draft[Generator: Draft Answer]
    Draft --> Critique[Critic: Score Grounding]
    
    Critique --> Decision{Score State?}
    
    Decision -- ">= 0.8" --> Success[Done: Return Answer]
    Decision -- "0.4 - 0.7" --> Refine[Feedback: Refine Draft]
    Decision -- "< 0.4" --> Reset[Full Loop: Rewrite & Re-Retrieve]
    
    Refine --> Draft
    Reset --> Exit([Loop back to CRAG])
    
    Success --> End([User View])
    
    subgraph "Iteration Limit (3x)"
    Draft
    Critique
    Decision
    Refine
    Reset
    end
```

## Refinement Scenarios

- **Success (>= 0.8)**: The drafted answer is perfectly grounded in the context.
- **Partial Grounding (0.4 - 0.7)**: The answer is mostly correct but contains unverified claims. The Critic identifies the gaps, and the Generator refines the specific sections.
- **Hallucination (< 0.4)**: The draft contains severe inaccuracies. The system wipes the draft (Hard Reset) and retries with a "Strict Fact-Check" prompt.
