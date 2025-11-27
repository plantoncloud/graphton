"""Integration tests for MCP tool loading with local invocation.

These tests verify that MCP tools can be loaded and invoked correctly
in a local execution environment (not LangGraph Cloud).

Tests require PLANTON_API_KEY environment variable to be set.
"""

import os

import pytest

from graphton import create_deep_agent


@pytest.mark.skipif(
    not os.getenv("PLANTON_API_KEY"),
    reason="Requires PLANTON_API_KEY environment variable for MCP testing"
)
class TestMcpIntegrationLocal:
    """Test MCP integration with local agent invocation."""
    
    def test_create_agent_with_mcp_tools(self) -> None:
        """Test creating an agent with MCP tool configuration."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            mcp_servers={
                "planton-cloud": {
                    "transport": "streamable_http",
                    "url": "https://mcp.planton.ai/",
                }
            },
            mcp_tools={
                "planton-cloud": ["list_organizations"]
            }
        )
        
        assert agent is not None
        # Agent should be a compiled graph
        assert hasattr(agent, "invoke")
    
    def test_invoke_agent_with_mcp_tools(self) -> None:
        """Test invoking an agent with MCP tools locally."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a Planton Cloud assistant. List the organizations.",
            mcp_servers={
                "planton-cloud": {
                    "transport": "streamable_http",
                    "url": "https://mcp.planton.ai/",
                }
            },
            mcp_tools={
                "planton-cloud": ["list_organizations"]
            }
        )
        
        # Get token from environment
        user_token = os.getenv("PLANTON_API_KEY")
        assert user_token, "PLANTON_API_KEY must be set"
        
        # Invoke with token in config
        result = agent.invoke(
            {"messages": [{"role": "user", "content": "List my organizations"}]},
            config={
                "configurable": {
                    "_user_token": user_token
                }
            }
        )
        
        # Verify result structure
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        # The agent should have used the tool to get organizations
        # and responded with information about them
        last_message = result["messages"][-1]
        assert "content" in last_message
    
    def test_invoke_without_token_fails(self) -> None:
        """Test that invoking without a token raises appropriate error."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            mcp_servers={
                "planton-cloud": {
                    "transport": "streamable_http",
                    "url": "https://mcp.planton.ai/",
                }
            },
            mcp_tools={
                "planton-cloud": ["list_organizations"]
            }
        )
        
        # Invoke without token - should fail
        with pytest.raises(ValueError, match="User token not found"):
            agent.invoke(
                {"messages": [{"role": "user", "content": "List organizations"}]},
                config={"configurable": {}}  # No token
            )
    
    def test_multiple_mcp_tools(self) -> None:
        """Test agent with multiple MCP tools from one server."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a Planton Cloud assistant.",
            mcp_servers={
                "planton-cloud": {
                    "transport": "streamable_http",
                    "url": "https://mcp.planton.ai/",
                }
            },
            mcp_tools={
                "planton-cloud": [
                    "list_organizations",
                    "list_cloud_resource_kinds",
                ]
            }
        )
        
        user_token = os.getenv("PLANTON_API_KEY")
        assert user_token
        
        # Invoke - agent should be able to use both tools
        result = agent.invoke(
            {
                "messages": [
                    {"role": "user", "content": "List organizations and cloud resource kinds"}
                ]
            },
            config={"configurable": {"_user_token": user_token}}
        )
        
        assert result is not None
        assert "messages" in result


class TestMcpConfigurationValidation:
    """Test MCP configuration validation during agent creation."""
    
    def test_mcp_servers_without_tools_fails(self) -> None:
        """Test that providing mcp_servers without mcp_tools fails."""
        with pytest.raises(ValueError, match="mcp_tools is missing"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a test assistant.",
                mcp_servers={
                    "planton-cloud": {
                        "transport": "streamable_http",
                        "url": "https://mcp.planton.ai/",
                    }
                },
                mcp_tools=None  # Missing
            )
    
    def test_mcp_tools_without_servers_fails(self) -> None:
        """Test that providing mcp_tools without mcp_servers fails."""
        with pytest.raises(ValueError, match="mcp_servers is missing"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a test assistant.",
                mcp_servers=None,  # Missing
                mcp_tools={
                    "planton-cloud": ["list_organizations"]
                }
            )
    
    def test_invalid_transport_fails(self) -> None:
        """Test that invalid transport type is rejected."""
        with pytest.raises(ValueError, match="Unsupported transport"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a test assistant.",
                mcp_servers={
                    "test": {
                        "transport": "stdio",  # Not supported yet
                        "url": "https://test.example.com/",
                    }
                },
                mcp_tools={
                    "test": ["test_tool"]
                }
            )
    
    def test_invalid_url_fails(self) -> None:
        """Test that invalid URL is rejected."""
        with pytest.raises(ValueError):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a test assistant.",
                mcp_servers={
                    "test": {
                        "transport": "streamable_http",
                        "url": "not-a-valid-url",  # Invalid
                    }
                },
                mcp_tools={
                    "test": ["test_tool"]
                }
            )

