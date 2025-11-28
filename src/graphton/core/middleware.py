"""Middleware for loading MCP tools with universal authentication support.

This middleware supports both static and dynamic MCP server configurations:

**Static configs** (no template variables):
- Tools are loaded once at agent creation time
- No runtime overhead
- Ideal for servers with hardcoded credentials or no authentication

**Dynamic configs** (with {{VAR_NAME}} templates):
- Templates are substituted at invocation time using config['configurable']
- Tools are loaded per-request with user-specific credentials
- Ideal for multi-tenant systems or user-specific authentication

The middleware automatically detects which mode to use based on the presence
of template variables in the server configurations.
"""

import asyncio
import logging
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langgraph.runtime import Runtime

from graphton.core.mcp_manager import load_mcp_tools
from graphton.core.template import extract_template_vars, substitute_templates

logger = logging.getLogger(__name__)


class McpToolsLoader(AgentMiddleware):
    """Middleware to load MCP tools with universal authentication support.
    
    This middleware automatically detects static vs dynamic configurations:
    
    - **Static mode**: No template variables ({{VAR}}) found in configs
      - Tools loaded once at initialization
      - Zero runtime overhead
      - Use for hardcoded credentials or public servers
    
    - **Dynamic mode**: Template variables found in configs
      - Templates substituted from config['configurable'] at invocation
      - Tools loaded per-request with user-specific auth
      - Use for multi-tenant or user-specific authentication
    
    Example (Dynamic - Planton Cloud):
        >>> servers = {
        ...     "planton-cloud": {
        ...         "transport": "streamable_http",
        ...         "url": "https://mcp.planton.ai/",
        ...         "headers": {
        ...             "Authorization": "Bearer {{USER_TOKEN}}"
        ...         }
        ...     }
        ... }
        >>> tool_filter = {"planton-cloud": ["list_organizations"]}
        >>> middleware = McpToolsLoader(servers, tool_filter)
        >>> middleware.is_dynamic
        True
        >>> # Later, at invocation:
        >>> # agent.invoke(input, config={'configurable': {'USER_TOKEN': 'token123'}})
    
    Example (Static - Public server):
        >>> servers = {
        ...     "public-api": {
        ...         "transport": "http",
        ...         "url": "https://api.example.com/mcp",
        ...         "headers": {
        ...             "X-API-Key": "hardcoded-key-123"
        ...         }
        ...     }
        ... }
        >>> tool_filter = {"public-api": ["search", "fetch"]}
        >>> middleware = McpToolsLoader(servers, tool_filter)
        >>> middleware.is_dynamic
        False
        >>> # Tools already loaded - no runtime overhead
    """
    
    def __init__(
        self,
        servers: dict[str, dict[str, Any]],
        tool_filter: dict[str, list[str]],
    ) -> None:
        """Initialize MCP tools loader middleware.
        
        Args:
            servers: Dictionary of server_name -> raw MCP server config.
                Configs can contain template variables like {{VAR_NAME}}.
            tool_filter: Dictionary of server_name -> list of tool names to load.

        """
        self.servers = servers
        self.tool_filter = tool_filter
        
        # Auto-detect static vs dynamic based on template variables
        self.template_vars = extract_template_vars(servers)
        self.is_dynamic = bool(self.template_vars)
        
        # Track whether tools have been loaded
        self._tools_loaded = False
        self._tools_cache: dict[str, Any] = {}
        
        # If static config (no templates), load tools immediately
        if not self.is_dynamic:
            logger.info(
                "Static MCP configuration detected (no template variables). "
                "Loading tools at agent creation time..."
            )
            self._load_static_tools()
        else:
            logger.info(
                f"Dynamic MCP configuration detected (template variables: {sorted(self.template_vars)}). "
                "Tools will be loaded at invocation time with user-provided values."
            )
    
    def _load_static_tools(self) -> None:
        """Load tools for static configurations (synchronous wrapper).
        
        Called at initialization for static configs (no template variables).
        """
        try:
            # Get or create event loop for async tool loading
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, we can't use run_until_complete
                    # This shouldn't happen at initialization, but handle gracefully
                    raise RuntimeError("Event loop already running during static tool loading")
            except RuntimeError:
                # No event loop in current thread, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Load tools synchronously
            tools = loop.run_until_complete(
                load_mcp_tools(self.servers, self.tool_filter)
            )
            
            if not tools:
                raise RuntimeError(
                    "No MCP tools were loaded from static configuration. "
                    "Check server accessibility and tool filter."
                )
            
            # Cache tools by name
            self._tools_cache = {tool.name: tool for tool in tools}
            self._tools_loaded = True
            
            logger.info(
                f"Successfully loaded {len(tools)} static MCP tool(s) at creation time: "
                f"{list(self._tools_cache.keys())}"
            )
            
        except Exception as e:
            logger.error(f"Failed to load static MCP tools: {e}", exc_info=True)
            raise RuntimeError(
                f"Static MCP tool loading failed during initialization: {e}. "
                "Check MCP server connectivity and configuration."
            ) from e
    
    async def abefore_agent(
        self,
        state: AgentState[Any],
        runtime: Runtime[None] | dict[str, Any],
    ) -> dict[str, Any] | None:
        """Load MCP tools before agent execution (async).
        
        Behavior depends on configuration mode:
        
        - **Static mode**: Tools already loaded at initialization, returns immediately
        - **Dynamic mode**: Substitutes templates from runtime context and loads tools
        
        This is the async version that directly awaits MCP tool loading, avoiding
        the event loop deadlock that occurred with run_coroutine_threadsafe.
        
        Args:
            state: Current agent state (unused but required by middleware protocol)
            runtime: Runtime object (production) or dict (tests) containing template values
            
        Returns:
            None (tools are cached in instance for wrapper access)
            
        Raises:
            ValueError: If runtime context is missing or required template variables not provided
            RuntimeError: If MCP tools fail to load

        """
        # Static mode: tools already loaded at initialization
        if not self.is_dynamic:
            logger.debug("Static MCP mode: tools already loaded, skipping")
            return None
        
        # Dynamic mode: substitute templates and load tools
        
        # Check if already loaded for this instance (idempotency)
        if self._tools_loaded:
            logger.info("MCP tools already loaded for this execution, skipping")
            return None
        
        logger.info("Loading MCP tools with dynamic authentication...")
        
        try:
            # Extract template values from runtime context
            # Handle both Runtime objects (production) and plain dicts (tests)
            if not runtime:
                raise ValueError(
                    f"Dynamic MCP configuration requires template variables: {sorted(self.template_vars)}. "
                    f"Pass config={{'configurable': {{{', '.join(f'{v!r}: value' for v in sorted(self.template_vars))}}}}} "
                    "when invoking agent."
                )
            
            # Extract config from runtime object
            if hasattr(runtime, 'context'):
                # Production: Runtime object - runtime.context IS the configurable dict
                # The framework maps config["configurable"] directly to runtime.context
                configurable = runtime.context or {}
                if not configurable:
                    raise ValueError(
                        f"Dynamic MCP configuration requires template variables: {sorted(self.template_vars)}. "
                        f"Pass config={{'configurable': {{{', '.join(f'{v!r}: value' for v in sorted(self.template_vars))}}}}} "
                        "when invoking agent."
                    )

            elif isinstance(runtime, dict):
                # Tests: plain dict with 'configurable' key (for test compatibility)
                config = runtime
                if "configurable" not in config:
                    raise ValueError(
                        f"Dynamic MCP configuration requires template variables: {sorted(self.template_vars)}. "
                        f"Pass config={{'configurable': {{{', '.join(f'{v!r}: value' for v in sorted(self.template_vars))}}}}} "
                        "when invoking agent."
                    )
                configurable = config["configurable"]
            else:
                # Unknown type
                raise ValueError(
                    f"Dynamic MCP configuration requires template variables: {sorted(self.template_vars)}. "
                    f"Unexpected runtime type: {type(runtime)}. "
                    f"Pass config={{'configurable': {{{', '.join(f'{v!r}: value' for v in sorted(self.template_vars))}}}}} "
                    "when invoking agent."
                )
            
            # Validate all required template variables are provided
            provided_vars = set(configurable.keys())
            missing_vars = self.template_vars - provided_vars
            
            if missing_vars:
                raise ValueError(
                    f"Missing required template variables: {sorted(missing_vars)}. "
                    f"Provide these in config['configurable']: "
                    f"{', '.join(sorted(missing_vars))}"
                )
            
            logger.info(
                f"Successfully extracted template values for: {sorted(self.template_vars)}"
            )
            
            # Substitute template variables with actual values
            substituted_servers = substitute_templates(
                self.servers,
                configurable
            )
            
            logger.debug(f"Template substitution complete for {len(substituted_servers)} server(s)")
            
            # Load MCP tools asynchronously - direct await, no deadlock!
            # This runs naturally in the async context without blocking
            tools = await load_mcp_tools(substituted_servers, self.tool_filter)
            
            if not tools:
                raise RuntimeError(
                    "No MCP tools were loaded. "
                    "Check MCP server accessibility and user permissions."
                )
            
            # Cache tools by name for wrapper access
            self._tools_cache = {tool.name: tool for tool in tools}
            self._tools_loaded = True
            
            logger.info(
                f"Successfully loaded {len(tools)} MCP tool(s) with dynamic auth: "
                f"{list(self._tools_cache.keys())}"
            )
            
            return None
            
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load MCP tools: {e}", exc_info=True)
            raise RuntimeError(
                f"MCP tool loading failed: {e}. "
                "Check MCP server connectivity and authentication."
            ) from e
    
    async def aafter_agent(
        self,
        state: AgentState[Any],
        runtime: Runtime[None] | dict[str, Any],
    ) -> dict[str, Any] | None:
        """Cleanup after agent execution (async).
        
        For dynamic configs, clears the tools cache to ensure fresh loading
        on next invocation (in case tokens change).
        
        For static configs, keeps tools cached permanently.
        
        Args:
            state: Current agent state (unused)
            runtime: Runtime object (production) or dict (tests) - unused
            
        Returns:
            None

        """
        if self.is_dynamic:
            # Clear cache for dynamic configs to ensure fresh auth on next request
            self._tools_cache.clear()
            self._tools_loaded = False
            logger.debug("Cleared dynamic MCP tools cache for next execution")
        
        # For static configs, keep tools cached permanently
        
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
            mode = "dynamic" if self.is_dynamic else "static"
            raise RuntimeError(
                f"MCP tools not loaded yet ({mode} mode). "
                f"For static mode, this indicates initialization failure. "
                f"For dynamic mode, ensure middleware.before_agent() has been called "
                f"with proper config['configurable'] values."
            )
        
        if tool_name not in self._tools_cache:
            available = list(self._tools_cache.keys())
            raise ValueError(
                f"Tool '{tool_name}' not found in cache. "
                f"Available tools: {available}"
            )
        
        return self._tools_cache[tool_name]
