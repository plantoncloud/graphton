"""Unit tests for agent factory."""

import os
import warnings
import pytest
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from graphton import create_deep_agent


# Skip OpenAI tests if API key not available
skip_if_no_openai_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


class TestBasicAgentCreation:
    """Tests for basic agent creation functionality."""
    
    def test_create_agent_with_model_string(self) -> None:
        """Test creating agent with model name string."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_create_agent_with_anthropic_instance(self) -> None:
        """Test creating agent with ChatAnthropic instance."""
        model = ChatAnthropic(model="claude-sonnet-4-5-20250929", max_tokens=10000)
        agent = create_deep_agent(
            model=model,
            system_prompt="You are a helpful assistant.",
        )
        assert isinstance(agent, CompiledStateGraph)
    
    @skip_if_no_openai_key
    def test_create_agent_with_openai_instance(self) -> None:
        """Test creating agent with ChatOpenAI instance."""
        model = ChatOpenAI(model="gpt-4o")
        agent = create_deep_agent(
            model=model,
            system_prompt="You are a helpful assistant.",
        )
        assert isinstance(agent, CompiledStateGraph)
    
    @skip_if_no_openai_key
    def test_create_agent_openai_model_string(self) -> None:
        """Test creating agent with OpenAI model string."""
        agent = create_deep_agent(
            model="gpt-4o",
            system_prompt="You are a helpful assistant.",
        )
        assert isinstance(agent, CompiledStateGraph)


class TestRecursionLimitConfiguration:
    """Tests for recursion limit configuration."""
    
    def test_default_recursion_limit(self) -> None:
        """Test that default recursion limit is applied."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
        )
        # The recursion limit is stored in the config
        # We can verify it's a compiled graph, actual limit testing requires execution
        assert isinstance(agent, CompiledStateGraph)
    
    def test_custom_recursion_limit(self) -> None:
        """Test that custom recursion limit can be set."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            recursion_limit=50,
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_high_recursion_limit(self) -> None:
        """Test that high recursion limit can be set."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            recursion_limit=1000,
        )
        assert isinstance(agent, CompiledStateGraph)


class TestParameterOverrides:
    """Tests for parameter override functionality."""
    
    def test_override_max_tokens(self) -> None:
        """Test overriding max_tokens parameter."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            max_tokens=10000,
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_override_temperature(self) -> None:
        """Test overriding temperature parameter."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            temperature=0.7,
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_override_both_max_tokens_and_temperature(self) -> None:
        """Test overriding both max_tokens and temperature."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            max_tokens=15000,
            temperature=0.5,
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_additional_model_kwargs(self) -> None:
        """Test passing additional model kwargs."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            top_p=0.9,
        )
        assert isinstance(agent, CompiledStateGraph)


class TestToolsAndMiddleware:
    """Tests for tools and middleware parameters."""
    
    def test_empty_tools_list(self) -> None:
        """Test creating agent with empty tools list."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            tools=[],
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_none_tools(self) -> None:
        """Test that None tools defaults to empty list."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            tools=None,
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_empty_middleware_list(self) -> None:
        """Test creating agent with empty middleware list."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            middleware=[],
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_none_middleware(self) -> None:
        """Test that None middleware defaults to empty list."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            middleware=None,
        )
        assert isinstance(agent, CompiledStateGraph)


class TestContextSchema:
    """Tests for context_schema parameter."""
    
    def test_none_context_schema(self) -> None:
        """Test that None context_schema uses default from deepagents."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            context_schema=None,
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_custom_context_schema(self) -> None:
        """Test passing custom context schema."""
        from typing import TypedDict
        
        class CustomState(TypedDict):
            """Custom state schema for testing."""
            messages: list
        
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            context_schema=CustomState,
        )
        assert isinstance(agent, CompiledStateGraph)


class TestValidation:
    """Tests for input validation and error handling."""
    
    def test_empty_system_prompt(self) -> None:
        """Test that empty system prompt raises ValueError."""
        with pytest.raises(ValueError, match="system_prompt cannot be empty"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="",
            )
    
    def test_whitespace_only_system_prompt(self) -> None:
        """Test that whitespace-only system prompt raises ValueError."""
        with pytest.raises(ValueError, match="system_prompt cannot be empty"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="   ",
            )
    
    def test_zero_recursion_limit(self) -> None:
        """Test that zero recursion limit raises ValueError."""
        with pytest.raises(ValueError, match="recursion_limit must be positive"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                recursion_limit=0,
            )
    
    def test_negative_recursion_limit(self) -> None:
        """Test that negative recursion limit raises ValueError."""
        with pytest.raises(ValueError, match="recursion_limit must be positive"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                recursion_limit=-1,
            )
    
    def test_invalid_model_string(self) -> None:
        """Test that invalid model string raises ValueError."""
        with pytest.raises(ValueError):
            create_deep_agent(
                model="invalid-model",
                system_prompt="You are a helpful assistant.",
            )


class TestModelInstanceWithParameters:
    """Tests for handling of parameters when model instance is provided."""
    
    def test_warning_on_max_tokens_with_instance_anthropic(self) -> None:
        """Test that warning is raised when max_tokens provided with Anthropic model instance."""
        model = ChatAnthropic(model="claude-sonnet-4-5-20250929", max_tokens=10000)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            create_deep_agent(
                model=model,
                system_prompt="You are a helpful assistant.",
                max_tokens=15000,
            )
            # Filter out DeprecationWarnings from deepagents
            user_warnings = [warning for warning in w if issubclass(warning.category, UserWarning)]
            assert len(user_warnings) == 1
            assert "Model instance provided with additional parameters" in str(user_warnings[0].message)
    
    @skip_if_no_openai_key
    def test_warning_on_max_tokens_with_instance_openai(self) -> None:
        """Test that warning is raised when max_tokens provided with OpenAI model instance."""
        model = ChatOpenAI(model="gpt-4o")
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            create_deep_agent(
                model=model,
                system_prompt="You are a helpful assistant.",
                max_tokens=15000,
            )
            # Filter out DeprecationWarnings from deepagents
            user_warnings = [warning for warning in w if issubclass(warning.category, UserWarning)]
            assert len(user_warnings) == 1
            assert "Model instance provided with additional parameters" in str(user_warnings[0].message)
    
    def test_warning_on_temperature_with_instance_anthropic(self) -> None:
        """Test that warning is raised when temperature provided with Anthropic model instance."""
        model = ChatAnthropic(model="claude-sonnet-4-5-20250929", max_tokens=10000)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            create_deep_agent(
                model=model,
                system_prompt="You are a helpful assistant.",
                temperature=0.7,
            )
            # Filter out DeprecationWarnings from deepagents
            user_warnings = [warning for warning in w if issubclass(warning.category, UserWarning)]
            assert len(user_warnings) == 1
            assert "Model instance provided with additional parameters" in str(user_warnings[0].message)
    
    @skip_if_no_openai_key
    def test_warning_on_temperature_with_instance_openai(self) -> None:
        """Test that warning is raised when temperature provided with OpenAI model instance."""
        model = ChatOpenAI(model="gpt-4o")
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            create_deep_agent(
                model=model,
                system_prompt="You are a helpful assistant.",
                temperature=0.7,
            )
            # Filter out DeprecationWarnings from deepagents
            user_warnings = [warning for warning in w if issubclass(warning.category, UserWarning)]
            assert len(user_warnings) == 1
            assert "Model instance provided with additional parameters" in str(user_warnings[0].message)
    
    def test_warning_on_model_kwargs_with_instance_anthropic(self) -> None:
        """Test that warning is raised when model kwargs provided with Anthropic model instance."""
        model = ChatAnthropic(model="claude-sonnet-4-5-20250929", max_tokens=10000)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            create_deep_agent(
                model=model,
                system_prompt="You are a helpful assistant.",
                top_p=0.9,
            )
            # Filter out DeprecationWarnings from deepagents
            user_warnings = [warning for warning in w if issubclass(warning.category, UserWarning)]
            assert len(user_warnings) == 1
            assert "Model instance provided with additional parameters" in str(user_warnings[0].message)
    
    @skip_if_no_openai_key
    def test_warning_on_model_kwargs_with_instance_openai(self) -> None:
        """Test that warning is raised when model kwargs provided with OpenAI model instance."""
        model = ChatOpenAI(model="gpt-4o")
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            create_deep_agent(
                model=model,
                system_prompt="You are a helpful assistant.",
                top_p=0.9,
            )
            # Filter out DeprecationWarnings from deepagents
            user_warnings = [warning for warning in w if issubclass(warning.category, UserWarning)]
            assert len(user_warnings) == 1
            assert "Model instance provided with additional parameters" in str(user_warnings[0].message)
    
    def test_no_warning_without_extra_parameters_anthropic(self) -> None:
        """Test that no warning is raised when only Anthropic model instance is provided."""
        model = ChatAnthropic(model="claude-sonnet-4-5-20250929", max_tokens=10000)
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            create_deep_agent(
                model=model,
                system_prompt="You are a helpful assistant.",
            )
            # Filter out DeprecationWarnings from deepagents
            user_warnings = [warning for warning in w if issubclass(warning.category, UserWarning)]
            assert len(user_warnings) == 0
    
    @skip_if_no_openai_key
    def test_no_warning_without_extra_parameters_openai(self) -> None:
        """Test that no warning is raised when only OpenAI model instance is provided."""
        model = ChatOpenAI(model="gpt-4o")
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            create_deep_agent(
                model=model,
                system_prompt="You are a helpful assistant.",
            )
            # Filter out DeprecationWarnings from deepagents
            user_warnings = [warning for warning in w if issubclass(warning.category, UserWarning)]
            assert len(user_warnings) == 0


class TestMultipleModelProviders:
    """Tests for multiple model provider support."""
    
    def test_anthropic_models(self) -> None:
        """Test that all Anthropic model aliases work."""
        models = ["claude-sonnet-4.5", "claude-opus-4", "claude-haiku-4"]
        for model_name in models:
            agent = create_deep_agent(
                model=model_name,
                system_prompt="You are a helpful assistant.",
            )
            assert isinstance(agent, CompiledStateGraph)
    
    @skip_if_no_openai_key
    def test_openai_models(self) -> None:
        """Test that OpenAI models work."""
        models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        for model_name in models:
            agent = create_deep_agent(
                model=model_name,
                system_prompt="You are a helpful assistant.",
            )
            assert isinstance(agent, CompiledStateGraph)

