"""Example: Deep Agent with Static MCP Configuration.

This example demonstrates static MCP server configuration (no template variables).
Tools are loaded once at agent creation time with zero runtime overhead.

Use this approach when:
- Credentials are hardcoded or environment-specific
- All users share the same MCP authentication
- MCP server doesn't require user-specific tokens

Prerequisites:
- Configure MCP_API_KEY with hardcoded credentials
- Set ANTHROPIC_API_KEY or OPENAI_API_KEY for the LLM

Usage:
    python examples/static_mcp_agent.py
"""

import os
import sys

from graphton import create_deep_agent

SYSTEM_PROMPT = """You are a helpful assistant with access to external tools.

You can search and fetch data using the available tools.
When asked for information, use the tools to provide accurate answers.
"""


def main() -> None:
    """Run the static MCP configuration example."""
    # Check for LLM API key
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("Error: Either ANTHROPIC_API_KEY or OPENAI_API_KEY must be set")
        sys.exit(1)
    
    print("Creating agent with static MCP configuration...")
    print("(Tools will be loaded once at creation time)\n")
    
    # Create agent with static MCP configuration
    # No template variables - tools loaded immediately
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt=SYSTEM_PROMPT,
        
        # Static MCP server configuration (no template variables)
        # Credentials are hardcoded
        mcp_servers={
            "public-api": {
                "transport": "http",
                "url": "https://api.example.com/mcp",
                "headers": {
                    # Hardcoded credentials - same for all users
                    "X-API-Key": "hardcoded-api-key-123",
                    "X-Client-ID": "graphton-client"
                }
            }
        },
        
        # Tool selection
        mcp_tools={
            "public-api": [
                "search",
                "fetch_data",
            ]
        }
    )
    
    print("Agent created successfully!")
    print("✅ Tools were loaded at creation time (static mode)")
    print("\nInvoking agent...\n")
    print("-" * 60)
    
    # Invoke agent - no need to provide tokens in config
    # Static config means no runtime authentication
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Search for information about Python programming."
                }
            ]
        }
        # No config['configurable'] needed - static authentication
    )
    
    # Extract and print the response
    if result and "messages" in result:
        response = result["messages"][-1]["content"]
        print(f"Agent: {response}")
        print("-" * 60)
    else:
        print("No response received from agent")
    
    print("\n✅ Example completed successfully!")
    print("\nKey features demonstrated:")
    print("  - Static MCP configuration (no template variables)")
    print("  - Tools loaded once at agent creation")
    print("  - Zero runtime authentication overhead")
    print("  - Hardcoded credentials for all users")
    print("\nUse cases:")
    print("  - Environment-specific credentials (dev/staging/prod)")
    print("  - Public APIs with fixed access tokens")
    print("  - Internal services with shared authentication")


if __name__ == "__main__":
    main()











