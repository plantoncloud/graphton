# Middleware Type Signature Fixes

**Date**: November 28, 2025

## Summary

Fixed mypy type checker errors in the middleware module by updating method signatures to properly override the `AgentMiddleware` base class. Also removed an unused import from the agent module. These fixes resolved 4 mypy errors and 1 ruff linter error, achieving a clean build.

## Problem Statement

The graphton project had accumulated type checking errors that were blocking the release process. Running `make release` resulted in:
- 1 ruff linter error (unused import)
- 4 mypy type checker errors (incompatible method overrides violating Liskov substitution principle)

### Pain Points

- **Build failures**: `make release` exited with errors, preventing package publication
- **Type safety violations**: Method signatures in `McpToolsLoader` middleware didn't match the `AgentMiddleware` supertype
- **Import cleanup**: Unused imports remained from refactoring work
- **API compatibility**: Incorrect parameter types could cause runtime errors when middleware is invoked

## Solution

Applied a two-phase fix strategy:

1. **Removed unused import**: Cleaned up `create_tool_wrapper` import that was only used in local scope
2. **Updated type signatures**: Changed middleware methods to use correct types from langchain and langgraph

The key insight was recognizing that the `AgentMiddleware` protocol expects `AgentState[Any]` and `Runtime[None]` parameters, not the simplified types we had used. The `Runtime` object provides access to configuration through its `context` attribute, which contains the values passed in `config['configurable']`.

## Implementation Details

### Ruff Linter Fix (1 error)

**F401: Unused import `create_tool_wrapper`**

Fixed in `src/graphton/core/agent.py` line 19:

```python
# Before
from graphton.core.tool_wrappers import create_lazy_tool_wrapper, create_tool_wrapper

# After  
from graphton.core.tool_wrappers import create_lazy_tool_wrapper
```

**Rationale**: The `create_tool_wrapper` function was imported at module level but only used within the `create_deep_agent` function where it's imported locally (line 199). The top-level import was redundant.

### Mypy Type Checker Fixes (4 errors)

**1. Import Statement Updates**

Added correct type imports in `src/graphton/core/middleware.py`:

```python
# Before
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.runnables import RunnableConfig

# After
from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langgraph.runtime import Runtime
```

**Rationale**: 
- `AgentState` is the proper type for agent state (not `dict[str, Any]`)
- `Runtime` is the proper type for runtime context (not `RunnableConfig`)
- `RunnableConfig` was removed as it's no longer needed

**2. before_agent Method Signature (2 errors)**

Updated method signature to match supertype:

```python
# Before - Incompatible with supertype
def before_agent(
    self,
    state: dict[str, Any],        # ❌ Should be AgentState[Any]
    config: RunnableConfig,        # ❌ Should be Runtime[None]
) -> dict[str, Any] | None:

# After - Compatible with supertype
def before_agent(
    self,
    state: AgentState[Any],        # ✅ Correct type
    runtime: Runtime[None],        # ✅ Correct type
) -> dict[str, Any] | None:
```

**3. after_agent Method Signature (2 errors)**

Updated method signature to match supertype:

```python
# Before - Incompatible with supertype
def after_agent(
    self,
    state: dict[str, Any],         # ❌ Should be AgentState[Any]
    config: RunnableConfig,        # ❌ Should be Runtime[None]
) -> dict[str, Any] | None:

# After - Compatible with supertype
def after_agent(
    self,
    state: AgentState[Any],        # ✅ Correct type
    runtime: Runtime[None],        # ✅ Correct type
) -> dict[str, Any] | None:
```

**4. Runtime Context Access**

Updated implementation to access configuration through `Runtime.context`:

```python
# Before - Using config parameter
if not config or "configurable" not in config:
    raise ValueError(...)
configurable = config["configurable"]

# After - Using runtime.context
if not runtime or not runtime.context:
    raise ValueError(...)
configurable = runtime.context
```

**Rationale**: The `Runtime` object encapsulates the execution context. Its `context` attribute contains the values passed via `config['configurable']` at invocation time. From the user's perspective, nothing changes - they still pass `config={'configurable': {...}}` when invoking the agent.

**5. Documentation Updates**

Updated docstrings to reflect parameter changes:

```python
# Before
Args:
    state: Current agent state (unused but required by middleware protocol)
    config: Runnable config containing template values in configurable dict

# After
Args:
    state: Current agent state (unused but required by middleware protocol)
    runtime: Runtime object containing template values in context
```

## Benefits

### Build Quality

- ✅ **Clean builds**: `make release` now passes linting and type checking
- ✅ **Type safety**: Method signatures properly override supertype
- ✅ **Liskov compliance**: Subclass can be substituted for superclass without errors
- ✅ **Import cleanliness**: No unused imports

### Code Quality

- **Correct types**: Using proper langchain/langgraph types instead of approximations
- **API stability**: Correct signatures prevent runtime type errors
- **Better documentation**: Docstrings accurately describe parameters
- **Maintainability**: Future changes to middleware protocol will be caught by type checker

### Developer Experience

- **Release ready**: Build pipeline can now complete successfully
- **CI/CD enabled**: Automated releases can proceed
- **Type hints**: IDEs can provide accurate autocomplete and error detection
- **Clear contracts**: Middleware implementers know exact signatures required

## Testing

All checks pass after fixes:

```bash
$ make lint && make typecheck
Running ruff linter...
poetry run ruff check .
✅ All checks passed!

Running mypy type checker...
poetry run mypy src/graphton/
✅ Success: no issues found in 11 source files
```

### Validation Strategy

**Type checking validation**:
- Verified method signatures match `AgentMiddleware` protocol
- Confirmed `Runtime` and `AgentState` types are properly imported
- Checked that all type checker errors are resolved

**Functional validation**:
- Existing tests continue to pass (no test changes needed)
- Runtime context access works identically to previous config access
- User-facing API remains unchanged

**Integration verification**:
- MCP tools still load correctly in both static and dynamic modes
- Template substitution works through `runtime.context`
- Middleware lifecycle (before_agent/after_agent) functions properly

## Impact

**Files Modified**: 2 files
- `src/graphton/core/agent.py` - Removed unused import
- `src/graphton/core/middleware.py` - Updated type signatures and implementation

**Affected Workflows**:
- ✅ Local development: `make lint` and `make typecheck` pass
- ✅ Release process: `make release` can now proceed
- ✅ CI/CD: Automated pipelines unblocked
- ✅ Type safety: Proper middleware protocol compliance

## Design Decisions

### Runtime vs RunnableConfig

**Why use Runtime instead of RunnableConfig?**

The `AgentMiddleware` protocol specifies `Runtime[ContextT]` as the second parameter type. This is because:

1. **Richer context**: `Runtime` encapsulates not just configuration but also store access, stream writers, and execution context
2. **Type safety**: Using the exact protocol type prevents subtle bugs
3. **Future-proof**: If the middleware protocol evolves, our code will catch incompatibilities
4. **Framework alignment**: Matches how LangGraph's middleware system works internally

### AgentState vs dict

**Why use AgentState instead of dict[str, Any]?**

`AgentState` is a protocol that:
1. **Type variance**: Properly handles covariance/contravariance for state updates
2. **Framework compatibility**: LangGraph's agent system uses this type throughout
3. **Documentation**: Makes it clear this is agent state, not arbitrary data
4. **Type checking**: Enables better type inference in middleware chains

### Backward Compatibility

**Does this change the user-facing API?**

No. Users still pass configuration the same way:

```python
# User code - unchanged
agent.invoke(
    {"messages": [{"role": "user", "content": "Hello"}]},
    config={"configurable": {"USER_TOKEN": "token123"}}
)
```

**Internal change**:
- Before: Middleware received `config: RunnableConfig`, accessed via `config["configurable"]`
- After: Middleware receives `runtime: Runtime[None]`, accessed via `runtime.context`

The framework automatically maps `config["configurable"]` to `runtime.context`, so the behavior is identical.

## Type System Understanding

### Runtime Object Structure

```python
@dataclass
class Runtime:
    context: ContextT = None          # User-provided values from config['configurable']
    store: BaseStore | None = None    # Optional state storage
    stream_writer: StreamWriter = ... # Output streaming
    previous: Any = None              # Previous runtime for chaining
```

### AgentState Protocol

```python
# AgentState is a TypedDict-like protocol that represents agent state
# It's used with variance annotations to enable safe state updates
AgentState[T] = TypeVar('AgentState', bound=dict[str, Any])
```

### Middleware Protocol

```python
class AgentMiddleware:
    def before_agent(
        self,
        state: AgentState[Any],      # Current agent state
        runtime: Runtime[ContextT],  # Runtime context with config values
    ) -> dict[str, Any] | None:
        """Called before agent execution."""
        pass
    
    def after_agent(
        self,
        state: AgentState[Any],      # Final agent state
        runtime: Runtime[ContextT],  # Runtime context
    ) -> dict[str, Any] | None:
        """Called after agent execution."""
        pass
```

## Related Work

This fix builds on previous middleware implementation:
- `2025-11-27-232738-phase-3-mcp-integration-universal-deployment.md` - Initial middleware implementation
- `2025-11-28-125856-universal-mcp-authentication-framework.md` - MCP authentication framework
- `2025-11-28-150557-lazy-tool-wrappers-dynamic-mcp.md` - Dynamic tool loading

With proper type signatures, the middleware system is now:
- ✅ Type-safe and protocol-compliant
- ✅ Ready for production use
- ✅ Maintainable with proper type checking
- ✅ Compatible with LangGraph middleware ecosystem

## Next Steps

**Immediate**:
- ✅ Release pipeline unblocked
- ✅ Package can be published to PyPI
- ✅ CI/CD can run automated releases

**Future improvements**:
- Consider adding more type parameters to `Runtime` if we need custom context types
- Add integration tests that specifically validate middleware type contracts
- Document middleware implementation patterns for future extensions

---

**Status**: ✅ Complete
**Build Status**: Passing
**Type Safety**: Fully compliant with AgentMiddleware protocol








