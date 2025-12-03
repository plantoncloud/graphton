# Phase 4: Configuration Validation with Pydantic

**Date**: November 27, 2025

## Summary

Implemented comprehensive configuration validation for the Graphton Framework using Pydantic models. This phase transforms configuration errors from runtime failures into immediate, helpful feedback at graph creation time. Invalid configurations now fail fast with clear, actionable error messages that guide developers toward correct usage. The validation layer includes a top-level `AgentConfig` model, enhanced validation for MCP configurations, 37 comprehensive tests, complete type coverage verified by mypy, and extensive documentation.

## Problem Statement

After completing Phase 3 (MCP integration), Graphton had basic validation through Pydantic's type system but lacked comprehensive validation logic. Configuration errors would manifest as runtime failures with generic messages, or worse, as subtle bugs during agent execution.

### Pain Points

**Developer Experience Issues**:
- Configuration errors discovered late (at runtime, not at graph creation)
- Generic error messages like "field required" without context
- No validation of parameter relationships (e.g., `mcp_servers` without `mcp_tools`)
- Unclear what constitutes a valid configuration

**Missing Validations**:
- System prompt length and meaningfulness
- Recursion limit bounds (could be 0 or negative)
- Temperature range validation (0.0-2.0)
- MCP server name consistency between `mcp_servers` and `mcp_tools`
- Tool name format validation
- Duplicate tool detection
- URL scheme validation for security

**Type Coverage**:
- Type hints incomplete in some modules
- No verification that mypy passes cleanly
- Potential None-handling issues

**Documentation Gap**:
- No comprehensive configuration reference
- Examples lacked validation context
- Error messages not documented

## Solution

Created a comprehensive validation framework that validates all configuration at graph creation time and provides helpful, actionable error messages.

### Core Components

1. **AgentConfig Model** - Top-level Pydantic model that validates all `create_deep_agent()` parameters
2. **Enhanced Config Models** - Improved `McpServerConfig` and `McpToolsConfig` with detailed validation
3. **Validation Integration** - Updated agent factory to validate through `AgentConfig`
4. **Comprehensive Tests** - 37 new tests covering all validation scenarios
5. **Type Coverage** - Verified complete type hints across all modules
6. **Configuration Documentation** - Complete reference guide

### Validation Strategy

**Early Detection**: All validation happens in the `create_deep_agent()` call, before any agent construction. Errors caught immediately with context.

**Helpful Messages**: Each validation includes:
- Clear description of what's wrong
- Explanation of why it's invalid
- Actionable suggestion for fixing it
- Relevant value ranges or examples

**Progressive Disclosure**: Simple cases work with minimal configuration, advanced options available with validation guardrails.

## Implementation Details

### 1. AgentConfig Model

Created top-level configuration model with field validators and model validators:

```python
class AgentConfig(BaseModel):
    """Top-level configuration for agent creation."""
    
    model: str | BaseChatModel
    system_prompt: str
    mcp_servers: dict[str, dict[str, Any]] | None = None
    mcp_tools: dict[str, list[str]] | None = None
    tools: Sequence[BaseTool] | None = None
    middleware: Sequence[Any] | None = None
    context_schema: type[Any] | None = None
    recursion_limit: int = 100
    max_tokens: int | None = None
    temperature: float | None = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
```

**Field Validators**:

- **system_prompt**: Must be ≥10 characters, non-empty
- **recursion_limit**: Must be positive; warning if >500
- **temperature**: Must be 0.0-2.0 with usage guidance

**Model Validator**:

- Validates MCP configuration consistency (both or neither)
- Checks server names match between `mcp_servers` and `mcp_tools`
- Provides specific guidance for mismatches

### 2. Enhanced McpServerConfig

Added validators for production-ready configurations:

```python
@field_validator("url")
@classmethod
def validate_url_scheme(cls, v: HttpUrl) -> HttpUrl:
    """Warn about HTTP in production."""
    if v.scheme == "http" and "localhost" not in str(v) and "127.0.0.1" not in str(v):
        warnings.warn(
            f"MCP server URL uses insecure HTTP: {v}. "
            "Use HTTPS in production for secure authentication.",
            UserWarning,
            stacklevel=2
        )
    return v

@field_validator("headers")
@classmethod
def validate_headers(cls, v: dict[str, str] | None) -> dict[str, str] | None:
    """Warn about Authorization header conflicts."""
    if v and "Authorization" in v:
        warnings.warn(
            "Static 'Authorization' header will be overwritten by per-user token. "
            "Remove it from headers or set auth_from_context=False.",
            UserWarning,
            stacklevel=2
        )
    return v
```

**Validation Features**:
- Transport type validation with helpful suggestions
- HTTPS recommendation for non-localhost URLs
- Authorization header conflict detection

### 3. Enhanced McpToolsConfig

Added comprehensive tool validation:

```python
@field_validator("tools")
@classmethod
def validate_tools_structure(cls, v: dict[str, list[str]]) -> dict[str, list[str]]:
    """Validate tool names and detect issues."""
    if not v:
        raise ValueError(
            "At least one MCP server with tools is required. "
            "Example: {'planton-cloud': ['list_organizations', 'create_cloud_resource']}"
        )
    
    for server_name, tool_list in v.items():
        # Non-empty check
        if not tool_list:
            raise ValueError(f"Server '{server_name}' has empty tool list.")
        
        # Type validation
        for tool_name in tool_list:
            if not isinstance(tool_name, str):
                raise ValueError(f"Tool name must be string, got {type(tool_name).__name__}")
            
            # Format validation
            if not tool_name.replace("_", "").replace("-", "").isalnum():
                raise ValueError(
                    f"Invalid tool name '{tool_name}' in server '{server_name}'. "
                    "Tool names should use alphanumeric characters, underscores, or hyphens."
                )
        
        # Duplicate detection
        if len(tool_list) != len(set(tool_list)):
            duplicates = [t for t in tool_list if tool_list.count(t) > 1]
            raise ValueError(f"Duplicate tool names in server '{server_name}': {set(duplicates)}")
    
    return v
```

**Validation Features**:
- Non-empty tool lists
- String type enforcement
- Tool name format validation (alphanumeric, underscores, hyphens)
- Duplicate tool detection within servers
- Clear examples in error messages

### 4. Agent Factory Integration

Updated `create_deep_agent()` to validate via `AgentConfig`:

```python
def create_deep_agent(
    model: str | BaseChatModel,
    system_prompt: str,
    # ... all parameters ...
) -> CompiledStateGraph:
    """Create a Deep Agent with validated configuration."""
    
    # Validate configuration using AgentConfig model
    try:
        _ = AgentConfig(
            model=model,
            system_prompt=system_prompt,
            mcp_servers=mcp_servers,
            mcp_tools=mcp_tools,
            tools=tools,
            middleware=middleware,
            context_schema=context_schema,
            recursion_limit=recursion_limit,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed:\n{e}") from e
    
    # Rest of existing implementation...
```

All existing logic remains unchanged—validation is a non-invasive addition that catches errors before agent construction.

### 5. Comprehensive Test Suite

Created `tests/test_config_validation.py` with 37 tests organized by component:

**McpServerConfig Tests (7 tests)**:
- Valid configurations
- Invalid transport types
- Invalid URLs
- HTTP warning for non-localhost
- Authorization header warnings

**McpToolsConfig Tests (9 tests)**:
- Valid configurations
- Empty dictionaries/lists
- Invalid tool name types
- Invalid characters
- Duplicate detection
- Valid underscore/hyphen formats

**AgentConfig Tests (17 tests)**:
- Valid minimal configurations
- System prompt validation (empty, short)
- Recursion limit validation (zero, negative, high)
- Temperature validation (negative, too high, boundaries)
- MCP configuration consistency
- Server name mismatches

**Integration Tests (4 tests)**:
- Invalid config caught by `create_deep_agent()`
- Valid config passes through
- Parameter-specific failures

All tests pass with comprehensive coverage of edge cases.

### 6. Type Coverage Verification

Fixed type errors and verified mypy passes cleanly:

**Issue Found**: Mypy reported Union type errors in `AgentConfig.validate_mcp_configuration()`:
```
error: Item "None" of "dict[str, dict[str, Any]] | None" has no attribute "keys"
```

**Fix Applied**: Type narrowing with assertions:
```python
if has_servers and has_tools:
    assert self.mcp_servers is not None
    assert self.mcp_tools is not None
    
    server_names = set(self.mcp_servers.keys())
    tool_server_names = set(self.mcp_tools.keys())
```

**Result**: `mypy` now passes cleanly:
```bash
$ make typecheck
Success: no issues found in 10 source files
```

### 7. Configuration Documentation

Created comprehensive `docs/CONFIGURATION.md` (580 lines) covering:

**Reference Sections**:
- AgentConfig parameters (required and optional)
- Model configuration (string format and instances)
- System prompt requirements and examples
- Recursion limit guidelines
- Temperature ranges and use cases
- MCP server configuration format
- MCP tools configuration format

**Error Message Examples**:
- System prompt errors (empty, too short)
- Parameter validation errors (recursion limit, temperature)
- MCP configuration errors (missing components, name mismatches)

**IDE Support**:
- Type hints and autocomplete
- Error detection workflows

**Migration Guide**:
- Before/after comparisons from raw LangGraph

### 8. README Updates

Added "Configuration Validation" section to `README.md`:

**Content**:
- Early error detection examples
- Helpful suggestion examples
- Parameter validation examples
- MCP configuration validation examples
- IDE autocomplete support
- Type safety with mypy

**Roadmap Update**: Marked Phase 4 as complete ✅

## Benefits

### Developer Experience

**Immediate Feedback**: Errors caught at graph creation, not during execution or worse, in production.

**Clear Guidance**: Error messages include:
- What's wrong: "system_prompt is too short (2 chars)"
- Why it matters: "Provide at least 10 characters describing the agent's purpose"
- How to fix: Contextual examples and suggestions

**IDE Support**: Pydantic models enable:
- Autocomplete for all parameters with types and defaults
- Type checking before running code
- Inline documentation in tooltips

### Code Quality

**Type Safety**:
- Complete type coverage verified by mypy
- No Union type errors or None-handling issues
- Consistent type hints across all modules

**Test Coverage**:
- 37 new validation tests
- Overall coverage: 68% (up from 63% in Phase 3)
- Config module coverage: 98%

**Maintainability**:
- Validation logic centralized in Pydantic models
- Easy to add new validations
- Clear separation of concerns

### Production Readiness

**Security Validation**:
- HTTPS recommended for production URLs
- Authorization header conflict detection
- Prevents insecure configurations silently

**Operational Safety**:
- Prevents invalid recursion limits (0, negative)
- Warns about extreme values (>500 recursion)
- Validates MCP configuration consistency

**Documentation**:
- Complete configuration reference
- Error message catalog
- Migration examples

## Impact

### Immediate

**Graphton Framework**:
- ✅ Phase 4 complete with comprehensive validation
- ✅ All 95 tests pass (37 new validation tests)
- ✅ Mypy clean (10 source files)
- ✅ 68% test coverage
- ✅ Production-ready validation layer

**Developer Productivity**:
- Configuration errors caught immediately (seconds vs. minutes)
- Clear error messages reduce debugging time
- IDE support improves coding speed

### User Experience

**Error Messages - Before**:
```python
agent = create_deep_agent(model="claude-sonnet-4.5", system_prompt="")
# ValueError: system_prompt cannot be empty
```

**Error Messages - After**:
```python
agent = create_deep_agent(model="claude-sonnet-4.5", system_prompt="")
# ValueError: Configuration validation failed:
# system_prompt cannot be empty. Provide a clear description 
# of the agent's role and capabilities.
```

**Validation Example**:
```python
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are helpful.",
    mcp_servers={"server-a": {"url": "https://a.example.com/"}},
    mcp_tools={"server-b": ["tool1"]},  # Name mismatch!
)
# ValueError: Configuration validation failed:
# Server(s) configured but no tools specified: {'server-a'}.
# Tools specified for undefined server(s): {'server-b'}.
# Add server configurations in mcp_servers.
```

### Long-Term

**Maintainability**:
- Centralized validation logic easy to extend
- New parameters can add validators incrementally
- Clear patterns for future enhancements

**Quality Standards**:
- Type safety enforced across all configurations
- Comprehensive test coverage for validation logic
- Documentation keeps pace with features

## Files Changed

### Modified (4 files)

1. **src/graphton/core/config.py** (+224 lines)
   - Added `AgentConfig` model with comprehensive validation
   - Enhanced `McpServerConfig` with URL scheme and header validation
   - Enhanced `McpToolsConfig` with tool name format validation
   - Added type narrowing assertions for mypy

2. **src/graphton/core/agent.py** (+20 lines)
   - Integrated `AgentConfig` validation in `create_deep_agent()`
   - Added `ValidationError` import from pydantic
   - Wrapped validation with helpful error context

3. **tests/test_mcp_integration.py** (+12 lines)
   - Updated error message assertions for new validation
   - Changed system prompts to meet 10-character minimum
   - Updated regex patterns to match enhanced error messages

4. **README.md** (+110 lines)
   - Added "Configuration Validation" section with examples
   - Updated Phase 4 status to complete ✅
   - Expanded roadmap with Phase 4 deliverables

### Created (2 files)

1. **tests/test_config_validation.py** (371 lines)
   - 7 tests for `McpServerConfig`
   - 9 tests for `McpToolsConfig`
   - 17 tests for `AgentConfig`
   - 4 integration tests with `create_deep_agent()`
   - Comprehensive edge case coverage

2. **docs/CONFIGURATION.md** (580 lines)
   - Complete parameter reference (required and optional)
   - Model configuration guide
   - System prompt requirements and examples
   - Recursion limit and temperature guidelines
   - MCP server and tools configuration format
   - Error message catalog with examples
   - IDE support and type checking guide
   - Migration guide from raw LangGraph

### Total Changes

- **6 files changed**
- **~1,300 lines added**
- **37 new tests added**
- **Test coverage: 68% (↑5% from Phase 3)**

## Design Decisions

### Why AgentConfig at the Top Level?

**Decision**: Create a top-level `AgentConfig` model that validates all parameters together.

**Alternatives Considered**:
1. Validate parameters individually in `create_deep_agent()`
2. Use separate validators per parameter type
3. Rely on Pydantic's built-in validation only

**Rationale**:
- ✅ Centralized validation logic
- ✅ Can validate parameter relationships (MCP consistency)
- ✅ Clear single source of truth
- ✅ Easy to extend with new validations
- ✅ Provides good error context

**Trade-off**: Slight overhead creating temporary config object, but negligible compared to benefits.

### Why Warnings Instead of Errors for HTTP URLs?

**Decision**: Issue warnings (not errors) for HTTP URLs on non-localhost.

**Rationale**:
- Development often uses HTTP locally
- Production should use HTTPS, but shouldn't block
- Warnings visible in logs for review
- Developers can make informed decisions

**Alternative**: Could make it an error, but that's too restrictive for legitimate development use cases.

### Why 10-Character Minimum for System Prompts?

**Decision**: Require system prompts to be at least 10 characters.

**Rationale**:
- Catches obvious mistakes like empty strings or typos
- 10 characters allows "Be helpful." but blocks "Hi" or "Test"
- Encourages meaningful prompts
- Can still be circumvented if really needed ("Test agent" is valid)

**Alternative**: Could be 20 or 50, but 10 is a good balance between strictness and flexibility.

### Why Validate Tool Names?

**Decision**: Validate tool names are alphanumeric with underscores/hyphens.

**Rationale**:
- MCP tool names should follow conventions
- Catches typos and formatting errors early
- Prevents special characters that might cause issues
- Still flexible (both snake_case and kebab-case work)

**Impact**: All tested MCP servers use conventional names, so no compatibility issues.

## Testing Strategy

### Unit Tests (37 tests)

**Coverage by Component**:
- `McpServerConfig`: 7 tests
- `McpToolsConfig`: 9 tests
- `AgentConfig`: 17 tests
- Integration: 4 tests

**Testing Approach**:
- Test valid configurations pass
- Test invalid configurations fail with specific messages
- Test edge cases (boundaries, empty values, None)
- Test warnings are issued appropriately

### Test Quality

**Pattern Used**:
```python
def test_invalid_temperature_negative(self) -> None:
    """Test error for negative temperature."""
    with pytest.raises(ValidationError) as exc_info:
        AgentConfig(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            temperature=-0.5,
        )
    assert "between 0.0 and 2.0" in str(exc_info.value)
```

**Benefits**:
- Clear test names describe what's being validated
- Docstrings explain the scenario
- Assertions verify both exception type and message content
- Type hints ensure test correctness

### Integration with Existing Tests

Updated existing MCP integration tests to work with new validation:
- Changed generic "Test" system prompts to valid 10+ character prompts
- Updated error message assertions to match new validation messages
- No behavioral changes—just adapting to stricter validation

## Known Limitations

1. **Arbitrary Types Configuration**: `AgentConfig` requires `ConfigDict(arbitrary_types_allowed=True)` for `BaseChatModel` and `BaseTool` types. This is a Pydantic limitation.

2. **Model Instance Validation**: When passing a model instance directly, parameter overrides trigger warnings but aren't validated by `AgentConfig`. This is intentional—advanced users passing instances have full control.

3. **Tool Name Validation Strictness**: Only validates format (alphanumeric + underscores/hyphens), not whether tools actually exist on the server. Runtime validation still needed.

4. **Warning Visibility**: Warnings (HTTP URLs, header conflicts) require proper logging setup to be visible in production. Consider making these errors in future versions.

## Future Enhancements

### Phase 5 Considerations

When preparing for open source release:
- Add more examples to configuration documentation
- Consider interactive validation in CLI tools
- Add configuration schema export (JSON Schema)

### Potential Improvements

**Validation Extensions**:
- Validate model names against known providers (with fallback)
- Add custom error types for better exception handling
- Validate tool names against server capabilities (if schema available)

**Developer Experience**:
- Configuration builder/wizard for complex setups
- VSCode extension with schema support
- Configuration validation CLI command

**Production Features**:
- Environment-specific validation (strict mode for production)
- Configuration validation hooks for CI/CD
- Logging integration for warning aggregation

## Related Work

**Dependencies**:
- Phase 1: Foundation - Project structure (complete ✅)
- Phase 2: Agent Factory - Model and prompt handling (complete ✅)
- Phase 3: MCP Integration - Server and tools (complete ✅)

**Enables**:
- Phase 5: Documentation and open source release (next)
- Phase 6: Graph-fleet migration with validated configs

**Related Features**:
- Configuration validation complements Phase 3's MCP authentication
- Error messages improve on Phase 2's model parsing feedback
- Type coverage builds on Phase 1's development tooling

## Code Metrics

**Lines Added**: ~1,300 lines
- Configuration validation: ~230 lines
- Tests: ~370 lines
- Documentation: ~580 lines
- README updates: ~110 lines

**Test Metrics**:
- Total tests: 95 (↑37 from Phase 3)
- Tests passing: 95
- Tests skipped: 28 (require API keys)
- Coverage: 68% overall, 98% for config module

**Quality Checks**:
- ✅ Linting: All checks passed (ruff)
- ✅ Type checking: Success, no issues found (mypy)
- ✅ Tests: 95 passed, 28 skipped

---

**Status**: ✅ Production Ready  
**Timeline**: Phase 4 completed in ~4 hours of focused implementation  
**Next Steps**: Phase 5 (Documentation and open source release)












