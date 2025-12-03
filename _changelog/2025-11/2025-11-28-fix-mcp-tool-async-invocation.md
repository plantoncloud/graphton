# Fix MCP Tool Sync Invocation Error

**Date:** 2025-11-28  
**Impact:** Critical bug fix  
**Component:** MCP Tool Wrappers

## Problem

MCP tools loaded from `langchain_mcp_adapters` are async-only `StructuredTool` instances that only implement `ainvoke()` and lack synchronous `_run()` methods. The tool wrapper functions in `graphton/core/tool_wrappers.py` were synchronous and called `mcp_tool.invoke()`, causing runtime failures:

```
NotImplementedError: StructuredTool does not support sync invocation
```

**Error Flow:**
1. LangGraph calls wrapper via `ainvoke()` (async context)
2. LangChain wraps sync function in thread executor
3. Sync wrapper calls `mcp_tool.invoke()` (sync)
4. MCP tool has no sync implementation → Error

## Solution

Converted both wrapper functions from synchronous to asynchronous:

### Changes Made

**File:** `src/graphton/core/tool_wrappers.py`

#### 1. `create_tool_wrapper` function
- Line 65: Changed `def wrapper` → `async def wrapper`
- Line 88: Changed `mcp_tool.invoke(kwargs)` → `await mcp_tool.ainvoke(kwargs)`

#### 2. `create_lazy_tool_wrapper` function  
- Line 165: Changed `def lazy_wrapper` → `async def lazy_wrapper`
- Line 192: Changed `mcp_tool.invoke(kwargs)` → `await mcp_tool.ainvoke(kwargs)`

## Why This Works

1. **Async Compatibility**: MCP tools from `langchain_mcp_adapters` are designed for async execution in LangGraph contexts
2. **Natural Flow**: LangGraph's async runtime naturally awaits async tools without thread executor wrapping
3. **No Sync-Async Bridge Issues**: Direct async/await eliminates deadlock risks from thread-based bridges

## Test Results

All tests passed successfully:
- **101 tests passed**
- **29 tests skipped** (require API keys - expected)
- **0 failures**

No test modifications were required because:
- Tests use `agent.invoke()` (sync) on the compiled graph
- LangGraph's `invoke()` method internally handles async tools via event loop
- The fix is at the wrapper-to-MCP-tool boundary, not the test-to-agent boundary

## Impact

- ✅ Eliminates "StructuredTool does not support sync invocation" errors in production
- ✅ MCP tools now execute correctly in both static and dynamic authentication modes
- ✅ All existing code continues to work without modification
- ✅ Aligns with LangGraph async patterns and research best practices

## Related

This fix addresses the root cause identified in the error logs showing MCP tool invocation failures in the graph-fleet service. The solution aligns with the async execution patterns emphasized in the LangGraph middleware research documentation.











