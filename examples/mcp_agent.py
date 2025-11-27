"""Example: Deep Agent with MCP tools from Planton Cloud.

This example demonstrates how to create an agent that uses MCP tools
from the Planton Cloud MCP server with per-user authentication.

Prerequisites:
- Set PLANTON_API_KEY environment variable with your token
- Set ANTHROPIC_API_KEY or OPENAI_API_KEY for the LLM

Usage:
    export PLANTON_API_KEY="your-token-here"
    export ANTHROPIC_API_KEY="your-key-here"
    python examples/mcp_agent.py
"""

import os
import sys

from graphton import create_deep_agent

# System prompt for the agent
SYSTEM_PROMPT = """You are a Planton Cloud assistant.

You help users manage their cloud resources on Planton Cloud.
You have access to tools that can list organizations, environments,
and search for cloud resources.

When asked to list organizations or resources, use the available tools
to fetch the actual data and provide accurate information to the user.
"""


def main() -> None:
    """Run the MCP-enabled agent example."""
    # Check for required API keys
    user_token = os.getenv("PLANTON_API_KEY")
    if not user_token:
        print("Error: PLANTON_API_KEY environment variable not set")
        print("Get your API key from: https://console.planton.cloud")
        sys.exit(1)
    
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("Error: Either ANTHROPIC_API_KEY or OPENAI_API_KEY must be set")
        sys.exit(1)
    
    print("Creating agent with MCP tools from Planton Cloud...")
    
    # Create agent with MCP tools
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt=SYSTEM_PROMPT,
        
        # MCP server configuration (Cursor-compatible format)
        mcp_servers={
            "planton-cloud": {
                "transport": "streamable_http",
                "url": "https://mcp.planton.ai/",
            }
        },
        
        # Tool selection - specify which tools to load
        mcp_tools={
            "planton-cloud": [
                "list_organizations",
                "list_environments_for_org",
                "search_cloud_resources",
            ]
        }
    )
    
    print("Agent created successfully!")
    print("\nAsking agent to list organizations...\n")
    print("-" * 60)
    
    # Invoke agent with user token
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "List all my organizations on Planton Cloud."
                }
            ]
        },
        config={
            "configurable": {
                "_user_token": user_token
            }
        }
    )
    
    # Extract and print the response
    if result and "messages" in result:
        response = result["messages"][-1]["content"]
        print(f"Agent: {response}")
        print("-" * 60)
    else:
        print("No response received from agent")
    
    # Example 2: Search for resources
    print("\nAsking agent to search for cloud resources...\n")
    print("-" * 60)
    
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Search for any Kubernetes deployments in my dev environment."
                }
            ]
        },
        config={
            "configurable": {
                "_user_token": user_token
            }
        }
    )
    
    if result and "messages" in result:
        response = result["messages"][-1]["content"]
        print(f"Agent: {response}")
        print("-" * 60)
    
    print("\n✅ Example completed successfully!")
    print("\nKey features demonstrated:")
    print("  - MCP server configuration")
    print("  - Per-user authentication via config")
    print("  - Multiple MCP tools from one server")
    print("  - Conversational agent with tool use")


if __name__ == "__main__":
    main()

