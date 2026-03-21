# AI Agent Framework

## Sources
- https://www.youtube.com/watch?v=ESBMgZHzfG0
- https://www.youtube.com/watch?v=ODwF-EZo_O8
- https://www.youtube.com/watch?v=EAeUiipzCTE
- https://www.youtube.com/watch?v=ZaPbP9DwBOE
- https://www.youtube.com/watch?v=FwOTs4UxQS4

## Related Concepts
- [[EZo]]
- [[FwOTs]]
- [[ODwF]]
- [[DwBOE]]
- [[EAeUiipzCTE]]
- [[UxQS]]
- [[ZaPbP]]
- [[ESBMgZHzfG]]

## Insights
**1. Summary**
*   **AI Agents over Chatbots:** While chatbots passively wait for inputs and generate text based on their training data, AI agents act as autonomous decision-makers equipped with memory, reasoning capabilities, and tools to actively plan and complete tasks on a user's behalf [1-4].
*   **The Role of Frameworks:** Agentic frameworks like LangChain, LangGraph, Microsoft Agent Framework, AutoGen, and Semantic Kernel organize the complex logic needed to connect AI models with databases, APIs, and memory storage, making code highly maintainable and scalable [5-9].
*   **Ecosystem Building Blocks:** Building effective agents involves combining fundamental AI primitives (prompts, embeddings, LLMs) with advanced compositions like retrieval-augmented generation (RAG), vector databases, and function calling [10-12].

**2. Key concepts**
*   **Levels of AI Operation:** AI progresses from basic Large Language Models (generating text from inputs) to **AI Workflows** (following strict, predefined paths dictated by a human) to **AI Agents** (where the LLM autonomously determines the steps and tools needed to reach a goal) [1, 2, 13-17].
*   **Embeddings & Vector Databases:** Because LLMs have limited context windows (short-term memory capacity), data must be converted into numerical vectors ("embeddings") capturing semantic meaning. Vector databases store these embeddings, allowing the AI to search vast amounts of data by *meaning* rather than exact keyword match [18-23].
*   **Memory Management:** To avoid acting like a "dumb" system that forgets past interactions, agents use **short-term memory** (session threads) and **long-term memory** (context providers) to store user preferences across sessions. Techniques like sliding windows and automated summarization keep memory within the LLM's token budget constraints [24-28].
*   **Function Calling & Tools:** Giving an AI "hands." This concept allows an agent to request external data or execute actions (like checking the weather API or booking a flight) by passing variables to specialized functions [11, 29-31].
*   **Model Context Protocol (MCP):** Acts as a universal "USB port" for AI. Instead of developers writing rigid, custom API integrations, MCP provides self-describing interfaces that AI agents can autonomously understand and plug into existing external databases and tools [32-35].

**3. Architecture explanation**
*   **The ReAct (Reason and Act) Loop:** The core architecture of an agent relies on a continuous loop. The agent receives a goal, **Thinks** (plans steps), **Acts** (calls functions or tools), and **Observes** the interim result, iterating until the objective is fulfilled [36-39].
*   **Retrieval-Augmented Generation (RAG):** RAG architectures integrate search with generation. When a user asks a question, the system queries a vector database, retrieves semantically relevant document chunks, and augments the prompt with this factual context before passing it to the LLM to generate an accurate response [12, 40-43].
*   **Framework Orchestration Paradigms:**
    *   **LangChain & Microsoft Agent Framework:** Provide standardized abstraction layers to link models, prompts, tools, and memory effortlessly [4-8].
    *   **LangGraph:** Manages complex, stateful workflows using a graph structure. It uses **nodes** (individual units of computation/functions) and **edges** (the execution flow and conditional routing) to allow for iterative loops and dynamic decision-making [44-47].
*   **Multi-Agent Systems:** Complex architectures distribute tasks among specialized agents. For example, a travel-planning application might use Agent A to research, Agent B to book flights, and Agent C to handle hotels, utilizing frameworks like AutoGen to let them collaborate and delegate [9, 48, 49].

**4. Important insights**
*   **Autonomy is the Defining Factor:** Simply linking APIs together does not create an AI agent; if a human explicitly scripts the execution path, it is merely an AI workflow. True agents require the LLM to be the orchestrator and decision-maker [2, 15, 17].
*   **Match the Framework to the Use Case:** Different frameworks serve different masteries. **Semantic Kernel** focuses on production-ready enterprise environments (supporting C#, Java, Python); **AutoGen** is tailored for researchers testing multi-agent concepts; and **LangGraph** excels at conditional, branching logic [9, 50].
*   **Complexity vs. Necessity:** Memory and tool integrations consume tokens and increase latency. For simple, stateless query tasks (like translating text or pulling general knowledge), full agent orchestration or permanent memory is overkill and can slow the system down [51, 52].
*   **Prompting Techniques Drive Quality:** How you talk to the agent impacts its behavior. Using **few-shot prompting** ensures the agent learns specific tone and formatting, while **chain-of-thought prompting** forces the AI to break down complex logic step-by-step, drastically improving reasoning accuracy [53-57].

**Action Plan**
1.  **Define System Requirements:** Assess whether your project needs a basic RAG setup (simple Q&A), an AI workflow (fixed multi-step tasks), or a true AI Agent (dynamic reasoning and action).
2.  **Select an Agent Framework:** Choose LangChain for general LLM abstraction, LangGraph for conditional loops, Semantic Kernel for enterprise C#/Java deployments, or AutoGen for multi-agent delegation.
3.  **Establish Knowledge & Memory Infrastructure:** Set up a Vector Database (like Chroma) to index embeddings for semantic search, and implement conversation threads paired with sliding window summarization to manage context limits.
4.  **Expose Tools Systematically:** Instead of hard-coding API integrations, build tools via Function Calling or deploy Model Context Protocol (MCP) servers to allow the agent to autonomously fetch real-time data or perform actions securely.
