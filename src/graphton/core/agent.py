"""Agent factory for creating Deep Agents with minimal boilerplate.

This module provides the main entry point for creating LangGraph Deep Agents
using Graphton's declarative API.
"""

from collections.abc import Sequence
from typing import Any

from deepagents import create_deep_agent as deepagents_create_deep_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from graphton.core.models import parse_model_string


def create_deep_agent(
    model: str | BaseChatModel,
    system_prompt: str,
    tools: Sequence[BaseTool] | None = None,
    middleware: Sequence[Any] | None = None,
    context_schema: type[Any] | None = None,
    recursion_limit: int = 100,
    max_tokens: int | None = None,
    temperature: float | None = None,
    **model_kwargs: Any,
) -> CompiledStateGraph:
    """Create a Deep Agent with minimal boilerplate.
    
    This is the main entry point for Graphton. It eliminates boilerplate by:
    - Accepting model name strings instead of requiring model instantiation
    - Providing sensible defaults for model parameters
    - Automatically applying recursion limits
    - Supporting both string-based and instance-based model configuration
    
    Args:
        model: Model name string (e.g., "claude-sonnet-4.5", "gpt-4o") or
            a LangChain model instance. String format supports friendly names
            that map to full model IDs.
        system_prompt: The system prompt for the agent. This defines the agent's
            role, capabilities, and behavior.
        tools: Optional list of tools the agent can use. Defaults to empty list.
            In Phase 3, MCP tools will be automatically loaded.
        middleware: Optional list of middleware to run before/after agent execution.
            In Phase 3, MCP tool loading middleware will be auto-injected.
        context_schema: Optional state schema for the agent. Defaults to FilesystemState
            from deepagents, which provides file system operations.
        recursion_limit: Maximum recursion depth for the agent (default: 100).
            This prevents infinite loops in agent reasoning.
        max_tokens: Override default max_tokens for the model. Defaults depend on
            the model provider (Anthropic: 20000, OpenAI: model default).
        temperature: Override default temperature for the model. Higher values
            (e.g., 0.7-1.0) make output more creative, lower values (e.g., 0.0-0.3)
            make it more deterministic.
        **model_kwargs: Additional model-specific parameters to pass to the model
            constructor (e.g., top_p, top_k for Anthropic).
    
    Returns:
        A compiled LangGraph agent ready to invoke with messages.
    
    Raises:
        ValueError: If system_prompt is empty or recursion_limit is invalid
        ValueError: If model string is invalid or unsupported
    
    Examples:
        Basic agent with model string:
        
        >>> agent = create_deep_agent(
        ...     model="claude-sonnet-4.5",
        ...     system_prompt="You are a helpful assistant.",
        ... )
        >>> result = agent.invoke({"messages": [{"role": "user", "content": "Hello"}]})
        
        Agent with custom parameters:
        
        >>> agent = create_deep_agent(
        ...     model="gpt-4o",
        ...     system_prompt="You are a code reviewer.",
        ...     temperature=0.3,
        ...     max_tokens=5000,
        ...     recursion_limit=50,
        ... )
        
        Agent with model instance (advanced):
        
        >>> from langchain_anthropic import ChatAnthropic
        >>> model = ChatAnthropic(model="claude-opus-4", max_tokens=30000)
        >>> agent = create_deep_agent(
        ...     model=model,
        ...     system_prompt="You are a research assistant.",
        ... )
    
    """
    # Validate system prompt
    if not system_prompt or not system_prompt.strip():
        raise ValueError("system_prompt cannot be empty")
    
    # Validate recursion limit
    if recursion_limit <= 0:
        raise ValueError(f"recursion_limit must be positive, got {recursion_limit}")
    
    # Parse model if string, otherwise use instance directly
    if isinstance(model, str):
        model_instance = parse_model_string(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **model_kwargs,
        )
    else:
        # Model instance provided directly
        model_instance = model
        
        # Warn if model parameters were provided but will be ignored
        if max_tokens is not None or temperature is not None or model_kwargs:
            import warnings
            warnings.warn(
                "Model instance provided with additional parameters. "
                "Additional parameters (max_tokens, temperature, **model_kwargs) "
                "are ignored when passing a model instance. "
                "To use these parameters, pass a model name string instead.",
                UserWarning,
                stacklevel=2,
            )
    
    # Default empty sequences if None provided
    tools = tools or []
    middleware = middleware or []
    
    # Create the Deep Agent using deepagents library
    agent = deepagents_create_deep_agent(
        model=model_instance,
        tools=list(tools),
        system_prompt=system_prompt,
        middleware=list(middleware),
        context_schema=context_schema,
    )
    
    # Apply recursion limit configuration
    configured_agent = agent.with_config({"recursion_limit": recursion_limit})
    
    return configured_agent

