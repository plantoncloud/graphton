"""MCP client manager for loading tools with authentication.

This module handles MCP client initialization, tool loading, and filtering.
It creates MCP clients with dynamic Authorization headers containing user tokens.
"""

import logging
from collections.abc import Sequence

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient  # type: ignore[import-untyped]

from graphton.core.config import McpServerConfig

logger = logging.getLogger(__name__)


async def load_mcp_tools(
    servers: dict[str, McpServerConfig],
    tool_filter: dict[str, list[str]],
    user_token: str,
) -> Sequence[BaseTool]:
    """Load MCP tools from configured servers with user authentication.
    
    This function:
    1. Builds MCP client configuration with Authorization headers
    2. Initializes MultiServerMCPClient for all configured servers
    3. Loads all available tools from the servers
    4. Filters tools based on the provided tool_filter
    5. Returns the filtered list of LangChain-compatible tools
    
    Args:
        servers: Dictionary mapping server names to McpServerConfig instances
        tool_filter: Dictionary mapping server names to lists of tool names to load
        user_token: User's JWT token or API key for authentication
        
    Returns:
        Sequence of LangChain BaseTool instances ready for use
        
    Raises:
        ValueError: If user_token is empty or no tools match the filter
        RuntimeError: If MCP client fails to connect or load tools
        
    Example:
        >>> servers = {
        ...     "planton-cloud": McpServerConfig(
        ...         transport="streamable_http",
        ...         url="https://mcp.planton.ai/"
        ...     )
        ... }
        >>> tool_filter = {
        ...     "planton-cloud": ["list_organizations", "create_cloud_resource"]
        ... }
        >>> tools = await load_mcp_tools(servers, tool_filter, "token123")
        >>> len(tools)
        2

    """
    # Validate token
    if not user_token or not user_token.strip():
        raise ValueError(
            "user_token is required for MCP authentication. "
            "Token cannot be None or empty."
        )
    
    # Build client config with dynamic Authorization headers
    client_config: dict[str, dict[str, str | dict[str, str]]] = {}
    
    for server_name, server_cfg in servers.items():
        # Start with base configuration
        config: dict[str, str | dict[str, str]] = {
            "transport": server_cfg.transport,
            "url": str(server_cfg.url),
        }
        
        # Add Authorization header with user token
        headers: dict[str, str] = {
            "Authorization": f"Bearer {user_token}",
        }
        
        # Merge with any static headers from config
        if server_cfg.headers:
            headers.update(server_cfg.headers)
        
        config["headers"] = headers
        client_config[server_name] = config
    
    logger.info(
        f"Connecting to {len(servers)} MCP server(s): {list(servers.keys())}"
    )
    
    try:
        # Initialize MCP client with dynamic configuration
        mcp_client = MultiServerMCPClient(client_config)
        
        # Get all tools from all servers
        all_tools = await mcp_client.get_tools()
        
        logger.info(
            f"Retrieved {len(all_tools)} total tool(s) from MCP server(s): "
            f"{[t.name for t in all_tools]}"
        )
        
        # Filter tools based on configuration
        # Build a set of all requested tool names for fast lookup
        requested_tools: set[str] = set()
        for tool_names in tool_filter.values():
            requested_tools.update(tool_names)
        
        # Filter tools
        filtered_tools = [
            tool for tool in all_tools
            if tool.name in requested_tools
        ]
        
        # Validate we found tools
        if not filtered_tools:
            available_names = [t.name for t in all_tools]
            raise ValueError(
                f"No tools found matching filter. "
                f"Available tools: {available_names}, "
                f"Requested tools: {sorted(requested_tools)}"
            )
        
        # Log what we're returning
        loaded_names = [t.name for t in filtered_tools]
        logger.info(
            f"Loaded {len(filtered_tools)} MCP tool(s): {loaded_names}"
        )
        
        # Check if any requested tools were not found
        found_names = set(loaded_names)
        missing_tools = requested_tools - found_names
        if missing_tools:
            logger.warning(
                f"Some requested tools were not found: {sorted(missing_tools)}"
            )
        
        return filtered_tools
        
    except ValueError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        logger.error(f"Failed to load MCP tools: {e}", exc_info=True)
        raise RuntimeError(
            f"MCP tool loading failed: {e}. "
            "Check MCP server connectivity and authentication."
        ) from e

