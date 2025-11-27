"""Tests for MCP integration in remote deployment scenarios.

These tests simulate LangGraph Cloud remote deployment conditions and verify
that the middleware correctly extracts tokens from config parameters rather
than relying on runtime.context (which is not available remotely).

These tests use mocking and do not require actual MCP server connectivity.
"""

from unittest.mock import MagicMock, patch

import pytest

from graphton.core.config import McpServerConfig
from graphton.core.middleware import McpToolsLoader


class TestRemoteDeploymentSimulation:
    """Test MCP middleware behavior in remote-like environments."""
    
    def test_config_parameter_extraction(self) -> None:
        """Test that middleware extracts token from config parameter.
        
        This is critical for remote deployments where runtime.context
        is not available (as discovered in graph-fleet).
        """
        servers = {
            "test-server": McpServerConfig(
                transport="streamable_http",
                url="https://test.example.com/"
            )
        }
        
        middleware = McpToolsLoader(
            servers=servers,
            tool_filter={"test-server": ["test_tool"]}
        )
        
        # Mock config like LangGraph Cloud provides it
        config = {
            "configurable": {
                "_user_token": "test-token-123"
            }
        }
        
        # Mock the async tool loading to avoid actual network calls
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            # Create a simple mock tool
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            # Mock asyncio components - create an async coroutine that returns immediately
            with patch('graphton.core.middleware.asyncio.run_coroutine_threadsafe') as mock_run:
                mock_future = MagicMock()
                mock_future.result.return_value = [mock_tool]
                mock_run.return_value = mock_future
                
                # This should NOT raise "Runtime context not available"
                # It should extract token from config parameter instead
                try:
                    result = middleware.before_agent(state={}, config=config)
                    
                    # Should return None (tools cached in middleware)
                    assert result is None
                    
                    # Verify token was extracted and passed to load_mcp_tools
                    mock_load.assert_called_once()
                    call_args = mock_load.call_args
                    # Third argument should be the user token
                    assert call_args[0][2] == "test-token-123"
                    
                except ValueError as e:
                    if "Runtime context not available" in str(e):
                        pytest.fail(
                            "Middleware still relies on runtime.context, "
                            "which fails in remote deployments!"
                        )
                    raise
    
    def test_missing_config_raises_clear_error(self) -> None:
        """Test clear error when config is missing entirely."""
        servers = {
            "test-server": McpServerConfig(
                transport="streamable_http",
                url="https://test.example.com/"
            )
        }
        
        middleware = McpToolsLoader(
            servers=servers,
            tool_filter={"test-server": ["test_tool"]}
        )
        
        # Config is None
        with pytest.raises(ValueError, match="Config is missing 'configurable'"):
            middleware.before_agent(state={}, config=None)  # type: ignore[arg-type]
    
    def test_missing_configurable_raises_clear_error(self) -> None:
        """Test clear error when configurable dict is missing."""
        servers = {
            "test-server": McpServerConfig(
                transport="streamable_http",
                url="https://test.example.com/"
            )
        }
        
        middleware = McpToolsLoader(
            servers=servers,
            tool_filter={"test-server": ["test_tool"]}
        )
        
        # Config without 'configurable' key
        config = {}
        
        with pytest.raises(ValueError, match="Config is missing 'configurable'"):
            middleware.before_agent(state={}, config=config)  # type: ignore[arg-type]
    
    def test_missing_token_in_config(self) -> None:
        """Test clear error when token is missing from config."""
        servers = {
            "test-server": McpServerConfig(
                transport="streamable_http",
                url="https://test.example.com/"
            )
        }
        
        middleware = McpToolsLoader(
            servers=servers,
            tool_filter={"test-server": ["test_tool"]}
        )
        
        # Config with configurable but no token
        config = {"configurable": {}}
        
        with pytest.raises(ValueError, match="User token not found"):
            middleware.before_agent(state={}, config=config)  # type: ignore[arg-type]
    
    def test_empty_token_raises_error(self) -> None:
        """Test that empty token string is rejected."""
        servers = {
            "test-server": McpServerConfig(
                transport="streamable_http",
                url="https://test.example.com/"
            )
        }
        
        middleware = McpToolsLoader(
            servers=servers,
            tool_filter={"test-server": ["test_tool"]}
        )
        
        # Token is empty string
        config = {"configurable": {"_user_token": ""}}
        
        with pytest.raises(ValueError, match="User token not found"):
            middleware.before_agent(state={}, config=config)  # type: ignore[arg-type]
    
    def test_idempotency_second_call_skips_loading(self) -> None:
        """Test that middleware is idempotent - second call skips loading."""
        servers = {
            "test-server": McpServerConfig(
                transport="streamable_http",
                url="https://test.example.com/"
            )
        }
        
        middleware = McpToolsLoader(
            servers=servers,
            tool_filter={"test-server": ["test_tool"]}
        )
        
        config = {"configurable": {"_user_token": "token-123"}}
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            with patch('graphton.core.middleware.asyncio.run_coroutine_threadsafe') as mock_run:
                mock_future = MagicMock()
                mock_future.result.return_value = [mock_tool]
                mock_run.return_value = mock_future
                
                # First call - should load tools
                middleware.before_agent(state={}, config=config)
                assert mock_load.call_count == 1
                
                # Second call - should skip loading
                middleware.before_agent(state={}, config=config)
                # Still only called once
                assert mock_load.call_count == 1
    
    def test_tool_cache_access(self) -> None:
        """Test that tools can be retrieved from cache after loading."""
        servers = {
            "test-server": McpServerConfig(
                transport="streamable_http",
                url="https://test.example.com/"
            )
        }
        
        middleware = McpToolsLoader(
            servers=servers,
            tool_filter={"test-server": ["test_tool"]}
        )
        
        config = {"configurable": {"_user_token": "token-123"}}
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            with patch('graphton.core.middleware.asyncio.run_coroutine_threadsafe') as mock_run:
                mock_future = MagicMock()
                mock_future.result.return_value = [mock_tool]
                mock_run.return_value = mock_future
                
                # Load tools
                middleware.before_agent(state={}, config=config)
                
                # Should be able to get tool from cache
                cached_tool = middleware.get_tool("test_tool")
                assert cached_tool is mock_tool
    
    def test_get_tool_before_loading_fails(self) -> None:
        """Test that accessing cache before loading raises error."""
        servers = {
            "test-server": McpServerConfig(
                transport="streamable_http",
                url="https://test.example.com/"
            )
        }
        
        middleware = McpToolsLoader(
            servers=servers,
            tool_filter={"test-server": ["test_tool"]}
        )
        
        # Try to get tool before loading
        with pytest.raises(RuntimeError, match="not loaded yet"):
            middleware.get_tool("test_tool")
    
    def test_get_nonexistent_tool_fails(self) -> None:
        """Test that accessing non-existent tool raises error."""
        servers = {
            "test-server": McpServerConfig(
                transport="streamable_http",
                url="https://test.example.com/"
            )
        }
        
        middleware = McpToolsLoader(
            servers=servers,
            tool_filter={"test-server": ["test_tool"]}
        )
        
        config = {"configurable": {"_user_token": "token-123"}}
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            with patch('graphton.core.middleware.asyncio.run_coroutine_threadsafe') as mock_run:
                mock_future = MagicMock()
                mock_future.result.return_value = [mock_tool]
                mock_run.return_value = mock_future
                
                middleware.before_agent(state={}, config=config)
                
                # Try to get non-existent tool
                with pytest.raises(ValueError, match="not found in cache"):
                    middleware.get_tool("nonexistent_tool")

