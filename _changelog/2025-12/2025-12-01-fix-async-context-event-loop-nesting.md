# Fix Async Context Event Loop Nesting in Static MCP Tool Loading

**Date**: December 1, 2025  
**Type**: Critical Bug Fix  
**Impact**: Resolves 100% reproducible event loop nesting error when creating Graphton agents from async contexts (Temporal activities)

## Summary

Fixed the event loop nesting error that occurred when `create_deep_agent()` was called from an async context (e.g., Temporal activity) with static MCP configurations. The middleware now detects when it's being initialized in an async context and defers tool loading until the first middleware invocation, avoiding the "Cannot run the event loop while another loop is running" error.

## Problem Statement

### Symptoms

- **100% reproducible error**: Every Graphton agent creation from async context failed with:
  ```
  RuntimeError: Cannot run the event loop while another loop is running
  ```
- **Failure point**: Occurred during `McpToolsLoader.__init__()` when trying to load static MCP tools
- **Affected scenario**: Temporal activities calling `create_deep_agent()` with resolved MCP configurations (no template variables)
- **Production impact**: All Graphton agents with static MCP configs were non-functional in agent-fleet-worker

### Error Log Pattern

```
2025-12-01 01:29:51,839 - graphton.core.middleware - INFO - Static MCP configuration detected (no template variables). Loading tools at agent creation time...
2025-12-01 01:29:51,840 - graphton.core.middleware - ERROR - Failed to load static MCP tools: Cannot run the event loop while another loop is running
```

## Root Cause: Event Loop Nesting

The problematic code in `_load_static_tools()`:

```python
# BROKEN: Assumes we're in a sync context
loop = asyncio.get_event_loop()
if loop.is_running():
    raise RuntimeError("Event loop already running during static tool loading")

# Tries to use run_until_complete() with running loop
tools = loop.run_until_complete(load_mcp_tools(...))
```

**The Execution Flow**:
1. Temporal activity (`execute_graphton`) is async (event loop running on main thread)
2. Activity calls `create_deep_agent()` (sync function)
3. Agent creation creates `McpToolsLoader` middleware
4. Middleware `__init__` calls `_load_static_tools()` (sync method)
5. Method tries to call `loop.run_until_complete()` → **FAILS** because loop is already running

**Key Insight**: You cannot call `run_until_complete()` on an event loop that's already running. This is a fundamental asyncio limitation.

## Solution: Deferred Loading in Async Contexts

Updated `McpToolsLoader` to detect async context and defer tool loading:

### 1. Added Deferred Loading Flag

```python
def __init__(self, servers, tool_filter):
    # ... existing code ...
    self._deferred_loading = False  # Track if loading was deferred
    
    if not self.is_dynamic:
        self._load_static_tools()  # May defer instead of loading immediately
```

### 2. Updated `_load_static_tools()` to Handle Async Context

```python
def _load_static_tools(self) -> None:
    """Load tools for static configurations (synchronous wrapper).
    
    If called from an async context (event loop already running), defers
    tool loading until the first middleware invocation to avoid event loop
    nesting issues.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context - defer loading
            logger.info(
                "Async context detected (event loop running). "
                "Deferring static tool loading to first invocation."
            )
            self._deferred_loading = True
            return  # Exit without loading
        
        # Sync context - load normally
        tools = loop.run_until_complete(load_mcp_tools(...))
        # ... cache tools ...
    except Exception as e:
        raise RuntimeError(f"Static MCP tool loading failed: {e}") from e
```

### 3. Added Async Tool Loading Method

```python
async def _load_static_tools_async(self) -> None:
    """Load tools for static configurations asynchronously.
    
    Called from abefore_agent() when tool loading was deferred due to
    async context at initialization time.
    """
    logger.info("Loading static MCP tools (deferred from initialization)...")
    
    # Load tools asynchronously (natural await, no blocking)
    tools = await load_mcp_tools(self.servers, self.tool_filter)
    
    # Cache tools by name
    self._tools_cache = {tool.name: tool for tool in tools}
    self._tools_loaded = True
```

### 4. Updated `abefore_agent()` to Perform Deferred Loading

```python
async def abefore_agent(self, state, runtime):
    """Load MCP tools before agent execution (async)."""
    
    # Static mode: check if deferred loading is needed
    if not self.is_dynamic:
        if self._deferred_loading and not self._tools_loaded:
            # Perform deferred loading now (in async context)
            await self._load_static_tools_async()
            self._deferred_loading = False
        else:
            logger.debug("Static MCP mode: tools already loaded, skipping")
        return None
    
    # Dynamic mode: existing logic
    # ...
```

## Behavior By Context

### Sync Context (e.g., direct script execution)
1. `__init__` calls `_load_static_tools()`
2. Detects no running event loop
3. Creates new event loop and loads tools immediately
4. Tools cached and ready before agent is used

### Async Context (e.g., Temporal activity)
1. `__init__` calls `_load_static_tools()`
2. Detects running event loop
3. Sets `_deferred_loading = True` and returns
4. Agent creation completes successfully
5. First call to `abefore_agent()` loads tools asynchronously
6. Subsequent calls skip loading (tools already cached)

## Testing

Added comprehensive test suite in `tests/test_async_context_init.py`:

### Test Coverage
- ✅ Static config in async context (defers loading)
- ✅ Dynamic config in async context (no impact)
- ✅ Static config in sync context (immediate loading)
- ✅ Deferred loading flag behavior
- ✅ Event loop detection logic
- ✅ Temporal activity simulation
- ✅ Multiple agent creations in same async context

### Test Results
```bash
$ poetry run pytest tests/test_async_context_init.py -v
============================= 9 passed ===================
```

All existing tests continue to pass:
```bash
$ poetry run pytest tests/ -v
============== 123 passed, 29 skipped ==================
```

## Production Deployment

### Prerequisites
1. ✅ Changes committed to Graphton main branch
2. ✅ All tests passing
3. ⏳ Agent-fleet-worker poetry.lock update needed

### Deployment Steps

**For agent-fleet-worker**:
```bash
cd backend/services/agent-fleet-worker
poetry update graphton  # Pull latest from GitHub main
poetry lock --no-update  # Update lock file
# Rebuild and redeploy service
```

**Expected Log Output After Fix**:
```
INFO - Static MCP configuration detected (no template variables). Loading tools at agent creation time...
INFO - Async context detected (event loop running). Deferring static tool loading to first invocation.
INFO - Loading static MCP tools (deferred from initialization)...
INFO - Successfully loaded 5 static MCP tool(s) (deferred): [tool_names...]
```

## Verification

After deployment, verify fix by:

1. **Check logs**: No "Cannot run the event loop" errors
2. **Test execution**: Create and execute a Graphton agent with static MCP config
3. **Verify MCP tools**: Confirm tools are loaded and functional
4. **Performance**: First agent call slightly slower (deferred loading), subsequent calls fast

## Impact

**Before Fix**:
- ❌ All Graphton agents in Temporal activities failed immediately
- ❌ Production agent-fleet-worker couldn't use static MCP configs
- ❌ Workaround: Force dynamic loading with dummy template variables

**After Fix**:
- ✅ Graphton agents work in both sync and async contexts
- ✅ Static MCP configs fully functional in production
- ✅ Minimal performance impact (one-time deferred loading)
- ✅ Cleaner logs with clear deferred loading messages

## Related Issues

- Original error: Temporal activity `execute_graphton` failing with event loop error
- Related to: MCP configuration resolution via gRPC (which was working correctly)
- Affects: agent-fleet-worker service in Planton Cloud production

## Files Modified

- `src/graphton/core/middleware.py` - Updated `McpToolsLoader` class
  - Modified `__init__` to add `_deferred_loading` flag
  - Updated `_load_static_tools()` to detect async context
  - Added `_load_static_tools_async()` for deferred loading
  - Modified `abefore_agent()` to perform deferred loading

- `tests/test_async_context_init.py` - New comprehensive test suite
  - 9 tests covering all async/sync context scenarios
  - Real-world Temporal activity simulation
  - Event loop detection validation

## Design Decisions

**Why defer loading instead of using threading?**
- Threading would add complexity and potential race conditions
- Deferred loading is simpler and safer
- Performance impact is minimal (one-time delay on first use)

**Why not make `create_deep_agent()` async?**
- Would break existing API and all calling code
- Not all callers are in async contexts
- Deferred loading handles both contexts gracefully

**Why not always use dynamic loading?**
- Static loading is more efficient when possible
- Reduces runtime overhead for non-template configs
- Preserves original design intent

## Lessons Learned

1. **Always consider execution context**: Code may be called from both sync and async contexts
2. **Event loop detection**: Use `asyncio.get_event_loop().is_running()` to detect async contexts
3. **Deferred initialization**: A valid pattern for handling async requirements in sync APIs
4. **Comprehensive testing**: Test both sync and async execution paths

---

**Status**: ✅ Fixed and tested locally  
**Next**: Deploy to production and verify in agent-fleet-worker











