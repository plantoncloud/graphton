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

**Note**: MCP tool loading middleware is auto-injected when `mcp_servers` and `mcp_tools` are provided.

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

### mcp_servers: dict[str, dict[str, Any]] | None = None

MCP server configurations mapping server names to server config dictionaries.

**Format** (compatible with Cursor's mcp.json):

```python
mcp_servers = {
    "server-name": {
        "transport": "streamable_http",
        "url": "https://mcp.example.com/",
        "auth_from_context": True,  # Default
        "headers": {                 # Optional static headers
            "X-Custom-Header": "value"
        }
    }
}
```

**Server configuration fields**:

- **transport** (str): Only `"streamable_http"` supported currently
- **url** (str): HTTP(S) endpoint URL
- **auth_from_context** (bool): Extract auth token from runtime context (default: `True`)
- **headers** (dict, optional): Static headers to include in requests

**Validation rules**:
- Must be provided together with `mcp_tools`
- Server names must match between `mcp_servers` and `mcp_tools`
- HTTPS recommended for production (HTTP triggers warning for non-localhost)
- Static `Authorization` header triggers warning (conflicts with per-user auth)

**Examples**:

```python
# ✅ Production configuration (HTTPS)
mcp_servers = {
    "planton-cloud": {
        "transport": "streamable_http",
        "url": "https://mcp.planton.ai/",
    }
}

# ✅ Local development (HTTP localhost - no warning)
mcp_servers = {
    "local-server": {
        "transport": "streamable_http",
        "url": "http://localhost:8000/",
    }
}

# ⚠️ HTTP non-localhost (warning issued)
mcp_servers = {
    "dev-server": {
        "transport": "streamable_http",
        "url": "http://dev.example.com/",  # UserWarning: insecure HTTP
    }
}

# ❌ Invalid transport
mcp_servers = {
    "server": {
        "transport": "stdio",  # ValueError: Unsupported transport
        "url": "https://mcp.example.com/",
    }
}
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

```python
from graphton import create_deep_agent

# Comprehensive agent configuration
agent = create_deep_agent(
    # Required
    model="claude-sonnet-4.5",
    system_prompt="You are a Planton Cloud assistant helping users manage cloud resources.",
    
    # MCP integration
    mcp_servers={
        "planton-cloud": {
            "transport": "streamable_http",
            "url": "https://mcp.planton.ai/",
        }
    },
    mcp_tools={
        "planton-cloud": [
            "list_organizations",
            "list_environments_for_org",
            "search_cloud_resources",
            "get_cloud_resource_by_id",
            "get_cloud_resource_schema",
            "create_cloud_resource",
            "update_cloud_resource",
            "delete_cloud_resource",
        ]
    },
    
    # Optional parameters
    recursion_limit=150,
    max_tokens=10000,
    temperature=0.3,
)

# Invoke with per-user authentication
import os
result = agent.invoke(
    {"messages": [{"role": "user", "content": "List my organizations"}]},
    config={
        "configurable": {
            "_user_token": os.getenv("PLANTON_API_KEY")
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

