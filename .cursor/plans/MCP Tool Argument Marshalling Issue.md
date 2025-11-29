

# **Technical Analysis of Tool Invocation Structures in LangChain MCP Adapters**

## **Executive Summary**

The convergence of generative artificial intelligence with deterministic computational tools has precipitated the need for standardized interoperability protocols. The Model Context Protocol (MCP), championed by Anthropic, has emerged as the definitive open standard for connecting AI assistants to systems of record—content repositories, business tools, and development environments. Within the Python ecosystem, the langchain-mcp-adapters library serves as the critical middleware, bridging the high-level orchestration capabilities of the LangChain framework with the strict, schema-driven architecture of MCP servers.

This report presents an exhaustive technical analysis of the tool invocation argument structures within langchain-mcp-adapters. It dissects the source code logic governing the tools/call request lifecycle, the dynamic transformation of LangChain StructuredTool inputs into MCP-compliant JSON-RPC 2.0 payloads, and the architectural nuances that frequently precipitate integration failures, such as argument double-nesting and schema validation anomalies. By synthesizing technical documentation, stack traces, and community implementation patterns, this analysis reconstructs the internal data flow of the adapter to provide a definitive reference for systems architects, protocol engineers, and developers building production-grade agentic systems.

The analysis reveals that the langchain-mcp-adapters library functions not merely as a pass-through mechanism but as an active translation layer that must reconcile the stateful, session-based nature of MCP with the stateless, execution-oriented paradigm of LangChain agents. This reconciliation process involves complex dynamic schema generation using Pydantic, asynchronous session management, and precise serialization logic, all of which introduce specific constraints and failure modes that are detailed herein.

## **1\. Architectural Context: The Convergence of LangChain and MCP**

To fully comprehend the mechanics of tool invocation within the langchain-mcp-adapters library, it is requisite to first establish the architectural divergence between the two systems it connects. The adapter exists to translate between the Python-native, object-oriented world of LangChain and the language-agnostic, message-based world of the Model Context Protocol.

### **1.1 The Model Context Protocol (MCP) Architecture**

The Model Context Protocol represents a significant evolution from proprietary function-calling APIs. Unlike REST APIs, which are typically resource-oriented and stateless, or GraphQL APIs, which are query-oriented, MCP is designed specifically for the unique requirements of Large Language Model (LLM) interactions. It operates on a client-host-server model, where the "Host" is the AI application (e.g., Claude Desktop, a LangChain Agent), the "Client" is the protocol implementation within that host, and the "Server" is the standalone process exposing tools and resources.1

#### **1.1.1 Transport Layer Agnosticism**

A defining characteristic of MCP is its transport agnosticism. The protocol is defined independently of the underlying communication channel, though it primarily utilizes two transport mechanisms in current implementations:

* **Standard Input/Output (stdio):** This is the predominant method for local integrations. The client spawns the server as a subprocess and communicates via stdin and stdout. This mechanism requires robust stream handling to ensure that log messages or other output do not corrupt the JSON-RPC messages.3  
* **Server-Sent Events (SSE) over HTTP:** This is utilized for remote connections. The client sends requests via HTTP POST, and the server pushes responses and notifications via an SSE connection. This decoupling of request and response channels introduces complexity in correlating asynchronous tool execution results.3

#### **1.1.2 The JSON-RPC 2.0 Backbone**

The Model Context Protocol relies strictly on JSON-RPC 2.0 for all message exchanges. This choice is significant because it imposes a rigid structure on invocation arguments. A tool invocation in MCP is not a function call in the programming sense; it is a Remote Procedure Call (RPC) request.

* **Message Envelope:** Every interaction is encapsulated in a JSON object containing jsonrpc, id, method, and params fields.5  
* **Method Specify:** Tool execution is triggered exclusively by the tools/call method.  
* **Parameter Strictness:** The params object must strictly adhere to the specification, containing a name string and an arguments dictionary. This arguments dictionary must map one-to-one with the JSON Schema defined during the tool discovery phase (the tools/list handshake).6

### **1.2 LangChain Tool Abstraction**

On the other side of the bridge lies LangChain's tooling architecture, which is deeply rooted in Python's typing system and the Pydantic data validation library.

#### **1.2.1 BaseTool and StructuredTool**

In LangChain, a tool is an instance of a class derived from BaseTool. The evolution of this class reflects the broader industry shift from simple text-in/text-out interfaces to complex structured data.

* **Legacy Tools:** Historically, tools often accepted a single string input (run(tool\_input: str)). This was sufficient for simple search queries but inadequate for complex APIs requiring multiple parameters.8  
* **StructuredTool:** Modern agentic workflows utilize StructuredTool, which wraps a function and an associated Pydantic model (args\_schema). This model defines the expected input structure, field types, and validation rules.9

#### **1.2.2 The Invocation Interface**

The standard entry point for tool execution in LangChain is the invoke (synchronous) or ainvoke (asynchronous) method. These methods are polymorphic, accepting inputs that can be a string, a dictionary, or a ToolCall object (a standardized representation of an LLM's intent to call a tool). The implementation of ainvoke in BaseTool is designed to handle this input variability, normalizing it into a dictionary of arguments before passing it to the internal logic.9

#### **1.2.3 Pydantic as the Schema Source of Truth**

In a native LangChain tool, the Pydantic args\_schema is the source of truth. The LLM's output is parsed and validated against this model *before* the tool logic is ever executed. This "fail-fast" mechanism allows agents to catch hallucinated arguments or type mismatches early. However, in the context of langchain-mcp-adapters, the source of truth is inverted: the remote MCP server's JSON Schema is the primary definition, and the local Pydantic model is merely a dynamically generated reflection of that remote truth.12

## **2\. Source Code Analysis: The langchain-mcp-adapters Architecture**

To understand how arguments are structured and passed during invocation, we must dissect the internal architecture of the langchain-mcp-adapters library. Based on stack traces, issue reports, and usage patterns, the library's architecture can be divided into two primary components: the Client Implementation (client.py) and the Tool Wrapper (tools.py).

### **2.1 The Client Implementation (client.py)**

The client.py module (and its associated MultiServerMCPClient class) is responsible for managing connections to MCP servers and handling the low-level details of the protocol.

#### **2.1.1 MultiServerMCPClient**

This class serves as a high-level manager for multiple server connections. It maintains a registry of configured servers and their transport settings.

* **Initialization:** It accepts a dictionary where keys are server names (namespaces) and values are configuration dictionaries (e.g., {"command": "python", "args": \[...\]}).  
* **Session Management:** It handles the lifecycle of ClientSession objects from the underlying mcp Python SDK. Crucially, MultiServerMCPClient is often stateless by default in simple examples, initializing a fresh session for each interaction, though robust implementations maintain persistent sessions.3

#### **2.1.2 The call\_tool Implementation**

The call\_tool method within the MCP ClientSession is the exact point where the Python dictionary of arguments is converted into a JSON-RPC message. The signature of this method is critical for understanding argument passing.

Python

async def call\_tool(  
    self,   
    name: str,   
    arguments: dict\[str, Any\] | None \= None,   
    \*\*kwargs  
) \-\> CallToolResult:  
    \# Logic reconstruction based on MCP SDK patterns  
    request\_params \= CallToolRequestParams(  
        name=name,  
        arguments=arguments or {}  
    )  
    request \= CallToolRequest(  
        method="tools/call",  
        params=request\_params  
    )  
    return await self.send\_request(request, CallToolResult)

**Analysis:** The arguments parameter is expected to be a dictionary. The MCP SDK explicitly maps this dictionary to the arguments key in the JSON-RPC params object. Any data passed here is serialized directly to JSON. This means that if the input dictionary is nested (e.g., {"input": {"a": 1}}), it will be serialized as nested JSON, which acts as the root cause for many validation errors discussed later.15

### **2.2 The Tool Wrapper (tools.py)**

The tools.py module is responsible for the critical task of bridging LangChain's StructuredTool interface with the MCP client. This is where the dynamic conversion happens.

#### **2.2.1 load\_mcp\_tools**

The load\_mcp\_tools function orchestrates the discovery and conversion process 3:

1. **List Tools:** It sends a tools/list request to the connected MCP server(s).  
2. **Schema Retrieval:** It receives the tool definitions, including the inputSchema (JSON Schema).  
3. **Dynamic Model Generation:** It uses Pydantic's create\_model to dynamically generate a Python class that replicates the validation logic of the remote JSON Schema. This generated model becomes the args\_schema of the resulting LangChain tool.  
   * *Significance:* This step is intended to ensure that LangChain performs local validation that matches the remote server's expectations. If this translation is imperfect (e.g., handling complex anyOf types or custom JSON Schema keywords), valid inputs might be rejected locally, or invalid inputs might leak through to the server.17

#### **2.2.2 The \_arun Execution Logic**

The heart of the tool invocation lies in the \_arun method of the wrapper class (typically an instance of StructuredTool configured with a specific coroutine). Stack traces allow us to reconstruct the logic flow 18:

Python

async def \_arun(self, \*args, \*\*kwargs) \-\> Any:  
    \# Logic reconstruction  
    tool\_name \= self.name  
    \# 1\. Argument Unpacking  
    \# If the input was validated via Pydantic, kwargs contains the fields  
    \# defined in the inputSchema (e.g., location="NYC", unit="celsius").  
      
    \# 2\. Session Retrieval  
    \# The tool needs access to the active MCP session.   
    \# This is typically bound via closure or instance variable.  
    session \= self.metadata.get("session")   
      
    \# 3\. Invocation  
    \# The kwargs are passed directly as the arguments dictionary.  
    call\_tool\_result \= await session.call\_tool(tool\_name, arguments=kwargs)  
      
    \# 4\. Result Conversion  
    return \_convert\_call\_tool\_result(call\_tool\_result)

**Critical Insight:** The \_arun method assumes that kwargs represents the *flat* dictionary of arguments expected by the tool. If LangChain's ainvoke passes the arguments differently—for example, as a single positional argument containing a dictionary—the wrapper logic must handle this unpacking. Failure to handle this variation is a primary source of "Invalid Params" errors.20

#### **2.2.3 Result Conversion (\_convert\_call\_tool\_result)**

The MCP protocol allows tools to return a complex result object containing content (list of text/image blocks) and isError (boolean). The adapter must flatten this into a format LangChain understands (usually a string or a ToolMessage).

* **Text Extraction:** The standard implementation iterates through the content list, concatenating text blocks.  
* **Error Handling:** If isError is true, the adapter raises a ToolException. This integrates with LangChain's error handling mechanisms (e.g., handle\_tool\_error), allowing the agent to attempt a retry or self-correction.18

## **3\. The Tool Invocation Cycle: A Step-by-Step Analysis**

To provide a comprehensive understanding of the arguments structure, we will trace a single tool invocation request from the Agent's intent to the final wire protocol.

Scenario: An agent decides to call a weather\_tool exposed by an MCP server.  
Goal: Get weather for "New York".  
Tool Schema: {"type": "object", "properties": {"city": {"type": "string"}}}.

### **Step 1: The Agent's Decision (LLM Output)**

The LLM (e.g., GPT-4o or Claude 3.5 Sonnet) generates a structured tool call.

* **Content:** FunctionCall(name="weather\_tool", arguments='{"city": "New York"}').  
* **LangChain Processing:** LangChain parses this output into a ToolCall object containing the name and the parsed arguments dictionary: {"city": "New York"}.23

### **Step 2: LangChain Input Processing (BaseTool.ainvoke)**

The ToolNode or AgentExecutor calls weather\_tool.ainvoke(input={"city": "New York"}).

* **Validation:** The StructuredTool uses its args\_schema (the dynamically generated Pydantic model) to validate the input.  
  * *Success:* {"city": "New York"} is valid.  
  * *Failure:* If the LLM output {"location": "New York"} but the schema required city, Pydantic raises a ValidationError immediately, halting execution.13

### **Step 3: Adapter Execution (\_arun)**

Once validation passes, control is handed to the adapter's \_arun method.

* **Input State:** kwargs \= {"city": "New York"}.  
* **Action:** The adapter calls session.call\_tool("weather\_tool", arguments=kwargs).

### **Step 4: MCP SDK Request Construction**

The mcp SDK constructs the JSON-RPC request object.

* **Method:** "tools/call"  
* **Params:** {"name": "weather\_tool", "arguments": {"city": "New York"}}.  
* **ID:** A unique integer or string ID is assigned for correlation.5

### **Step 5: Serialization and Transport**

The request object is serialized to a JSON string and transmitted.

* **Stdio:** The JSON string is written to the subprocess stdin, followed by a newline character.  
* **SSE:** The JSON string is sent as the body of an HTTP POST request to the server's endpoint (e.g., http://localhost:8000/mcp/messages).4

**Final Payload on the Wire:**

JSON

{  
  "jsonrpc": "2.0",  
  "id": 1,  
  "method": "tools/call",  
  "params": {  
    "name": "weather\_tool",  
    "arguments": {  
      "city": "New York"  
    }  
  }  
}

## **4\. The "Double Nesting" Anomaly and Argument Structures**

One of the most pervasive issues identified in the research material is the "double nesting" of arguments. This section analyzes the mechanics of this failure mode, which serves as a critical case study in the interaction between LangChain's input handling and MCP's strict schema enforcement.

### **4.1 The Mechanism of Double Nesting**

Double nesting occurs when the dictionary of arguments is wrapped inside another dictionary, typically under a key like input or \_\_arg1, resulting in a payload that does not match the server's expectations.

**Incorrect Payload (The Anomaly):**

JSON

{  
  "jsonrpc": "2.0",  
  "method": "tools/call",  
  "params": {  
    "name": "weather\_tool",  
    "arguments": {  
      "input": {  \<-- Extra nesting layer  
        "city": "New York"  
      }  
    }  
  }  
}

**Root Causes:**

1. **Legacy Agent Executors:** Older LangChain AgentExecutor implementations were designed around single-input tools (Tool), often defaulting to passing a dictionary {"input": "value"} or {"query": "value"}. When applied to StructuredTool, this wrapper dictionary acts as a single positional argument rather than being unpacked into kwargs.26  
2. **infer\_schema Behavior:** If infer\_schema=True is used (which is default in load\_mcp\_tools), and the tool signature is generic, LangChain may treat the input as a single object.  
3. **Adapter Unpacking Failure:** The \_arun implementation in tools.py ideally should detect if args contains a single dictionary and kwargs is empty. If it fails to unpack args, it passes the wrapper dictionary as the arguments payload.27

### **4.2 Impact on Schema Validation**

When the MCP server receives the double-nested payload, it validates params.arguments against the tool's schema.

* **Expected:** {"city": "string"}  
* **Received:** {"input": {"city": "string"}}  
* **Result:** The server rejects the request with an INVALID\_ARGUMENT or Invalid params error code (-32602). This error comes from the *remote* server, not the local Pydantic validation, leading to confusion because the local validation (which saw the correct structure inside the agent) passed successfully.5

### **4.3 Mitigation Strategies**

Research indicates several strategies to resolve this:

* **Using LangGraph:** The newer LangGraph framework and bind\_tools paradigm handle structured inputs more natively, preserving the dictionary structure correctly without legacy wrappers.29  
* **Explicit Unpacking Wrappers:** Developers sometimes implement middleware or custom wrappers around the adapter tools to explicitly check for and remove the input key before invocation.20  
* **Schema Normalization:** Ensuring that the Pydantic model generated by load\_mcp\_tools accurately reflects the need for flat arguments can prevent the agent from generating nested structures in the first place.

## **5\. Transport Layer Nuances: Stdio vs. SSE**

The argument structure is conceptually identical across transports (JSON-RPC 2.0), but the mechanism of delivery introduces specific constraints that affect how arguments are handled and debugged.

### **5.1 Stdio Transport**

In the Stdio transport, the argument structure is serialized to a string and piped to the server's standard input.

* **Constraint:** The arguments payload must be fully serializable to JSON. This precludes passing Python-specific objects (like complex class instances) that haven't been converted to dicts. Pydantic handles this serialization generally, but custom types can cause issues.  
* **Debugging:** Debugging Stdio argument issues is challenging because the traffic happens over an OS pipe. Developers often need to wrap the transport or use tools like mcp-inspector to view the raw JSON traffic.3  
* **Buffer Handling:** Large argument payloads (e.g., passing a large file content as a string argument) can potentially hit buffer limits depending on the OS pipe implementation, though MCP implementations usually handle framing.4

### **5.2 SSE (HTTP) Transport**

In the SSE transport, the arguments are sent as the HTTP body.

* **Constraint:** Similar JSON serialization rules apply. However, additional metadata (like authentication tokens or org\_id) must often be passed.  
* **Header Injection:** The arguments structure itself does not standardly contain authentication data. Instead, MultiServerMCPClient allows configuring HTTP headers. These headers are sent with the POST request that carries the tools/call message. This is critical for connecting to secure enterprise MCP servers.29  
* **Missing \_meta:** As noted in the research, the current Python SDK call\_tool signature does not expose the \_meta field of the JSON-RPC request. This field is intended for out-of-band data (like tracing IDs). Workarounds involve manually constructing the ClientRequest object instead of using the helper method.15

## **6\. Schema Mismatches and Validation Anomalies**

The translation between JSON Schema (used by MCP) and Pydantic (used by LangChain) is a fertile ground for argument structure issues.

### **6.1 The "Snake Case" vs. "Camel Case" Conflict**

JSON APIs often use camelCase (e.g., maxTokens), while Python conventionally uses snake\_case (e.g., max\_tokens).

* **The Issue:** If the MCP server defines arguments in camelCase, the dynamically generated Pydantic model must handle this. If the LLM is trained to generate Python code, it might default to snake\_case.  
* **Impact:** If LangChain passes max\_tokens to an MCP server expecting maxTokens, the server validates it as an unknown field (if additionalProperties: false) or a missing required field.  
* **Resolution:** The adapter's model generation logic needs to handle aliasing correctly, mapping the Python-friendly name to the wire-protocol name.17

### **6.2 Handling Complex Types (Enums and Nested Objects)**

Snippets suggest issues with Google Vertex AI and other platforms when schemas contain Enums or complex nested objects.

* **Enums:** An Enum in JSON Schema ({"enum": \["a", "b"\]}) must be converted to a Python Enum or Literal type in Pydantic. Mismatches here (e.g., passing the string "A" instead of "a") cause validation errors.  
* **Nested Objects:** If a tool requires a list of objects, the adapter creates nested Pydantic models. If the agent generates a simplified structure (e.g., a list of strings instead of a list of objects containing strings), validation fails. This highlights the importance of the fidelity of the load\_mcp\_tools schema conversion process.17

## **7\. Strategic Recommendations for Implementation**

Based on the analysis of source code structures and common failure modes, the following recommendations are synthesized for developers integrating langchain-mcp-adapters.

### **7.1 Prioritize LangGraph for Orchestration**

The architectural mismatch between legacy LangChain AgentExecutor and MCP's strict schema is the primary cause of argument nesting errors. LangGraph's design, specifically the ToolNode and bind\_tools workflow, aligns more closely with the atomic, structured nature of MCP tool calls. It provides a cleaner "LLM \-\> ToolCall \-\> Adapter \-\> JSON-RPC" pipeline with fewer implicit wrappers.29

### **7.2 Implement Robust Error Handling Wrappers**

Given that MCP servers return errors as data (inside the tools/call response), not exceptions, the standard adapter logic raises ToolException on error. Developers should implement a handle\_tool\_error function in their agent configuration. This function should parse the ToolException message (which often contains the MCP error code) and feed it back to the LLM. This allows the LLM to self-correct arguments (e.g., fixing a missing parameter) rather than crashing the agent loop.18

### **7.3 Use Manual Verification for Schema Fidelity**

Before deploying an agent, perform manual verification of the loaded tools.

Python

\# Verification Pattern  
client \= MultiServerMCPClient({...})  
async with client.session("server") as session:  
    \# 1\. Inspect the loaded Pydantic schema  
    tools \= await load\_mcp\_tools(session)  
    print(tools.args\_schema.schema\_json())  
      
    \# 2\. Manually invoke to test argument serialization  
    \# This bypasses the agent and tests the adapter-\>server link  
    result \= await session.call\_tool("tool\_name", arguments={"arg": "val"})

This pattern isolates schema conversion issues from LLM hallucination issues.33

## **8\. Conclusion**

The langchain-mcp-adapters library represents a sophisticated but intricate integration point in the modern AI stack. Its primary function is to marshal data between two disparate architectural paradigms: the dynamic, object-oriented world of LangChain/Pydantic and the strict, message-based world of MCP/JSON-RPC.

The analysis of the source code and invocation logic reveals that the tools/call arguments structure is the most fragile component of this integration. The fidelity of the system relies on the precise alignment of dynamic Pydantic model generation, proper argument unpacking in the \_arun method, and strict adherence to the JSON-RPC 2.0 specification in the client.py module. Common failures like argument double-nesting are symptomatic of impedance mismatches between legacy agent patterns and the new protocol standards.

As the ecosystem matures, the move towards LangGraph and more standardized tool definitions will likely mitigate these issues. However, for current implementations, a deep understanding of the underlying JSON-RPC payload structure and the adapter's serialization logic is indispensable for building robust, production-grade AI agents.

---

## **9\. Appendix: Reference Data**

### **9.1 JSON-RPC Payload Structural Reference**

The following tables define the strict structural requirements for MCP tool invocation payloads.

| Field | Type | Constraint | Description |
| :---- | :---- | :---- | :---- |
| jsonrpc | String | Must be "2.0" | Protocol version identifier. |
| id | String/Int | Unique per session | Used to correlate the Request with the Response. |
| method | String | "tools/call" | The specific MCP method for tool execution. |
| params | Object | Required | Container for tool details. |
| params.name | String | Exact Match | Must match the tool name from tools/list. |
| params.arguments | Object | Flat Dictionary | The actual arguments. Must not be wrapped in input or other keys unless the schema explicitly defines them. |

### **9.2 Comparative Argument Flow**

| Stage | Data Representation | Responsible Component | Potential Failure Mode |
| :---- | :---- | :---- | :---- |
| **1\. Agent Intent** | ToolCall Object | LLM / LangChain Core | Hallucinated parameters; invalid types. |
| **2\. Local Validation** | Pydantic Model (args\_schema) | StructuredTool | ValidationError (Fail-fast). |
| **3\. Adapter Invocation** | Python dict (kwargs) | langchain-mcp-adapters (tools.py) | Double nesting (passing dict as positional arg). |
| **4\. Wire Protocol** | JSON String | MCP SDK (client.py) | Serialization errors; Missing \_meta. |
| **5\. Server Validation** | JSON Schema | MCP Server | INVALID\_ARGUMENT (Schema mismatch). |

#### **Works cited**

1. The Model Context Protocol (MCP) for AI Tool Integration | Cirra, accessed on November 28, 2025, [https://cirra.ai/articles/model-context-protocol-ai-tool-integration](https://cirra.ai/articles/model-context-protocol-ai-tool-integration)  
2. Tools \- Model Context Protocol, accessed on November 28, 2025, [https://modelcontextprotocol.io/legacy/concepts/tools](https://modelcontextprotocol.io/legacy/concepts/tools)  
3. Model Context Protocol (MCP) \- Docs by LangChain, accessed on November 28, 2025, [https://docs.langchain.com/oss/python/langchain/mcp](https://docs.langchain.com/oss/python/langchain/mcp)  
4. Model Context Protocol (MCP) \- Docs by LangChain, accessed on November 28, 2025, [https://docs.langchain.com/oss/javascript/langchain/mcp](https://docs.langchain.com/oss/javascript/langchain/mcp)  
5. JSON-RPC Protocol in MCP \- Complete Guide \- MCPcat, accessed on November 28, 2025, [https://mcpcat.io/guides/understanding-json-rpc-protocol-mcp/](https://mcpcat.io/guides/understanding-json-rpc-protocol-mcp/)  
6. Tools \- Model Context Protocol, accessed on November 28, 2025, [https://modelcontextprotocol.io/specification/draft/server/tools](https://modelcontextprotocol.io/specification/draft/server/tools)  
7. Architecture overview \- Model Context Protocol, accessed on November 28, 2025, [https://modelcontextprotocol.io/docs/concepts/architecture](https://modelcontextprotocol.io/docs/concepts/architecture)  
8. Structured tools not able to pass structured data to each other · Issue \#13602 · langchain-ai/langchain \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain/issues/13602](https://github.com/langchain-ai/langchain/issues/13602)  
9. langchain\_core.tools.StructuredTool — LangChain 0.0.354, accessed on November 28, 2025, [https://api.python.langchain.com/en/v0.0.354/tools/langchain\_core.tools.StructuredTool.html](https://api.python.langchain.com/en/v0.0.354/tools/langchain_core.tools.StructuredTool.html)  
10. Mastering Tools and Tool Calling Agents in LangChain: A Comprehensive Guide | by Maria Waheed | Medium, accessed on November 28, 2025, [https://medium.com/@mariaaawaheed/mastering-tools-and-tool-calling-agents-in-langchain-a-comprehensive-guide-18a566f2aac5](https://medium.com/@mariaaawaheed/mastering-tools-and-tool-calling-agents-in-langchain-a-comprehensive-guide-18a566f2aac5)  
11. langchain\_core.tools.BaseTool — LangChain 0.0.354 \- GitHub Pages, accessed on November 28, 2025, [https://datastax.github.io/ragstack-ai/api\_reference/0.5.0/langchain/tools/langchain\_core.tools.BaseTool.html](https://datastax.github.io/ragstack-ai/api_reference/0.5.0/langchain/tools/langchain_core.tools.BaseTool.html)  
12. Issue: How to validate Tool input arguments without raising ValidationError \#13662 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain/issues/13662](https://github.com/langchain-ai/langchain/issues/13662)  
13. Structured Tool Calling with LangChain and Groq | by Dinesh Ram \- Medium, accessed on November 28, 2025, [https://medium.com/@dineshramdsml/structured-tool-calling-with-langchain-and-groq-e619da26c993](https://medium.com/@dineshramdsml/structured-tool-calling-with-langchain-and-groq-e619da26c993)  
14. langchain-ai/langchain-mcp-adapters: LangChain MCP \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters)  
15. Expose \_meta in ClientSession methods · Issue \#1216 · modelcontextprotocol/python-sdk, accessed on November 28, 2025, [https://github.com/modelcontextprotocol/python-sdk/issues/1216](https://github.com/modelcontextprotocol/python-sdk/issues/1216)  
16. langchain-mcp-tools \- PyPI, accessed on November 28, 2025, [https://pypi.org/project/langchain-mcp-tools/](https://pypi.org/project/langchain-mcp-tools/)  
17. Issue with Google ADK when trying to load tools from an MCP server \- Reddit, accessed on November 28, 2025, [https://www.reddit.com/r/googlecloud/comments/1kaskpt/issue\_with\_google\_adk\_when\_trying\_to\_load\_tools/](https://www.reddit.com/r/googlecloud/comments/1kaskpt/issue_with_google_adk_when_trying_to_load_tools/)  
18. Issues Langchain MCP adapters with Playwright MCP \#301 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain-mcp-adapters/issues/301](https://github.com/langchain-ai/langchain-mcp-adapters/issues/301)  
19. Getting these errors intermittently and then I have to restart my service. · Issue \#142 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain-mcp-adapters/issues/142](https://github.com/langchain-ai/langchain-mcp-adapters/issues/142)  
20. Support for Parameter Passing in MCP Configuration and Runtime Context \#233 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain-mcp-adapters/issues/233](https://github.com/langchain-ai/langchain-mcp-adapters/issues/233)  
21. Issue: UnboundLocalError in call\_tool on Client Disconnect — Due to Uninitialized Variable \#314 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain-mcp-adapters/issues/314](https://github.com/langchain-ai/langchain-mcp-adapters/issues/314)  
22. langchain-mcp-adapters ignores structuredContent field from MCP tool responses · Issue \#283 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain-mcp-adapters/issues/283](https://github.com/langchain-ai/langchain-mcp-adapters/issues/283)  
23. Tool Calling with LangChain, accessed on November 28, 2025, [https://blog.langchain.com/tool-calling-with-langchain/](https://blog.langchain.com/tool-calling-with-langchain/)  
24. LangChain vs CrewAI for multi-agent workflows \- Scalekit, accessed on November 28, 2025, [https://www.scalekit.com/blog/langchain-vs-crewai-multi-agent-workflows](https://www.scalekit.com/blog/langchain-vs-crewai-multi-agent-workflows)  
25. Handling a ValidationError from inputs not conforming to a provided args\_schema with a structured tool in langchain \- Stack Overflow, accessed on November 28, 2025, [https://stackoverflow.com/questions/77617074/handling-a-validationerror-from-inputs-not-conforming-to-a-provided-args-schema](https://stackoverflow.com/questions/77617074/handling-a-validationerror-from-inputs-not-conforming-to-a-provided-args-schema)  
26. How to pass runtime argument to Structured Tool for agents? \#24906 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain/discussions/24906](https://github.com/langchain-ai/langchain/discussions/24906)  
27. Tools | LangChain Reference, accessed on November 28, 2025, [https://reference.langchain.com/python/langchain/tools/](https://reference.langchain.com/python/langchain/tools/)  
28. Correct Usage of AgentExecutor.as\_tool()? TypeError: Tool input must be str or dict. If dict, dict arguments must be typed. Either annotate types (e.g., with TypedDict) or pass arg\_types into \`.as\_tool\` to specify. typing.Dict\[str, typing.Any\] is not a module, class, method, or function. · langchain-ai langchain · Discussion \#25023 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain/discussions/25023](https://github.com/langchain-ai/langchain/discussions/25023)  
29. Best Practices for Production-Ready LLM Apps with LangChain 1.0 \- Skywork.ai, accessed on November 28, 2025, [https://skywork.ai/blog/ai-agent/best-practices-langchain-1-0-production-ready-llm-apps/](https://skywork.ai/blog/ai-agent/best-practices-langchain-1-0-production-ready-llm-apps/)  
30. MCP in LangChain Agents: When It Fits, When It Doesn't | by Georgi Pavlov \- Medium, accessed on November 28, 2025, [https://medium.com/@g\_pavlov/mcp-in-langchain-agents-when-it-fits-when-it-doesnt-532ea79789a1](https://medium.com/@g_pavlov/mcp-in-langchain-agents-when-it-fits-when-it-doesnt-532ea79789a1)  
31. Support for Logging in MCP Client (per MCP Spec) \#167 \- GitHub, accessed on November 28, 2025, [https://github.com/langchain-ai/langchain-mcp-adapters/issues/167](https://github.com/langchain-ai/langchain-mcp-adapters/issues/167)  
32. Auth0 Changelog, accessed on November 28, 2025, [https://auth0.com/changelog](https://auth0.com/changelog)  
33. LangGraph MCP Client Setup Made Easy \[2025 Guide\] \- Generect, accessed on November 28, 2025, [https://generect.com/blog/langgraph-mcp/](https://generect.com/blog/langgraph-mcp/)