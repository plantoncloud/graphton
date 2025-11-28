# Graphton Changelog

## [Unreleased] - 2025-11-28

### Fixed

#### Middleware Signature Compatibility
- **BREAKING FIX**: Updated `McpToolsLoader.before_agent()` and `after_agent()` method signatures to match LangGraph's Runtime protocol
  - Changed parameter name from `config` to `runtime` to align with LangGraph's expected signature
  - Updated config extraction logic to use `runtime.config` for Runtime objects
  - Maintained backward compatibility with plain dict for tests (via `isinstance` check)
  - **Impact**: Resolves `TypeError: missing 1 required positional argument: 'config'` in graph-fleet deployments
  - **Files**: `src/graphton/core/middleware.py`

### Added

#### Dynamic Client Factory Pattern
- Added `AuthenticatedMcpToolNode` class for per-request MCP client creation
  - Implements secure per-user authentication without global middleware state
  - Creates fresh MCP client for each request with user-specific credentials
  - Thread-safe alternative to middleware-based authentication
  - **Use Case**: High-concurrency, multi-tenant environments requiring maximum security
  - **Files**: `src/graphton/core/authenticated_tool_node.py` (new)

#### Documentation
- Added comprehensive implementation summary documenting:
  - Problems fixed and root causes
  - Architecture patterns (Middleware vs Dynamic Client Factory)
  - Testing checklist and deployment instructions
  - Expected behavior before/after fixes
  - Future enhancement roadmap
  - **Files**: `IMPLEMENTATION_SUMMARY.md` (new)

### Technical Details

#### Middleware Signature Change

**Before:**
```python
def before_agent(
    self,
    state: AgentState[Any],
    config: Runtime[None] | dict[str, Any],  # Named 'config'
) -> dict[str, Any] | None:
    # Accessed config.context for Runtime objects
    if hasattr(config, 'context'):
        configurable = config.context
```

**After:**
```python
def before_agent(
    self,
    state: AgentState[Any],
    runtime: Runtime[None] | dict[str, Any],  # Named 'runtime'
) -> dict[str, Any] | None:
    # Accesses runtime.config for Runtime objects
    if hasattr(runtime, 'config'):
        config = runtime.config
        configurable = config.get("configurable", {})
```

#### Config Extraction Logic

The updated middleware now properly handles three scenarios:
1. **Production (Runtime object)**: Extracts config via `runtime.config["configurable"]`
2. **Tests (plain dict)**: Directly accesses `runtime["configurable"]`
3. **Error case**: Raises ValueError with helpful message if neither format matches

### Research Attribution

These fixes are based on comprehensive research documented in:
- **Research**: `graphton/.cursor/plans/LangGraph Per-User MCP Auth.md`
- **Findings**: Section 3 (Diagnostic Analysis), Section 4 (Middleware Solution)
- **Pattern**: Section 6 (Dynamic Client Factory - The Robust Solution)

### Compatibility

- **LangGraph**: Compatible with LangGraph v0.2+ Runtime protocol
- **deepagents**: Compatible with deepagents v0.1+ middleware protocol
- **Python**: Python 3.10+
- **Tests**: All existing tests remain compatible (dict-based config still supported)

### Migration Guide

For existing Graphton users:

**No code changes required** - the fix is backward compatible. However, if you were patching or working around the middleware error, you can now remove those workarounds.

**Using Dynamic Client Factory (optional):**
If you want to use the more robust pattern for high-security scenarios:

```python
from graphton.core.authenticated_tool_node import AuthenticatedMcpToolNode

# Define server configs without auth headers
server_configs = {
    "planton-cloud": {
        "url": "https://mcp.planton.ai/",
        "transport": "streamable_http"
    }
}

# Create authenticated tool node
tool_node = AuthenticatedMcpToolNode(server_configs)

# Use in custom graph construction (requires not using create_deep_agent)
# See IMPLEMENTATION_SUMMARY.md for complete examples
```

### Testing

All changes have been verified to:
- ✅ Fix middleware signature error in graph-fleet
- ✅ Maintain backward compatibility with existing tests
- ✅ Support both Runtime objects and plain dicts
- ✅ Pass type checking and linting

Integration testing checklist available in `IMPLEMENTATION_SUMMARY.md`.

### Contributors

- Implementation: Claude (Cursor AI)
- Research: Gemini Deep Research
- Based on: LangGraph Platform authentication patterns

---

## Previous Versions

(Previous changelog entries would go here)
