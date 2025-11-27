"""Configuration models for MCP integration.

This module provides Pydantic models for validating MCP server and tool
configurations. The format is compatible with Cursor's mcp.json while
being optimized for programmatic Python usage.
"""

from typing import Any

from pydantic import BaseModel, HttpUrl, field_validator


class McpServerConfig(BaseModel):
    """MCP server configuration (Cursor-compatible format).
    
    Attributes:
        transport: Transport protocol (only "streamable_http" supported currently)
        url: MCP server HTTP endpoint URL
        auth_from_context: Whether to extract auth token from runtime context
        headers: Optional static headers to include in requests
        
    Example:
        >>> config = McpServerConfig(
        ...     transport="streamable_http",
        ...     url="https://mcp.planton.ai/",
        ...     auth_from_context=True,
        ... )

    """
    
    transport: str = "streamable_http"
    url: HttpUrl
    auth_from_context: bool = True
    headers: dict[str, str] | None = None
    
    @field_validator("transport")
    @classmethod
    def validate_transport(cls, v: str) -> str:
        """Validate that only supported transports are used.
        
        Args:
            v: Transport protocol string
            
        Returns:
            Validated transport string
            
        Raises:
            ValueError: If transport is not supported

        """
        if v != "streamable_http":
            raise ValueError(
                f"Only 'streamable_http' transport is currently supported, got '{v}'"
            )
        return v


class McpToolsConfig(BaseModel):
    """MCP tools configuration - maps server names to tool lists.
    
    Attributes:
        tools: Dictionary mapping server names to lists of tool names to load
        
    Example:
        >>> config = McpToolsConfig(
        ...     tools={
        ...         "planton-cloud": ["list_organizations", "create_cloud_resource"]
        ...     }
        ... )

    """
    
    tools: dict[str, list[str]]
    
    @field_validator("tools")
    @classmethod
    def validate_non_empty(cls, v: dict[str, list[str]]) -> dict[str, list[str]]:
        """Validate that tool configuration is non-empty and well-formed.
        
        Args:
            v: Tools dictionary to validate
            
        Returns:
            Validated tools dictionary
            
        Raises:
            ValueError: If configuration is empty or has empty tool lists

        """
        if not v:
            raise ValueError("At least one MCP server with tools is required")
        
        for server_name, tool_list in v.items():
            if not tool_list:
                raise ValueError(
                    f"Server '{server_name}' has an empty tool list. "
                    "Specify at least one tool to load."
                )
        
        return v


def parse_mcp_server_config(config_dict: dict[str, Any]) -> McpServerConfig:
    """Parse and validate MCP server configuration dictionary.
    
    Args:
        config_dict: Dictionary containing server configuration
        
    Returns:
        Validated McpServerConfig instance
        
    Raises:
        ValueError: If configuration is invalid
        
    Example:
        >>> config = parse_mcp_server_config({
        ...     "transport": "streamable_http",
        ...     "url": "https://mcp.planton.ai/",
        ... })

    """
    return McpServerConfig(**config_dict)

