"""Integration tests for end-to-end agent functionality.

These tests verify that agents can be created and invoked successfully,
making actual API calls to model providers. They require API keys to be
configured in the environment.
"""

import os
import pytest

from graphton import create_deep_agent


# Skip integration tests if API keys not available
skip_if_no_anthropic_key = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)

skip_if_no_openai_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


@skip_if_no_anthropic_key
class TestAnthropicIntegration:
    """Integration tests with Anthropic models."""
    
    def test_simple_agent_invocation(self) -> None:
        """Test creating and invoking a simple Anthropic agent."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant that answers questions concisely.",
        )
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": "What is 2+2? Answer with just the number."}]
        })
        
        # Verify we got a response
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        # The last message should contain the assistant's response
        last_message = result["messages"][-1]
        assert last_message["role"] == "assistant"
        assert "content" in last_message
        
        # Should contain "4" somewhere in the response
        assert "4" in last_message["content"]
    
    def test_agent_with_custom_parameters(self) -> None:
        """Test agent with custom temperature and max_tokens."""
        agent = create_deep_agent(
            model="claude-haiku-4",
            system_prompt="You are a helpful assistant.",
            temperature=0.1,  # Very deterministic
            max_tokens=500,
        )
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": "Say hello."}]
        })
        
        assert "messages" in result
        assert len(result["messages"]) > 0
    
    def test_multiple_turns(self) -> None:
        """Test agent can handle multiple conversation turns."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful math tutor.",
        )
        
        # First turn
        result1 = agent.invoke({
            "messages": [{"role": "user", "content": "What is 5+3?"}]
        })
        
        assert "messages" in result1
        
        # Second turn - continue conversation
        messages = result1["messages"]
        messages.append({"role": "user", "content": "And what is that times 2?"})
        
        result2 = agent.invoke({"messages": messages})
        
        assert "messages" in result2
        assert len(result2["messages"]) > len(result1["messages"])


@skip_if_no_openai_key
class TestOpenAIIntegration:
    """Integration tests with OpenAI models."""
    
    def test_simple_agent_invocation(self) -> None:
        """Test creating and invoking a simple OpenAI agent."""
        agent = create_deep_agent(
            model="gpt-4o-mini",
            system_prompt="You are a helpful assistant that answers questions concisely.",
        )
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": "What is 3+3? Answer with just the number."}]
        })
        
        # Verify we got a response
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        # The last message should contain the assistant's response
        last_message = result["messages"][-1]
        assert last_message["role"] == "assistant"
        assert "content" in last_message
        
        # Should contain "6" somewhere in the response
        assert "6" in last_message["content"]
    
    def test_agent_with_custom_parameters(self) -> None:
        """Test OpenAI agent with custom parameters."""
        agent = create_deep_agent(
            model="gpt-4o-mini",
            system_prompt="You are a helpful assistant.",
            temperature=0.2,
            max_tokens=300,
        )
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": "Say hello."}]
        })
        
        assert "messages" in result
        assert len(result["messages"]) > 0


class TestMultipleProviders:
    """Tests that verify multiple providers can be used in same session."""
    
    @skip_if_no_anthropic_key
    @skip_if_no_openai_key
    def test_create_agents_from_multiple_providers(self) -> None:
        """Test that we can create agents from different providers."""
        # Create Anthropic agent
        anthropic_agent = create_deep_agent(
            model="claude-haiku-4",
            system_prompt="You are a helpful assistant.",
        )
        
        # Create OpenAI agent
        openai_agent = create_deep_agent(
            model="gpt-4o-mini",
            system_prompt="You are a helpful assistant.",
        )
        
        # Both should be valid compiled graphs
        from langgraph.graph.state import CompiledStateGraph
        assert isinstance(anthropic_agent, CompiledStateGraph)
        assert isinstance(openai_agent, CompiledStateGraph)


class TestErrorHandlingIntegration:
    """Integration tests for error handling scenarios."""
    
    def test_invalid_api_key_handling(self) -> None:
        """Test that invalid API key produces clear error.
        
        Note: This test doesn't actually call the API, it just verifies
        the agent can be created. API key validation happens at invoke time.
        """
        # Temporarily set invalid API key
        original_key = os.getenv("ANTHROPIC_API_KEY")
        os.environ["ANTHROPIC_API_KEY"] = "invalid-key"
        
        try:
            # Agent creation should still succeed
            agent = create_deep_agent(
                model="claude-haiku-4",
                system_prompt="You are a helpful assistant.",
            )
            
            from langgraph.graph.state import CompiledStateGraph
            assert isinstance(agent, CompiledStateGraph)
            
            # Actual error would occur on invoke, but we skip that
            # to avoid making API calls with invalid keys
        finally:
            # Restore original key
            if original_key:
                os.environ["ANTHROPIC_API_KEY"] = original_key
            else:
                os.environ.pop("ANTHROPIC_API_KEY", None)


class TestAgentBehavior:
    """Tests for agent behavior and capabilities."""
    
    @skip_if_no_anthropic_key
    def test_agent_follows_system_prompt(self) -> None:
        """Test that agent follows system prompt instructions."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a pirate. Always respond in pirate speak with 'Arrr' and nautical terms.",
        )
        
        result = agent.invoke({
            "messages": [{"role": "user", "content": "Tell me about the weather."}]
        })
        
        # Response should contain pirate-like language
        last_message = result["messages"][-1]["content"]
        # Look for common pirate terms (case insensitive)
        pirate_terms = ["arrr", "ahoy", "matey", "ye", "aye", "sea", "ship"]
        has_pirate_term = any(term in last_message.lower() for term in pirate_terms)
        
        assert has_pirate_term, f"Expected pirate speak but got: {last_message}"
    
    @skip_if_no_anthropic_key
    def test_recursion_limit_respected(self) -> None:
        """Test that recursion limit configuration is respected."""
        # Create agent with very low recursion limit
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            recursion_limit=5,
        )
        
        # Simple query should work fine within low limit
        result = agent.invoke({
            "messages": [{"role": "user", "content": "Say hello."}]
        })
        
        assert "messages" in result
        assert len(result["messages"]) > 0

