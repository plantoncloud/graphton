# Remove Redundant Token Validation from MCP Tool Wrappers

**Date**: November 28, 2025

## Summary

Removed redundant authentication token validation from MCP tool wrappers that was causing authentication failures in production. The validation was checking for a hardcoded token key name and failing when template variables used different names. Since authentication already happens during MCP tool loading via template substitution, the wrapper-level validation was unnecessary and problematic.

## Problem Statement

MCP tool wrappers were calling `get_user_token()` to validate authentication before invoking tools, but this validation was fundamentally flawed:

1. **No token storage**: The middleware never called `set_user_token()`, so the ContextVar was always empty
2. **Hardcoded assumptions**: The validation assumed a single key name (`USER_TOKEN`), but template variables can have any name (e.g., `PLANTON_USER_TOKEN`, `AUTH_KEY`, etc.)
3. **Redundant check**: Authentication already succeeded when middleware loaded MCP tools with substituted credentials

### Pain Points

- 🚨 **Production failures**: All MCP tool invocations failing with "User token not available in context"
- 🔴 **Agent Fleet Worker blocked**: Unable to execute any MCP tools
- 🤔 **Misleading error message**: Suggested the token wasn't passed, when the issue was internal validation logic
- 🔧 **Inflexible design**: Hardcoded key name prevented using different template variable names
- 📊 **Logs showed success then failure**: Middleware successfully extracted tokens, but wrappers failed validation

### Error Example

```
graph-fleet-5445bb976d-mfdq6 microservice 2025-11-28T12:35:51.050526Z [info] 
Successfully extracted template values for: ['USER_TOKEN']

graph-fleet-5445bb976d-mfdq6 microservice 2025-11-28T12:35:55.921245Z [error] 
Token validation failed for tool 'get_cloud_resource_schema': 
User token not available in context. Ensure McpToolsLoader middleware is 
properly configured and token is passed via config={'configurable': {'_user_token': token}}.
```

Note the mismatch: extracted `USER_TOKEN` (caps, no underscore) but error message references `_user_token` (lowercase with underscore).

## Solution

Remove the token validation entirely from tool wrappers. Authentication is already validated at the correct layer: when middleware loads MCP tools.

### Authentication Flow (After Fix)

```
1. Graph Fleet invokes agent with config={'configurable': {'USER_TOKEN': 'jwt...'}}
   ↓
2. McpToolsLoader.abefore_agent() extracts template variables
   ↓
3. Middleware substitutes {{USER_TOKEN}} → actual JWT in MCP server headers
   ↓
4. Middleware loads MCP tools with authenticated transport
   ✅ If auth fails, tool loading fails here
   ↓
5. Tool wrappers invoke pre-authenticated MCP tools
   ✅ No additional validation needed
```

### Why This Works

**Authentication happens at transport layer, not invocation layer:**

- MCP clients connect to servers with auth headers
- Once connected, all tool calls use that authenticated session
- If credentials are invalid, the connection fails during tool loading (step 4)
- Tool wrappers just need to invoke already-authenticated tools

**Supports any template variable names:**

- No hardcoded assumptions about key names
- Works with `USER_TOKEN`, `PLANTON_USER_TOKEN`, `API_KEY`, etc.
- Template extraction is dynamic based on actual config

## Implementation Details

### Changes to `graphton/src/graphton/core/tool_wrappers.py`

**1. Removed validation from `create_tool_wrapper`:**

```python
# BEFORE:
try:
    get_user_token()  # Validate token exists
    logger.debug(f"Invoking MCP tool '{tool_name}' with user token")
except ValueError as e:
    logger.error(f"Token validation failed for tool '{tool_name}': {e}")
    raise

# AFTER:
logger.debug(f"Invoking MCP tool '{tool_name}'")
```

**2. Removed validation from `create_lazy_tool_wrapper`:**

```python
# BEFORE:
try:
    get_user_token()  # Validate token exists
    logger.debug(f"Invoking MCP tool '{tool_name}' with user token (lazy mode)")
except ValueError as e:
    logger.error(f"Token validation failed for tool '{tool_name}': {e}")
    raise

# AFTER:
logger.debug(f"Invoking MCP tool '{tool_name}' (lazy mode)")
```

**3. Removed unused import:**

```python
# REMOVED:
from graphton.core.context import get_user_token
```

**4. Updated docstrings:**

Both wrapper functions had their docstrings updated to remove references to "Validates user token is available in context" from the step lists.

### Files Modified

- `graphton/src/graphton/core/tool_wrappers.py` - Removed validation logic, updated docstrings, removed unused import

### Note: context.py Preserved

The `graphton/src/graphton/core/context.py` module with `set_user_token()` and `get_user_token()` functions was preserved for potential future use cases, but is no longer used in the current architecture.

## Benefits

### Immediate Fixes

- ✅ **Resolves authentication failures**: MCP tools now invoke successfully
- ✅ **Works with any template variable names**: No hardcoded key assumptions
- ✅ **Cleaner code**: Removed 20+ lines of redundant validation logic
- ✅ **Better error messages**: If auth fails, it fails at tool loading with proper MCP error

### Architectural Improvements

- 🎯 **Validation at correct layer**: Authentication checked when establishing MCP connection
- 🔄 **Follows separation of concerns**: Middleware handles auth, wrappers handle invocation
- 🧪 **Easier to test**: No need to mock ContextVar state in tool wrapper tests
- 📚 **More maintainable**: Fewer moving parts, clearer responsibility boundaries

### Developer Experience

- 🚀 **Faster debugging**: Auth failures happen early with clear errors
- 💡 **Intuitive behavior**: Wrappers just wrap, don't validate
- 🔧 **Flexible configuration**: Any template variable name works

## Impact

### Who's Affected

- **Agent Fleet Worker**: Now able to invoke MCP tools successfully
- **All agents using MCP tools**: Benefit from cleaner validation flow
- **Future MCP integrations**: No hardcoded key name constraints

### What Changed

**Before:**
- Tool wrapper checks ContextVar for token
- Always fails (nothing sets the ContextVar)
- Generic error message doesn't help debugging

**After:**
- Tool wrapper directly invokes MCP tool
- If auth is bad, MCP client fails with specific error
- Failure happens at tool loading time, not invocation time

### Breaking Changes

None. This is purely internal validation logic removal. The external API (how agents are configured and invoked) remains unchanged.

## Testing

**Manual verification:**
1. Run agent with MCP tools configured
2. Verify middleware logs show successful template extraction
3. Verify tool invocations succeed without validation errors
4. Confirm auth failures still caught (at tool loading time)

**No new tests needed:**
- Existing middleware tests cover template substitution
- Existing MCP integration tests cover tool invocation
- Removed code doesn't need tests

## Related Work

- **Universal MCP Authentication Framework** (2025-11-28-125856): Established the template-based auth pattern
- **Runtime Context Access Fix** (2025-11-28-170733): Fixed middleware to use `runtime.context` correctly
- **Lazy Tool Wrappers** (2025-11-28-150557): Introduced lazy wrapper pattern for dynamic mode

This change completes the MCP authentication architecture by removing the last piece of unnecessary validation logic.

---

**Status**: ✅ Production Ready

**Files Changed**: 1 file, ~30 lines removed, docstrings updated

**Timeline**: Single session (1 hour investigation + implementation)














