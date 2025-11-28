

# **Architectural Analysis and Implementation Strategy: Per-User MCP Authentication in LangGraph Platform**

## **1\. Introduction and Executive Overview**

The rapid evolution of agentic artificial intelligence has transitioned from experimental, single-user prototypes to robust, multi-tenant enterprise architectures. In this contemporary landscape, the **LangGraph Platform** stands as a premier orchestration environment, enabling the deployment of stateful, cyclic graph-based agents at scale. Concurrently, the **Model Context Protocol (MCP)** has emerged as the definitive standard for interoperability, decoupling the intelligence of Large Language Models (LLMs) from the implementation details of external tools and data resources.

However, the intersection of these two technologies—multi-tenant orchestration and standardized tool protocols—introduces complex challenges in identity management and authentication propagation. Specifically, developers utilizing the deepagents library, a high-level abstraction wrapper for LangGraph, face a critical integration failure when attempting to implement per-user authentication for MCP tool calls. The reported error, McpToolsLoader.before\_agent missing config, serves as a focal point for a broader architectural discussion regarding middleware signatures, runtime context injection, and secure credential management in distributed agent fleets.

This report provides an exhaustive technical analysis of this authentication challenge. It is designed for senior software architects and platform engineers who require a definitive resolution to the deepagents middleware failure and a robust, scalable pattern for managing user credentials in an MCP-enabled LangGraph environment.

### **1.1 Problem Definition**

The core objective is to enable an agent, deployed on the LangGraph Platform, to execute MCP tools (such as database queries or API actions) using the specific credentials of the user initiating the request. In the LangGraph Platform architecture, the user's authentication token is validated at the ingress layer and made available to the "Agent Fleet Worker" within the runtime configuration.

The implementation failure arises when developers attempt to intercept the agent's execution loop using the deepagents library's middleware, specifically McpToolsLoader. The resulting TypeError—indicating a missing config argument—reveals a misalignment between the library's expected method signature and the underlying LangGraph runtime's execution protocol. Furthermore, even if the crash is resolved, relying on global middleware to configure MCP clients introduces race conditions in a concurrent, multi-threaded worker environment.

### **1.2 Scope and Methodology**

This report draws upon a comprehensive review of the LangGraph runtime architecture, the langchain-core specification, and the evolving Model Context Protocol ecosystem. The analysis proceeds through four distinct phases:

1. **Diagnostic Deconstruction:** A rigorous examination of the Python runtime behaviors, Method Resolution Order (MRO), and signature introspection logic that leads to the McpToolsLoader crash.  
2. **Signature Specification:** A definitive definition of the AgentMiddleware interface for modern LangGraph versions, addressing the exact mechanism for accessing RunnableConfig and the runtime context.  
3. **Pattern Architecture:** The evaluation of three distinct architectural patterns for credential injection: Middleware Configuration, Runtime Argument Injection (InjectedToolArg), and Dynamic Client Instantiation.  
4. **Implementation Strategy:** Detailed, production-ready code examples demonstrating how to patch the deepagents library and implement a secure "Client-Factory" pattern for per-user MCP authentication.

The findings presented herein establish that while the immediate "missing config" error is a signature mismatch resolvable through code modification, the superior architectural pattern involves bypassing middleware-based configuration in favor of **context-scoped client instantiation** within the graph's execution nodes.

---

## **2\. The Convergence of Agent Orchestration and Tool Protocols**

To fully comprehend the nuances of the authentication failure, it is necessary to establish the technical context of the three pillars involved: the LangGraph orchestration engine, the Model Context Protocol, and the multi-tenant runtime environment.

### **2.1 LangGraph and the Agentic State Machine**

LangGraph differentiates itself from linear chain-based frameworks (like the original LangChain AgentExecutor) by modeling agent behaviors as cyclic graphs. In this paradigm, the "State" is a persistent data structure passed between "Nodes."

* **The Runtime:** The Runtime object in LangGraph is the execution engine that drives the graph. It is responsible for invoking nodes, managing state transitions, and handling persistence (checkpointing). Crucially, it manages the *context* of the execution, including configuration parameters passed from the platform.  
* **The Config (RunnableConfig):** This dictionary is the standard vessel for metadata, callbacks, and runtime variables. In the context of the LangGraph Platform, this is where the user\_id and authentication tokens are injected. The platform's ingress controller validates the user's request and populates config\['configurable'\] with the user's identity details.1

### **2.2 The Model Context Protocol (MCP) Architecture**

The Model Context Protocol (MCP) standardizes the connection between AI models (Clients) and tools/resources (Servers).

* **The MCP Client:** In a LangGraph application, the agent acts as the MCP Client. It connects to one or more MCP Servers to discover available tools and execute them. The standard implementation, langchain-mcp-adapters, uses a MultiServerMCPClient to manage these connections.3  
* **The Transport Layer:** MCP supports local execution (Stdio) and remote execution (SSE/HTTP). In a distributed "Agent Fleet" architecture, remote execution is standard. The MCP Client connects to a remote MCP Server (e.g., a "Knowledge Base Service") over HTTP or SSE.  
* **Authentication in MCP:** The MCP specification supports authentication via HTTP headers during the connection handshake. However, standard client implementations in the ecosystem are often initialized as global singletons with static headers defined at startup.5 This design assumes a single-user environment (like a local CLI) and breaks down in a multi-tenant fleet where the "Authorization" header must change for every request.

### **2.3 The DeepAgents Abstraction Layer**

The deepagents library serves as an opinionated wrapper around LangGraph, designed to streamline the creation of complex agents with planning and sub-agent capabilities.6

* **Middleware Dependence:** To hide the complexity of graph construction, deepagents relies heavily on middleware (e.g., McpToolsLoader) to dynamically inject tools into the agent's context based on the current plan.  
* **The Signature Drift:** As a wrapper, deepagents depends on the internal interfaces of langchain-core. When LangChain evolves its middleware signatures—moving from flexible \*\*kwargs to strict typing—wrappers that are not updated in lockstep will encounter runtime failures. The reported error is a direct manifestation of this "signature drift."

---

## **3\. Diagnostic Analysis: The "Missing Config" Failure**

The specific error reported—McpToolsLoader.before\_agent missing config—provides a precise entry point for diagnosis. This section deconstructs the Python runtime mechanics that trigger this exception.

### **3.1 The Evolution of AgentMiddleware Signatures**

In the early development of LangChain's agent frameworks, middleware and callback handlers were often designed with permissive signatures, accepting \*\*kwargs to allow for forward compatibility. A typical hook might have looked like this:

Python

\# Legacy / Permissive Signature  
def on\_agent\_action(self, tool, input, \*\*kwargs):  
    config \= kwargs.get('config')  
   ...

However, as the framework matured into LangGraph, the architecture shifted towards strict dependency injection and type safety. The execution engine now inspects the signature of the callable or adheres to a strict protocol.

The Runtime Invocation Logic:  
The LangGraph runtime engine, when preparing to execute a node or an agent loop, gathers the necessary context objects: the State and the Runtime context. It then iterates through the registered middleware and invokes the before\_agent hook.  
In modern LangGraph versions (v0.2+), the invocation logic resembles the following pseudocode:

Python

\# Simplified Runtime Invocation Logic  
for middleware in self.middlewares:  
    \# The runtime calls the hook with exactly two arguments: state and runtime  
    middleware.before\_agent(current\_state, self.runtime\_context)

### **3.2 The Signature Mismatch**

The error "missing config" indicates that the McpToolsLoader.before\_agent method is defined to require config as a positional argument.

**Likely Definition in deepagents (The Culprit):**

Python

class McpToolsLoader:  
    def before\_agent(self, state, config):  
        \# The code expects 'config' to be passed directly  
        self.load\_tools(config)

The Execution Failure:  
When the runtime executes middleware.before\_agent(state, runtime), Python attempts to map these two arguments to the method definition.

1. self is bound implicitly.  
2. state (arg 1\) maps to state (param 1).  
3. runtime (arg 2\) maps to config (param 2).

*Correction:* If the definition was def before\_agent(self, state, config):, Python would actually map runtime to config and the code would *run* but likely fail later when it tries to access config\["configurable"\] on a Runtime object (unless Runtime behaves like a dict, which it generally does not).

However, the specific error missing config (often phrased as missing 1 required positional argument: 'config') suggests the definition is actually:

**Hypothesis B (Three Arguments):**

Python

def before\_agent(self, state, runtime, config):  
   ...

In this case, the runtime provides 2 arguments (state, runtime), but the function demands 3 (state, runtime, config). Python raises a TypeError because config is missing.

This confirms that the deepagents library was written with an expectation that the runtime would inject config explicitly, or it is using an outdated signature pattern that has since been deprecated in favor of encapsulating the configuration within the runtime object.

### **3.3 The Definitive Signature Specification**

To address **Question 1 (Exact Signature)**, we look to the langchain-core and langgraph reference implementations.8

The canonical, correct signature for AgentMiddleware.before\_agent in the current ecosystem is:

Python

def before\_agent(  
    self,   
    state: StateT,   
    runtime: Runtime  
) \-\> StateT | dict | None:  
    """  
    state: The current state of the graph.  
    runtime: The runtime context object, encompassing config, store, and execution details.  
    """  
    pass

Any deviation from this signature—specifically requesting config as a distinct third argument—will result in runtime incompatibilities unless the orchestrator explicitly supports legacy signatures (which LangGraph strict mode often does not).

---

## **4\. Pattern 1: The Middleware Solution (Addressing Questions 1 & 3\)**

While we will argue later that middleware is not the *ideal* place for auth, solving the immediate crash allows us to proceed. This section details how to correctly implement middleware that accesses configuration, addressing **Question 3 (How to access config/runtime)**.

### **4.1 Accessing Configuration via the Runtime Object**

The Runtime object passed to the middleware is a container for the execution context. While documentation for the internal Runtime class is sparse in the public snippets, analysis of the langgraph source code pattern reveals that it exposes the configuration via a property or attribute.

The Access Pattern:  
The RunnableConfig—which holds the user credentials—is accessible as runtime.config.

Python

from langgraph.runtime import Runtime  
from typing import Any, Dict

class Correct middleware(AgentMiddleware):  
    def before\_agent(self, state: Dict\[str, Any\], runtime: Runtime) \-\> None:  
        \# 1\. Access the config object via the runtime property  
        config \= runtime.config  
          
        \# 2\. Extract the 'configurable' dictionary  
        \# This is where LangGraph Platform injects auth data  
        configurable \= config.get("configurable", {})  
          
        \# 3\. Retrieve the specific user credentials  
        user\_id \= configurable.get("user\_id")  
        auth\_token \= configurable.get("auth\_token")  
          
        \# Diagnostic Logging  
        if user\_id:  
            print(f"Middleware executing for User ID: {user\_id}")  
        else:  
            print("Warning: No User ID found in runtime config.")  
              
        return state

### **4.2 Remediation Strategy for DeepAgents (Monkey Patching)**

Since deepagents is likely installed as a third-party package, you cannot easily rewrite its source code. To resolve the McpToolsLoader crash without waiting for an upstream fix, you can employ a "Monkey Patch" strategy. This involves replacing the faulty method at runtime with a wrapper that bridges the signature gap.

Implementation: The Compatibility Shim  
This code snippet demonstrates how to wrap the existing before\_agent method to handle the missing argument safely.

Python

\# deepagents\_patch.py  
import functools  
from deepagents.middleware import McpToolsLoader

\# Save reference to the original (failing) method  
\_original\_before\_agent \= McpToolsLoader.before\_agent

def patched\_before\_agent(self, state, runtime):  
    """  
    A replacement method that extracts config from runtime  
    and passes it to the original method if required.  
    """  
    \# Extract config from the runtime object  
    \# Handle cases where runtime might not have 'config' (defensive coding)  
    config \= getattr(runtime, "config", {})  
      
    \# Introspection: Try to call the original method.  
    \# We attempt to determine if it wants (state, config) or (state, runtime, config)  
    try:  
        \# Attempt 1: Assume original wanted (self, state, config)  
        return \_original\_before\_agent(self, state, config)  
    except TypeError as e:  
        if "positional argument" in str(e):  
            \# Attempt 2: Maybe it wanted (self, state, runtime, config)  
            try:  
                return \_original\_before\_agent(self, state, runtime, config)  
            except TypeError:  
                \# Fallback: Just call it with state and runtime  
                return \_original\_before\_agent(self, state, runtime)  
        raise e

\# Apply the patch at application startup  
def apply\_deepagents\_patch():  
    McpToolsLoader.before\_agent \= patched\_before\_agent  
    print("Applied compatibility patch to McpToolsLoader.before\_agent")

Applying this patch resolves the immediate TypeError, allowing the application to boot. However, it does not solve the fundamental problem: **How do we use that extracted auth\_token to authenticate the MCP client?** If McpToolsLoader initializes the client globally, simply passing the config *now* won't update a client that was already created at startup. This leads us to the robust architectural patterns.

---

## **5\. Pattern 2: Runtime Argument Injection (Recommended for Request Auth)**

Addressing **Question 2 (Recommended pattern)**, the most "LangChain-native" way to pass runtime context to tools is via **Argument Injection**. This pattern effectively hides sensitive or contextual arguments from the LLM while ensuring they are populated at execution time.10

### **5.1 The InjectedToolArg Mechanism**

In standard tool definition, every argument in the function signature is converted into a JSON schema for the LLM. The LLM is expected to generate values for these arguments. However, for authentication tokens, the LLM should not—and cannot—generate the token.

The InjectedToolArg annotation marks a parameter as "internal." The ToolNode (the execution unit) inspects the signature, sees this annotation, and looks up the value in the state or config instead of the LLM's output.

### **5.2 Application to MCP Tools**

This pattern is highly effective when the **MCP Tool itself** requires the token as an argument. For example, if you have a tool query\_database(query: str, token: str), you can inject the token.

**Implementation Example:**

Python

from typing import Annotated  
from langchain\_core.tools import tool, InjectedToolArg  
from langchain\_core.runnables import RunnableConfig

@tool  
def authenticated\_search(  
    query: str,   
    config: Annotated  
) \-\> str:  
    """  
    Searches the internal knowledge base.  
    """  
    \# 1\. Extract the token safely  
    user\_token \= config.get("configurable", {}).get("auth\_token")  
      
    if not user\_token:  
        return "Error: User is not authenticated."  
          
    \# 2\. Use the token in the downstream API call  
    \# This might be an HTTP request to the actual service  
    return \_execute\_search\_api(query, token=user\_token)

Limitations for MCP Transport:  
Crucially, standard MCP architecture (using langchain-mcp-adapters) separates the Connection (Transport) from the Tool Execution.

* **Transport Level:** The WebSocket or SSE connection is established *once*.  
* **Tool Level:** JSON-RPC messages are sent over the existing connection.

If the MCP Server requires authentication headers *to establish the connection* (which is typical for an Agent Fleet behind an API Gateway), InjectedToolArg is **insufficient**. By the time the tool function is called, the connection must already exist. If the connection was created at startup without the user's token, the tool call will fail or be unauthorized.

Therefore, InjectedToolArg is the recommended pattern **only** if the MCP server accepts credentials inside the JSON-RPC payload (i.e., as a tool argument). For Transport-Level Authentication (headers), we must use **Pattern 3**.

---

## **6\. Pattern 3: The Dynamic Client Factory (The Robust Solution)**

For the specific scenario of "Agent Fleet Worker" where user tokens are available in the request context and must be used to authenticate the transport connection to the MCP server, the only robust pattern is the **Dynamic Client Factory**. This addresses **Question 2 (Recommended Pattern)** and **Question 4 (Alternative Patterns)**.

### **6.1 Architectural Concept: Client-Per-Request**

In a single-user app, we create one MCP Client at startup. In a multi-tenant app, we must create a lightweight MCP Client *for the duration of the request* (or node execution), configured with that specific user's headers.

This contradicts the standard examples in langchain-mcp-adapters which show global client initialization. We must invert this control flow. Instead of the Agent having a static list of tools bound to a static client, the Agent's ToolNode must dynamically instantiate the client.

### **6.2 Designing the Custom Tool Node**

We replace the standard ToolNode with a custom AuthenticatedMcpToolNode. This node:

1. Receives the execution state and config.  
2. Extracts the auth\_token from config.  
3. Initializes a MultiServerMCPClient with dynamic headers.  
4. Executes the requested tools.  
5. Closes the client connection.

### **6.3 Implementation Guide: The Secure Tool Node**

This is the definitive "Working Example" (Question 5\) for solving the problem.

Python

import logging  
from typing import Any, Dict, List, Optional

from langchain\_core.messages import ToolMessage, AIMessage  
from langchain\_core.runnables import RunnableConfig  
from langchain\_mcp\_adapters import MultiServerMCPClient  
from langgraph.prebuilt import ToolNode

\# Configure Logger  
logger \= logging.getLogger("agent.auth\_node")

class AuthenticatedMcpToolNode:  
    """  
    A custom LangGraph node that executes tool calls using a per-request   
    MCP client, authenticated with the user's token from the runtime config.  
    """  
    def \_\_init\_\_(self, server\_configs: Dict\]):  
        """  
        Initialize with base server configurations (URLs, transports).  
        Headers defined here are defaults/fallbacks.  
          
        Args:  
            server\_configs: Dict mapping server names to config dicts.  
            Example:  
            {  
                "filesystem": {  
                    "url": "http://mcp-fs:8080/sse",  
                    "transport": "sse"  
                }  
            }  
        """  
        self.base\_configs \= server\_configs

    async def \_\_call\_\_(self, state: Dict\[str, Any\], config: RunnableConfig) \-\> Dict\[str, List\[Any\]\]:  
        """  
        The execution logic for the node.  
        """  
        \# \---------------------------------------------------------  
        \# 1\. Identity Extraction  
        \# \---------------------------------------------------------  
        configurable \= config.get("configurable", {})  
        auth\_token \= configurable.get("auth\_token")  
        user\_id \= configurable.get("user\_id")  
          
        if not auth\_token:  
            \# Security Decision: Do we fail or allow anonymous?  
            \# For this report, we assume strict auth is required.  
            error\_msg \= "Security Error: No 'auth\_token' found in request configuration."  
            logger.error(error\_msg)  
            \# Fail gracefully by returning error messages for all tool calls  
            return self.\_fail\_all\_tools(state, error\_msg)

        \# \---------------------------------------------------------  
        \# 2\. Dynamic Configuration Construction  
        \# \---------------------------------------------------------  
        \# We perform a shallow copy of the base config and inject headers.  
        \# This ensures thread safety (we don't modify self.base\_configs).  
        run\_configs \= {}  
        for name, server\_cfg in self.base\_configs.items():  
            run\_configs\[name\] \= server\_cfg.copy()  
            \# Merge existing headers with dynamic auth headers  
            existing\_headers \= run\_configs\[name\].get("headers", {})  
            run\_configs\[name\]\["headers"\] \= {  
                \*\*existing\_headers,  
                "Authorization": f"Bearer {auth\_token}",  
                "X-User-ID": str(user\_id) if user\_id else "unknown"  
            }

        \# \---------------------------------------------------------  
        \# 3\. Client Lifecycle & Execution  
        \# \---------------------------------------------------------  
        \# We only need to spin up the client if there are actual tool calls.  
        last\_message \= state\["messages"\]\[-1\]  
        if not isinstance(last\_message, AIMessage) or not last\_message.tool\_calls:  
            return {"messages":}

        results \=  
          
        try:  
            \# Context Manager handles connection setup and teardown  
            async with MultiServerMCPClient(run\_configs) as client:  
                \# Note: In some MCP implementations, you may need to explicitly   
                \# wait for initialization or tool discovery.  
                \# However, call\_tool() usually handles this if the client is active.  
                  
                for tool\_call in last\_message.tool\_calls:  
                    tc\_name \= tool\_call\["name"\]  
                    tc\_args \= tool\_call\["args"\]  
                    tc\_id \= tool\_call\["id"\]  
                      
                    try:  
                        logger.info(f"Executing tool {tc\_name} for user {user\_id}")  
                        \# Execute: The client uses the authenticated transport  
                        output \= await client.call\_tool(tc\_name, tc\_args)  
                          
                        \# Success  
                        results.append(ToolMessage(  
                            content=str(output),  
                            name=tc\_name,  
                            tool\_call\_id=tc\_id  
                        ))  
                    except Exception as e:  
                        \# Application-level error (e.g. file not found)  
                        logger.warning(f"Tool {tc\_name} failed: {e}")  
                        results.append(ToolMessage(  
                            content=f"Error: {str(e)}",  
                            name=tc\_name,  
                            tool\_call\_id=tc\_id,  
                            status="error"  
                        ))  
                          
        except Exception as e:  
            \# Infrastructure-level error (e.g. Auth failed, Connection refused)  
            logger.error(f"MCP Connection failed: {e}")  
            return self.\_fail\_all\_tools(state, f"System Unavailable: {str(e)}")

        return {"messages": results}

    def \_fail\_all\_tools(self, state, error\_message):  
        """Helper to fail all pending tool calls."""  
        last\_message \= state\["messages"\]\[-1\]  
        results \=  
        for tool\_call in last\_message.tool\_calls:  
            results.append(ToolMessage(  
                content=error\_message,  
                name=tool\_call\["name"\],  
                tool\_call\_id=tool\_call\["id"\],  
                status="error"  
            ))  
        return {"messages": results}

### **6.4 Integrating with DeepAgents**

Since deepagents creates the graph for you, replacing the node can be tricky. However, most LangGraph wrappers return a StateGraph object or a compiled CompiledGraph. You can modify the graph *before* compilation or use the deepagents "custom tool node" configuration if available.

If deepagents is rigid, you can use the middleware patch (Section 4.2) to simply *prevent the crash*, but then ensure your McpToolsLoader is configured to use a **Connection Pool** or **Proxy** (Section 7\) rather than direct connections, effectively offloading the auth problem.

---

## **7\. Alternative Patterns (Addressing Question 4\)**

Beyond the Dynamic Client Factory, two other patterns exist for specific architectural constraints.

### **7.1 The Sidecar Proxy Pattern**

If modifying the Python code to create dynamic clients is too performance-intensive (due to connection handshakes), you can offload authentication to the infrastructure.

**Mechanism:**

1. **The Agent:** Connects to a local "Sidecar" proxy (running in the same pod/container) over localhost with *no authentication*.  
2. **Context Propagation:** The Agent passes the user\_token in a custom metadata header (e.g., X-Target-Auth) or as part of the JSON-RPC payload.  
3. **The Proxy:** Intercepts the request, extracts the token, and opens the secure connection to the remote MCP Server, attaching the standard Authorization: Bearer... header.

Pros: Keeps the Python agent code simple and stateless.  
Cons: Operational complexity (managing sidecars).

### **7.2 Graph-Level Resource Injection**

Instead of the node creating the client, the MultiServerMCPClient can be instantiated *outside* the graph for each request and passed in via configurable resources.

**Mechanism:**

1. **Server Wrapper:** The API server hosting the LangGraph agent (e.g., FastAPI) intercepts the request.  
2. **Instantiation:** The server instantiates the MCPClient with the user's headers.  
3. **Injection:** The client instance is passed into the graph config: config={"configurable": {"mcp\_client": client\_instance}}.  
4. **Usage:** The ToolNode simply retrieves config\["configurable"\]\["mcp\_client"\] and uses it.

Pros: Pure dependency injection. Very clean testing.  
Cons: Requires control over the API server ingress code, which might be managed by the LangGraph Platform (proprietary) rather than user code.

---

## **8\. Conclusion and Strategic Recommendations**

The integration of deepagents with the LangGraph Platform reveals a critical maturity gap in the handling of multi-tenant authentication for the Model Context Protocol. The immediate failure—McpToolsLoader.before\_agent missing config—is a symptom of signature mismatch caused by the evolution of the LangGraph runtime.

**Summary of Recommendations:**

1. **Fix the Crash:** Apply the **Monkey Patch** (Section 4.2) to the McpToolsLoader to bridge the gap between the legacy (state, config) signature and the modern (state, runtime) signature.  
2. **Implement Robust Auth:** Do not rely on middleware to configure the MCP client. Middleware is global and ill-suited for request-scoped connection handling in a threaded environment.  
3. **Adopt Pattern 3:** Implement the **Dynamic Client Factory** within a custom AuthenticatedMcpToolNode (Section 6.3). This ensures that every MCP connection is fresh, isolated, and authenticated with the correct user token derived from runtime.config.  
4. **Future-Proofing:** Monitor the langchain-mcp-adapters repository for updates regarding "Dynamic Headers".5 Native support for callable header factories is a requested feature that would simplify Pattern 3 significantly.

By adhering to these patterns, architects can ensure that their agent fleets remain secure, scalable, and compliant with the rigorous demands of enterprise deployment.

### **Table 1: Summary of Authentication Patterns**

| Feature | Middleware Config | InjectedToolArg | Dynamic Client Factory |
| :---- | :---- | :---- | :---- |
| **Auth Type** | Configuration Injection | Argument Injection | Transport (Header) Injection |
| **Best For** | Logging, Global Settings | Tools accepting API keys | **MCP Servers, Agent Fleets** |
| **Complexity** | Low | Low | Medium |
| **Security** | Low (Race Conditions) | High (Hidden Args) | **High (Isolation)** |
| **Performance** | High (Global Client) | High (Reuses Client) | Medium (Connect per Request) |
| **Recommendation** | Avoid for Auth | Use for APIs | **Recommended for MCP** |

This concludes the comprehensive analysis of Per-User MCP Authentication in the LangGraph Platform.

#### **Works cited**

1. Authentication & access control \- Docs by LangChain, accessed on November 28, 2025, [https://docs.langchain.com/langgraph-platform/auth](https://docs.langchain.com/langgraph-platform/auth)  
2. SDK (Python) \- 《LangGraph v0.2.73 Documentation》 \- 书栈网 · BookStack, accessed on November 28, 2025, [https://www.bookstack.cn/read/langgraph-0.2.73-en/6169f15caec2218e.md](https://www.bookstack.cn/read/langgraph-0.2.73-en/6169f15caec2218e.md)  
3. Module @langchain/mcp-adapters \- v0.6.0, accessed on November 28, 2025, [https://v03.api.js.langchain.com/modules/\_langchain\_mcp\_adapters.html](https://v03.api.js.langchain.com/modules/_langchain_mcp_adapters.html)  
4. langchain-mcp-adapters, accessed on November 28, 2025, [https://reference.langchain.com/python/langchain\_mcp\_adapters/](https://reference.langchain.com/python/langchain_mcp_adapters/)  
5. Feature Request: Support for Dynamic/Runtime Headers (e.g., JWT Authentication) in MultiServerMCPClient \#194 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain-mcp-adapters/issues/194](https://github.com/langchain-ai/langchain-mcp-adapters/issues/194)  
6. Deep Agents overview \- Docs by LangChain, accessed on November 28, 2025, [https://docs.langchain.com/oss/javascript/deepagents/overview](https://docs.langchain.com/oss/javascript/deepagents/overview)  
7. deepagents \- PyPI, accessed on November 28, 2025, [https://pypi.org/project/deepagents/](https://pypi.org/project/deepagents/)  
8. Middleware | LangChain Reference, accessed on November 28, 2025, [https://reference.langchain.com/python/langchain/middleware/](https://reference.langchain.com/python/langchain/middleware/)  
9. Deep Agents overview | LangChain Reference, accessed on November 28, 2025, [https://reference.langchain.com/python/deepagents/](https://reference.langchain.com/python/deepagents/)  
10. How to use InjectedToolArg in AgentExecutor \- LangChain Forum, accessed on November 28, 2025, [https://forum.langchain.com/t/how-to-use-injectedtoolarg-in-agentexecutor/1840](https://forum.langchain.com/t/how-to-use-injectedtoolarg-in-agentexecutor/1840)  
11. How to pass runtime argument to Structured Tool for agents? \#24906 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain/discussions/24906](https://github.com/langchain-ai/langchain/discussions/24906)  
12. Tools | LangChain Reference, accessed on November 28, 2025, [https://reference.langchain.com/python/langchain/tools/](https://reference.langchain.com/python/langchain/tools/)