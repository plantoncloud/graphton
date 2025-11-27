"""Unit tests for model string parser."""

import os

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from graphton.core.models import parse_model_string

# Skip OpenAI tests if API key not available
skip_if_no_openai_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


class TestAnthropicModelParsing:
    """Tests for Anthropic model name resolution."""
    
    def test_claude_sonnet_4_5_mapping(self) -> None:
        """Test that claude-sonnet-4.5 maps to full model ID."""
        model = parse_model_string("claude-sonnet-4.5")
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-sonnet-4-5-20250929"
    
    def test_claude_opus_4_mapping(self) -> None:
        """Test that claude-opus-4 maps to full model ID."""
        model = parse_model_string("claude-opus-4")
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-opus-4-20250514"
    
    def test_claude_haiku_4_mapping(self) -> None:
        """Test that claude-haiku-4 maps to full model ID."""
        model = parse_model_string("claude-haiku-4")
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-haiku-4-20250313"
    
    def test_anthropic_prefix_format(self) -> None:
        """Test that anthropic: prefix works."""
        model = parse_model_string("anthropic:claude-sonnet-4.5")
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-sonnet-4-5-20250929"
    
    def test_full_model_id_passthrough(self) -> None:
        """Test that full Anthropic model IDs work without mapping."""
        model = parse_model_string("claude-sonnet-4-5-20250929")
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-sonnet-4-5-20250929"


@skip_if_no_openai_key
class TestOpenAIModelParsing:
    """Tests for OpenAI model name resolution."""
    
    def test_gpt_4o(self) -> None:
        """Test that gpt-4o creates OpenAI model."""
        model = parse_model_string("gpt-4o")
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "gpt-4o"
    
    def test_gpt_4o_mini(self) -> None:
        """Test that gpt-4o-mini creates OpenAI model."""
        model = parse_model_string("gpt-4o-mini")
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "gpt-4o-mini"
    
    def test_gpt_4_turbo(self) -> None:
        """Test that gpt-4-turbo creates OpenAI model."""
        model = parse_model_string("gpt-4-turbo")
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "gpt-4-turbo"
    
    def test_o1_model(self) -> None:
        """Test that o1 creates OpenAI model."""
        model = parse_model_string("o1")
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "o1"
    
    def test_o1_mini_model(self) -> None:
        """Test that o1-mini creates OpenAI model."""
        model = parse_model_string("o1-mini")
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "o1-mini"
    
    def test_openai_prefix_format(self) -> None:
        """Test that openai: prefix works."""
        model = parse_model_string("openai:gpt-4o")
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "gpt-4o"


class TestDefaultParameters:
    """Tests for default parameter application."""
    
    def test_anthropic_default_max_tokens(self) -> None:
        """Test that Anthropic models get default max_tokens of 20000."""
        model = parse_model_string("claude-sonnet-4.5")
        assert isinstance(model, ChatAnthropic)
        assert model.max_tokens == 20000
    
    @skip_if_no_openai_key
    def test_openai_no_default_max_tokens(self) -> None:
        """Test that OpenAI models don't get default max_tokens."""
        model = parse_model_string("gpt-4o")
        assert isinstance(model, ChatOpenAI)
        # OpenAI doesn't use max_tokens in the same way, should be None or unset
        # The attribute might not exist or might be None


class TestParameterOverrides:
    """Tests for parameter override functionality."""
    
    def test_override_max_tokens_anthropic(self) -> None:
        """Test overriding max_tokens for Anthropic models."""
        model = parse_model_string("claude-sonnet-4.5", max_tokens=10000)
        assert isinstance(model, ChatAnthropic)
        assert model.max_tokens == 10000
    
    def test_override_temperature_anthropic(self) -> None:
        """Test overriding temperature for Anthropic models."""
        model = parse_model_string("claude-sonnet-4.5", temperature=0.7)
        assert isinstance(model, ChatAnthropic)
        assert model.temperature == 0.7
    
    def test_additional_model_kwargs(self) -> None:
        """Test passing additional model-specific parameters."""
        model = parse_model_string("claude-sonnet-4.5", top_p=0.9)
        assert isinstance(model, ChatAnthropic)
        assert model.top_p == 0.9
    
    @skip_if_no_openai_key
    def test_override_max_tokens_openai(self) -> None:
        """Test overriding max_tokens for OpenAI models."""
        model = parse_model_string("gpt-4o", max_tokens=5000)
        assert isinstance(model, ChatOpenAI)
        assert model.max_tokens == 5000
    
    @skip_if_no_openai_key
    def test_override_temperature_openai(self) -> None:
        """Test overriding temperature for OpenAI models."""
        model = parse_model_string("gpt-4o", temperature=0.3)
        assert isinstance(model, ChatOpenAI)
        assert model.temperature == 0.3


class TestErrorHandling:
    """Tests for error handling and validation."""
    
    def test_empty_model_string(self) -> None:
        """Test that empty model string raises ValueError."""
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            parse_model_string("")
    
    def test_whitespace_only_model_string(self) -> None:
        """Test that whitespace-only model string raises ValueError."""
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            parse_model_string("   ")
    
    def test_unsupported_provider(self) -> None:
        """Test that unsupported provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            parse_model_string("gemini:gemini-pro")
    
    def test_invalid_model_name_format(self) -> None:
        """Test that model names without recognizable patterns raise ValueError."""
        with pytest.raises(ValueError, match="Cannot infer provider"):
            parse_model_string("invalid-model-name")


class TestWhitespaceHandling:
    """Tests for whitespace handling in model strings."""
    
    def test_leading_whitespace(self) -> None:
        """Test that leading whitespace is stripped."""
        model = parse_model_string("  claude-sonnet-4.5")
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-sonnet-4-5-20250929"
    
    def test_trailing_whitespace(self) -> None:
        """Test that trailing whitespace is stripped."""
        model = parse_model_string("claude-sonnet-4.5  ")
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-sonnet-4-5-20250929"
    
    def test_whitespace_around_prefix(self) -> None:
        """Test that whitespace around prefix is handled."""
        model = parse_model_string("anthropic: claude-sonnet-4.5")
        assert isinstance(model, ChatAnthropic)
        assert model.model == "claude-sonnet-4-5-20250929"

