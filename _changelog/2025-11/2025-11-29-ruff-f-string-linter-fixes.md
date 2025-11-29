# Ruff F-String Linter Fixes

**Date**: November 29, 2025

## Summary

Fixed 2 ruff linter errors (F541) in the tool wrappers module by removing unnecessary f-string prefixes from static warning messages that contained no placeholders. This achieves a clean build with all linter checks passing.

## Problem Statement

The graphton project had accumulated 2 ruff linter errors that were flagged during build checks:

- **F541**: f-string without any placeholders (2 occurrences)
- Both errors were in `src/graphton/core/tool_wrappers.py` on lines 102 and 226

### Pain Points

- **Build warnings**: Ruff linter flagged inefficient f-string usage
- **Code quality**: F-strings without placeholders are unnecessary and misleading
- **Best practices**: Static strings should use regular string literals, not f-strings
- **Release readiness**: Clean builds are required for production releases

### Error Output

```
F541 f-string without any placeholders
   --> src/graphton/core/tool_wrappers.py:102:36
    |
102 |                     logger.warning(f"⚠️  Potential double-nesting detected: kwargs has single 'input' key")
    |                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
help: Remove extraneous `f` prefix

F541 f-string without any placeholders
   --> src/graphton/core/tool_wrappers.py:226:36
    |
226 |                     logger.warning(f"⚠️  Potential double-nesting detected: kwargs has single 'input' key")
    |                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
help: Remove extraneous `f` prefix
```

## Solution

Remove the `f` prefix from both warning messages since they don't contain any variable interpolation (no `{variable}` placeholders). F-strings are only beneficial when they contain dynamic content.

### Why F-Strings Were Used

The original code likely used f-strings out of habit or anticipating future dynamic content. However, since these are purely static warning messages, regular string literals are more appropriate.

## Implementation Details

### Changes to `src/graphton/core/tool_wrappers.py`

**1. Line 102 - Static mode tool wrapper:**

```python
# Before
logger.warning(f"⚠️  Potential double-nesting detected: kwargs has single 'input' key")

# After  
logger.warning("⚠️  Potential double-nesting detected: kwargs has single 'input' key")
```

**2. Line 226 - Lazy mode tool wrapper:**

```python
# Before
logger.warning(f"⚠️  Potential double-nesting detected: kwargs has single 'input' key")

# After
logger.warning("⚠️  Potential double-nesting detected: kwargs has single 'input' key")
```

### Context

Both warning messages are part of diagnostic logging that helps detect potential argument marshalling issues when invoking MCP tools. They appear in:

1. `create_tool_wrapper()` - Used for static MCP configuration
2. `create_lazy_tool_wrapper()` - Used for dynamic MCP configuration

The warning message itself is static and doesn't need to interpolate any variables, making it a perfect candidate for a regular string literal.

## Benefits

### Code Quality

- ✅ **Cleaner code**: Uses appropriate string literal types
- ✅ **Better performance**: Regular strings are slightly faster than f-strings (no formatting overhead)
- ✅ **Code clarity**: Makes it obvious these are static messages
- ✅ **Linter compliance**: Follows Python best practices enforced by ruff

### Build Quality

- ✅ **Clean builds**: `make lint` passes with no errors
- ✅ **Release ready**: All build checks (lint, typecheck, test) pass successfully
- ✅ **CI/CD ready**: Automated pipelines can proceed without warnings

## Testing

All checks pass after fixes:

```bash
$ make lint
Running ruff linter...
poetry run ruff check .
All checks passed!

$ make typecheck
Running mypy type checker...
poetry run mypy src/graphton/
Success: no issues found in 12 source files

$ make build
Running ruff linter...
✅ All checks passed!
Running mypy type checker...
✅ Success: no issues found in 12 source files
Running tests with pytest...
✅ 101 passed, 29 skipped, 77 warnings in 4.95s
✅ All checks passed!
```

### Validation Strategy

**Linter validation**:
- Verified ruff no longer reports F541 errors
- Confirmed all other linter rules still pass
- Checked that warnings about deprecated rules (ANN101, ANN102) are unrelated

**Functional validation**:
- Warning messages still log correctly at runtime
- MCP tool invocation behavior unchanged
- Both static and lazy tool wrappers function identically

**Integration verification**:
- All 101 tests continue to pass
- No regression in tool wrapper functionality
- Diagnostic logging works as expected

## Impact

**Files Modified**: 1 file (`src/graphton/core/tool_wrappers.py`)
- 2 lines changed (removed f-string prefixes)
- No functional changes
- Zero impact on runtime behavior

**Affected Workflows**:
- ✅ Local development: Clean linter output
- ✅ Release process: Build checks pass
- ✅ CI/CD: No linter warnings in automated pipelines

**Breaking Changes**: None. This is purely a code quality improvement with no API or behavior changes.

## Design Decisions

### When to Use F-Strings

F-strings should be used when:
- ✅ Interpolating variables: `f"Tool '{tool_name}' failed"`
- ✅ Formatting expressions: `f"Count: {len(items)}"`
- ✅ Complex formatting: `f"Value: {value:.2f}"`

F-strings should NOT be used for:
- ❌ Static strings: `"This is a constant message"`
- ❌ No placeholders: `f"Error occurred"` → `"Error occurred"`

### Code Review Learning

This fix highlights the importance of:
1. **Using linters**: Ruff caught inefficient code patterns
2. **Paying attention to warnings**: Even minor issues matter for code quality
3. **Regular cleanup**: Removing unnecessary syntax improves readability
4. **Tool assistance**: Linters help maintain consistency across the codebase

## Related Work

This fix is part of ongoing code quality improvements:
- `2025-11-28-152800-middleware-type-signature-fixes.md` - Fixed mypy type errors
- `2025-11-27-225824-linter-and-type-error-fixes.md` - Previous linter cleanup
- `2025-11-28-132635-docstring-and-code-cleanup.md` - Documentation improvements

These incremental fixes maintain high code quality standards and ensure the codebase stays clean and maintainable.

## Next Steps

**Immediate**:
- ✅ Build checks passing
- ✅ Ready for next release
- ✅ No blockers remaining

**Continuous improvement**:
- Continue monitoring linter output for new issues
- Address warnings proactively before they accumulate
- Maintain zero-warning policy for production releases

---

**Status**: ✅ Complete
**Build Status**: All checks passing
**Linter Status**: No errors or warnings (F541 resolved)
**Impact**: Minimal - code quality improvement only
