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

🚧 **Phase 1 (Current)**: Foundation - Project structure and packaging  
🔜 **Phase 2**: Core agent factory - Model and system prompt handling  
🔜 **Phase 3**: MCP integration - Server config and tool loading  
🔜 **Phase 4**: Configuration validation - Pydantic models  
🔜 **Phase 5**: Documentation and open source release  

## Installation

**Coming Soon**: Graphton will be published to PyPI after Phase 5.

```bash
pip install graphton
# or
poetry add graphton
```

## Quick Start

**Coming Soon**: Full quick start guide will be available after Phase 2-3 implementation.

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

### Phase 2: Agent Factory (Next)
- [ ] `create_deep_agent()` function
- [ ] Model name parsing
- [ ] System prompt handling
- [ ] State schema configuration
- [ ] Basic agent creation without MCP tools

### Phase 3: MCP Integration
- [ ] MCP server configuration parser
- [ ] Tool loading with per-user authentication
- [ ] Automatic tool wrapper generation
- [ ] Dynamic middleware injection
- [ ] Integration tests with mock MCP server

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

