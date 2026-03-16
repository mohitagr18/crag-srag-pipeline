

# 🔮 Advanced CRAG + SR-RAG Pipeline

### *Agentic Retrieval-Augmented Generation with Adaptive Intelligence*

[]($1)
[]($1)
[]($1)
[]($1)
[]($1)



  *🎯 Adaptive Retrieval • 🔍 Utility-Aware Evaluation • 🌐 Web Fallback • 🔄 Recursive Loops*




[Features]($1) • [Quick Start]($1) • [Architecture]($1) • [Documentation]($1) • [Issues Log]($1)





╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   📄 Local Docs  →  🔍 Smart Retrieval  →  🤖 Agentic Gen    ║
║                                                              ║
║   ✅ CRAG: 3-Way Routing (Correct/Ambiguous/Incorrect)      ║
║   ✅ SR-RAG: Utility-Aware Iterative Grounding              ║
║   ✅ Loops: Full-Loop Recursive Re-Retrieval                ║
║   ✅ Intent: Original Query Preservation via Decoupling     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
`



## ✨ Features





### 🎯 **Corrective RAG (CRAG)**


- 📊 **LLM-based relevance evaluation**

- 🌐 **Real-time web fallback** (Serper)

- 🔀 **3-Way routing** (Local/Hybrid/Web)

- ⚡ **Dynamic context augmentation**





### 🔍 **Self-Reflective (SR-RAG)**


- ✅ **Grounding &amp; Utility validation**

- 🔄 **Iterative draft refinement**

- 🎯 **"Truthful Ignorance" detection**

- 📝 **Best-effort grounded delivery**







### 🚀 **Recursive Intelligence**


- 🔮 **Full-loop adaptive retrieval**

- 🏆 **Surgical Query Rewriting**

- 🌐 **Web search preserved across loops**

- 🎓 **Production-ready accuracy**





### 🛠️ **Core Capabilities**


- 🔍 **Vector Search**: Qdrant In-Memory

- 📄 **Advanced Parsing**: Docling integration

- 🧩 **Query Decoupling**: Search vs. Intent

- 🔧 **Observability**: Loguru + Opik traces







## 🏗️ Architecture



graph TD
    User([User Query]) --&gt; Decouple{Decouple Queries}
    Decouple --&gt; |"Search Query"| Retrieval[Retrieve from Qdrant]
    Decouple --&gt; |"Original Intent"| Draft
    
    Retrieval --&gt; CRAG{CRAG Evaluator}
    
    CRAG -- status: correct --&gt; Grounding[Active Context]
    CRAG -- status: ambiguous --&gt; Hybrid[Merge: Local + Web]
    CRAG -- status: incorrect --&gt; Web[Serper Web Search]
    
    Hybrid --&gt; Grounding
    Web --&gt; Grounding
    
    Grounding --&gt; Draft[Generator: Draft Answer]
    Draft --&gt; Critique{Critic: Score &amp; Utility}
    
    Critique -- "score &gt;= 0.8 AND utility: true" --&gt; Success([Final Answer])
    Critique -- "0.4 &lt;= score &lt; 0.8" --&gt; Refine[Feedback: Refine Draft]
    Critique -- "Utility: False OR score &lt; 0.4" --&gt; LoopCheck{Loop Count?}
    
    Refine --&gt; Draft
    
    LoopCheck -- "Loops &lt; Max" --&gt; Rewriter[Query Rewriter]
    Rewriter --&gt; |"New Search Query"| Retrieval
    
    LoopCheck -- "Loops Exhausted" --&gt; BestEffort{Best Effort?}
    BestEffort -- "score &gt;= 0.8" --&gt; Success
    BestEffort -- "score &lt; 0.8" --&gt; Failure([Generic Disclaimer])
`



## 🚀 Quick Start

### 1. Prerequisites

✅ Python 3.9+
✅ uv (ultra-fast package manager)
✅ Google GenAI API Key
✅ Serper API Key
`
### 2. Installation &amp; Setup

# 1️⃣ Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2️⃣ Clone and setup
git clone &lt;repo-url&gt;
cd crag-srag-pipeline
cp .env.example .env
# Edit .env with your API keys

# 3️⃣ Run a query
uv run python src/main.py "Your question here"
`


## 🧠 Adaptive Intelligence &amp; Core Concepts

### 🔄 Full-Loop Adaptive Retrieval

Unlike standard linear RAG, this pipeline can "re-think" its strategy. If initial results lead to a disclaimer or hallucination, the **Query Rewriter** transforms the feedback into a surgical search query and re-triggers the entire CRAG/Retrieval process.


### 🎯 Utility vs. Grounding

We solve the "Truthful Ignorance" problem. While LLMs are often truthful in their disclaimers (e.g., *"I don't know"*), these are **unhelpful**.



- **Grounding**: Is the answer factually supported?

- **Utility**: Does it actually address the user's intent?
The pipeline rejects grounded but unhelpful answers, forcing a re-search until substantive data is found.


### 🧩 Query Decoupling (Intent Preservation)

To prevent "Query Drift," we decouple searching from answering. Refined queries are used for surgical retrieval, but the **Original User Query** is always preserved for the Generator to ensure all parts of a multi-part question are addressed.


### 📝 Best-Effort Delivery

If search loops are exhausted, the system prioritizes **Grounded Truth** over generic error messages. It will deliver the grounded portions of an answer (Partial Success) instead of a total failure disclaimer.



## 📖 Documentation


- 🛠️ **[Issues &amp; Resolutions]($1)** - Documentation of technical hurdles like "Truthful Ignorance."

- 🧪 **[Testing Queries]($1)** - Curated list of multi-part and edge-case test queries.

- 📊 **[Mermaid Workflows]($1)** - Detailed visual diagrams of CRAG and SR-RAG logic.



## 🎓 Technology Stack


- **LLM**: [Google Gemini 1.5]($1)

- **Vector DB**: [Qdrant]($1)

- **Document Processing**: [Docling]($1)

- **Web Search**: [Serper]($1)

- **Observability**: [Opik]($1)

- **Package Manager**: [uv]($1)


### 



