# Phase 1: Graphton Framework Foundation - Project Setup and Infrastructure

**Date**: November 27, 2025

## Summary

Completed Phase 1 of the Graphton Framework, establishing the complete project foundation for an open source declarative agent creation library for LangGraph. Created a production-ready Python package with modern development tooling, comprehensive documentation, GitHub repository with branch protection, and CI/CD pipeline. The repository is structured using the src/ layout pattern (matching graph-fleet), properly configured with Poetry, and ready for Phase 2 implementation of core agent factory functionality.

## Problem Statement

Building LangGraph agents currently requires significant boilerplate code. In the graph-fleet service, we've built three agents (AWS RDS Instance Creator, RDS Manifest Generator, Session Subject Generator) and discovered substantial code duplication—each requiring 100+ lines of configuration before writing actual agent logic:

### Pain Points

- **High friction for new agents**: 30-60 minutes of setup per agent before writing logic
- **Repetitive boilerplate**: MCP client creation, authentication, tool wrappers, middleware
- **Inconsistent patterns**: Each agent handles MCP loading differently without standard patterns
- **Maintenance burden**: Bug fixes must be replicated across all agents manually
- **Steep learning curve**: New developers must understand LangGraph, MCP, middleware, async/sync patterns, and authentication flows
- **No reusable abstraction**: Common patterns exist but aren't captured in a framework

The vision is to create a declarative framework that eliminates this boilerplate, allowing developers to create production-ready agents in 3-10 lines instead of 100+.

## Solution

Phase 1 establishes the complete foundation for the Graphton Framework:

### Project Goals

1. **Open Source Package**: Publishable Python package on PyPI
2. **Modern Development Practices**: Type checking, linting, testing, CI/CD
3. **Professional Documentation**: README, contributing guidelines, Apache 2.0 license
4. **Proper Structure**: src/ layout matching graph-fleet patterns
5. **GitHub Repository**: Public repository with branch protection and automation
6. **Quality Standards**: 100% test coverage, passing all checks

### Architecture Decisions

**Src/ Layout Structure**:
```
graphton/
├── src/
│   └── graphton/           # Main package
│       ├── __init__.py     # Version and exports
│       ├── core/           # Core functionality (Phase 2-3)
│       └── utils/          # Utilities (Phase 2-3)
├── tests/                  # Test suite
├── docs/                   # Documentation
├── .github/workflows/      # CI/CD
└── pyproject.toml          # Poetry configuration
```

**Why src/ Layout**:
- Prevents accidental imports from development directory
- Forces proper installation for testing (catches packaging issues early)
- Clearer separation between package code and project files
- Consistent with graph-fleet (our reference implementation)
- Python Packaging Authority recommendation

**Technology Stack**:
- **Package Manager**: Poetry (modern dependency management)
- **Linting**: Ruff (fast Python linter)
- **Type Checking**: MyPy with strict mode
- **Testing**: Pytest with coverage reporting
- **CI/CD**: GitHub Actions (Python 3.11 and 3.12)
- **License**: Apache 2.0 (patent protection, contributor agreement)

## Implementation Details

### 1. Repository Structure Created

**Package Files**:
- `src/graphton/__init__.py`: Version 0.1.0, package docstring
- `src/graphton/core/__init__.py`: Core functionality module (Phase 2-3)
- `src/graphton/utils/__init__.py`: Utility functions module (Phase 2-3)
- `tests/__init__.py`: Test suite package
- `tests/test_import.py`: Basic import tests (3 tests, 100% coverage)

**Configuration Files**:
- `pyproject.toml`: Poetry configuration with dependencies and dev tools
- `.gitignore`: Comprehensive Python exclusions (85 lines)
- `.python-version`: Pinned to Python 3.11
- `mypy.ini`: Strict type checking configuration
- `Makefile`: Development commands (deps, test, lint, typecheck, build, clean)

**Dependencies Installed**:
- **Core**: langgraph (>=1.0.0), langchain (>=1.0.0), pydantic (>=2.0.0)
- **MCP**: langchain-mcp-adapters (>=0.1.9)
- **LLM Providers**: langchain-anthropic, langchain-openai
- **Dev Tools**: ruff (>=0.6.0), mypy (>=1.10.0), pytest (>=8.0.0)
- **Total**: 72 packages installed

### 2. Documentation Created

**README.md** (Comprehensive project overview):
- Problem statement and motivation
- Features and value proposition
- Status indicators for all phases
- Installation instructions (placeholder for PyPI)
- Quick start guide (placeholder for Phase 2+)
- Roadmap with phase breakdown
- Development setup instructions
- Contributing guidelines reference
- CI badges and license information

**CONTRIBUTING.md** (Full contribution guidelines):
- Code of conduct principles
- Issue reporting guidelines
- Pull request process
- Development setup instructions
- Coding standards (PEP 8, type hints, docstrings)
- Testing requirements (unit tests, >80% coverage)
- Commit message guidelines (conventional commits)
- Recognition for contributors

**LICENSE** (Apache 2.0):
- Full Apache License 2.0 text
- Copyright 2025 Planton Cloud
- Patent protection and contributor agreement

### 3. GitHub CI/CD Setup

**CI Workflow** (`.github/workflows/ci.yml`):
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - Checkout code
      - Set up Python
      - Install Poetry
      - Cache dependencies
      - Run linting (ruff)
      - Run type checking (mypy)
      - Run tests with coverage
      - Upload coverage to Codecov
```

**Automation Benefits**:
- Tests run on every push and pull request
- Multi-Python version testing (3.11, 3.12)
- Dependency caching for faster builds
- Coverage reporting to Codecov
- Branch protection enforcement

### 4. GitHub Repository Configuration

**Repository Created**:
- URL: https://github.com/plantoncloud-inc/graphton
- Visibility: Public (open source)
- Description: "Declarative agent creation framework for LangGraph - eliminate boilerplate, build agents in minutes"
- Homepage: https://github.com/plantoncloud-inc/graphton

**Settings Applied**:
- Issues: Enabled (bug reports, feature requests)
- Wiki: Disabled (using README and docs/)
- Projects: Enabled (roadmap tracking)
- Topics: langgraph, langchain, ai-agents, mcp, python, framework

**Branch Protection Rules**:
- Required status checks: CI test job must pass
- Strict branch policy: PRs required for changes
- Stale review dismissal: Enabled
- Admin override: Allowed (enforce_admins: false)
- No force pushes or deletions
- Result: Maintains code quality while allowing admin flexibility

### 5. Initial Commits

**Commit 1** (`bd9c415`): Initial repository setup
- Complete project structure
- Poetry configuration with all dependencies
- Development tooling (ruff, mypy, pytest)
- CI workflow with linting and testing
- Apache 2.0 license
- Comprehensive README and contributing guidelines

**Commit 2** (`1f9014b`): Configuration fix
- Removed unsupported `pydantic-validation` config from ruff
- Fixed linting errors to pass CI

**Commit 3** (`f5c1787`): Structure refactoring
- Restructured from flat layout to src/ layout
- Updated author to Suresh Attaluri <suresh@planton.ai>
- Updated pyproject.toml packages config
- Updated Makefile and CI workflow paths

### 6. Quality Verification

**All Checks Passing**:
```bash
✅ Import test: graphton v0.1.0
✅ Linting (ruff): All checks passed
✅ Type checking (mypy): No issues found in 3 source files
✅ Tests: 3/3 passing with 100% coverage
✅ Build: All checks passed

Coverage Report:
Name                             Stmts   Miss  Cover
------------------------------------------------------
src/graphton/__init__.py             2      0   100%
src/graphton/core/__init__.py        0      0   100%
src/graphton/utils/__init__.py       0      0   100%
------------------------------------------------------
TOTAL                                2      0   100%
```

**Development Commands Available**:
```bash
make deps       # Install dependencies with Poetry
make test       # Run tests with coverage
make lint       # Run ruff linter
make typecheck  # Run mypy type checker
make build      # Run all checks (lint + typecheck + test)
make clean      # Clean cache files
```

## Benefits

### For Graphton Development

1. **Clean Foundation**: Professional project structure ready for development
2. **Quality Enforcement**: Automated linting, type checking, and testing on every commit
3. **Multi-Python Support**: Tested on Python 3.11 and 3.12 automatically
4. **Developer Experience**: Simple Makefile commands for all common tasks
5. **Documentation First**: README and contributing guidelines written before code

### For Open Source Community

1. **Clear Entry Point**: Comprehensive README explains vision and roadmap
2. **Contribution Ready**: Full contributing guidelines with coding standards
3. **Professional Appearance**: License, CI badges, proper structure signal quality
4. **GitHub Integration**: Issues enabled, branch protection configured
5. **Transparent Development**: Public repository from day one

### For Future Phases

1. **Solid Base**: No need to revisit project structure or tooling
2. **Test Infrastructure**: Pytest and coverage already configured
3. **CI/CD Pipeline**: Automatic testing on all changes
4. **Documentation Templates**: Structure established for future docs
5. **Import Tests**: Will catch breaking changes as functionality is added

## Code Metrics

**Files Created**: 15 files
- Python files: 5
- Configuration files: 5
- Documentation files: 3
- CI/CD files: 1
- Version control: 1 (.gitignore)

**Lines of Code**:
- Python code: ~50 lines (package initialization + tests)
- Configuration: ~150 lines (pyproject.toml, mypy.ini, Makefile)
- Documentation: ~500 lines (README, CONTRIBUTING, LICENSE)
- Total: ~700 lines of project infrastructure

**Dependencies Installed**: 72 packages
- Direct dependencies: 7
- Development dependencies: 5
- Transitive dependencies: 60

**Time Investment**: ~2 hours
- Planning and structure: 20 minutes
- Implementation: 60 minutes
- Documentation: 30 minutes
- Testing and refinement: 10 minutes

## Design Decisions

### Src/ Layout vs Flat Layout

**Decision**: Use src/ layout (`src/graphton/`) instead of flat layout (`graphton/`)

**Rationale**:
- Matches graph-fleet structure (consistency)
- Prevents accidental imports during development
- Forces proper installation for testing
- Python Packaging Authority recommendation
- Clearer separation of concerns

**Trade-off**: Slightly longer import paths in development, but better practices

### Poetry vs Other Tools

**Decision**: Use Poetry for dependency management

**Rationale**:
- Modern, widely adopted in Python community
- Excellent dependency resolution
- Lock file for reproducible builds
- Integrated build and publish commands
- Better developer experience than setup.py

**Alternative Considered**: pip + requirements.txt (too basic for library distribution)

### Apache 2.0 vs MIT License

**Decision**: Apache 2.0 License

**Rationale**:
- Patent protection for users and contributors
- Explicit contributor license agreement
- Better for commercial adoption
- Matches mcp-server-planton (consistency)
- More comprehensive than MIT

**Trade-off**: Slightly more complex than MIT, but better legal protection

### Ruff vs Other Linters

**Decision**: Ruff for linting

**Rationale**:
- Extremely fast (100x faster than flake8)
- All-in-one tool (replaces flake8, isort, pyupgrade)
- Growing adoption in Python community
- Good defaults for modern Python
- Active development

**Alternative Considered**: flake8 + plugins (too slow, too many tools)

### Python 3.11+ Requirement

**Decision**: Require Python 3.11 or later

**Rationale**:
- LangGraph requires 3.11+
- Modern type hint support
- Performance improvements
- Not too bleeding edge (3.11 released Oct 2022)
- Matches graph-fleet requirement

**Trade-off**: Excludes Python 3.10 users (acceptable for new project)

## Impact

### Immediate Impact

1. **Repository Live**: https://github.com/plantoncloud-inc/graphton is public and accessible
2. **CI/CD Active**: Automated testing runs on every commit
3. **Development Ready**: Team can clone and start Phase 2 development immediately
4. **Quality Baseline**: All checks passing, 100% test coverage maintained
5. **Professional Appearance**: Project looks polished and production-ready

### Phase 2 Readiness

Phase 2 can now proceed with implementing `create_deep_agent()`:
- Package structure in place
- Import tests will catch breaking changes
- CI will verify all changes automatically
- Documentation structure ready for API docs
- Testing infrastructure configured

### Long-term Impact

1. **Open Source Presence**: Graphton is discoverable on GitHub
2. **Community Building**: Issues and contributions enabled from day one
3. **Reference Implementation**: Serves as template for other Planton Cloud open source projects
4. **Brand Building**: Professional project reflects well on Planton Cloud engineering

## Related Work

### Related to Graph-Fleet

This Phase 1 directly supports the graph-fleet roadmap:
- **Issue #116**: [Phased Plan] Graphton Framework - Declarative Agent Creation for LangGraph
- **Phase 2-6**: Will build on this foundation to implement core functionality
- **Graph-Fleet Agents**: Will eventually migrate to use Graphton, reducing boilerplate

### Pattern Reuse

Structure and patterns borrowed from:
- **graph-fleet**: src/ layout, Poetry configuration, Makefile patterns
- **mcp-server-planton**: Apache 2.0 license, GitHub repository setup
- **deepagents**: Inspiration for agent abstraction approach

### Future Connections

Will connect to:
- **Phase 2**: Core agent factory implementation
- **Phase 3**: MCP integration with per-user authentication
- **Phase 4**: Configuration validation with Pydantic
- **Phase 5**: Comprehensive documentation and PyPI release
- **Phase 6**: Production validation with graph-fleet migration

## Next Steps

### Immediate (Phase 2)

1. Implement `create_deep_agent()` function
2. Add model name parsing (e.g., "claude-sonnet-4.5" → ChatAnthropic)
3. Implement system prompt handling
4. Add state schema configuration support
5. Create basic agent without MCP tools (proof of concept)
6. Add unit tests for agent creation
7. Update README with basic usage examples

### Near-term (Phase 3-4)

1. Add MCP server configuration parsing
2. Implement tool loading with per-user authentication
3. Generate automatic tool wrappers
4. Add Pydantic models for configuration validation
5. Expand test coverage for MCP integration
6. Add integration tests with mock MCP server

### Long-term (Phase 5-6)

1. Write comprehensive API documentation
2. Create example agents demonstrating features
3. Publish to PyPI (v0.1.0 release)
4. Migrate graph-fleet agents to Graphton
5. Gather community feedback
6. Iterate based on real-world usage

## Testing Strategy

### Current Tests

**Import Tests** (`tests/test_import.py`):
- `test_graphton_import()`: Verifies package can be imported and version is correct
- `test_core_import()`: Verifies core submodule can be imported
- `test_utils_import()`: Verifies utils submodule can be imported

Coverage: 100% (2 statements in package, all covered)

### Future Test Strategy

As functionality is added in Phase 2+:
- **Unit tests**: For each function and class
- **Integration tests**: For MCP tool loading and agent creation
- **Type tests**: Verify type hints with mypy
- **Example tests**: Ensure README examples work
- **Coverage target**: Maintain >80% coverage

## Known Limitations

### Current Limitations

1. **No functionality yet**: Package is just infrastructure (Phase 1 scope)
2. **No examples**: Can't demonstrate usage until Phase 2
3. **Not published**: Not yet on PyPI (planned for Phase 5)
4. **Documentation incomplete**: API docs depend on Phase 2-4 implementation

### Intentional Decisions

1. **Minimal dependencies**: Core dependencies only, will expand in Phase 2-3
2. **Bare package structure**: core/ and utils/ modules empty (will fill in later phases)
3. **Simple tests**: Just import tests, real tests come with real functionality
4. **README placeholders**: Quick start and examples marked as "Coming Soon"

These are appropriate for Phase 1 - establishing foundation before building functionality.

---

**Status**: ✅ Completed and Deployed  
**Timeline**: November 27, 2025 (~2 hours)  
**GitHub**: https://github.com/plantoncloud-inc/graphton  
**Next Phase**: Phase 2 - Core Agent Factory Implementation















