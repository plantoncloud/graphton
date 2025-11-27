"""Comprehensive tests for configuration validation."""

import pytest
from pydantic import ValidationError

from graphton.core.config import (
    AgentConfig,
    McpServerConfig,
    McpToolsConfig,
)


class TestMcpServerConfig:
    """Test McpServerConfig validation."""
    
    def test_valid_server_config(self) -> None:
        """Test valid server configuration."""
        config = McpServerConfig(
            transport="streamable_http",
            url="https://mcp.planton.ai/",
        )
        assert config.transport == "streamable_http"
        assert str(config.url) == "https://mcp.planton.ai/"
    
    def test_invalid_transport(self) -> None:
        """Test error for unsupported transport."""
        with pytest.raises(ValidationError) as exc_info:
            McpServerConfig(
                transport="stdio",
                url="https://mcp.planton.ai/",
            )
        assert "Unsupported transport" in str(exc_info.value)
        assert "Currently supported: ['streamable_http']" in str(exc_info.value)
    
    def test_invalid_url(self) -> None:
        """Test error for invalid URL format."""
        with pytest.raises(ValidationError):
            McpServerConfig(
                transport="streamable_http",
                url="not-a-url",  # type: ignore[arg-type]
            )
    
    def test_http_warning_for_non_localhost(self) -> None:
        """Test warning for HTTP (non-HTTPS) URLs."""
        with pytest.warns(UserWarning, match="insecure HTTP"):
            McpServerConfig(
                transport="streamable_http",
                url="http://mcp.example.com/",
            )
    
    def test_http_localhost_no_warning(self) -> None:
        """Test no warning for localhost HTTP."""
        # Should not raise warning
        config = McpServerConfig(
            transport="streamable_http",
            url="http://localhost:8000/",
        )
        assert config is not None
    
    def test_http_127_no_warning(self) -> None:
        """Test no warning for 127.0.0.1 HTTP."""
        config = McpServerConfig(
            transport="streamable_http",
            url="http://127.0.0.1:8000/",
        )
        assert config is not None
    
    def test_authorization_header_warning(self) -> None:
        """Test warning for Authorization header conflict."""
        with pytest.warns(UserWarning, match="Authorization.*overwritten"):
            McpServerConfig(
                transport="streamable_http",
                url="https://mcp.planton.ai/",
                headers={"Authorization": "Bearer static-token"},
            )


class TestMcpToolsConfig:
    """Test McpToolsConfig validation."""
    
    def test_valid_tools_config(self) -> None:
        """Test valid tools configuration."""
        config = McpToolsConfig(
            tools={
                "planton-cloud": ["list_organizations", "create_cloud_resource"]
            }
        )
        assert "planton-cloud" in config.tools
    
    def test_empty_tools_dict(self) -> None:
        """Test error for empty tools dictionary."""
        with pytest.raises(ValidationError) as exc_info:
            McpToolsConfig(tools={})
        assert "At least one MCP server with tools is required" in str(exc_info.value)
    
    def test_empty_tool_list(self) -> None:
        """Test error for empty tool list."""
        with pytest.raises(ValidationError) as exc_info:
            McpToolsConfig(
                tools={"planton-cloud": []}
            )
        assert "empty tool list" in str(exc_info.value)
    
    def test_invalid_tool_name_type(self) -> None:
        """Test error for non-string tool name."""
        with pytest.raises(ValidationError) as exc_info:
            McpToolsConfig(
                tools={"planton-cloud": [123]}  # type: ignore[list-item]
            )
        # Pydantic validates type before custom validator
        assert "string" in str(exc_info.value).lower()
    
    def test_invalid_tool_name_characters(self) -> None:
        """Test error for invalid characters in tool name."""
        with pytest.raises(ValidationError) as exc_info:
            McpToolsConfig(
                tools={"planton-cloud": ["tool@invalid!"]}
            )
        assert "Invalid tool name" in str(exc_info.value)
    
    def test_duplicate_tool_names(self) -> None:
        """Test error for duplicate tool names."""
        with pytest.raises(ValidationError) as exc_info:
            McpToolsConfig(
                tools={"planton-cloud": ["tool1", "tool2", "tool1"]}
            )
        assert "Duplicate tool names" in str(exc_info.value)
    
    def test_empty_tool_name(self) -> None:
        """Test error for empty string as tool name."""
        with pytest.raises(ValidationError) as exc_info:
            McpToolsConfig(
                tools={"planton-cloud": [""]}
            )
        assert "Empty tool name" in str(exc_info.value)
    
    def test_valid_tool_names_with_underscores(self) -> None:
        """Test valid tool names with underscores."""
        config = McpToolsConfig(
            tools={"planton-cloud": ["list_organizations", "get_cloud_resource"]}
        )
        assert config is not None
    
    def test_valid_tool_names_with_hyphens(self) -> None:
        """Test valid tool names with hyphens."""
        config = McpToolsConfig(
            tools={"planton-cloud": ["list-organizations", "get-cloud-resource"]}
        )
        assert config is not None


class TestAgentConfig:
    """Test AgentConfig validation."""
    
    def test_valid_minimal_config(self) -> None:
        """Test valid minimal agent configuration."""
        config = AgentConfig(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
        )
        assert config.model == "claude-sonnet-4.5"
        assert config.recursion_limit == 100  # default
    
    def test_empty_system_prompt(self) -> None:
        """Test error for empty system prompt."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="",
            )
        assert "system_prompt cannot be empty" in str(exc_info.value)
    
    def test_whitespace_only_system_prompt(self) -> None:
        """Test error for whitespace-only system prompt."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="   ",
            )
        assert "system_prompt cannot be empty" in str(exc_info.value)
    
    def test_short_system_prompt(self) -> None:
        """Test error for too-short system prompt."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="Hi",
            )
        assert "too short" in str(exc_info.value)
        assert "at least 10 characters" in str(exc_info.value)
    
    def test_invalid_recursion_limit_zero(self) -> None:
        """Test error for recursion limit of zero."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                recursion_limit=0,
            )
        assert "must be positive" in str(exc_info.value)
    
    def test_invalid_recursion_limit_negative(self) -> None:
        """Test error for negative recursion limit."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                recursion_limit=-10,
            )
        assert "must be positive" in str(exc_info.value)
    
    def test_high_recursion_limit_warning(self) -> None:
        """Test warning for very high recursion limit."""
        with pytest.warns(UserWarning, match="very high"):
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                recursion_limit=600,
            )
    
    def test_valid_high_recursion_limit(self) -> None:
        """Test valid but high recursion limit (200)."""
        config = AgentConfig(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            recursion_limit=200,
        )
        assert config.recursion_limit == 200
    
    def test_invalid_temperature_negative(self) -> None:
        """Test error for negative temperature."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                temperature=-0.5,
            )
        assert "between 0.0 and 2.0" in str(exc_info.value)
    
    def test_invalid_temperature_too_high(self) -> None:
        """Test error for temperature > 2.0."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                temperature=3.0,
            )
        assert "between 0.0 and 2.0" in str(exc_info.value)
    
    def test_valid_temperature_zero(self) -> None:
        """Test valid temperature of 0.0."""
        config = AgentConfig(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            temperature=0.0,
        )
        assert config.temperature == 0.0
    
    def test_valid_temperature_two(self) -> None:
        """Test valid temperature of 2.0."""
        config = AgentConfig(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            temperature=2.0,
        )
        assert config.temperature == 2.0
    
    def test_mcp_servers_without_tools(self) -> None:
        """Test error when mcp_servers provided without mcp_tools."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                mcp_servers={"planton-cloud": {"url": "https://mcp.planton.ai/"}},
                mcp_tools=None,
            )
        assert "mcp_tools is missing" in str(exc_info.value)
    
    def test_mcp_tools_without_servers(self) -> None:
        """Test error when mcp_tools provided without mcp_servers."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                mcp_servers=None,
                mcp_tools={"planton-cloud": ["tool1"]},
            )
        assert "mcp_servers is missing" in str(exc_info.value)
    
    def test_mcp_server_name_mismatch_missing_tools(self) -> None:
        """Test error when server configured but no tools specified."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                mcp_servers={"server-a": {"url": "https://a.example.com/"}},
                mcp_tools={"server-b": ["tool1"]},
            )
        error_str = str(exc_info.value)
        assert "server-a" in error_str or "no tools specified" in error_str.lower()
    
    def test_mcp_server_name_mismatch_undefined_server(self) -> None:
        """Test error when tools specified for undefined server."""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                mcp_servers={"server-a": {"url": "https://a.example.com/"}},
                mcp_tools={"server-b": ["tool1"]},
            )
        error_str = str(exc_info.value)
        assert "server-b" in error_str or "undefined server" in error_str.lower()
    
    def test_valid_mcp_configuration(self) -> None:
        """Test valid MCP server and tools configuration."""
        config = AgentConfig(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            mcp_servers={
                "planton-cloud": {
                    "url": "https://mcp.planton.ai/",
                    "transport": "streamable_http",
                }
            },
            mcp_tools={
                "planton-cloud": ["list_organizations", "create_cloud_resource"]
            },
        )
        assert config is not None
        assert config.mcp_servers is not None
        assert "planton-cloud" in config.mcp_servers


class TestIntegrationWithCreateDeepAgent:
    """Test validation integration with create_deep_agent function."""
    
    def test_create_agent_with_invalid_config(self) -> None:
        """Test that invalid config is caught by create_deep_agent."""
        from graphton import create_deep_agent
        
        with pytest.raises(ValueError, match="Configuration validation failed"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="",  # Invalid: empty
            )
    
    def test_create_agent_with_valid_config(self) -> None:
        """Test that valid config passes validation."""
        from graphton import create_deep_agent
        
        # Should not raise
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
        )
        assert agent is not None
    
    def test_create_agent_with_invalid_temperature(self) -> None:
        """Test that invalid temperature is caught."""
        from graphton import create_deep_agent
        
        with pytest.raises(ValueError, match="Configuration validation failed"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                temperature=5.0,  # Invalid: > 2.0
            )
    
    def test_create_agent_with_invalid_recursion_limit(self) -> None:
        """Test that invalid recursion limit is caught."""
        from graphton import create_deep_agent
        
        with pytest.raises(ValueError, match="Configuration validation failed"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                recursion_limit=0,  # Invalid: must be positive
            )

