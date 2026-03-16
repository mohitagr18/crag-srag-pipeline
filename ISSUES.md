# Technical Issues & Resolution Log

This document chronicles the major technical challenges, edge cases, and design hurdles encountered during the development of the Corrective and Self-Reflective RAG (CRAG/SR-RAG) pipeline.

## 1. The "Truthful Ignorance" Dilemma (Utility vs. Grounding)

### Issue
LLMs are trained to be honest. When asked a question like *"Detail the secret lizard colony in Orion,"* the model would correctly state: *"The provided context does not mention a lizard colony."* 

Because this statement is **100% truthful**, the Critic would assign a **1.0 Grounding Score**. In our initial linear logic, a 1.0 score meant "Success," so the pipeline would stop and return a disclaimer to the user, even if better information existed on the web.

### Example
- **Query**: "Detail the secret lizard colony in Orion fuel tanks."
- **Draft**: "There is no information about lizards in the specs."
- **Critique**: Score 1.0 (True) -> Success.

### Resolution
We introduced the **Utility Check**. The Critic now evaluates both Grounding (Precision) and Utility (Recall). If an answer is grounded but has **Low Utility** (e.g., a disclaimer), it is now flagged as a failure. This forces the pipeline to trigger the **Query Rewriter** and re-search the web before finally giving up.

---

## 2. Query Drift in Recursive Loops

### Issue
When the SR-RAG stage determined it needed more info, it would "rewrite" the query (e.g., *"Starship payload capacity estimates"*). In early iterations, this rewritten query was being passed as the `query` to the **Generator**.

As a result, the system would "forget" the first half of a multi-part question because it was strictly following the latest search term.

### Example
- **User**: "Summarize Orion specs **and** predict Starship thresholds."
- **Rewritten Search**: "Starship payload capacity."
- **Final Result**: Only talked about Starship; Orion specs were lost.

### Resolution
We **decoupled Searching from Answering** in `src/main.py`. The system now maintains two separate strings:
1. `search_query`: Refined surgically for retries (e.g., "Starship capacity").
2. `original_query`: Always passed to the Generator (ensuring the full context of the user's intent is preserved).

---

## 3. "Binary Failure" of Multi-part Questions

### Issue
Our pipeline was initially too "all-or-nothing." If a user asked a two-part question and the system found a grounded answer for Part A but had zero data for Part B, the low **Utility** score would trigger a loop failure. After all search retries were exhausted, the system would return a generic error: *"I'm sorry, I couldn't find a grounded answer."*

This was frustrating because the system actually *did* have half the answer (Part A), but threw it away.

### Resolution
Implemented **Best-Effort Delivery**. In the final loop, we now check the **Grounding Score** independently of Utility. If the answer is highly grounded (truthful), we deliver it **even if utility is low**. This ensures the user gets a "Partial Success" (Part A + a disclaimer for Part B) rather than a total failure message.

---

## 4. 3-State Corrective Routing (Binary vs. Nuanced)

### Issue
Standard CRAG often uses a binary "Relevant" vs "Irrelevant" check. However, we found many cases where context was **Ambiguous**—containing some related keywords but not enough details to answer fully. In a binary system, these were often treated as "Correct," leading to hallucinations when the model tried to "force" an answer.

### Resolution
Modified `src/schema.py` and `src/evaluator.py` to support a **3-State Status**:
- `correct`: Use local chunks only.
- `ambiguous`: Trigger **Hybrid Search** (Merge local + Web).
- `incorrect`: Discard local chunks; Fallback to Web only.

---

## 5. Dependency Hardening (NumPy & Qdrant)

### Issue
A version conflict occurred between `qdrant-client`, `fastembed`, and the latest `numpy` releases (NumPy 2.0+). The `qdrant-client` had internal requirements for `numpy<2`, causing the pipeline to crash during ingestion.

### Resolution
Pinned the dependencies in the environment:
- `numpy<2`
- `qdrant-client<=1.12.0`
This ensured cross-compatibility between the vector store and the embedding models.
