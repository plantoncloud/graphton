# Remove Template Detection - Always Use Eager Tool Loading

**Date:** 2025-12-11  
**Impact:** Architecture simplification  
**Component:** MCP Middleware  

---

## Problem

Graphton had template detection logic (`{{VAR_NAME}}`) that determined whether to use lazy or eager tool wrappers. This was based on an outdated assumption:

**Original design (Nov 28)**: Graphton handles template substitution internally  
**Current reality**: Agent-fleet-worker substitutes templates BEFORE calling Graphton

This mismatch caused **lazy wrappers to be created even when tools could be loaded eagerly**, resulting in:
- ❌ Missing `args_schema` on tool wrappers
- ❌ LLM inferring parameter names instead of using actual schema
- ❌ Wrong parameter names (`org_slug` instead of `org_id`)
- ❌ Tool invocation failures with "INVALID_ARGUMENT" errors

---

## Root Cause

From the changelog history analysis:

**Nov 28 - Universal Authentication Framework** introduced template detection:

```python
self.template_vars = extract_template_vars(servers)
self.is_dynamic = bool(self.template_vars)

if self.is_dynamic:
    # Defer tool loading until invocation
    # Create lazy wrappers without args_schema
else:
    # Load tools immediately
    # Create eager wrappers with complete args_schema
```

This was designed for Graphton to handle template substitution. However, **the actual usage pattern evolved**:

1. Agent YAML has `{{USER_TOKEN}}` template
2. **Agent-fleet-worker substitutes template** with real token
3. Agent-fleet-worker calls Graphton with **complete MCP config**
4. But Graphton still detects template-like strings and goes into "lazy mode"

---

## Solution

**Removed all template detection and dynamic mode logic.** Graphton now assumes:

1. Caller has resolved all authentication
2. MCP configs are complete and ready to use
3. Tools should be loaded immediately (or deferred only if in async context)
4. Always use eager wrappers with complete schemas

### Files Modified

**1. `src/graphton/core/middleware.py`**

- Removed `extract_template_vars()` import
- Removed `substitute_templates()` import
- Removed `is_dynamic` attribute
- Removed `template_vars` attribute
- Simplified `__init__` to always call `_load_tools_sync()`
- Renamed `_load_static_tools()` → `_load_tools_sync()`
- Renamed `_load_static_tools_async()` → `_load_tools_async()`
- Simplified `abefore_agent()` to only handle deferred loading
- Simplified `aafter_agent()` to be a no-op
- Updated error messages to remove "static/dynamic mode" references

**2. `src/graphton/core/agent.py`**

- Removed `create_lazy_tool_wrapper` import
- Removed lazy wrapper detection logic
- Always use `create_tool_wrapper()` for all MCP tools

**3. `tests/test_async_context_init.py`**

- Removed `is_dynamic` and `template_vars` checks
- Updated test expectations for simplified behavior
- Updated error messages in assertions

**4. `tests/test_mcp_remote.py`**

- Rewrote all tests to reflect resolved configs
- Removed template substitution tests
- Updated to test eager loading behavior

---

## Impact

### Before (Broken)

```
Agent YAML: headers: {"Authorization": "Bearer {{USER_TOKEN}}"}
     ↓
Agent-fleet-worker: Substitutes → "Bearer pck_abc123..."
     ↓
Graphton: Sees "Bearer pck_abc123..." but detects {{}} pattern in YAML history
     ↓
Graphton: is_dynamic = True → create_lazy_tool_wrapper()
     ↓
Lazy wrapper: NO args_schema set
     ↓
LLM: Infers parameter names from tool name
     ↓
LLM generates: {"org_slug": "...", "service_slug": "..."}
     ↓
MCP Server: ❌ "INVALID_ARGUMENT: org_id is required"
```

### After (Fixed)

```
Agent YAML: headers: {"Authorization": "Bearer {{USER_TOKEN}}"}
     ↓
Agent-fleet-worker: Substitutes → "Bearer pck_abc123..."
     ↓
Graphton: Receives complete config → load_tools_sync()
     ↓
Graphton: create_tool_wrapper() with complete args_schema
     ↓
Wrapper: args_schema = {properties: {org_id: {...}, slug: {...}}}
     ↓
LLM: Uses actual schema
     ↓
LLM generates: {"org_id": "blueberry-labs", "slug": "hello-world-service-demo"}
     ↓
MCP Server: ✅ Tool executes successfully
```

---

## Benefits

1. **Fixed Schema Issue**: Tool wrappers now have complete `args_schema`
2. **Correct Parameter Names**: LLM uses actual schema instead of inferring
3. **Simplified Architecture**: Removed ~200 lines of unnecessary complexity
4. **Clearer Responsibilities**: Graphton loads tools, callers handle auth
5. **Faster Initialization**: No template detection overhead
6. **Better Performance**: Tools loaded once, not per-request

---

## Testing

**All 153 tests passing:**

```bash
$ poetry run pytest tests/ -v --tb=line -q
================ 153 passed, 29 skipped, 113 warnings in 3.41s =================
```

**Tests updated:**
- `test_async_context_init.py`: 9 tests (all passing)
- `test_mcp_remote.py`: 9 tests (all passing)

---

## Migration Impact

### For Agent-Fleet-Worker

✅ **No changes required** - Already substituting templates before calling Graphton

### For Direct Graphton Users

If you were passing raw templates to Graphton:

**Before (no longer supported):**
```python
agent = create_deep_agent(
    mcp_servers={
        "planton-cloud": {
            "headers": {"Authorization": "Bearer {{USER_TOKEN}}"}
        }
    }
)
# Later: Pass token in config
agent.invoke(input, config={"configurable": {"USER_TOKEN": token}})
```

**After (required):**
```python
# Resolve template before creating agent
agent = create_deep_agent(
    mcp_servers={
        "planton-cloud": {
            "headers": {"Authorization": f"Bearer {token}"}
        }
    }
)
# No config needed for MCP
agent.invoke(input)
```

---

## Related Issues

This fixes the issue reported in the screenshot where:
- Agent: `pipeline-troubleshooter` 
- Tool: `get_service_by_org_by_slug`
- Error: `"INVALID_ARGUMENT: org_id is required"`
- Cause: LLM generated `org_slug` instead of `org_id` due to missing schema

---

## Conclusion

Removing template detection aligns Graphton's implementation with its actual usage pattern. This architectural simplification:

- Fixes the immediate parameter naming bug
- Reduces code complexity
- Improves maintainability
- Clarifies responsibility boundaries

The original template detection feature was well-intentioned but based on assumptions that didn't match production usage.

