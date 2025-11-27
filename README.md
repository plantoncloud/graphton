# Graphton

**Declarative agent creation for LangGraph - eliminate boilerplate, build agents in minutes**

[![CI](https://github.com/plantoncloud-inc/graphton/actions/workflows/ci.yml/badge.svg)](https://github.com/plantoncloud-inc/graphton/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)

## Overview

Graphton is a declarative framework that eliminates boilerplate when creating LangGraph agents with MCP (Model Context Protocol) tools. Build production-ready agents in 3-10 lines instead of 100+.

### The Problem

Building LangGraph agents currently requires significant boilerplate:
- 100+ lines of setup code before writing agent logic
- Manual MCP client creation with authentication
- Writing tool wrapper functions for every MCP tool
- Configuring middleware and handling async/sync patterns
- Repeating the same patterns across multiple agents

### The Solution

Graphton provides a declarative API that abstracts away the boilerplate while maintaining full power and flexibility:

```python
from graphton import create_deep_agent

# That's it! Agent ready in ~10 lines
graph = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt=YOUR_SYSTEM_PROMPT,
    
    mcp_servers={
        "planton-cloud": {
            "transport": "streamable_http",
            "url": "https://mcp.planton.ai/",
            "auth_from_context": True,
        }
    },
    
    mcp_tools={
        "planton-cloud": [
            "get_cloud_resource_schema",
            "create_cloud_resource",
        ]
    }
)

# Invoke with user credentials
result = graph.invoke(
    {"messages": [...]}, 
    config={"configurable": {"_user_token": user_token}}
)
```

## Features

- **🚀 Rapid Development**: Create agents in minutes, not hours
- **🔒 Per-User Authentication**: Built-in support for multi-tenant MCP authentication
- **🎯 Declarative Configuration**: Describe what you want, not how to build it
- **🛠️ Zero Boilerplate**: No manual tool wrappers, middleware, or client setup
- **✅ Type-Safe**: Full Pydantic validation with clear error messages
- **🔌 MCP-First**: First-class support for Model Context Protocol tools
- **📦 Production-Ready**: Battle-tested patterns from the graph-fleet service

## Status

✅ **Phase 1**: Foundation - Project structure and packaging  
✅ **Phase 2**: Core agent factory - Model and system prompt handling  
✅ **Phase 3 (Current)**: MCP integration - Server config and tool loading  
🔜 **Phase 4**: Configuration validation enhancements  
🔜 **Phase 5**: Documentation and open source release  

## Installation

**Coming Soon**: Graphton will be published to PyPI after Phase 5.

For now, you can install from source:

```bash
# Clone the repository
git clone https://github.com/plantoncloud-inc/graphton.git
cd graphton

# Install with Poetry
poetry install

# Or install in development mode with pip
pip install -e .
```

## Quick Start

### Basic Agent Creation

Graphton eliminates boilerplate when creating LangGraph Deep Agents. Here's how to create a simple agent:

```python
from graphton import create_deep_agent

# Create an agent with just model name and system prompt
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a helpful assistant that answers questions concisely.",
)

# Invoke the agent
result = agent.invoke({
    "messages": [{"role": "user", "content": "What is the capital of France?"}]
})

print(result["messages"][-1]["content"])
```

That's it! No need to:
- Manually instantiate `ChatAnthropic` or other model classes
- Configure model parameters (sensible defaults provided)
- Set up recursion limits
- Write boilerplate configuration code

### Supported Models

**Anthropic** (with friendly aliases):
- `claude-sonnet-4.5` → claude-sonnet-4-5-20250929
- `claude-opus-4` → claude-opus-4-20250514
- `claude-haiku-4` → claude-haiku-4-20250313

**OpenAI**:
- `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- `o1`, `o1-mini`

### Custom Parameters

You can override defaults easily:

```python
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a creative writer.",
    temperature=0.9,        # More creative
    max_tokens=5000,        # Limit response length
    recursion_limit=50,     # Lower recursion limit
)
```

### Advanced Usage

For complete control, you can pass a model instance directly:

```python
from langchain_anthropic import ChatAnthropic

model = ChatAnthropic(
    model="claude-opus-4-20250514",
    max_tokens=30000,
    temperature=0.5,
    top_p=0.9,
)

agent = create_deep_agent(
    model=model,
    system_prompt="You are a research assistant.",
)
```

### Multi-Turn Conversations

Agents maintain conversation context:

```python
# First turn
result = agent.invoke({
    "messages": [{"role": "user", "content": "What is 5+3?"}]
})

# Continue the conversation
messages = result["messages"]
messages.append({"role": "user", "content": "And what is that times 2?"})

result = agent.invoke({"messages": messages})
```

### Examples

See the [`examples/`](examples/) directory for complete working examples:
- [`simple_agent.py`](examples/simple_agent.py) - Basic agent creation and usage
- [`mcp_agent.py`](examples/mcp_agent.py) - Agent with MCP tools from Planton Cloud

### MCP Tools Integration (Phase 3)

Create agents with MCP (Model Context Protocol) tools with zero boilerplate:

```python
from graphton import create_deep_agent
import os

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a Planton Cloud assistant.",
    
    # MCP server configuration (Cursor-compatible format)
    mcp_servers={
        "planton-cloud": {
            "transport": "streamable_http",
            "url": "https://mcp.planton.ai/",
        }
    },
    
    # Select which tools to load
    mcp_tools={
        "planton-cloud": [
            "list_organizations",
            "list_environments_for_org",
            "create_cloud_resource",
        ]
    }
)

# Invoke with per-user authentication
result = agent.invoke(
    {"messages": [{"role": "user", "content": "List my organizations"}]},
    config={
        "configurable": {
            "_user_token": os.getenv("PLANTON_API_KEY")
        }
    }
)
```

**Key Features**:
- ✅ **Zero Tool Wrappers**: No manual `@tool` decorator code required
- ✅ **Per-User Authentication**: Pass tokens via config for multi-tenant apps
- ✅ **Works Everywhere**: Local and remote LangGraph Cloud deployments
- ✅ **Auto-Loading**: Tools loaded on first invocation with your credentials
- ✅ **Type-Safe**: Pydantic validation with clear error messages

**Why It Works Everywhere**:

Unlike approaches that rely on `runtime.context` (unavailable in LangGraph Cloud), Graphton uses Python's `contextvars` and config parameter passing. This ensures your agents work identically in local development and production deployments.

See [`examples/mcp_agent.py`](examples/mcp_agent.py) for a complete working example.

## Motivation

The Graphton Framework was born from building the [graph-fleet](https://github.com/plantoncloud-inc/graph-fleet) service for Planton Cloud. After implementing three agents (AWS RDS Instance Creator, RDS Manifest Generator, Session Subject Generator), we discovered substantial code duplication—each requiring 100+ lines of configuration before writing actual agent logic.

Key insights:
- **High friction for new agents**: 30-60 minutes of setup per agent
- **Inconsistent patterns**: Each agent handling MCP loading differently  
- **Maintenance burden**: Bug fixes replicated across all agents
- **Steep learning curve**: New developers must understand LangGraph, MCP, middleware, async/sync patterns, and authentication flows

Graphton abstracts these patterns into a declarative framework, making agent creation fast, consistent, and maintainable.

## Design Philosophy

1. **Declarative over Imperative**: Describe what you want (model, tools, prompt), not how to build it
2. **Smart Defaults, Easy Overrides**: Sensible defaults for 90% of cases, full control when needed
3. **Consistency with Ecosystem**: MCP config format matches Cursor, follows LangGraph patterns
4. **Progressive Disclosure**: Simple APIs for simple cases, advanced options available

## Roadmap

### Phase 1: Foundation ✅ (Current)
- [x] Project structure and packaging
- [x] Poetry configuration
- [x] Development tooling (ruff, mypy, pytest)
- [x] CI/CD setup
- [x] Basic import tests

### Phase 2: Agent Factory ✅ (Complete)
- [x] `create_deep_agent()` function
- [x] Model name parsing (Anthropic and OpenAI)
- [x] System prompt handling
- [x] State schema configuration
- [x] Basic agent creation without MCP tools
- [x] Parameter overrides (max_tokens, temperature)
- [x] Comprehensive unit and integration tests

### Phase 3: MCP Integration ✅ (Complete)
- [x] MCP server configuration parser
- [x] Tool loading with per-user authentication
- [x] Automatic tool wrapper generation
- [x] Dynamic middleware injection
- [x] Context-based token storage (works in local + remote)
- [x] Integration tests with real and mock MCP servers

### Phase 4: Configuration Validation
- [ ] Pydantic models for validation
- [ ] Clear error messages
- [ ] Type hints throughout
- [ ] URL and tool name validation

### Phase 5: Documentation & Release
- [ ] Comprehensive README
- [ ] API documentation
- [ ] Example agents
- [ ] Migration guide from raw LangGraph
- [ ] PyPI publication (v0.1.0)

### Phase 6: Production Validation
- [ ] Migrate graph-fleet agents to Graphton
- [ ] Real-world testing and refinement
- [ ] Performance optimization

## Related Projects

- **[LangGraph](https://github.com/langchain-ai/langgraph)**: Graphton builds on top of LangGraph
- **[graph-fleet](https://github.com/plantoncloud-inc/graph-fleet)**: Reference implementation using Graphton patterns
- **[deepagents](https://github.com/langchain-ai/deepagents)**: Deep Agent pattern that Graphton wraps

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/plantoncloud-inc/graphton.git
cd graphton

# Install dependencies
make deps

# Run tests
make test

# Run linting
make lint

# Run type checking
make typecheck

# Run all checks
make build
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/plantoncloud-inc/graphton/issues)
- **Discussions**: [GitHub Discussions](https://github.com/plantoncloud-inc/graphton/discussions)
- **Documentation**: [GitHub README](https://github.com/plantoncloud-inc/graphton#readme)

## Acknowledgments

Built with ❤️ by [Planton Cloud](https://planton.cloud) engineering team.

Inspired by the needs of the graph-fleet service and the broader LangGraph community.

