# Contributing to Graphton

Thank you for your interest in contributing to Graphton! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and collaborative environment for all contributors.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check if the issue already exists in [GitHub Issues](https://github.com/plantoncloud-inc/graphton/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the problem or feature
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Environment details (Python version, OS, etc.)

### Submitting Pull Requests

1. **Fork the repository** and create your branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards:
   - Write clear, descriptive commit messages
   - Follow PEP 8 style guidelines (enforced by ruff)
   - Add type hints to all functions
   - Write docstrings for public APIs
   - Keep changes focused and atomic

3. **Add tests** for your changes:
   - Unit tests for new functionality
   - Integration tests for MCP interactions
   - Ensure all tests pass: `make test`

4. **Run code quality checks**:
   ```bash
   make build  # Runs lint, typecheck, and test
   ```

5. **Update documentation** if needed:
   - Update README.md for user-facing changes
   - Add docstrings for new functions/classes
   - Update examples if applicable

6. **Submit your pull request**:
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure CI passes
   - Request review from maintainers

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/graphton.git
cd graphton

# Install dependencies
make deps

# Activate virtual environment
poetry shell

# Run tests
make test

# Run linting
make lint

# Run type checking
make typecheck

# Run all checks
make build
```

## Coding Standards

### Python Style

- **PEP 8 compliance**: Enforced by ruff linter
- **Type hints**: Required for all function signatures
- **Docstrings**: Required for public APIs (Google style)
- **Line length**: 100 characters maximum
- **Imports**: Organized and sorted by ruff

### Testing

- **Unit tests**: Required for all new functionality
- **Test coverage**: Aim for >80% coverage
- **Test naming**: `test_<function_name>_<scenario>`
- **Fixtures**: Use pytest fixtures for reusable test data
- **Async tests**: Use `pytest-asyncio` for async functions

### Documentation

- **Docstring format**: Google style
- **Type information**: Include in docstrings and type hints
- **Examples**: Provide usage examples in docstrings
- **README updates**: Keep README.md current with features

### Example Code Style

```python
"""Module docstring explaining purpose."""

from typing import Any


def create_agent(
    model: str,
    system_prompt: str,
    *,
    tools: list[str] | None = None,
) -> Any:
    """Create a LangGraph agent with specified configuration.
    
    Args:
        model: Model name (e.g., "claude-sonnet-4.5")
        system_prompt: System prompt for the agent
        tools: Optional list of tool names to include
    
    Returns:
        Compiled LangGraph agent ready to invoke
    
    Raises:
        ValueError: If model name is invalid
    
    Example:
        >>> agent = create_agent(
        ...     model="claude-sonnet-4.5",
        ...     system_prompt="You are a helpful assistant",
        ...     tools=["search", "calculator"]
        ... )
    """
    # Implementation
    pass
```

## Commit Message Guidelines

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example:**
```
feat(mcp): add support for multiple MCP servers

Implement multi-server MCP configuration allowing agents to
connect to multiple MCP servers simultaneously. Each server
can have its own authentication and transport configuration.

Closes #42
```

## Pull Request Process

1. **CI must pass**: All automated checks must succeed
2. **Code review**: At least one maintainer review required
3. **Documentation**: Must be updated if applicable
4. **Tests**: Must include tests for new functionality
5. **Changelog**: Maintainers will update changelog on merge

## Release Process

Releases are managed by maintainers following semantic versioning:

- **Major (X.0.0)**: Breaking changes
- **Minor (0.X.0)**: New features, backwards compatible
- **Patch (0.0.X)**: Bug fixes, backwards compatible

## Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Discord**: [Planton Cloud Community](https://planton.cloud/discord) (coming soon)

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Release notes for significant contributions
- Special thanks in project README

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to Graphton! 🚀

