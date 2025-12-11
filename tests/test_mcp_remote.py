"""Tests for MCP integration in remote deployment scenarios.

These tests verify that the middleware loads tools correctly in both sync
and async contexts, regardless of deployment environment.

These tests use mocking and do not require actual MCP server connectivity.
"""

from unittest.mock import MagicMock, patch

import pytest

from graphton.core.middleware import McpToolsLoader


class TestRemoteDeploymentSimulation:
    """Test MCP middleware behavior in remote-like environments."""
    
    async def test_tools_loaded_at_creation(self) -> None:
        """Test that middleware loads tools at creation time (or defers in async context).
        
        Since templates are resolved by the caller (agent-fleet-worker), Graphton
        receives complete configs and loads tools immediately.
        """
        servers = {
            "test-server": {
                "transport": "streamable_http",
                "url": "https://test.example.com/",
                "headers": {
                    "Authorization": "Bearer resolved-token-123"
                }
            }
        }
        
        # Mock the async tool loading to avoid actual network calls
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            # Create a simple mock tool
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            # Create middleware in async context - should defer loading
            middleware = McpToolsLoader(
                servers=servers,
                tool_filter={"test-server": ["test_tool"]}
            )
            
            # Should have deferred loading (async context)
            assert middleware._deferred_loading is True
            assert middleware._tools_loaded is False
            
            # Call abefore_agent to trigger deferred loading
            result = await middleware.abefore_agent(state={}, runtime={})
            
            # Should return None (tools cached in middleware)
            assert result is None
            
            # Verify tools were loaded with correct config
            mock_load.assert_called_once()
            call_args = mock_load.call_args
            loaded_servers = call_args[0][0]
            # Check that resolved token is in config
            assert "resolved-token-123" in loaded_servers["test-server"]["headers"]["Authorization"]
    
    async def test_missing_config_doesnt_error(self) -> None:
        """Test that missing config doesn't cause errors (deferred loading)."""
        servers = {
            "test-server": {
                "transport": "streamable_http",
                "url": "https://test.example.com/",
                "headers": {
                    "Authorization": "Bearer token-123"
                }
            }
        }
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            middleware = McpToolsLoader(
                servers=servers,
                tool_filter={"test-server": ["test_tool"]}
            )
            
            # Config is None - should not raise error
            result = await middleware.abefore_agent(state={}, runtime=None)
            assert result is None
    
    async def test_missing_configurable_doesnt_error(self) -> None:
        """Test clear error when configurable dict is missing."""
        servers = {
            "test-server": {
                "transport": "streamable_http",
                "url": "https://test.example.com/",
                "headers": {
                    "Authorization": "Bearer {{USER_TOKEN}}"
                }
            }
        }
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            middleware = McpToolsLoader(
                servers=servers,
                tool_filter={"test-server": ["test_tool"]}
            )
            
            # Config without 'configurable' key should not cause error
            config = {}
            result = await middleware.abefore_agent(state={}, runtime=config)  # type: ignore[arg-type]
            assert result is None
    
    async def test_resolved_token_in_config(self) -> None:
        """Test that resolved token in config works correctly."""
        servers = {
            "test-server": {
                "transport": "streamable_http",
                "url": "https://test.example.com/",
                "headers": {
                    "Authorization": "Bearer token-123"  # Already resolved
                }
            }
        }
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            middleware = McpToolsLoader(
                servers=servers,
                tool_filter={"test-server": ["test_tool"]}
            )
            
            # Config with configurable (though not needed for resolved config)
            config = {"configurable": {"some_key": "some_value"}}
            
            result = await middleware.abefore_agent(state={}, runtime=config)  # type: ignore[arg-type]
            assert result is None
    
    def test_empty_token_works(self) -> None:
        """Test that empty token in resolved config works."""
        servers = {
            "test-server": {
                "transport": "streamable_http",
                "url": "https://test.example.com/",
                "headers": {
                    "Authorization": "Bearer "  # Empty but valid
                }
            }
        }
        
        # Should not raise at middleware level (MCP server handles validation)
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            McpToolsLoader(
                servers=servers,
                tool_filter={"test-server": ["test_tool"]}
            )
    
    async def test_idempotency_second_call_skips_loading(self) -> None:
        """Test that middleware is idempotent - second call skips loading."""
        servers = {
            "test-server": {
                "transport": "streamable_http",
                "url": "https://test.example.com/",
                "headers": {
                    "Authorization": "Bearer token-123"  # Already resolved
                }
            }
        }
        
        config = {}
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            middleware = McpToolsLoader(
                servers=servers,
                tool_filter={"test-server": ["test_tool"]}
            )
            
            # First call - tools already loaded during init (deferred in async context)
            await middleware.abefore_agent(state={}, runtime=config)
            assert mock_load.call_count == 1
            
            # Second call - should skip loading
            await middleware.abefore_agent(state={}, runtime=config)
            # Still only called once
            assert mock_load.call_count == 1
    
    async def test_tool_cache_access(self) -> None:
        """Test that tools can be retrieved from cache after loading."""
        servers = {
            "test-server": {
                "transport": "streamable_http",
                "url": "https://test.example.com/",
                "headers": {
                    "Authorization": "Bearer token-123"  # Already resolved
                }
            }
        }
        
        config = {}
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            middleware = McpToolsLoader(
                servers=servers,
                tool_filter={"test-server": ["test_tool"]}
            )
            
            # Load tools (deferred loading triggers)
            await middleware.abefore_agent(state={}, runtime=config)
            
            # Should be able to get tool from cache
            cached_tool = middleware.get_tool("test_tool")
            assert cached_tool is mock_tool
    
    async def test_get_tool_before_loading_fails(self) -> None:
        """Test that accessing cache before loading raises error."""
        servers = {
            "test-server": {
                "transport": "streamable_http",
                "url": "https://test.example.com/",
                "headers": {
                    "Authorization": "Bearer token-123"  # Already resolved
                }
            }
        }
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            middleware = McpToolsLoader(
                servers=servers,
                tool_filter={"test-server": ["test_tool"]}
            )
            
            # Try to get tool before abefore_agent triggers deferred loading
            # (Tools deferred in async context, not loaded yet)
            with pytest.raises(RuntimeError, match="not loaded yet"):
                middleware.get_tool("test_tool")
    
    async def test_get_nonexistent_tool_fails(self) -> None:
        """Test that accessing non-existent tool raises error."""
        servers = {
            "test-server": {
                "transport": "streamable_http",
                "url": "https://test.example.com/",
                "headers": {
                    "Authorization": "Bearer token-123"  # Already resolved
                }
            }
        }
        
        config = {}
        
        with patch('graphton.core.middleware.load_mcp_tools') as mock_load:
            mock_tool = MagicMock()
            mock_tool.name = "test_tool"
            mock_load.return_value = [mock_tool]
            
            middleware = McpToolsLoader(
                servers=servers,
                tool_filter={"test-server": ["test_tool"]}
            )
            
            await middleware.abefore_agent(state={}, runtime=config)
            
            # Try to get non-existent tool
            with pytest.raises(ValueError, match="not found in cache"):
                middleware.get_tool("nonexistent_tool")

