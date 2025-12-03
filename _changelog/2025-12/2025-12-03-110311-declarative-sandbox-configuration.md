# Declarative Sandbox Configuration for Deep Agents

**Date**: December 3, 2025

## Summary

Added declarative sandbox backend configuration to Graphton's `create_deep_agent()` function, enabling users to configure file system backends through simple dictionary-based configuration. This follows the same declarative pattern established for MCP server configuration, providing a consistent and user-friendly API surface. The implementation supports filesystem backends currently, with extensibility built in for future cloud sandbox providers (Modal, Runloop, Daytona, Harbor).

## Problem Statement

Deep Agents from LangGraph include powerful file operation tools (`read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`) and an `execute` tool for terminal commands. However, these tools only work when a backend implementing `BackendProtocol` or `SandboxBackendProtocol` is provided. 

Graphton was not exposing this backend configuration capability, leaving users unable to leverage file system operations in their agents. The default behavior used ephemeral state storage, which works for simple cases but doesn't provide persistent file access or sandboxed execution environments.

### Pain Points

- **No backend configuration**: Users couldn't configure backends for file operations
- **Inconsistent API**: MCP tools used declarative config, but backends required manual instantiation
- **Missing documentation**: No guidance on how to enable file system operations
- **Limited extensibility**: No clear path to support cloud sandbox providers in the future

## Solution

Introduced a `sandbox_config` parameter to `create_deep_agent()` that accepts configuration dictionaries and automatically creates the appropriate backend instance. This mirrors the MCP configuration pattern, providing a familiar and consistent developer experience.

### Architecture

```
User Configuration (Dict)
    ↓
sandbox_config: {"type": "filesystem", "root_dir": "/workspace"}
    ↓
create_deep_agent()
    ↓
sandbox_factory.create_sandbox_backend(config)
    ↓
FilesystemBackend instance
    ↓
deepagents.create_deep_agent(..., backend=backend)
    ↓
Agent with file operation tools enabled
```

### Key Components

**1. Sandbox Factory** (`sandbox_factory.py`)
- Factory function that creates backend instances from config dictionaries
- Type-based dispatch for different backend providers
- Comprehensive validation and error messages
- Extensible design for adding new backend types

**2. Agent Factory Integration** (`agent.py`)
- Added `sandbox_config` optional parameter
- Automatic backend creation when config is provided
- Backward compatible (parameter is optional)
- Clear documentation and examples

**3. Configuration Validation** (`config.py`)
- Pydantic model validation for sandbox_config
- Type checking and structure validation
- Helpful error messages for common mistakes

**4. Test Suite** (`test_sandbox_config.py`)
- 23 comprehensive tests covering all scenarios
- Backend factory tests
- Agent creation tests
- Configuration validation tests
- Backward compatibility tests

## Implementation Details

### Supported Backend Types

**Filesystem** (Currently Available):
```python
sandbox_config = {
    "type": "filesystem",
    "root_dir": "/workspace"  # optional, defaults to "."
}
```

Provides file operations (read, write, edit, ls, glob, grep) but not terminal execution. The `execute` tool is available but returns an error when called.

**Future Backend Types** (Planned):
- `modal`: Modal.com cloud sandboxes with full execution
- `runloop`: Runloop cloud sandboxes
- `daytona`: Daytona workspace sandboxes  
- `harbor`: LangGraph Cloud/Harbor environments

### Code Changes

**File: `graphton/src/graphton/core/sandbox_factory.py` (NEW)**
```python
def create_sandbox_backend(config: dict[str, Any]) -> BackendProtocol:
    """Create sandbox backend from declarative configuration.
    
    Supports:
    - filesystem: Local filesystem with file operations
    - modal, runloop, daytona, harbor: Coming soon
    """
    backend_type = config.get("type")
    
    if backend_type == "filesystem":
        from deepagents.backends import FilesystemBackend
        root_dir = config.get("root_dir", ".")
        return FilesystemBackend(root_dir=root_dir)
    
    # Validation and future backend support...
```

**File: `graphton/src/graphton/core/agent.py` (MODIFIED)**

Added parameter to function signature:
```python
def create_deep_agent(
    model: str | BaseChatModel,
    system_prompt: str,
    mcp_servers: dict[str, dict[str, Any]] | None = None,
    mcp_tools: dict[str, list[str]] | None = None,
    tools: Sequence[BaseTool] | None = None,
    middleware: Sequence[Any] | None = None,
    context_schema: type[Any] | None = None,
    sandbox_config: dict[str, Any] | None = None,  # NEW
    recursion_limit: int = 100,
    max_tokens: int | None = None,
    temperature: float | None = None,
    **model_kwargs: Any,
) -> CompiledStateGraph:
```

Backend creation logic:
```python
# Create sandbox backend if configured
backend = None
if sandbox_config:
    from graphton.core.sandbox_factory import create_sandbox_backend
    backend = create_sandbox_backend(sandbox_config)

# Pass to deepagents
agent = deepagents_create_deep_agent(
    model=model_instance,
    tools=tools_list,
    system_prompt=system_prompt,
    middleware=middleware_list,
    context_schema=context_schema,
    backend=backend,  # NEW
)
```

**File: `graphton/src/graphton/core/config.py` (MODIFIED)**

Added validation:
```python
sandbox_config: dict[str, Any] | None = None

@field_validator("sandbox_config")
@classmethod
def validate_sandbox_config(
    cls, v: dict[str, Any] | None
) -> dict[str, Any] | None:
    """Validate sandbox configuration structure."""
    if v is None:
        return v
    
    # Validate dict structure
    # Validate 'type' key exists
    # Validate type is supported
    # Return validated config
```

### Usage Examples

**Basic filesystem backend:**
```python
from graphton import create_deep_agent

agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a file management assistant.",
    sandbox_config={"type": "filesystem", "root_dir": "/workspace"}
)

# Agent can now perform file operations
result = agent.invoke({
    "messages": [{"role": "user", "content": "List files in current directory"}]
})
```

**Backward compatible (no sandbox):**
```python
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a helpful assistant."
    # No sandbox_config - uses default ephemeral state
)
```

**Combined with other features:**
```python
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a DevOps assistant.",
    sandbox_config={"type": "filesystem"},
    mcp_servers={"planton-cloud": {...}},
    mcp_tools={"planton-cloud": ["list_organizations"]},
    recursion_limit=75,
    max_tokens=10000
)
```

## Benefits

### For Users

**Consistent API**: Sandbox configuration follows the same pattern as MCP configuration - simple dictionaries, no manual instantiation required.

**Declarative**: Express what you want, not how to create it:
```python
# Before (not available in Graphton)
from deepagents.backends import FilesystemBackend
backend = FilesystemBackend(root_dir="/workspace")
# ...manual agent creation...

# After (Graphton)
sandbox_config = {"type": "filesystem", "root_dir": "/workspace"}
agent = create_deep_agent(..., sandbox_config=sandbox_config)
```

**Better Error Messages**: Pydantic validation provides clear, actionable errors:
```
ValueError: sandbox_config must include 'type' key.
Supported types: filesystem, modal, runloop, daytona, harbor
```

**File Operations Enabled**: Users can now leverage Deep Agents' file system tools for reading, writing, and editing files.

### For Maintainers

**Extensible Design**: Adding new backend types is straightforward - just add a new case to the factory function.

**Type Safe**: Pydantic validation catches configuration errors at agent creation time, not runtime.

**Well Tested**: 23 comprehensive tests ensure robustness and catch regressions.

**Documented**: Clear docstrings and examples make the feature discoverable and usable.

## Test Coverage

**23 tests, all passing:**

1. **Sandbox Backend Factory** (10 tests)
   - Creating backends with valid configs
   - Error handling for invalid configs
   - Validation of all supported types

2. **Agent Creation** (7 tests)
   - Creating agents with/without sandbox
   - Configuration validation
   - Error handling

3. **Backward Compatibility** (3 tests)
   - Existing code continues to work
   - Optional parameter doesn't break anything
   - Combining with other features

4. **Configuration Validation** (3 tests)
   - Valid configs pass
   - Invalid configs rejected with helpful errors
   - Type validation

## Impact

### Current Impact

- **Graphton users** can now configure filesystem backends for file operations
- **Existing code** remains unaffected (backward compatible)
- **API surface** is consistent with MCP configuration pattern
- **Documentation** clearly explains usage and limitations

### Future Impact

The extensible architecture supports adding cloud sandbox backends:

- **Modal.com**: Remote sandboxes with full execution capabilities
- **Runloop**: Cloud-based execution environments
- **Daytona**: Workspace-based sandboxes
- **Harbor/LangGraph Cloud**: Production deployment environments

Each can be added with minimal changes - just implement the backend type in the factory function.

## Known Limitations

**Filesystem Backend Scope**: The current `filesystem` backend type provides file operations but not terminal execution. The `execute` tool is present but returns an error when called. This is a limitation of DeepAgents' `FilesystemBackend` implementation, not Graphton.

For terminal execution, future backend types (Modal, Runloop, etc.) that implement `SandboxBackendProtocol` will provide full capabilities.

**Single Backend**: Currently, only one backend can be configured per agent. Composite backends (routing different paths to different backends) must be manually created and passed as instances.

## Design Decisions

### Why Dictionary Configuration?

**Consistency**: Matches the MCP server configuration pattern already established in Graphton. Users learn one pattern and apply it everywhere.

**Serializable**: Dict configs can be easily serialized to JSON/YAML, enabling external configuration files and environment-specific settings.

**Extensible**: Easy to add new keys for backend-specific options without changing the API signature.

### Why Factory Pattern?

**Separation of Concerns**: Backend creation logic is isolated in the factory, keeping the agent creation function clean.

**Testability**: Factory function can be tested independently of agent creation.

**Flexibility**: Users can still manually create and pass backend instances if they need custom configuration.

### Why Optional Parameter?

**Backward Compatibility**: Existing Graphton code continues to work without changes.

**Progressive Enhancement**: Users can add sandbox configuration when they need it, not upfront.

**Default Behavior**: The default (no backend) is reasonable for many use cases - agents work with ephemeral state.

## Related Work

**Builds on**:
- Universal MCP Authentication Framework (2025-11-28)
- Phase 3: MCP Integration (2025-11-27)

**Enables**:
- Future cloud sandbox integrations
- Persistent file storage patterns
- Multi-environment agent deployments

**Follows patterns from**:
- MCP server declarative configuration
- Pydantic validation for agent config

## Code Metrics

- **Files created**: 2 (factory, tests)
- **Files modified**: 2 (agent.py, config.py)
- **Lines of code**: ~300 (excluding tests)
- **Test lines**: ~250
- **Test coverage**: 23 tests, 100% pass rate
- **Backward compatibility**: ✅ All existing tests pass

---

**Status**: ✅ Production Ready  
**Timeline**: Single session implementation (~2 hours)  
**Testing**: Comprehensive (23 tests, all passing)

