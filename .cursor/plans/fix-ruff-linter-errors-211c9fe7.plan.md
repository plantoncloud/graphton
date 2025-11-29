<!-- 211c9fe7-ad84-4e13-b966-a20cc402d359 e14792cc-5501-4939-994a-942df1e40e12 -->
# Fix Ruff Linter Errors in tool_wrappers.py

## Issues Identified

Ruff linter found 2 errors in `src/graphton/core/tool_wrappers.py`:

- **Line 102**: F-string without placeholders (F541)
- **Line 226**: F-string without placeholders (F541)

Both errors are on the same warning message: `f"⚠️  Potential double-nesting detected: kwargs has single 'input' key"`

## Fix Strategy

Remove the `f` prefix from both strings since they don't contain any placeholders (no `{variable}` interpolation).

### Changes Required

**File**: `src/graphton/core/tool_wrappers.py`

1. **Line 102** - Change:
   ```python
   logger.warning(f"⚠️  Potential double-nesting detected: kwargs has single 'input' key")
   ```


To:

   ```python
   logger.warning("⚠️  Potential double-nesting detected: kwargs has single 'input' key")
   ```

2. **Line 226** - Change:
   ```python
   logger.warning(f"⚠️  Potential double-nesting detected: kwargs has single 'input' key")
   ```


To:

   ```python
   logger.warning("⚠️  Potential double-nesting detected: kwargs has single 'input' key")
   ```

## Verification

After making changes, verify with:

- `make lint` - Should pass with no errors
- `make build` - Full build should pass (already passes: mypy ✓, tests ✓)

### To-dos

- [ ] Remove f-string prefix from lines 102 and 226 in tool_wrappers.py
- [ ] Run make lint to verify all linter errors are fixed