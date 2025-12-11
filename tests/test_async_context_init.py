"""Tests for middleware initialization in async contexts.

This module tests the middleware's ability to handle initialization when
create_deep_agent() is called from an async context (like Temporal activities)
where an event loop is already running.
"""

import asyncio

from graphton.core.middleware import McpToolsLoader


class TestAsyncContextInitialization:
    """Tests for middleware initialization in async contexts."""
    
    async def test_static_config_in_async_context(self) -> None:
        """Test that config defers loading when initialized in async context.
        
        This simulates what happens when create_deep_agent() is called from
        within a Temporal activity or other async context where an event loop
        is already running.
        """
        servers = {
            "test-server": {
                "transport": "http",
                "url": "https://api.example.com",
                "headers": {"X-API-Key": "hardcoded"}
            }
        }
        tool_filter = {"test-server": ["tool1"]}
        
        # Initialize middleware in async context (event loop is running)
        # This should NOT raise "RuntimeError: Cannot run the event loop while another loop is running"
        # Instead, it should defer loading
        middleware = McpToolsLoader(servers, tool_filter)
        
        # Verify loading was deferred (not loaded at init time)
        assert middleware._deferred_loading is True
        assert middleware._tools_loaded is False
        
        # Note: We can't actually test the deferred loading here without a real MCP server
        # The actual loading will fail, but we've verified the mechanism works
    
    async def test_resolved_config_in_async_context(self) -> None:
        """Test that resolved config works normally in async context.
        
        All configs (with auth already resolved) defer loading in async context.
        """
        servers = {
            "planton-cloud": {
                "transport": "streamable_http",
                "url": "https://mcp.planton.ai/",
                "headers": {
                    "Authorization": "Bearer pck_abc123..."
                }
            }
        }
        tool_filter = {"planton-cloud": ["list_organizations"]}
        
        # Initialize middleware in async context
        middleware = McpToolsLoader(servers, tool_filter)
        
        # Should defer loading in async context
        assert middleware._tools_loaded is False
        assert middleware._deferred_loading is True
    
    def test_static_config_in_sync_context(self) -> None:
        """Test that static config attempts immediate loading in sync context.
        
        When initialized outside an async context, static configs should try
        to load tools immediately (though it will fail without a real server).
        """
        # Run this in a separate thread to ensure no event loop is running
        import threading
        
        result = {}
        
        def init_middleware() -> None:
            servers = {
                "test-server": {
                    "transport": "http",
                    "url": "https://nonexistent.example.com",
                    "headers": {"X-API-Key": "hardcoded"}
                }
            }
            tool_filter = {"test-server": ["tool1"]}
            
            try:
                McpToolsLoader(servers, tool_filter)
                result["error"] = None
            except RuntimeError as e:
                result["error"] = str(e)
        
        thread = threading.Thread(target=init_middleware)
        thread.start()
        thread.join()
        
        # Should fail to load tools (no real server), but with a different error
        # The important thing is it tried to load (not deferred)
        assert result["error"] is not None
        assert "MCP tool loading failed" in result["error"]


class TestDeferredLoadingBehavior:
    """Tests for deferred loading behavior in async contexts."""
    
    async def test_deferred_flag_set_in_async_context(self) -> None:
        """Test that _deferred_loading flag is set when initialized in async context."""
        servers = {
            "static-server": {
                "url": "https://api.example.com",
                "headers": {"X-API-Key": "hardcoded"}
            }
        }
        tool_filter = {"static-server": ["tool1"]}
        
        # Create in async context
        middleware = McpToolsLoader(servers, tool_filter)
        
        # Verify deferred loading flag is set
        assert middleware._deferred_loading is True
        assert middleware._tools_loaded is False
    
    async def test_deferred_flag_set_in_all_async_contexts(self) -> None:
        """Test that _deferred_loading flag is set for all configs in async context."""
        servers = {
            "server": {
                "url": "https://api.example.com",
                "headers": {"Authorization": "Bearer token123"}
            }
        }
        tool_filter = {"server": ["tool1"]}
        
        # Create in async context
        middleware = McpToolsLoader(servers, tool_filter)
        
        # All configs defer loading in async context
        assert middleware._deferred_loading is True
        assert middleware._tools_loaded is False


class TestEventLoopDetection:
    """Tests for event loop detection logic."""
    
    async def test_detects_running_event_loop(self) -> None:
        """Test that middleware detects when event loop is already running."""
        servers = {
            "test-server": {
                "url": "https://api.example.com",
                "headers": {"X-API-Key": "hardcoded"}
            }
        }
        tool_filter = {"test-server": ["tool1"]}
        
        # Verify we're in an async context
        loop = asyncio.get_event_loop()
        assert loop.is_running()
        
        # Create middleware - should detect the running loop
        middleware = McpToolsLoader(servers, tool_filter)
        
        # Should have deferred loading
        assert middleware._deferred_loading is True
    
    def test_detects_no_event_loop(self) -> None:
        """Test behavior when no event loop is running."""
        import threading
        
        result = {}
        
        def check_loop() -> None:
            try:
                # Try to get event loop when none exists
                loop = asyncio.get_event_loop()
                result["has_loop"] = True
                result["is_running"] = loop.is_running() if loop else False
            except RuntimeError:
                result["has_loop"] = False
                result["is_running"] = False
        
        thread = threading.Thread(target=check_loop)
        thread.start()
        thread.join()
        
        # In a fresh thread, there should be no running event loop
        assert result["is_running"] is False


class TestRealWorldAsyncScenarios:
    """Tests simulating real-world async scenarios."""
    
    async def test_temporal_activity_simulation(self) -> None:
        """Simulate what happens in a Temporal activity (async context).
        
        This is the actual scenario that was failing in production:
        - Temporal activity is async (event loop running)
        - Activity calls create_deep_agent()
        - Agent creation instantiates McpToolsLoader
        - Static configs should defer loading instead of failing
        """
        # Simulate MCP configuration resolved from backend
        mcp_servers = {
            "planton-cloud": {
                "transport": "streamable_http",
                "url": "https://mcp.planton.ai/",
                "headers": {
                    "Authorization": "Bearer actual-token-here"
                }
            }
        }
        
        mcp_tools = {
            "planton-cloud": [
                "list_organizations",
                "search_cloud_resources",
                "get_cloud_resource_by_id"
            ]
        }
        
        # This is what happens in execute_graphton activity
        # Should not raise "Cannot run the event loop while another loop is running"
        middleware = McpToolsLoader(mcp_servers, mcp_tools)
        
        # Verify loading was deferred
        assert middleware._deferred_loading is True
        assert middleware._tools_loaded is False
        
        # In production, abefore_agent() would be called next and would
        # perform the deferred loading, but we can't test that without
        # a real MCP server
    
    async def test_multiple_agent_creations_in_async_context(self) -> None:
        """Test creating multiple agents in the same async context."""
        servers1 = {
            "server1": {
                "url": "https://api1.example.com",
                "headers": {"X-API-Key": "key1"}
            }
        }
        
        servers2 = {
            "server2": {
                "url": "https://api2.example.com",
                "headers": {"X-API-Key": "key2"}
            }
        }
        
        tool_filter1 = {"server1": ["tool1"]}
        tool_filter2 = {"server2": ["tool2"]}
        
        # Create multiple middlewares in the same async context
        middleware1 = McpToolsLoader(servers1, tool_filter1)
        middleware2 = McpToolsLoader(servers2, tool_filter2)
        
        # Both should defer loading
        assert middleware1._deferred_loading is True
        assert middleware2._deferred_loading is True
        
        assert middleware1._tools_loaded is False
        assert middleware2._tools_loaded is False

