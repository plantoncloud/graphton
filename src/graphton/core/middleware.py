"""Middleware for loading MCP tools with per-user authentication.

This middleware runs before agent execution to:
1. Extract user token from config['configurable']['_user_token']
2. Set token in contextvars for tool wrapper access
3. Load MCP tools asynchronously with user authentication
4. Cache tools for tool wrapper access

Unlike graph-fleet's approach which relies on runtime.context (unavailable in
LangGraph Cloud remote deployments), this uses the config parameter which is
reliably available in both local and remote environments.
"""

import asyncio
import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from graphton.core.config import McpServerConfig
from graphton.core.context import clear_user_token, set_user_token
from graphton.core.mcp_manager import load_mcp_tools

logger = logging.getLogger(__name__)


class McpToolsLoader:
    """Middleware to load MCP tools with per-user authentication.
    
    This middleware:
    1. Extracts user token from config['configurable']['_user_token']
    2. Sets token in contextvars for tool wrapper access
    3. Loads MCP tools asynchronously with the user's token
    4. Caches tools for access by wrapper functions
    
    Works in both local and remote LangGraph deployments by using the config
    parameter instead of runtime.context.
    
    Example:
        >>> from graphton.core.middleware import McpToolsLoader
        >>> from graphton.core.config import McpServerConfig
        >>> 
        >>> servers = {
        ...     "planton-cloud": McpServerConfig(
        ...         transport="streamable_http",
        ...         url="https://mcp.planton.ai/"
        ...     )
        ... }
        >>> tool_filter = {"planton-cloud": ["list_organizations"]}
        >>> middleware = McpToolsLoader(servers, tool_filter)

    """
    
    def __init__(
        self,
        servers: dict[str, McpServerConfig],
        tool_filter: dict[str, list[str]],
    ) -> None:
        """Initialize MCP tools loader middleware.
        
        Args:
            servers: Dictionary of server_name -> McpServerConfig
            tool_filter: Dictionary of server_name -> list of tool names

        """
        self.servers = servers
        self.tool_filter = tool_filter
        self._tools_loaded = False
        self._tools_cache: dict[str, Any] = {}
    
    def before_agent(
        self,
        state: dict[str, Any],
        config: RunnableConfig,
    ) -> dict[str, Any] | None:
        """Load MCP tools before agent execution.
        
        This method is called by LangGraph before the agent processes a request.
        It extracts the user token from the config parameter (not runtime.context),
        sets it in contextvars, and loads MCP tools asynchronously.
        
        Args:
            state: Current agent state (unused but required by middleware protocol)
            config: Runnable config containing user token in configurable dict
            
        Returns:
            None (tools are cached in instance and token is in contextvars)
            
        Raises:
            ValueError: If config is missing or token not found
            RuntimeError: If MCP tools fail to load

        """
        # Check if already loaded for this instance (idempotency)
        if self._tools_loaded:
            logger.info("MCP tools already loaded for this instance, skipping")
            return None
        
        logger.info("Loading MCP tools with per-user authentication...")
        
        try:
            # Extract token from config parameter (works in both local and remote)
            # This is different from graph-fleet which tried to use runtime.context
            if not config or "configurable" not in config:
                raise ValueError(
                    "Config is missing 'configurable' dictionary. "
                    "Pass config={'configurable': {'_user_token': '...'}} when invoking agent."
                )
            
            configurable = config["configurable"]
            user_token = configurable.get("_user_token")
            
            if not user_token:
                raise ValueError(
                    "User token not found in config['configurable']['_user_token']. "
                    "Pass token when invoking: "
                    "agent.invoke(input, config={'configurable': {'_user_token': token}})"
                )
            
            logger.info("Successfully extracted user token from config")
            
            # Set token in context for tool wrappers to access
            set_user_token(user_token)
            
            # Load MCP tools asynchronously
            # We're in a sync middleware context but need async tool loading
            # Use asyncio.run_coroutine_threadsafe to bridge sync/async
            loop = asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(
                load_mcp_tools(self.servers, self.tool_filter, user_token),
                loop
            )
            
            # Wait for tools to load (with timeout)
            tools = future.result(timeout=30)
            
            if not tools:
                raise RuntimeError(
                    "No MCP tools were loaded. "
                    "Check MCP server accessibility and user permissions."
                )
            
            # Cache tools by name for wrapper access
            self._tools_cache = {tool.name: tool for tool in tools}
            self._tools_loaded = True
            
            logger.info(
                f"Successfully loaded {len(tools)} MCP tool(s): "
                f"{list(self._tools_cache.keys())}"
            )
            
            return None
            
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
        except TimeoutError as e:
            logger.error("Timeout loading MCP tools after 30 seconds")
            raise RuntimeError(
                "MCP tool loading timed out after 30 seconds. "
                "Check MCP server connectivity."
            ) from e
        except Exception as e:
            logger.error(f"Failed to load MCP tools: {e}", exc_info=True)
            raise RuntimeError(
                f"MCP tool loading failed: {e}. "
                "Check MCP server connectivity and user authentication."
            ) from e
    
    def after_agent(
        self,
        state: dict[str, Any],
        config: RunnableConfig,
    ) -> dict[str, Any] | None:
        """Cleanup after agent execution.
        
        Clears the user token from context to prevent leakage between executions.
        
        Args:
            state: Current agent state (unused)
            config: Runnable config (unused)
            
        Returns:
            None

        """
        # Clear token from context for security
        clear_user_token()
        logger.debug("Cleared user token from context")
        return None
    
    def get_tool(self, tool_name: str) -> Any:  # noqa: ANN401
        """Get a cached MCP tool by name.
        
        Called by tool wrappers to get the actual MCP tool instance.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            The MCP tool instance
            
        Raises:
            RuntimeError: If tools haven't been loaded yet
            ValueError: If tool name not found in cache
            
        Example:
            >>> tool = middleware.get_tool("list_organizations")

        """
        if not self._tools_loaded:
            raise RuntimeError(
                "MCP tools not loaded yet. "
                "Ensure middleware.before_agent() has been called."
            )
        
        if tool_name not in self._tools_cache:
            available = list(self._tools_cache.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found in cache. "
                f"Available tools: {available}"
            )
        
        return self._tools_cache[tool_name]

