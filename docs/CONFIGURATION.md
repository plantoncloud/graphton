# Configuration Reference

Complete reference for Graphton agent configuration.

## Overview

Graphton validates all configuration at graph creation time using Pydantic models. This provides:

- **Early error detection**: Invalid configurations fail immediately with helpful messages
- **Type safety**: Full type checking with mypy support
- **IDE autocomplete**: Rich editor support for configuration parameters
- **Clear documentation**: Self-documenting code with type hints

## AgentConfig

Top-level configuration for `create_deep_agent()`.

### Required Parameters

#### model: str | BaseChatModel

Model name string or LangChain model instance.

**String format** (recommended):

```python
# Anthropic models
model = "claude-sonnet-4.5"  # → Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)
model = "claude-opus-4"      # → Claude Opus 4 (claude-opus-4-20250514)
model = "claude-haiku-4"     # → Claude Haiku 4 (claude-haiku-4-20250313)

# OpenAI models
model = "gpt-4o"             # → GPT-4 Optimized
model = "gpt-4o-mini"        # → GPT-4 Optimized Mini
model = "gpt-4-turbo"        # → GPT-4 Turbo
model = "o1"                 # → OpenAI o1
model = "o1-mini"            # → OpenAI o1 Mini
```

**Model instance** (advanced):

```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Anthropic with custom parameters
model = ChatAnthropic(
    model="claude-opus-4-20250514",
    max_tokens=30000,
    temperature=0.3
)

# OpenAI with custom parameters
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.0
)
```

**Note**: When passing a model instance, `max_tokens`, `temperature`, and other model parameters passed to `create_deep_agent()` are ignored.

#### system_prompt: str

System prompt defining agent behavior and capabilities.

**Requirements**:
- Must be at least 10 characters
- Should clearly describe agent's role, capabilities, and constraints
- Cannot be empty or whitespace-only

**Examples**:

```python
# ✅ Good: Clear, specific, comprehensive
system_prompt = """You are a helpful coding assistant specializing in Python and TypeScript.

Your capabilities:
- Write clean, well-documented code
- Explain complex concepts clearly
- Suggest best practices and design patterns
- Debug and fix code issues

Always prioritize code quality, readability, and maintainability."""

# ✅ Good: Concise but clear
system_prompt = "You are a cloud infrastructure expert helping users manage AWS resources using the AWS CLI."

# ❌ Bad: Too short
system_prompt = "Assistant"

# ❌ Bad: Empty
system_prompt = ""
```

### Optional Parameters

#### auto_enhance_prompt: bool = True

Whether to automatically enhance `system_prompt` with awareness of Deep Agents capabilities.

**Default**: `True` (automatic enhancement enabled)

**What it does**:
- Appends high-level context about planning system (write_todos, read_todos)
- Adds awareness of file system tools (ls, read_file, write_file, edit_file, glob, grep)
- Includes MCP tools context when MCP is configured
- Helps agents understand what capabilities they have and when to use them

**Enhancement philosophy**:
- Always appends (doesn't try to detect redundancy)
- Keeps enhancement minimal and high-level (under 150 words)
- Focuses on WHEN/WHY to use capabilities, not HOW (middleware handles details)
- User instructions always come first, capability context added after

**When to disable**:
- You've already included comprehensive capability descriptions in your system_prompt
- You need complete control over every word in the prompt
- You're testing minimal prompts or conducting prompt experiments

**Examples**:

```python
# Default: automatic enhancement (recommended)
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a research assistant.",
    # auto_enhance_prompt=True by default
)
# Result: Agent understands it has planning and file system tools

# With MCP tools configured
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You help manage cloud resources.",
    mcp_servers={...},
    mcp_tools={...},
    # Enhancement includes MCP awareness
)

# Opt-out when you've included everything
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="""You are a research assistant.

    Available tools:
    - Planning: Use write_todos/read_todos for complex multi-step tasks
    - File System: Use ls, read_file, write_file, etc. for context management
    - [... comprehensive capability descriptions ...]
    """,
    auto_enhance_prompt=False,  # Already included all context
)
```

**Redundancy handling**:

If your `system_prompt` already mentions planning or file system, some overlap will occur. This is **intentional and acceptable**:
- LLMs handle redundant information gracefully
- Reinforcement helps ensure agents actually use available tools
- Better to have slight redundancy than miss informing the agent

**What gets added** (example):

```
## Your Capabilities

**Planning System**: For complex or multi-step tasks, you have access to a 
planning system (write_todos, read_todos). Use it to break down work, track 
progress, and manage task complexity. Skip it for simple single-step tasks.

**File System**: You have file system tools (ls, read_file, write_file, 
edit_file, glob, grep) for managing information across your work. Use the 
file system to store large content, offload context, and maintain state 
between operations. All file paths must start with '/'.

**MCP Tools**: You have access to MCP (Model Context Protocol) tools 
configured specifically for this agent. These are domain-specific tools 
for specialized operations.
```



#### recursion_limit: int = 100

Maximum agent reasoning steps before stopping.

**Range**: Must be positive (> 0)

**Recommended values**:
- **10-50**: Simple agents with straightforward tasks
- **50-100**: Moderate complexity agents (default)
- **100-200**: Complex agents with multi-step reasoning
- **>200**: Advanced agents (warning issued, may cause long execution times)

**Examples**:

```python
# Simple Q&A agent
recursion_limit = 20

# Code generation agent
recursion_limit = 50

# Research agent with multiple sources
recursion_limit = 150

# Very high limit (warning issued)
recursion_limit = 600  # UserWarning: recursion_limit of 600 is very high
```

**Validation**:
- Values ≤ 0 raise `ValueError`
- Values > 500 trigger `UserWarning`

#### temperature: float | None = None

Model temperature controlling output randomness.

**Range**: 0.0 to 2.0

**Guidelines**:
- **0.0-0.3**: Deterministic, factual responses (code generation, data analysis)
- **0.4-0.7**: Balanced creativity and consistency (general assistance)
- **0.7-1.0**: Creative responses (brainstorming, content generation)
- **1.0-2.0**: Highly creative (experimental use cases)

**Examples**:

```python
# Code generation (deterministic)
temperature = 0.0

# General assistance
temperature = 0.7

# Creative writing
temperature = 1.0

# ❌ Invalid: out of range
temperature = -0.5  # ValueError: temperature must be between 0.0 and 2.0
temperature = 3.0   # ValueError: temperature must be between 0.0 and 2.0
```

#### max_tokens: int | None = None

Override default max_tokens for the model.

**Defaults by provider**:
- **Anthropic**: 20,000 (Deep Agents need high limits)
- **OpenAI**: Model default (varies by model)

**Examples**:

```python
# Use default
agent = create_deep_agent(model="claude-sonnet-4.5", ...)  # max_tokens=20000

# Override for shorter responses
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    max_tokens=5000,
    ...
)

# Override for longer responses
agent = create_deep_agent(
    model="claude-opus-4",
    max_tokens=40000,
    ...
)
```

#### tools: Sequence[BaseTool] | None = None

Additional tools for the agent (non-MCP tools).

**Examples**:

```python
from langchain_core.tools import tool

@tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a calculator assistant.",
    tools=[calculate],
)
```

#### middleware: Sequence[Any] | None = None

Additional middleware for the agent.

**Auto-injected middleware**:
- **Loop Detection**: Automatically injected to prevent infinite loops (see [Loop Detection](#loop-detection) below)
- **MCP Tool Loading**: Auto-injected when `mcp_servers` and `mcp_tools` are provided

**Examples**:

```python
from deepagents import LoggingMiddleware

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    middleware=[LoggingMiddleware()],
)
```

#### context_schema: type[Any] | None = None

Custom state schema for the agent.

**Default**: `FilesystemState` from deepagents (provides file system operations)

**Examples**:

```python
from pydantic import BaseModel

class CustomState(BaseModel):
    messages: list
    custom_field: str

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    context_schema=CustomState,
)
```

## MCP Configuration

Graphton's universal MCP authentication framework supports any MCP server configuration format and authentication method through template-based token injection.

### Universal Authentication Framework

The framework automatically detects two modes:

**Static Mode** (no template variables):
- Tools loaded once at agent creation time
- Zero runtime overhead
- Use for hardcoded credentials or public servers

**Dynamic Mode** (with `{{VAR}}` templates):
- Templates substituted from `config['configurable']` at invocation time
- Tools loaded per-request with user-specific authentication
- Use for multi-tenant systems or per-user tokens

### mcp_servers: dict[str, dict[str, Any]] | None = None

Raw MCP server configurations mapping server names to server config dictionaries.

**Accepts any format** compatible with the MCP client. No structural validation - you control the configuration.

**Template syntax**: Use `{{VAR_NAME}}` placeholders for dynamic values.

**Dynamic configuration** (template variables - per-user auth):

```python
mcp_servers = {
    "planton-cloud": {
        "transport": "streamable_http",
        "url": "https://mcp.planton.ai/",
        "headers": {
            "Authorization": "Bearer {{USER_TOKEN}}"  # Substituted at runtime
        }
    }
}
```

**Static configuration** (no templates - shared credentials):

```python
mcp_servers = {
    "public-api": {
        "transport": "http",
        "url": "https://api.example.com/mcp",
        "headers": {
            "X-API-Key": "hardcoded-key-123"  # Same for all users
        }
    }
}
```

**Mixed configuration** (multiple auth methods):

```python
mcp_servers = {
    # Dynamic: Bearer token
    "planton-cloud": {
        "transport": "streamable_http",
        "url": "https://mcp.planton.ai/",
        "headers": {
            "Authorization": "Bearer {{USER_TOKEN}}"
        }
    },
    
    # Dynamic: API Key
    "external-api": {
        "transport": "http",
        "url": "{{BASE_URL}}/api",
        "headers": {
            "X-API-Key": "{{API_KEY}}"
        }
    },
    
    # Static: Hardcoded
    "public-server": {
        "transport": "http",
        "url": "https://public.example.com",
        "headers": {
            "X-Client-ID": "client-123"
        }
    }
}
```

**Validation rules**:
- Must be provided together with `mcp_tools`
- Server names must match between `mcp_servers` and `mcp_tools`
- Template variables must be provided in `config['configurable']` at invocation (dynamic mode only)

**Supported authentication methods** (examples):

```python
# Bearer token (OAuth, JWT)
"headers": {"Authorization": "Bearer {{TOKEN}}"}

# API Key
"headers": {"X-API-Key": "{{API_KEY}}"}

# Basic Auth (encode credentials as base64)
"headers": {"Authorization": "Basic {{BASIC_CREDS}}"}

# Custom headers
"headers": {
    "X-Client-ID": "{{CLIENT_ID}}",
    "X-Client-Secret": "{{CLIENT_SECRET}}"
}
```
```

### mcp_tools: dict[str, list[str]] | None = None

MCP tools configuration mapping server names to lists of tool names to load.

**Format**:

```python
mcp_tools = {
    "server-name": [
        "tool_name_1",
        "tool_name_2",
    ]
}
```

**Validation rules**:
- Must be provided together with `mcp_servers`
- Server names must match those in `mcp_servers`
- Tool lists cannot be empty
- Tool names must be strings
- Tool names should use alphanumeric characters, underscores, or hyphens
- No duplicate tool names within a server

**Examples**:

```python
# ✅ Valid configuration
mcp_tools = {
    "planton-cloud": [
        "list_organizations",
        "list_environments_for_org",
        "search_cloud_resources",
        "create_cloud_resource",
    ]
}

# ✅ Multiple servers
mcp_tools = {
    "planton-cloud": ["list_organizations", "create_cloud_resource"],
    "aws-tools": ["list_ec2_instances", "create_s3_bucket"],
}

# ✅ Tool names with hyphens
mcp_tools = {
    "server": ["list-resources", "get-resource-by-id"]
}

# ❌ Empty tool list
mcp_tools = {
    "planton-cloud": []  # ValueError: empty tool list
}

# ❌ Invalid tool name characters
mcp_tools = {
    "server": ["tool@invalid!"]  # ValueError: Invalid tool name
}

# ❌ Duplicate tool names
mcp_tools = {
    "server": ["tool1", "tool2", "tool1"]  # ValueError: Duplicate tool names
}

# ❌ Server name mismatch
mcp_servers = {"server-a": {...}}
mcp_tools = {"server-b": ["tool1"]}  # ValueError: server names don't match
```

## Complete Example

### Dynamic Authentication (Per-User Tokens)

```python
from graphton import create_deep_agent
import os

# Agent with dynamic MCP authentication
agent = create_deep_agent(
    # Required
    model="claude-sonnet-4.5",
    system_prompt="You are a Planton Cloud assistant helping users manage cloud resources.",
    
    # MCP integration with template variables
    mcp_servers={
        "planton-cloud": {
            "transport": "streamable_http",
            "url": "https://mcp.planton.ai/",
            "headers": {
                "Authorization": "Bearer {{USER_TOKEN}}"  # Template variable
            }
        }
    },
    mcp_tools={
        "planton-cloud": [
            "list_organizations",
            "list_environments_for_org",
            "search_cloud_resources",
            "create_cloud_resource",
        ]
    },
    
    # Optional parameters
    recursion_limit=150,
    max_tokens=10000,
    temperature=0.3,
)

# Invoke with user-specific token
# Template variable {{USER_TOKEN}} is substituted at runtime
result = agent.invoke(
    {"messages": [{"role": "user", "content": "List my organizations"}]},
    config={
        "configurable": {
            "USER_TOKEN": os.getenv("PLANTON_API_KEY")  # Substituted into template
        }
    }
)
```

### Static Authentication (Shared Credentials)

```python
# Agent with static MCP configuration
# Tools loaded once at creation time
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are an API assistant.",
    
    mcp_servers={
        "public-api": {
            "transport": "http",
            "url": "https://api.example.com/mcp",
            "headers": {
                "X-API-Key": "hardcoded-key-123"  # No templates = static
            }
        }
    },
    mcp_tools={
        "public-api": ["search", "fetch"]
    }
)

# Invoke without auth config - credentials already in config
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Search for Python"}]}
)
```

### Multi-Server with Mixed Authentication

```python
# Multiple servers with different auth methods
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a multi-cloud assistant.",
    
    mcp_servers={
        # Dynamic: User-specific Bearer token
        "planton-cloud": {
            "transport": "streamable_http",
            "url": "https://mcp.planton.ai/",
            "headers": {
                "Authorization": "Bearer {{USER_TOKEN}}"
            }
        },
        
        # Dynamic: User-specific API key
        "external-api": {
            "transport": "http",
            "url": "https://api.example.com",
            "headers": {
                "X-API-Key": "{{API_KEY}}"
            }
        },
        
        # Static: Shared credentials
        "public-api": {
            "transport": "http",
            "url": "https://public.example.com",
            "headers": {
                "X-Client-ID": "client-123"
            }
        }
    },
    mcp_tools={
        "planton-cloud": ["list_organizations"],
        "external-api": ["search"],
        "public-api": ["get_info"]
    }
)

# Invoke with multiple template values
result = agent.invoke(
    {"messages": [{"role": "user", "content": "List resources"}]},
    config={
        "configurable": {
            "USER_TOKEN": os.getenv("PLANTON_API_KEY"),
            "API_KEY": os.getenv("EXTERNAL_API_KEY")
            # No value needed for public-api (static)
        }
    }
)
```

## Error Messages

Graphton provides clear, actionable error messages for configuration issues.

### System Prompt Errors

```python
# Empty prompt
agent = create_deep_agent(model="claude-sonnet-4.5", system_prompt="")
# ValueError: Configuration validation failed:
# system_prompt cannot be empty. Provide a clear description of the agent's role and capabilities.

# Too short
agent = create_deep_agent(model="claude-sonnet-4.5", system_prompt="Hi")
# ValueError: Configuration validation failed:
# system_prompt is too short (2 chars). Provide at least 10 characters describing the agent's purpose.
```

### Parameter Validation Errors

```python
# Invalid recursion limit
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    recursion_limit=0
)
# ValueError: Configuration validation failed:
# recursion_limit must be positive, got 0. Recommended range: 10-200 depending on agent complexity.

# Invalid temperature
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    temperature=5.0
)
# ValueError: Configuration validation failed:
# temperature must be between 0.0 and 2.0, got 5.0. Use 0.0-0.3 for deterministic output, 0.7-1.0 for creative output.
```

### MCP Configuration Errors

```python
# mcp_servers without mcp_tools
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    mcp_servers={"planton-cloud": {"url": "https://mcp.planton.ai/"}}
)
# ValueError: Configuration validation failed:
# mcp_servers provided but mcp_tools is missing. Specify which tools to load: mcp_tools={'server-name': ['tool1', 'tool2']}

# Server name mismatch
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    mcp_servers={"server-a": {"url": "https://a.example.com/"}},
    mcp_tools={"server-b": ["tool1"]}
)
# ValueError: Configuration validation failed:
# Server(s) configured but no tools specified: {'server-a'}. Add tools for these servers in mcp_tools.
# Tools specified for undefined server(s): {'server-b'}. Add server configurations in mcp_servers.
```

## IDE Support

Graphton uses Pydantic models, enabling excellent IDE support:

### Type Hints

```python
from graphton import create_deep_agent

agent = create_deep_agent(
    model="claude-sonnet-4.5",  # IDE knows: str | BaseChatModel
    system_prompt="...",         # IDE knows: str
    recursion_limit=100,         # IDE knows: int (default: 100)
    temperature=0.7,             # IDE knows: float | None (default: None)
)
```

### Autocomplete

When typing parameter names, your IDE will show:
- Parameter name
- Parameter type
- Default value (if any)
- Docstring

### Error Detection

Invalid configurations are caught by:
1. **IDE type checker**: Warns about type mismatches before running
2. **Pydantic validation**: Catches invalid values at runtime with helpful messages
3. **mypy**: Static type checking in CI/CD pipelines

## Migration from Raw LangGraph

**Before (Raw LangGraph)**:

```python
from deepagents import create_deep_agent as deepagents_create_deep_agent
from langchain_anthropic import ChatAnthropic

# Manual model instantiation
model = ChatAnthropic(
    model_name="claude-sonnet-4-5-20250929",
    max_tokens=1000,
)

# Create agent with manual configuration
agent = deepagents_create_deep_agent(
    model=model,
    tools=[],
    system_prompt=SYSTEM_PROMPT,
    middleware=[],
).with_config({"recursion_limit": 10})
```

**After (Graphton)**:

```python
from graphton import create_deep_agent

# Declarative configuration with validation
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt=SYSTEM_PROMPT,
    recursion_limit=10,
    max_tokens=1000,
)
```

**Benefits**:
- 80% less code
- Early error detection with helpful messages
- Type-safe configuration
- IDE autocomplete support
- Consistent patterns across agents

## Loop Detection

Graphton automatically injects loop detection middleware to prevent infinite loops in autonomous agents. This is a common issue in agent systems and can waste significant resources.

### How It Works

The loop detection middleware:

1. **Tracks tool invocations**: Monitors the last 10 tool calls (tool name + parameter hash)
2. **Detects consecutive repetitions**: If the same tool with similar parameters is called 3+ times in a row, injects a warning message
3. **Detects total repetitions**: If the same tool is called 5+ times total (even with other tools in between), forces graceful conclusion
4. **Intervenes intelligently**: Guides the agent toward different approaches or graceful completion

### Default Configuration

Loop detection is enabled by default with these settings:

```python
# Auto-injected in every agent
LoopDetectionMiddleware(
    history_size=10,              # Track last 10 tool calls
    consecutive_threshold=3,       # Warn after 3 consecutive repeats
    total_threshold=5,             # Stop after 5 total repeats
    enabled=True,                  # Active by default
)
```

### Intervention Strategy

**First Detection (3 consecutive repeats)**: Warning message injected

```
⚠️ LOOP WARNING: Repetitive pattern detected.

You have called 'read_file' 3 times in a row. This suggests you may be 
stuck or approaching the problem incorrectly.

Recommended actions:
1. Try a completely different approach or tool
2. Re-examine your assumptions about the problem
3. Consider if you have enough information to conclude
4. Avoid calling 'read_file' again unless absolutely necessary

Adapt your strategy to make progress.
```

**Second Detection (5 total repeats)**: Final intervention - force stop

```
⚠️ LOOP DETECTED: Critical repetition limit reached.

You have called 'read_file' 5 times with similar parameters. This 
indicates you are stuck in a loop and unable to make progress.

You MUST conclude your work now:
1. Summarize what you have learned so far
2. Explain the obstacle preventing progress
3. Provide your best assessment based on available information
4. Do NOT call 'read_file' again

Conclude gracefully with the information you have gathered.
```

### Why Loop Detection Matters

**Cost Savings**: Prevents wasted LLM API calls on stuck agents

**Reliability**: Agents complete successfully or fail fast with clear reason

**Observability**: Logs show where agents get stuck, informing improvements

**User Experience**: Users get results faster instead of waiting for timeout

### Example: Loop Detection in Action

```python
from graphton import create_deep_agent

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a troubleshooting assistant.",
    recursion_limit=1000,  # High limit for deep investigation
)

# Loop detection automatically prevents infinite loops
# even with high recursion limit
result = agent.invoke({
    "messages": [{"role": "user", "content": "Debug this pipeline failure"}]
})
```

In this example:
- Agent has `recursion_limit=1000` for maximum autonomy
- If agent gets stuck calling the same tool repeatedly, loop detection intervenes
- Agent either adapts its strategy or concludes gracefully
- Cost and time are saved by early intervention

### Monitoring Loop Detection

Loop detection events are logged for observability:

```
WARNING - LOOP WARNING - Consecutive threshold reached: read_file called 3 times in a row
INFO - Loop detection: Warning intervention injected (intervention #1)
WARNING - LOOP DETECTED - Total threshold exceeded: read_file called 5 times
INFO - Loop detection: Final intervention injected, execution will stop
```

These logs help you:
- Identify which tools cause agents to loop
- Understand where agents get stuck
- Tune system prompts to avoid common loops
- Adjust thresholds if needed

### Relationship with Recursion Limit

Loop detection and recursion limit work together:

- **Recursion limit**: Maximum total agent steps (default: 100, recommended: 1000 for autonomous agents)
- **Loop detection**: Stops execution early if repetitive patterns detected

This combination provides:
- **Maximum autonomy**: High recursion limit allows deep investigation
- **Cost protection**: Loop detection prevents wasted iterations
- **Reliability**: Agents complete or fail fast with clear diagnostics


