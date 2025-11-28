

# **Asynchronous Middleware Architectures in LangGraph: Implementation, Concurrency Patterns, and Deadlock Mitigation**

## **1\. Introduction: The Paradigm Shift to Stateful, Asynchronous Agent Orchestration**

The domain of Large Language Model (LLM) application development has undergone a radical architectural transformation in recent years, shifting from linear, stateless execution chains to complex, stateful, and cyclic graph-based workflows. This evolution, necessitated by the demand for autonomous agents capable of reasoning, planning, and long-horizon task execution, has culminated in frameworks like LangGraph. LangGraph represents a fundamental departure from the legacy "Chain" abstraction, introducing a graph-based runtime where nodes represent discrete units of computation (reasoning, tool execution, state mutation) and edges define the control flow, allowing for loops, conditionals, and persistence.1

However, the complexity of orchestrating these autonomous agents introduces significant engineering challenges, particularly regarding concurrency and side-effect management. As agents move from simple request-response patterns to continuous running loops that interact with external environments—databases, file systems, APIs, and human users—the need for a robust middleware layer becomes paramount. Middleware in this context serves as an implementation of the Aspect-Oriented Programming (AOP) paradigm, allowing developers to inject cross-cutting concerns such as logging, security, state initialization, and observability into the agent's lifecycle without polluting the core reasoning logic.2

A critical, yet often underestimated, aspect of this architecture is the requirement for asynchronous execution. Modern AI agents are inherently I/O bound; they spend the vast majority of their execution time waiting—waiting for model tokens to stream, waiting for database queries to return, or waiting for external tools to complete. To achieve high throughput and scalability, particularly in web-serving contexts like FastAPI or LangServe, agents must operate non-blocking event loops. This necessitates the use of Python's asyncio framework and specific middleware hooks like abefore\_agent.

This report provides an exhaustive technical analysis of implementing asynchronous middleware within the LangGraph ecosystem, with a specific focus on the before\_agent and abefore\_agent hooks. It rigorously examines the underlying mechanisms of the Python event loop, the specific architectural patterns employed by libraries such as deepagents, and the pervasive issue of thread-based deadlocks that occur when integrating synchronous legacy code with asynchronous agent runtimes. Furthermore, it offers detailed troubleshooting strategies and proven design patterns to mitigate concurrency hazards in production environments.

### **1.1 From Linear Chains to Cyclic Graphs: The Architectural Necessity**

To understand the role of middleware, one must first appreciate the runtime environment it inhabits. Early LLM applications were constructed as Directed Acyclic Graphs (DAGs), or more commonly, simple linear chains. In these systems, data flowed unidirectionally from input to output. State was ephemeral, existing only for the duration of the request.

Agents, by definition, require loops. An agent must observe the environment, decide on an action, execute that action, observe the result, and then loop back to decide the next action. This cyclic requirement renders linear chain architectures insufficient. LangGraph solves this by modeling the agent as a state machine. The state is a persistent data structure (often a TypedDict or Pydantic model) that is passed between nodes. Each node receives the current state, performs a computation, and returns a state update. The runtime then determines the next node based on the graph topology and conditional edges.4

In this cyclic environment, "middleware" takes on a more complex role than in a linear web server. In a web server (e.g., Django or Express.js), middleware typically runs once per request (before the handler) and once per response (after the handler). In a LangGraph agent, the "request" might initiate a workflow that runs for minutes or hours, looping hundreds of times. Therefore, middleware hooks must be granular. We distinguish between "Agent-level" hooks, which run once per workflow invocation, and "Model-level" or "Step-level" hooks, which run on every iteration of the reasoning loop.5

### **1.2 The DeepAgents Reference Architecture**

The deepagents library serves as a primary reference implementation for advanced LangGraph middleware usage. It demonstrates a modular architecture where capabilities are injected into the agent via middleware rather than being hardcoded into the agent's prompt or tools.

For instance, deepagents uses FilesystemMiddleware to provide agents with a virtual file system. This is not merely a collection of tools; the middleware actively manages the agent's context window. If a tool execution (e.g., reading a large log file) returns a result that exceeds a token threshold, the middleware intercepts the result, writes it to the virtual file system, and returns a file reference to the model instead of the raw text. This logic is implemented via the awrap\_tool\_call hook. Similarly, SubAgentMiddleware manages the spawning of child agents, injecting the necessary system prompts and tools to facilitate delegation.6

These capabilities rely heavily on the before\_agent (or abefore\_agent) hook to initialize the environment—mounting the file system, loading user-specific configuration, or hydrating the state with long-term memory retrieval—before the agent begins its main execution loop.8

---

## **2\. The Python Asynchronous Runtime Model and Agent Concurrency**

To effectively implement abefore\_agent and troubleshoot the deadlocks frequently encountered in these systems, a deep theoretical understanding of Python's asynchronous runtime model is required. The challenges discussed in this report—specifically deadlocks involving run\_coroutine\_threadsafe—are rooted in the fundamental design of asyncio.

### **2.1 The Global Interpreter Lock (GIL) and Cooperative Multitasking**

Python (specifically CPython) employs a Global Interpreter Lock (GIL) that prevents multiple native threads from executing Python bytecodes simultaneously. While this simplifies memory management, it imposes severe limitations on CPU-bound concurrency. To achieve concurrency for I/O-bound tasks (like network requests to LLMs), Python utilizes asyncio, which implements cooperative multitasking on a single thread.

In this model, an **Event Loop** schedules and runs **Coroutines**. A coroutine is a function that can suspend its execution (yield control) to the event loop while waiting for an external event (like an I/O operation) to complete. When the event occurs, the loop resumes the coroutine.

The critical implication for LangGraph agents is that the entire agent workflow usually runs on a single thread (the Main Thread) inside a single event loop. If any piece of code blocks this thread—for example, by performing a synchronous HTTP request, a heavy regex calculation, or waiting on a thread lock—the entire agent freezes. No other tasks, including heartbeats, streaming responses, or other concurrent user requests, can proceed.9

### **2.2 The "Sync-Async Bridge" Problem**

A pervasive architectural challenge in modern AI engineering is the integration of legacy synchronous codebases with new asynchronous agent frameworks. Developers often find themselves in situations where:

1. They have a legacy library (e.g., a proprietary database client or a specialized simulation engine) that is blocking (synchronous).  
2. They are building a LangGraph agent that must be asynchronous to handle streaming and high concurrency.  
3. They need to call the async agent from the sync legacy code, or vice-versa.

This boundary is where deadlocks thrive. The mechanism asyncio.run\_coroutine\_threadsafe was designed to bridge this gap by allowing a synchronous thread to submit work to an asynchronous event loop running in a *different* thread.11 However, misusing this primitive by attempting to cross boundaries within the *same* thread, or by blocking the thread that the event loop requires, leads to the catastrophic "deadlock on same loop" scenario described in the research materials.11

### **2.3 Async Context Propagation**

Another layer of complexity is context propagation. Modern observability tools (like OpenTelemetry or LangSmith) and internal frameworks rely on contextvars to track execution traces across asynchronous boundaries. When an agent spawns a sub-task or offloads a job to a thread, this context must be explicitly propagated. Failure to do so results in "fragmented traces," where the child task's logs are disconnected from the parent request, making debugging impossible.14

Standard threading tools like concurrent.futures.ThreadPoolExecutor do not propagate context variables by default. In contrast, asyncio.to\_thread (introduced in Python 3.9) is specifically designed to handle this propagation automatically, making it the preferred primitive for integrating blocking code into LangGraph agents.15

---

## **3\. Anatomy of LangGraph Middleware: The AgentMiddleware Class**

The AgentMiddleware class provides the structural foundation for intercepting agent execution. It operates on a series of lifecycle hooks that wrap the agent's core processing steps. Understanding the precise signatures and execution order of these hooks is prerequisite to implementing robust state management.

### **3.1 The Hierarchy of Lifecycle Hooks**

The middleware architecture defines four primary interception points, each available in both synchronous and asynchronous variants. The distinction is crucial: using a synchronous hook in an async agent can degrade performance by blocking the loop, while using an async hook requires the runtime to support await at that specific injection point.8

| Lifecycle Stage | Synchronous Hook | Asynchronous Hook | Operational Scope | Typical Use Cases |
| :---- | :---- | :---- | :---- | :---- |
| **Initialization** | before\_agent | abefore\_agent | Runs once per workflow invocation. | State hydration, user authentication, loading long-term memory, dynamic tool selection. |
| **Pre-Reasoning** | before\_model | abefore\_model | Runs before every LLM call. | Prompt engineering, context trimming/summarization, injecting dynamic system instructions. |
| **Post-Reasoning** | after\_model | aafter\_model | Runs after every LLM call. | Logging, compliance scanning, PII redaction (output), human-in-the-loop triggers. |
| **Termination** | after\_agent | aafter\_agent | Runs once after workflow completion. | Cleanup, saving state to external storage, metrics aggregation. |
| **Interception** | wrap\_model\_call | awrap\_model\_call | Wraps the LLM invocation. | Retry logic, fallback models, rate limiting, low-level error handling. |
| **Interception** | wrap\_tool\_call | awrap\_tool\_call | Wraps tool execution. | Result caching, output truncation (filesystem offloading), validation of tool arguments. |

Table 1: Comprehensive definitions of LangGraph middleware hooks.5

### **3.2 The abefore\_agent Signature and Contract**

The abefore\_agent hook is the primary focus for initialization logic. Its signature is strictly defined to ensure compatibility with the LangGraph runtime.

**Method Signature:**

Python

async def abefore\_agent(  
    self,   
    state: AgentState,   
    runtime: Runtime  
) \-\> dict\[str, Any\] | None:  
   ...

* **state (AgentState):** A dictionary-like object representing the current snapshot of the agent's graph state. This typically includes the messages history and any custom keys defined in the StateGraph schema.16  
* **runtime (Runtime):** An object providing access to the execution context. This includes the RunnableConfig, which holds user-provided configuration, secrets, and callbacks.17  
* **Return Value:** The method expects a dict\[str, Any\] or None.  
  * If a dictionary is returned, it is treated as a state update. LangGraph merges this dictionary into the existing state before the first node executes. This is the mechanism for injecting data.  
  * If None is returned, execution proceeds without state modification.

### **3.3 Accessing Runtime Configuration (RunnableConfig)**

A frequent requirement for middleware is accessing configuration passed at runtime—for example, a user\_id for personalization or a thread\_id for memory retrieval. In LangChain and LangGraph, this is handled via RunnableConfig.

When an agent is invoked:

Python

agent.ainvoke(inputs, config={"configurable": {"user\_id": "123", "tier": "premium"}})

Inside abefore\_agent, this configuration is accessible via the runtime object. Research indicates that the Runtime object wraps the underlying config.19

**Access Pattern:**

Python

async def abefore\_agent(self, state: AgentState, runtime: Runtime) \-\> dict\[str, Any\] | None:  
    \# Accessing the 'configurable' dictionary  
    config \= runtime.config  
    user\_settings \= config.get("configurable", {})  
    user\_id \= user\_settings.get("user\_id")  
      
    if not user\_id:  
        raise ValueError("User ID required for this middleware")  
          
    \# Logic using user\_id...

This pattern enables multi-tenant middleware where behavior (like rate limits or available tools) changes dynamically based on the calling user.20

---

## **4\. Deep Dive: Implementing abefore\_agent for Asynchronous Initialization**

The abefore\_agent hook is the designated location for "Bootstrapping" the agent. In a stateless REST API, every request is fresh. In a stateful agent, the "request" might be the continuation of a conversation that started days ago, or it might require loading a massive amount of context (e.g., a user's entire email history) before the model can answer the first question. Doing this synchronously would destroy performance.

### **4.1 Pattern: Asynchronous State Hydration**

Consider an agent designed to answer questions about a user's documents stored in a vector database. We do not want to load *all* documents, nor do we want to query the database during the import of the Python module. We want to query the database strictly when the agent starts executing for a specific user.

Python

class ContextHydrationMiddleware(AgentMiddleware):  
    def \_\_init\_\_(self, vector\_store):  
        self.vector\_store \= vector\_store

    async def abefore\_agent(self, state: AgentState, runtime: Runtime) \-\> dict\[str, Any\] | None:  
        \# 1\. Extract context keys  
        user\_id \= runtime.config.get("configurable", {}).get("user\_id")  
          
        \# 2\. Asynchronous I/O call (Non-blocking)  
        \# This awaits the DB query without blocking the loop  
        relevant\_docs \= await self.vector\_store.asimilarity\_search(  
            state\["messages"\]\[-1\].content,   
            k=5,   
            filter\={"user\_id": user\_id}  
        )  
          
        \# 3\. Format into System Message  
        context\_str \= "\\n".join(\[d.page\_content for d in relevant\_docs\])  
        system\_msg \= SystemMessage(content=f"Context:\\n{context\_str}")  
          
        \# 4\. Inject into State  
        \# This appends the system message to the history before the model sees it  
        return {"messages": \[system\_msg\]}

This implementation allows the agent to appear "stateless" to the caller while dynamically hydrating itself with highly relevant, user-specific context in a non-blocking manner.

### **4.2 Pattern: Dynamic Tool Selection (The "Many Tools" Problem)**

In enterprise agents, the number of available tools often exceeds the context window of the LLM (or simply confuses it). Middleware can solve this via dynamic tool loading. Instead of binding 100 tools to the agent at creation time, the middleware uses abefore\_agent (or abefore\_model) to select a subset of tools based on the user's intent.22

The logic proceeds as follows:

1. **Intercept:** abefore\_agent receives the user's initial query.  
2. **Retrieve:** It queries a tool index (a lightweight vector store of tool descriptions).  
3. **Inject:** It updates the state or the runtime context to include only the schemas of the top 10 relevant tools.  
4. **Execute:** The model is invoked with a curated toolkit, reducing token costs and hallucination risks.

### **4.3 Handling NotImplementedError in Async Chains**

A critical finding from the research data is that certain built-in middleware classes in the LangChain ecosystem—specifically PlanningMiddleware, AnthropicPromptCachingMiddleware, and ModelFallbackMiddleware—may not yet fully support the async path. Using these in an async agent (via .ainvoke) can raise a NotImplementedError because the awrap\_model\_call or abefore\_agent methods are missing.23

Mitigation Strategy:  
Developers faced with this must implement a subclass that bridges the gap.

Python

class AsyncPlanningMiddleware(PlanningMiddleware):  
    async def abefore\_agent(self, state, runtime):  
        \# Implementation required if the base class lacks it  
        return await super().abefore\_agent(state, runtime)   
        \# Or provide custom async implementation

If the upstream middleware is purely synchronous and CPU-bound, one might use asyncio.to\_thread to wrap the synchronous parent method, though native async re-implementation is always preferred for performance.

---

## **5\. Concurrency Perils: Troubleshooting Deadlocks in Mixed Sync/Async Environments**

The most significant operational risk identified in the research regarding before\_agent and async support is the potential for deadlocks. These occur when integrating the asynchronous agent runtime with synchronous code patterns. This section provides a forensic analysis of the run\_coroutine\_threadsafe deadlock mechanism and definitive patterns to avoid it.

### **5.1 The Mechanics of the "Same-Loop" Deadlock**

The function asyncio.run\_coroutine\_threadsafe(coro, loop) is often misunderstood. It returns a concurrent.futures.Future. To get the result of the coroutine, synchronous code typically calls future.result().

**The Fatal Sequence:**

1. **Context:** The application is running an asyncio event loop on the Main Thread (e.g., inside a FastAPI request or a LangGraph .ainvoke).  
2. **Call Stack:** An async node calls a synchronous function (perhaps a legacy validation library).  
3. **Recursion:** The synchronous function needs to run a sub-component that happens to be async. It grabs the current event loop (asyncio.get\_running\_loop()).  
4. **Submission:** It calls asyncio.run\_coroutine\_threadsafe(sub\_task(), loop). This successfully schedules the task on the loop.  
5. **The Block:** The synchronous function calls future.result() to wait for the answer.  
6. **The Deadlock:** future.result() blocks the Main Thread. The Event Loop *is* the Main Thread. The Event Loop cannot run the sub\_task because the thread is blocked waiting for the result. The task never starts, the result never arrives, and the thread hangs indefinitely.11

This is a classic circular dependency: The thread is waiting for the loop, but the loop needs the thread.

### **5.2 Solution Pattern A: The Dedicated Background Thread**

To safely use run\_coroutine\_threadsafe, the target event loop must be running on a *different* thread than the one calling .result().

Implementation:  
Create a dedicated thread responsible solely for running a "sidecar" event loop.

Python

import threading  
import asyncio

\# Global reference to the background loop  
background\_loop \= None

def start\_background\_loop():  
    global background\_loop  
    background\_loop \= asyncio.new\_event\_loop()  
    asyncio.set\_event\_loop(background\_loop)  
    background\_loop.run\_forever()

\# Start it once at app startup  
t \= threading.Thread(target=start\_background\_loop, daemon=True)  
t.start()

\# Usage inside a synchronous middleware method  
def safe\_sync\_call():  
    future \= asyncio.run\_coroutine\_threadsafe(async\_task(), background\_loop)  
    return future.result()  \# Safe: Main thread blocks, background thread runs the task

This pattern decouples the blocking wait from the execution resources.24

### **5.3 Solution Pattern B: asyncio.to\_thread (The Modern Standard)**

For the inverse problem—calling blocking sync code from within an async middleware hook like abefore\_agent—the robust solution is asyncio.to\_thread. This function runs the synchronous code in a separate thread (using a ThreadPoolExecutor) and returns a coroutine that can be awaited. Crucially, it handles contextvars propagation, ensuring that tracing IDs and auth tokens stored in context variables are available to the synchronous code (if it supports them).15

**Correct Implementation in Middleware:**

Python

async def abefore\_agent(self, state, runtime):  
    \# BAD: Blocks the loop  
    \# result \= my\_heavy\_sync\_function(state)   
      
    \# GOOD: Yields control, runs in thread pool  
    result \= await asyncio.to\_thread(my\_heavy\_sync\_function, state)  
      
    return {"processed\_data": result}

### **5.4 Anti-Pattern Warning: nest\_asyncio**

The library nest\_asyncio patches the event loop to allow re-entrancy (calling run\_until\_complete from within a running loop). While frequently used in Jupyter notebooks to allow async code to run, relying on it for production middleware is discouraged. It alters the fundamental behavior of the event loop and can lead to unpredictable behavior with signal handlers, connection pools, and third-party async libraries (like aiohttp or asyncpg) that assume standard loop behavior.9

---

## **6\. Case Study: Middleware in the deepagents Library**

The deepagents library provides a production-grade example of how these patterns come together. It is built entirely on the LangGraph/LangChain middleware foundation.

### **6.1 FilesystemMiddleware**

This middleware provides persistence and context management.

* **Initialization (abefore\_agent):** It checks if the agent is resuming a session. If so, it asynchronously loads the virtual filesystem state from the backend (e.g., S3 or Postgres) into memory. This ensures that when the model calls read\_file, the data is available.  
* **Output Interception (awrap\_tool\_call):** This is a critical optimization. If a tool returns 50,000 tokens of text (e.g., cat big\_data.csv), passing this to the LLM would crash the context window or cost a fortune. The middleware intercepts this *asynchronously*, writes it to a file, and returns File saved to /tmp/big\_data.csv. Use read\_file with pagination to view. This logic encapsulates the "Deep Agent" philosophy: smart context management via middleware.7

### **6.2 SubAgentMiddleware**

This middleware enables hierarchical planning.

* **Mechanism:** It injects a specialized task tool. When the main agent calls this tool, the middleware intercepts the call.  
* **Delegation:** It spawns a *new* LangGraph instance (the sub-agent) with a restricted context and a specific goal.  
* **Concurrency:** The sub-agent runs asynchronously. The main agent's awrap\_tool\_call awaits the sub-agent's completion. This allows for parallel execution if the main agent were to spawn multiple sub-agents simultaneously (using asyncio.gather), although standard sequential reasoning usually implies serial execution.3

---

## **7\. Advanced Integration: Security, Auth, and MCP**

Middleware is the primary enforcement point for security boundaries in agentic systems.

### **7.1 User Authentication and configurable Secrets**

In a deployed LangGraph Platform environment, authentication is often handled at the edge, but the *user identity* is passed down. The abefore\_agent hook is the standard place to enforce logic based on this identity.

**Secure Token Handling Pattern:**

1. **Pass Token:** The API client passes an auth token in the headers. LangGraph maps this to config\["configurable"\]\["auth\_token"\].  
2. **Verify (Async):** In abefore\_agent, the middleware calls the identity provider's /userinfo endpoint using the token.  
3. **Scope:** The middleware determines the user's scope (e.g., "What rows in the DB can they see?").  
4. **Inject:** It writes a SecurityContext object into the agent state.  
5. **Enforce:** Subsequent tool calls check this SecurityContext before executing SQL queries.27

### **7.2 Model Context Protocol (MCP) Integration**

The Model Context Protocol (MCP) creates a standard way for agents to connect to data sources and tools. Middleware acts as the bridge (or "Adapter") between LangGraph and MCP servers.

An MCPMiddleware can be implemented to:

* **Connect:** In abefore\_agent, establish an async SSE (Server-Sent Events) connection to an MCP server (e.g., a GitHub MCP server).  
* **Discover:** Asynchronously fetch the list of available tools from the server.  
* **Bind:** Dynamically bind these tools to the model for the duration of the run.  
* **Cleanup:** In aafter\_agent, close the connection.

This highlights the necessity of async hooks; connecting to remote MCP servers via SSE is an inherently asynchronous operation that would freeze a synchronous agent.28

---

## **8\. Conclusion**

The transition to asynchronous, graph-based agents represents a maturation of the generative AI engineering stack. LangGraph provides the necessary primitives—cyclic graphs, state persistence, and granular control flow—but it is the Middleware layer that operationalizes these agents for production.

The implementation of abefore\_agent and its sibling hooks allows developers to decouple infrastructure concerns (auth, persistence, observability) from reasoning logic. However, this power comes with the responsibility of managing Python's concurrency model correctly. The risk of deadlocks in mixed sync/async environments is non-trivial and requires disciplined adherence to patterns like asyncio.to\_thread for blocking code and isolated event loop threads for bridging legacy systems.

By adopting these patterns and leveraging the architectural blueprints provided by libraries like deepagents, organizations can build agentic systems that are not only intelligent but also scalable, secure, and robust enough for mission-critical deployment.

---

## **9\. Appendix: Summary of Troubleshooting Strategies**

| Symptom | Root Cause | Diagnosis Method | Remediation |
| :---- | :---- | :---- | :---- |
| **Agent Hangs Indefinitely** | Deadlock: Sync code awaiting async result on the same loop. | Check call stack for future.result() inside a callback running on MainThread. | Offload sync code to asyncio.to\_thread, or use a dedicated background thread loop for run\_coroutine\_threadsafe. |
| **"Event loop is closed"** | Attempting to schedule tasks on a loop that has been stopped or garbage collected. | Logs show RuntimeError: Event loop is closed. | Ensure background loops are created with run\_forever and managed globally or via robust lifecycle managers. |
| **Missing Traces/Logs** | Context variables not propagating to worker threads. | Distributed tracing shows broken spans or missing parent IDs. | Use asyncio.to\_thread (which supports context propagation) instead of raw ThreadPoolExecutor. |
| **High Latency / Heartbeat Failure** | Blocking the event loop with CPU-intensive sync code. | asyncio debug mode shows "loop blocked for X seconds". | Move CPU-bound work (regex, data processing) to ProcessPoolExecutor. |
| **NotImplementedError** | Middleware class lacks async hook implementation. | Exception raised during .ainvoke(). | Subclass the middleware and implement the missing abefore\_agent or awrap\_... method using super() or custom logic. |

*Table 2: Diagnostic matrix for asynchronous agent middleware issues.*

#### **Works cited**

1. LangGraph Custom Agent. Introduction | by Seahorse \- Medium, accessed on November 28, 2025, [https://medium.com/@seahorse.technologies.sl/langgraph-custom-agent-848ec348e270](https://medium.com/@seahorse.technologies.sl/langgraph-custom-agent-848ec348e270)  
2. Unlocking the Power of LangChain Agent Middleware | by DhanushKumar \- Stackademic, accessed on November 28, 2025, [https://blog.stackademic.com/unlocking-the-power-of-langchain-agent-middleware-f6fb61d6bf99](https://blog.stackademic.com/unlocking-the-power-of-langchain-agent-middleware-f6fb61d6bf99)  
3. Building Production-Ready Deep Agents with LangChain 1.0 | by Debal B \- Medium, accessed on November 28, 2025, [https://medium.com/data-science-collective/building-deep-agents-with-langchain-1-0s-middleware-architecture-7fdbb3e47123](https://medium.com/data-science-collective/building-deep-agents-with-langchain-1-0s-middleware-architecture-7fdbb3e47123)  
4. How to use Langchain v1.x middleware in langgraph?, accessed on November 28, 2025, [https://forum.langchain.com/t/how-to-use-langchain-v1-x-middleware-in-langgraph/2058](https://forum.langchain.com/t/how-to-use-langchain-v1-x-middleware-in-langgraph/2058)  
5. Middleware | LangChain Reference, accessed on November 28, 2025, [https://reference.langchain.com/python/langchain/middleware/](https://reference.langchain.com/python/langchain/middleware/)  
6. deepagents \- PyPI, accessed on November 28, 2025, [https://pypi.org/project/deepagents/](https://pypi.org/project/deepagents/)  
7. langchain-ai/deepagents-quickstarts \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/deepagents-quickstarts](https://github.com/langchain-ai/deepagents-quickstarts)  
8. Deep Agents overview | LangChain Reference, accessed on November 28, 2025, [https://reference.langchain.com/python/deepagents/](https://reference.langchain.com/python/deepagents/)  
9. LangGraph Workflows Part 2: Asynchronous State Management with Snowflake Checkpointing | by Siva Krishna Yetukuri | Medium, accessed on November 28, 2025, [https://medium.com/@siva\_yetukuri/langgraph-workflows-part-2-asynchronous-state-management-with-snowflake-checkpointing-76648a1e35af](https://medium.com/@siva_yetukuri/langgraph-workflows-part-2-asynchronous-state-management-with-snowflake-checkpointing-76648a1e35af)  
10. calling sync functions from async function \- python \- Stack Overflow, accessed on November 28, 2025, [https://stackoverflow.com/questions/54685210/calling-sync-functions-from-async-function](https://stackoverflow.com/questions/54685210/calling-sync-functions-from-async-function)  
11. How to call an async function from a child thread using asyncio.run\_coroutine\_threadsafe() and the main thread's loop? \- Stack Overflow, accessed on November 28, 2025, [https://stackoverflow.com/questions/79041942/how-to-call-an-async-function-from-a-child-thread-using-asyncio-run-coroutine-th](https://stackoverflow.com/questions/79041942/how-to-call-an-async-function-from-a-child-thread-using-asyncio-run-coroutine-th)  
12. Developing with asyncio — Python 3.14.0 documentation, accessed on November 28, 2025, [https://docs.python.org/3/library/asyncio-dev.html](https://docs.python.org/3/library/asyncio-dev.html)  
13. Compose futures in Python (asyncio) \- Stack Overflow, accessed on November 28, 2025, [https://stackoverflow.com/questions/51254050/compose-futures-in-python-asyncio](https://stackoverflow.com/questions/51254050/compose-futures-in-python-asyncio)  
14. Troubleshooting LangChain/LangGraph Traces: Common Issues and Fixes | Last9, accessed on November 28, 2025, [https://last9.io/blog/troubleshooting-langchain-langgraph-traces-issues-and-fixes/](https://last9.io/blog/troubleshooting-langchain-langgraph-traces-issues-and-fixes/)  
15. Coroutines and Tasks — Python 3.14.0 documentation, accessed on November 28, 2025, [https://docs.python.org/3/library/asyncio-task.html](https://docs.python.org/3/library/asyncio-task.html)  
16. 2万字一文读懂LangChain 1.0：智能体（Agent）的核心组件 \- 稀土掘金, accessed on November 28, 2025, [https://juejin.cn/post/7570247858869485620](https://juejin.cn/post/7570247858869485620)  
17. LangChain1.0の気になるトピックをDatabricks Free Editionで検証：ミドルウェアのカスタム \- Qiita, accessed on November 28, 2025, [https://qiita.com/isanakamishiro2/items/da88b297b7473f3ea8ae](https://qiita.com/isanakamishiro2/items/da88b297b7473f3ea8ae)  
18. Runnables (Classic) | LangChain Reference, accessed on November 28, 2025, [https://reference.langchain.com/python/langchain\_classic/runnables/](https://reference.langchain.com/python/langchain_classic/runnables/)  
19. How to retrieve the current conversation ID inside a tool function in LangGraph?, accessed on November 28, 2025, [https://forum.langchain.com/t/how-to-retrieve-the-current-conversation-id-inside-a-tool-function-in-langgraph/1448](https://forum.langchain.com/t/how-to-retrieve-the-current-conversation-id-inside-a-tool-function-in-langgraph/1448)  
20. \`middleware\` and Custom \`state\_schema\` are mutually exclusive in \`create\_agent()\` · Issue \#33217 · langchain-ai/langchain \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain/issues/33217](https://github.com/langchain-ai/langchain/issues/33217)  
21. Configurable headers \- Docs by LangChain, accessed on November 28, 2025, [https://docs.langchain.com/langsmith/configurable-headers](https://docs.langchain.com/langsmith/configurable-headers)  
22. How to handle large numbers of tools \- GitHub Pages, accessed on November 28, 2025, [https://langchain-ai.github.io/langgraph/how-tos/many-tools/](https://langchain-ai.github.io/langgraph/how-tos/many-tools/)  
23. AgentMiddleware lacks async support \- NotImplementedError in awrap\_model\_call for some built-in middleware (1.0.0a14) · Issue \#33474 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain/issues/33474](https://github.com/langchain-ai/langchain/issues/33474)  
24. Running async code from sync code in Python \- death and gravity, accessed on November 28, 2025, [https://death.andgravity.com/asyncio-bridge](https://death.andgravity.com/asyncio-bridge)  
25. python asyncio, how to create and cancel tasks from another thread \- Stack Overflow, accessed on November 28, 2025, [https://stackoverflow.com/questions/29296064/python-asyncio-how-to-create-and-cancel-tasks-from-another-thread](https://stackoverflow.com/questions/29296064/python-asyncio-how-to-create-and-cancel-tasks-from-another-thread)  
26. Streaming deepagents and task delegation with real-time output | by Dogukan Tuna, accessed on November 28, 2025, [https://medium.com/@dtunai/streaming-deepagents-and-task-delegation-with-real-time-output-023e9ec049ba](https://medium.com/@dtunai/streaming-deepagents-and-task-delegation-with-real-time-output-023e9ec049ba)  
27. Authentication & access control \- Docs by LangChain, accessed on November 28, 2025, [https://docs.langchain.com/langgraph-platform/auth](https://docs.langchain.com/langgraph-platform/auth)  
28. LangGraph MCP: Building Powerful Agents with MCP Integration \- Leanware, accessed on November 28, 2025, [https://www.leanware.co/insights/langgraph-mcp-building-powerful-agents-with-mcp-integration](https://www.leanware.co/insights/langgraph-mcp-building-powerful-agents-with-mcp-integration)  
29. The Complete Guide to Building AI Agents with MCP: LangGraph, Azure Functions, and Confluent Kafka in Action \- Leandro Calado, accessed on November 28, 2025, [https://leandrocaladoferreira.medium.com/the-complete-guide-to-building-ai-agents-with-mcp-langgraph-azure-functions-and-confluent-kafka-ceebcb983076](https://leandrocaladoferreira.medium.com/the-complete-guide-to-building-ai-agents-with-mcp-langgraph-azure-functions-and-confluent-kafka-ceebcb983076)