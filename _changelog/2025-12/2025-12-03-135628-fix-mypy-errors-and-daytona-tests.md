# Fix Mypy Import Errors and Daytona Backend Tests

**Date**: December 3, 2025

## Summary

Fixed mypy type checking errors for optional Daytona dependencies and updated tests to reflect that the Daytona sandbox backend is now fully implemented. This clears all type checking errors and ensures the test suite accurately validates the current implementation state.

## Problem Statement

The CI/CD pipeline was failing due to mypy type checking errors and test failures in the sandbox configuration module. The issues were:

### Pain Points

- **Mypy errors**: Three import statements for optional Daytona dependencies were using `# type: ignore[import-untyped]` but mypy was reporting `import-not-found` errors, causing the type checker to fail
- **Outdated tests**: Test suite expected Daytona backend to raise "coming soon" errors, but the backend was actually fully implemented
- **Dead code**: Duplicate `elif backend_type == "daytona"` block (lines 160-164) was unreachable because Daytona was already handled earlier (lines 86-146)
- **Test failures**: Two tests failing with "Regex pattern did not match" errors

## Solution

Applied targeted fixes to align type ignore comments with actual error codes and update tests to match current implementation:

### Changes Made

1. **Updated type ignore comments** in `sandbox_factory.py`:
   - Changed `# type: ignore[import-untyped]` to `# type: ignore[import-not-found]` for three Daytona imports
   - This correctly suppresses errors for optional dependencies that may not be installed

2. **Removed dead code**:
   - Deleted unreachable duplicate Daytona handler (lines 160-164)
   - Cleaned up control flow in backend factory function

3. **Updated test expectations** in `test_sandbox_config.py`:
   - Renamed `test_daytona_not_yet_supported` → `test_daytona_requires_package`
   - Changed expected error from "coming soon" to "requires 'daytona' package"
   - Updated `test_all_supported_types_pass_validation` to handle Daytona as implemented backend

## Implementation Details

### Type Ignore Comment Fixes

The optional Daytona dependencies are only imported when `backend_type == "daytona"`, making them truly optional. Changed from:

```python
from daytona import Daytona, DaytonaConfig  # type: ignore[import-untyped]
from daytona.common.daytona import (
    CreateSandboxFromSnapshotParams,  # type: ignore[import-untyped]
)
from deepagents_cli.integrations.daytona import (
    DaytonaBackend,  # type: ignore[import-untyped]
)
```

To:

```python
from daytona import Daytona, DaytonaConfig  # type: ignore[import-not-found]
from daytona.common.daytona import (  # type: ignore[import-not-found]
    CreateSandboxFromSnapshotParams,
)
from deepagents_cli.integrations.daytona import (  # type: ignore[import-not-found]
    DaytonaBackend,
)
```

### Test Updates

Updated tests to expect the correct error message when Daytona package is not installed:

```python
def test_daytona_requires_package(self) -> None:
    """Test that daytona type requires daytona package to be installed."""
    config = {"type": "daytona"}
    
    with pytest.raises(ValueError, match="Daytona backend requires 'daytona' package"):
        create_sandbox_backend(config)
```

And added special handling in validation tests to distinguish between:
- **Filesystem**: Works without additional dependencies
- **Daytona**: Implemented but requires optional package
- **Modal/Runloop/Harbor**: Not yet implemented ("coming soon")

## Benefits

- ✅ **Clean type checking**: All 14 source files pass mypy with no errors
- ✅ **Accurate tests**: 23/23 tests passing with correct expectations
- ✅ **Code clarity**: Removed unreachable dead code
- ✅ **Developer experience**: CI/CD pipeline now passes completely
- ✅ **Documentation through tests**: Test names and assertions clearly communicate implementation status

## Impact

### Immediate Impact
- CI/CD builds now pass without type checking failures
- Test suite accurately reflects the current state of backend implementations
- Developers can run `make typecheck` successfully

### Downstream Effects
- Future Daytona backend development can proceed without test confusion
- Clear separation between "not yet implemented" vs "requires optional dependency" backends
- Cleaner codebase with dead code removed

## Code Metrics

**Files Modified**: 2
- `src/graphton/core/sandbox_factory.py`: Fixed type ignores, removed 6 lines of dead code
- `tests/test_sandbox_config.py`: Updated 2 test methods

**Test Results**:
- Before: 2 failures, 3 mypy errors
- After: 23/23 passing, 0 mypy errors

---

**Status**: ✅ Production Ready  
**Timeline**: ~30 minutes

