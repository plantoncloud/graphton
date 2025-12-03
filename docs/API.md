# API Reference

Complete API reference for Graphton.

## Table of Contents

- [create_deep_agent](#create_deep_agent)
- [AgentConfig](#agentconfig)
- [McpToolsLoader](#mcptoolsloader)
- [Template Functions](#template-functions)
- [Model Utilities](#model-utilities)

## create_deep_agent

Main entry point for creating Deep Agents with Graphton.

```python
def create_deep_agent(
    model: str | BaseChatModel,
    system_prompt: str,
    mcp_servers: dict[str, dict[str, Any]] | None = None,
    mcp_tools: dict[str, list[str]] | None = None,
    tools: Sequence[BaseTool] | None = None,
    middleware: Sequence[Any] | None = None,
    context_schema: type[Any] | None = None,
    recursion_limit: int = 100,
    max_tokens: int | None = None,
    temperature: float | None = None,
    auto_enhance_prompt: bool = True,
    **model_kwargs: Any,
) -> CompiledStateGraph:
```

### Parameters

#### model (required)
- **Type:** `str | BaseChatModel`
- **Description:** Model name string or LangChain model instance

**String format** (recommended):
```python
# Anthropic models
model = "claude-sonnet-4.5"  # Claude Sonnet 4.5
model = "claude-opus-4"      # Claude Opus 4
model = "claude-haiku-4"     # Claude Haiku 4

# OpenAI models
model = "gpt-4o"             # GPT-4 Optimized
model = "gpt-4o-mini"        # GPT-4 Optimized Mini
model = "gpt-4-turbo"        # GPT-4 Turbo
model = "o1"                 # OpenAI o1
model = "o1-mini"            # OpenAI o1 Mini

# Full model IDs also supported
model = "claude-sonnet-4-5-20250929"
```

**Model instance** (advanced):
```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Custom Anthropic configuration
model = ChatAnthropic(
    model="claude-opus-4-20250514",
    max_tokens=30000,
    temperature=0.3
)

# Custom OpenAI configuration
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.0
)
```

**Note:** When passing a model instance, `max_tokens`, `temperature`, and other model parameters are ignored.

#### system_prompt (required)
- **Type:** `str`
- **Description:** System prompt defining agent behavior. By default, this is automatically enhanced with awareness of Deep Agents capabilities (planning, file system, MCP tools).
- **Validation:** Must be at least 10 characters
- **Enhancement:** Automatically enriched with capability context unless `auto_enhance_prompt=False`

```python
# Good examples - will be auto-enhanced
system_prompt = """You are a helpful coding assistant specializing in Python.

Your capabilities:
- Write clean, well-documented code
- Explain complex concepts clearly
- Suggest best practices
"""

system_prompt = "You are a cloud infrastructure expert helping users manage AWS resources."

# Note: Graphton automatically adds context about planning system,
# file system tools, and MCP capabilities (if configured)
```

#### mcp_servers (optional)
- **Type:** `dict[str, dict[str, Any]] | None`
- **Default:** `None`
- **Description:** MCP server configurations with optional template variables

**Supports any format** compatible with the MCP client. Use `{{VAR}}` for dynamic values.

**Examples:**

```python
# Dynamic configuration (per-user authentication)
mcp_servers = {
    "planton-cloud": {
        "transport": "streamable_http",
        "url": "https://mcp.planton.ai/",
        "headers": {
            "Authorization": "Bearer {{USER_TOKEN}}"  # Template variable
        }
    }
}

# Static configuration (shared credentials)
mcp_servers = {
    "public-api": {
        "transport": "http",
        "url": "https://api.example.com/mcp",
        "headers": {
            "X-API-Key": "hardcoded-key-123"  # No templates
        }
    }
}

# Multiple servers with mixed authentication
mcp_servers = {
    "planton-cloud": {
        "transport": "streamable_http",
        "url": "https://mcp.planton.ai/",
        "headers": {"Authorization": "Bearer {{USER_TOKEN}}"}
    },
    "external-api": {
        "transport": "http",
        "url": "{{BASE_URL}}/api",
        "headers": {"X-API-Key": "{{API_KEY}}"}
    },
    "public-api": {
        "transport": "http",
        "url": "https://public.example.com",
        "headers": {"X-Client-ID": "client-123"}
    }
}
```

**Validation:**
- Must be provided together with `mcp_tools`
- Server names must match between `mcp_servers` and `mcp_tools`

#### mcp_tools (optional)
- **Type:** `dict[str, list[str]] | None`
- **Default:** `None`
- **Description:** Tool names to load from each MCP server

```python
# Single server
mcp_tools = {
    "planton-cloud": [
        "list_organizations",
        "list_environments_for_org",
        "search_cloud_resources",
        "create_cloud_resource",
    ]
}

# Multiple servers
mcp_tools = {
    "planton-cloud": ["list_organizations", "create_cloud_resource"],
    "aws-tools": ["list_ec2_instances", "create_s3_bucket"],
}
```

**Validation:**
- Must be provided together with `mcp_servers`
- Server names must match those in `mcp_servers`
- Tool lists cannot be empty
- Tool names must be strings with alphanumeric characters, underscores, or hyphens
- No duplicate tool names within a server

#### tools (optional)
- **Type:** `Sequence[BaseTool] | None`
- **Default:** `None`
- **Description:** Additional non-MCP tools for the agent

```python
from langchain_core.tools import tool

@tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # Implementation here
    return results

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a helpful assistant with calculator and web search.",
    tools=[calculate, search_web],
)
```

#### middleware (optional)
- **Type:** `Sequence[Any] | None`
- **Default:** `None`
- **Description:** Additional middleware for the agent

**Note:** MCP tool loading middleware is automatically injected when `mcp_servers` and `mcp_tools` are provided.

```python
from deepagents import LoggingMiddleware

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    middleware=[LoggingMiddleware()],
)
```

#### context_schema (optional)
- **Type:** `type[Any] | None`
- **Default:** `None` (uses `FilesystemState` from deepagents)
- **Description:** Custom state schema for the agent

```python
from pydantic import BaseModel

class CustomState(BaseModel):
    messages: list
    custom_field: str
    user_id: int

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    context_schema=CustomState,
)
```

#### recursion_limit (optional)
- **Type:** `int`
- **Default:** `100`
- **Description:** Maximum agent reasoning steps before stopping
- **Validation:** Must be positive (> 0)

```python
# Simple agents
recursion_limit = 20

# Moderate complexity (default)
recursion_limit = 100

# Complex reasoning
recursion_limit = 200
```

**Note:** Values > 500 trigger a `UserWarning`.

#### max_tokens (optional)
- **Type:** `int | None`
- **Default:** `None` (provider defaults: Anthropic=20000, OpenAI=model default)
- **Description:** Maximum tokens for model output
- **Note:** Ignored when passing a model instance

```python
# Override default
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    max_tokens=5000,
)
```

#### temperature (optional)
- **Type:** `float | None`
- **Default:** `None` (provider default)
- **Description:** Model temperature controlling output randomness
- **Validation:** Must be between 0.0 and 2.0
- **Note:** Ignored when passing a model instance

```python
# Conservative (deterministic)
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a code reviewer.",
    temperature=0.0  # Very deterministic
)

# Creative
agent = create_deep_agent(
    model="gpt-4o",
    system_prompt="You are a creative writing assistant.",
    temperature=0.9  # More random/creative
)
```

#### auto_enhance_prompt (optional)
- **Type:** `bool`
- **Default:** `True`
- **Description:** Whether to automatically enhance system_prompt with awareness of Deep Agents capabilities
- **Added:** Phase 5

**When enabled** (default):
- Automatically appends high-level context about planning system, file system, and MCP tools
- Helps agents understand what capabilities they have and when to use them
- No action needed from users - enhancement happens automatically

**When disabled** (`auto_enhance_prompt=False`):
- Uses system_prompt exactly as provided
- Useful when you've already included detailed capability descriptions
- Or when you want complete control over the prompt

```python
# Default: automatic enhancement
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a research assistant.",
    # auto_enhance_prompt=True by default
)
# Agent will understand planning and file system capabilities

# Opt-out: use prompt as-is
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="""You are a research assistant.

    You have access to:
    - Planning tools (write_todos, read_todos) for complex tasks
    - File system (ls, read_file, write_file, etc.) for context
    - [... detailed capability descriptions ...]
    """,
    auto_enhance_prompt=False,  # Disable automatic enhancement
)
```

**Note on redundancy:**  
If your system_prompt already mentions planning or file system capabilities, some overlap will occur when enhancement is enabled. This is intentional and acceptable - LLMs handle redundant information gracefully, and reinforcement is better than missing critical context.

```python
# Deterministic (code generation)
temperature = 0.0

# Balanced (general use)
temperature = 0.7

# Creative (content generation)
temperature = 1.0
```

#### **model_kwargs (optional)
- **Type:** `Any`
- **Description:** Additional model-specific parameters
- **Note:** Ignored when passing a model instance

```python
# Anthropic-specific
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="...",
    top_p=0.95,
    top_k=40,
)

# OpenAI-specific
agent = create_deep_agent(
    model="gpt-4o",
    system_prompt="...",
    frequency_penalty=0.0,
    presence_penalty=0.0,
)
```

### Returns

- **Type:** `CompiledStateGraph`
- **Description:** A compiled LangGraph agent ready to invoke

### Raises

- **ValueError:** If configuration validation fails (system_prompt empty, invalid recursion_limit, MCP config errors, etc.)
- **ValidationError:** If Pydantic validation fails

### Examples

#### Basic Agent

```python
from graphton import create_deep_agent

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a helpful assistant.",
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Hello!"}]
})

print(result["messages"][-1]["content"])
```

#### Agent with Custom Parameters

```python
agent = create_deep_agent(
    model="gpt-4o",
    system_prompt="You are a code reviewer.",
    temperature=0.3,
    max_tokens=5000,
    recursion_limit=50,
)
```

#### Agent with Static MCP Tools

```python
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are an API assistant.",
    mcp_servers={
        "public-api": {
            "transport": "http",
            "url": "https://api.example.com/mcp",
            "headers": {"X-API-Key": "hardcoded-key-123"}
        }
    },
    mcp_tools={
        "public-api": ["search", "fetch"]
    }
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Search for Python"}]
})
```

#### Agent with Dynamic MCP Authentication

```python
import os

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a Planton Cloud assistant.",
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
        "planton-cloud": ["list_organizations", "search_cloud_resources"]
    },
    recursion_limit=150,
)

# Invoke with user-specific token
result = agent.invoke(
    {"messages": [{"role": "user", "content": "List my organizations"}]},
    config={
        "configurable": {
            "USER_TOKEN": os.getenv("PLANTON_API_KEY")  # Substituted at runtime
        }
    }
)
```

#### Multi-Server with Mixed Authentication

```python
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a multi-cloud assistant.",
    mcp_servers={
        "planton-cloud": {
            "transport": "streamable_http",
            "url": "https://mcp.planton.ai/",
            "headers": {"Authorization": "Bearer {{USER_TOKEN}}"}
        },
        "external-api": {
            "transport": "http",
            "url": "https://api.example.com",
            "headers": {"X-API-Key": "{{API_KEY}}"}
        },
        "public-api": {
            "transport": "http",
            "url": "https://public.example.com",
            "headers": {"X-Client-ID": "client-123"}
        }
    },
    mcp_tools={
        "planton-cloud": ["list_organizations"],
        "external-api": ["search"],
        "public-api": ["get_info"]
    }
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "List resources"}]},
    config={
        "configurable": {
            "USER_TOKEN": os.getenv("PLANTON_API_KEY"),
            "API_KEY": os.getenv("EXTERNAL_API_KEY")
        }
    }
)
```

## AgentConfig

Pydantic model for validating agent configuration.

```python
class AgentConfig(BaseModel):
    model: str | BaseChatModel
    system_prompt: str
    mcp_servers: dict[str, dict[str, Any]] | None = None
    mcp_tools: dict[str, list[str]] | None = None
    tools: Sequence[BaseTool] | None = None
    middleware: Sequence[Any] | None = None
    context_schema: type[Any] | None = None
    recursion_limit: int = 100
    max_tokens: int | None = None
    temperature: float | None = None
```

### Validation Rules

The config model validates:

1. **System Prompt:**
   - Cannot be empty or whitespace-only
   - Must be at least 10 characters

2. **Recursion Limit:**
   - Must be positive (> 0)
   - Warning if > 500

3. **Temperature:**
   - Must be between 0.0 and 2.0

4. **MCP Configuration:**
   - `mcp_servers` and `mcp_tools` must be provided together
   - Server names must match between the two
   - Tool lists cannot be empty
   - Tool names must be valid (alphanumeric, underscores, hyphens)

### Usage

Typically not used directly - validation happens automatically in `create_deep_agent()`.

```python
# Manual validation (advanced)
from graphton.core.config import AgentConfig

config = AgentConfig(
    model="claude-sonnet-4.5",
    system_prompt="You are a helpful assistant.",
    recursion_limit=100,
)
```

## McpToolsLoader

Middleware for loading MCP tools with dynamic authentication.

### Class Definition

```python
class McpToolsLoader:
    def __init__(
        self,
        mcp_servers: dict[str, dict[str, Any]],
        mcp_tools: dict[str, list[str]],
    ):
```

### Parameters

- **mcp_servers:** MCP server configurations (supports template variables)
- **mcp_tools:** Tool names to load from each server

### Usage

**Note:** This middleware is automatically created and injected by `create_deep_agent()` when MCP configuration is provided. You typically don't need to use it directly.

```python
# Manual usage (advanced)
from graphton.core.middleware import McpToolsLoader

middleware = McpToolsLoader(
    mcp_servers={
        "planton-cloud": {
            "transport": "streamable_http",
            "url": "https://mcp.planton.ai/",
            "headers": {"Authorization": "Bearer {{USER_TOKEN}}"}
        }
    },
    mcp_tools={
        "planton-cloud": ["list_organizations"]
    }
)
```

## Template Functions

Utilities for working with template variables in MCP configurations.

### has_templates

Check if configuration contains template variables.

```python
def has_templates(config: dict[str, Any]) -> bool:
```

**Parameters:**
- **config:** Configuration dictionary to check

**Returns:**
- `True` if config contains `{{VAR}}` patterns, `False` otherwise

**Example:**

```python
from graphton import has_templates

config = {
    "headers": {"Authorization": "Bearer {{USER_TOKEN}}"}
}

if has_templates(config):
    print("Dynamic configuration detected")
else:
    print("Static configuration detected")
```

### extract_template_vars

Extract all template variables from configuration.

```python
def extract_template_vars(config: dict[str, Any]) -> set[str]:
```

**Parameters:**
- **config:** Configuration dictionary

**Returns:**
- Set of variable names found in `{{VAR}}` patterns

**Example:**

```python
from graphton import extract_template_vars

config = {
    "url": "{{BASE_URL}}/api",
    "headers": {
        "Authorization": "Bearer {{USER_TOKEN}}",
        "X-API-Key": "{{API_KEY}}"
    }
}

vars = extract_template_vars(config)
print(vars)  # {'BASE_URL', 'USER_TOKEN', 'API_KEY'}
```

### substitute_templates

Substitute template variables with actual values.

```python
def substitute_templates(
    config: dict[str, Any],
    values: dict[str, str]
) -> dict[str, Any]:
```

**Parameters:**
- **config:** Configuration with template variables
- **values:** Dictionary mapping variable names to values

**Returns:**
- New configuration with templates substituted

**Raises:**
- **ValueError:** If required template variable is missing

**Example:**

```python
from graphton import substitute_templates

config = {
    "url": "{{BASE_URL}}/api",
    "headers": {"Authorization": "Bearer {{USER_TOKEN}}"}
}

substituted = substitute_templates(
    config,
    {"BASE_URL": "https://api.example.com", "USER_TOKEN": "secret-token"}
)

print(substituted)
# {
#     "url": "https://api.example.com/api",
#     "headers": {"Authorization": "Bearer secret-token"}
# }
```

## Model Utilities

### parse_model_string

Parse model name string and return configured model instance.

```python
def parse_model_string(
    model: str,
    max_tokens: int | None = None,
    temperature: float | None = None,
    **model_kwargs: Any,
) -> BaseChatModel:
```

**Parameters:**
- **model:** Model name string
- **max_tokens:** Override default max_tokens
- **temperature:** Override default temperature
- **model_kwargs:** Additional model-specific parameters

**Returns:**
- Configured `BaseChatModel` instance

**Raises:**
- **ValueError:** If model string is invalid or unsupported

**Supported Models:**

```python
# Anthropic (friendly names)
"claude-sonnet-4.5" → claude-sonnet-4-5-20250929
"claude-opus-4"    → claude-opus-4-20250514
"claude-haiku-4"   → claude-haiku-4-20250313

# OpenAI
"gpt-4o"
"gpt-4o-mini"
"gpt-4-turbo"
"o1"
"o1-mini"

# Full model IDs also supported
"claude-sonnet-4-5-20250929"
```

**Example:**

```python
from graphton.core.models import parse_model_string

# Parse with defaults
model = parse_model_string("claude-sonnet-4.5")

# Parse with custom parameters
model = parse_model_string(
    "claude-sonnet-4.5",
    max_tokens=10000,
    temperature=0.7
)
```

## Type Hints

Graphton uses type hints extensively for better IDE support:

```python
from typing import Any, Sequence
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

# All functions have complete type hints
agent: CompiledStateGraph = create_deep_agent(
    model: str | BaseChatModel,
    system_prompt: str,
    ...
)
```

## Exports

Public API exports from `graphton`:

```python
from graphton import (
    __version__,              # Package version
    create_deep_agent,        # Main factory function
    AgentConfig,              # Configuration model
    McpToolsLoader,           # MCP middleware
    extract_template_vars,    # Template utilities
    has_templates,
    substitute_templates,
)
```

## Version

```python
import graphton
print(graphton.__version__)  # "0.1.0"
```

## See Also

- [Configuration Guide](CONFIGURATION.md) - Complete configuration reference
- [Examples](../examples/) - Usage examples
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [Migration Guide](MIGRATION.md) - Migrating from raw LangGraph
