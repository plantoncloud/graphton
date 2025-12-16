"""Tests for sub-agent support in Graphton."""

import pytest

from graphton import create_deep_agent


def test_subagent_parameter_accepted() -> None:
    """Test that subagents parameter is accepted."""
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a coordinator.",
        subagents=[
            {
                "name": "researcher",
                "description": "Research specialist",
                "system_prompt": "You are a researcher.",
            }
        ],
    )
    assert agent is not None


def test_multiple_subagents() -> None:
    """Test that multiple sub-agents can be configured."""
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a coordinator.",
        subagents=[
            {
                "name": "researcher",
                "description": "Research specialist",
                "system_prompt": "You are a researcher.",
            },
            {
                "name": "reviewer",
                "description": "Code reviewer",
                "system_prompt": "You are a code reviewer.",
            }
        ],
    )
    assert agent is not None


def test_general_purpose_agent_default() -> None:
    """Test that general_purpose_agent defaults to True."""
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a coordinator.",
        subagents=[],
    )
    # Should include general-purpose sub-agent by default
    assert agent is not None


def test_general_purpose_agent_only() -> None:
    """Test that general-purpose agent can be used without custom sub-agents."""
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a coordinator.",
        # No subagents, but general_purpose_agent=True by default
    )
    assert agent is not None


def test_disable_general_purpose_agent() -> None:
    """Test disabling general-purpose sub-agent."""
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a coordinator.",
        subagents=[
            {
                "name": "specialist",
                "description": "Specialist only",
                "system_prompt": "You are a specialist.",
            }
        ],
        general_purpose_agent=False,
    )
    assert agent is not None


def test_subagent_with_custom_tools() -> None:
    """Test sub-agent with custom tools specification."""
    from langchain_core.tools import tool

    @tool
    def custom_tool(input: str) -> str:
        """Custom tool for testing."""
        return f"Processed: {input}"

    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a coordinator.",
        subagents=[
            {
                "name": "specialist",
                "description": "Specialist with custom tools",
                "system_prompt": "You are a specialist.",
                "tools": [custom_tool],
            }
        ],
    )
    assert agent is not None


def test_subagent_validation_missing_name() -> None:
    """Test validation fails when sub-agent missing name."""
    with pytest.raises(ValueError, match="missing required field 'name'"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents=[
                {
                    "description": "No name provided",
                    "system_prompt": "System prompt",
                }
            ],
        )


def test_subagent_validation_missing_description() -> None:
    """Test validation fails when sub-agent missing description."""
    with pytest.raises(ValueError, match="missing required field 'description'"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents=[
                {
                    "name": "researcher",
                    "system_prompt": "System prompt",
                }
            ],
        )


def test_subagent_validation_missing_system_prompt() -> None:
    """Test validation fails when sub-agent missing system_prompt."""
    with pytest.raises(ValueError, match="missing required field 'system_prompt'"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents=[
                {
                    "name": "researcher",
                    "description": "Research specialist",
                }
            ],
        )


def test_subagent_validation_empty_name() -> None:
    """Test validation fails when sub-agent has empty name."""
    with pytest.raises(ValueError, match="'name' must be a non-empty string"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents=[
                {
                    "name": "",
                    "description": "Empty name",
                    "system_prompt": "System prompt",
                }
            ],
        )


def test_subagent_validation_empty_description() -> None:
    """Test validation fails when sub-agent has empty description."""
    with pytest.raises(ValueError, match="'description' must be a non-empty string"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents=[
                {
                    "name": "researcher",
                    "description": "",
                    "system_prompt": "System prompt",
                }
            ],
        )


def test_subagent_validation_empty_system_prompt() -> None:
    """Test validation fails when sub-agent has empty system_prompt."""
    with pytest.raises(ValueError, match="'system_prompt' must be a non-empty string"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents=[
                {
                    "name": "researcher",
                    "description": "Research specialist",
                    "system_prompt": "",
                }
            ],
        )


def test_subagent_validation_duplicate_names() -> None:
    """Test validation fails when sub-agents have duplicate names."""
    with pytest.raises(ValueError, match="Duplicate sub-agent names found"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents=[
                {
                    "name": "agent1",
                    "description": "First agent",
                    "system_prompt": "System prompt 1",
                },
                {
                    "name": "agent1",
                    "description": "Second agent with same name",
                    "system_prompt": "System prompt 2",
                }
            ],
        )


def test_subagent_validation_not_dict() -> None:
    """Test validation fails when sub-agent is not a dict."""
    with pytest.raises(ValueError, match="Input should be a valid dictionary"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents=[
                "not a dict"  # type: ignore
            ],
        )


def test_subagent_validation_not_list() -> None:
    """Test validation fails when subagents is not a list."""
    with pytest.raises(ValueError, match="Input should be a valid list"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents={"not": "a list"},  # type: ignore
        )


def test_backward_compatibility_no_subagents() -> None:
    """Test that existing code without sub-agents still works."""
    # This ensures backward compatibility
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a helpful assistant.",
    )
    assert agent is not None


def test_backward_compatibility_with_other_params() -> None:
    """Test that sub-agents work with other existing parameters."""
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a helpful assistant.",
        recursion_limit=50,
        temperature=0.7,
        max_tokens=5000,
        subagents=[
            {
                "name": "researcher",
                "description": "Research specialist",
                "system_prompt": "You are a researcher.",
            }
        ],
    )
    assert agent is not None


def test_subagents_with_other_parameters() -> None:
    """Test that sub-agents work with various other parameters."""
    # Test that subagents are compatible with other Graphton features
    from langchain_core.tools import tool

    @tool
    def test_tool(input: str) -> str:
        """Test tool."""
        return f"Test: {input}"

    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a coordinator with additional tools.",
        tools=[test_tool],
        recursion_limit=200,
        temperature=0.5,
        max_tokens=5000,
        subagents=[
            {
                "name": "researcher",
                "description": "Research specialist",
                "system_prompt": "You are a researcher.",
            }
        ],
    )
    assert agent is not None


def test_empty_subagents_list() -> None:
    """Test that empty subagents list is valid."""
    # Empty list should work (only general-purpose agent if enabled)
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="You are a coordinator.",
        subagents=[],
    )
    assert agent is not None


def test_subagent_name_types() -> None:
    """Test that sub-agent names must be strings."""
    with pytest.raises(ValueError, match="'name' must be a non-empty string"):
        create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a coordinator.",
            subagents=[
                {
                    "name": 123,  # type: ignore
                    "description": "Invalid name type",
                    "system_prompt": "System prompt",
                }
            ],
        )
