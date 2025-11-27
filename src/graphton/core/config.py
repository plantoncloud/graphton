"""Configuration models for MCP integration.

This module provides Pydantic models for validating MCP server and tool
configurations. The format is compatible with Cursor's mcp.json while
being optimized for programmatic Python usage.
"""

from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator, model_validator


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
        """Validate transport type with helpful suggestions.
        
        Args:
            v: Transport protocol string
            
        Returns:
            Validated transport string
            
        Raises:
            ValueError: If transport is not supported

        """
        supported = ["streamable_http"]
        if v not in supported:
            raise ValueError(
                f"Unsupported transport: '{v}'. "
                f"Currently supported: {supported}. "
                f"For local MCP servers, use 'streamable_http' over localhost."
            )
        return v
    
    @field_validator("url")
    @classmethod
    def validate_url_scheme(cls, v: HttpUrl) -> HttpUrl:
        """Validate URL uses HTTPS in production.
        
        Args:
            v: URL to validate
            
        Returns:
            Validated URL
        
        """
        if v.scheme == "http" and "localhost" not in str(v) and "127.0.0.1" not in str(v):
            import warnings
            warnings.warn(
                f"MCP server URL uses insecure HTTP: {v}. "
                "Use HTTPS in production for secure authentication.",
                UserWarning,
                stacklevel=2
            )
        return v
    
    @field_validator("headers")
    @classmethod
    def validate_headers(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        """Validate headers don't conflict with auth.
        
        Args:
            v: Headers dictionary to validate
            
        Returns:
            Validated headers dictionary
        
        """
        if v and "Authorization" in v:
            import warnings
            warnings.warn(
                "Static 'Authorization' header will be overwritten by per-user token. "
                "Remove it from headers or set auth_from_context=False.",
                UserWarning,
                stacklevel=2
            )
        return v


class McpToolsConfig(BaseModel):
    """MCP tools configuration with enhanced validation.
    
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
    def validate_tools_structure(cls, v: dict[str, list[str]]) -> dict[str, list[str]]:
        """Validate tool configuration structure and tool names.
        
        Args:
            v: Tools dictionary to validate
            
        Returns:
            Validated tools dictionary
            
        Raises:
            ValueError: If configuration is invalid

        """
        if not v:
            raise ValueError(
                "At least one MCP server with tools is required. "
                "Example: {'planton-cloud': ['list_organizations', 'create_cloud_resource']}"
            )
        
        for server_name, tool_list in v.items():
            # Validate non-empty tool list
            if not tool_list:
                raise ValueError(
                    f"Server '{server_name}' has empty tool list. "
                    "Specify at least one tool to load."
                )
            
            # Validate tool names are strings
            for tool_name in tool_list:
                if not isinstance(tool_name, str):
                    raise ValueError(
                        f"Tool name must be string, got {type(tool_name).__name__}: {tool_name}"
                    )
                
                # Validate tool name format (lowercase snake_case recommended)
                if not tool_name:
                    raise ValueError(f"Empty tool name in server '{server_name}'")
                
                if not tool_name.replace("_", "").replace("-", "").isalnum():
                    raise ValueError(
                        f"Invalid tool name '{tool_name}' in server '{server_name}'. "
                        "Tool names should use alphanumeric characters, underscores, or hyphens."
                    )
            
            # Check for duplicate tool names within server
            if len(tool_list) != len(set(tool_list)):
                duplicates = [t for t in tool_list if tool_list.count(t) > 1]
                raise ValueError(
                    f"Duplicate tool names in server '{server_name}': {set(duplicates)}"
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


class AgentConfig(BaseModel):
    """Top-level configuration for agent creation.
    
    This model validates all parameters for create_deep_agent() and provides
    helpful error messages with suggestions for common mistakes.
    
    Attributes:
        model: Model name string or LangChain model instance
        system_prompt: System prompt defining agent behavior
        mcp_servers: Optional dict of MCP server configurations
        mcp_tools: Optional dict mapping server names to tool lists
        tools: Optional list of additional tools
        middleware: Optional list of middleware
        context_schema: Optional state schema for the agent
        recursion_limit: Maximum recursion depth (default: 100)
        max_tokens: Override default max_tokens for the model
        temperature: Override default temperature for the model
    
    """
    
    model: str | BaseChatModel
    system_prompt: str
    mcp_servers: dict[str, dict[str, Any]] | None = None
    mcp_tools: dict[str, list[str]] | None = None
    tools: Sequence[BaseTool] | None = None
    middleware: Sequence[Any] | None = None
    context_schema: type[Any] | None = None
    recursion_limit: int = 100
    max_tokens: int | None = None
    temperature: float | None = None
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt(cls, v: str) -> str:
        """Validate system prompt is non-empty and meaningful.
        
        Args:
            v: System prompt string
            
        Returns:
            Validated system prompt
            
        Raises:
            ValueError: If prompt is empty or too short
        
        """
        if not v or not v.strip():
            raise ValueError(
                "system_prompt cannot be empty. Provide a clear description "
                "of the agent's role and capabilities."
            )
        if len(v.strip()) < 10:
            raise ValueError(
                f"system_prompt is too short ({len(v)} chars). "
                "Provide at least 10 characters describing the agent's purpose."
            )
        return v
    
    @field_validator("recursion_limit")
    @classmethod
    def validate_recursion_limit(cls, v: int) -> int:
        """Validate recursion limit is reasonable.
        
        Args:
            v: Recursion limit value
            
        Returns:
            Validated recursion limit
            
        Raises:
            ValueError: If recursion limit is invalid
        
        """
        if v <= 0:
            raise ValueError(
                f"recursion_limit must be positive, got {v}. "
                "Recommended range: 10-200 depending on agent complexity."
            )
        if v > 500:
            import warnings
            warnings.warn(
                f"recursion_limit of {v} is very high. This may cause long execution times. "
                "Consider values between 10-200 for most agents.",
                UserWarning,
                stacklevel=2
            )
        return v
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float | None) -> float | None:
        """Validate temperature is in valid range.
        
        Args:
            v: Temperature value
            
        Returns:
            Validated temperature
            
        Raises:
            ValueError: If temperature is out of range
        
        """
        if v is not None and (v < 0.0 or v > 2.0):
            raise ValueError(
                f"temperature must be between 0.0 and 2.0, got {v}. "
                "Use 0.0-0.3 for deterministic output, 0.7-1.0 for creative output."
            )
        return v
    
    @model_validator(mode="after")
    def validate_mcp_configuration(self) -> "AgentConfig":
        """Validate MCP server and tools are provided together.
        
        Returns:
            Validated AgentConfig instance
            
        Raises:
            ValueError: If MCP configuration is invalid
        
        """
        has_servers = self.mcp_servers is not None and bool(self.mcp_servers)
        has_tools = self.mcp_tools is not None and bool(self.mcp_tools)
        
        if has_servers and not has_tools:
            raise ValueError(
                "mcp_servers provided but mcp_tools is missing. "
                "Specify which tools to load: mcp_tools={'server-name': ['tool1', 'tool2']}"
            )
        
        if has_tools and not has_servers:
            raise ValueError(
                "mcp_tools provided but mcp_servers is missing. "
                "Configure MCP servers: mcp_servers={'server-name': {'url': '...', 'transport': '...'}}"
            )
        
        # Validate server names match between mcp_servers and mcp_tools
        if has_servers and has_tools:
            # Type narrowing: at this point we know both are not None
            assert self.mcp_servers is not None
            assert self.mcp_tools is not None
            
            server_names = set(self.mcp_servers.keys())
            tool_server_names = set(self.mcp_tools.keys())
            
            missing_in_tools = server_names - tool_server_names
            missing_in_servers = tool_server_names - server_names
            
            if missing_in_tools:
                raise ValueError(
                    f"Server(s) configured but no tools specified: {missing_in_tools}. "
                    f"Add tools for these servers in mcp_tools."
                )
            
            if missing_in_servers:
                raise ValueError(
                    f"Tools specified for undefined server(s): {missing_in_servers}. "
                    f"Add server configurations in mcp_servers."
                )
        
        return self

