<!-- 6c1f96f7-33aa-4201-beb6-450c4afad6ba 7238204e-4de5-47c9-a785-d74eaab5935e -->
# Fix Middleware Test Failures

## Problem Analysis

There are 9 failing tests split into two categories:

### 1. TypeError: unexpected keyword argument 'config' (7 tests)

- Tests in [`tests/test_mcp_remote.py`](tests/test_mcp_remote.py) call `middleware.before_agent(state={}, config=config)`
- But the method signature is `before_agent(self, state: AgentState[Any], runtime: Runtime[None])`
- Tests are passing `config` as keyword argument, but method expects `runtime`

### 2. AttributeError: 'dict' object has no attribute 'context' (2 tests)  

- Tests in [`tests/test_static_dynamic_mcp.py`](tests/test_static_dynamic_mcp.py) call `middleware.before_agent({}, config)`
- They pass a plain dict like `{"configurable": {...}}`
- Middleware tries to access `runtime.context` which doesn't exist on a dict

## Root Cause

The middleware was recently updated (per changelog [`_changelog/2025-11/2025-11-28-152800-middleware-type-signature-fixes.md`](_changelog/2025-11/2025-11-28-152800-middleware-type-signature-fixes.md)) to use `Runtime` instead of `RunnableConfig`, but the tests weren't updated to match. The middleware needs to handle both:

- **Runtime objects** (in production): Access via `runtime.context`
- **Plain dicts** (in tests): Access via dict `["configurable"]` key

## Solution

Update [`src/graphton/core/middleware.py`](src/graphton/core/middleware.py) `before_agent` method to:

1. **Accept flexible runtime parameter**: Check if it's a Runtime object or plain dict
2. **Extract configurable safely**: Use appropriate access pattern based on type
3. **Maintain backward compatibility**: Tests can pass plain dicts, production gets Runtime objects

### Implementation Details

In `before_agent` method (line ~203):

```python
# Current code:
if not runtime or not runtime.context:
    raise ValueError(...)
configurable = runtime.context

# Updated code:
# Handle both Runtime objects and plain dicts for test compatibility
if not runtime:
    raise ValueError(...)

# Check if runtime is a Runtime object with context attribute
if hasattr(runtime, 'context'):
    # Production: Runtime object
    if not runtime.context:
        raise ValueError(...)
    configurable = runtime.context
else:
    # Tests: plain dict with 'configurable' key
    if not isinstance(runtime, dict) or "configurable" not in runtime:
        raise ValueError(...)
    configurable = runtime["configurable"]
```

## Files to Modify

1. **[`src/graphton/core/middleware.py`](src/graphton/core/middleware.py)** - Update `before_agent` method to handle both Runtime objects and plain dicts

## Testing

After the fix, run:

```bash
make build
```

All 9 failing tests should pass:

- 7 tests in `test_mcp_remote.py`
- 2 tests in `test_static_dynamic_mcp.py`