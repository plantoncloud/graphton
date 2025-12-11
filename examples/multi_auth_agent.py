"""Example: Deep Agent with Multiple Authentication Methods.

This example demonstrates the universal MCP authentication framework with
multiple servers using different authentication methods:
- Bearer token authentication (dynamic)
- API Key authentication (dynamic)
- Static hardcoded credentials (static)

Prerequisites:
- Set PLANTON_API_KEY environment variable
- Set EXTERNAL_API_KEY environment variable
- Set ANTHROPIC_API_KEY or OPENAI_API_KEY for the LLM

Usage:
    export PLANTON_API_KEY="your-planton-token"
    export EXTERNAL_API_KEY="your-external-key"
    export ANTHROPIC_API_KEY="your-key-here"
    python examples/multi_auth_agent.py
"""

import os
import sys

from graphton import create_deep_agent

SYSTEM_PROMPT = """You are a multi-cloud assistant with access to multiple services.

You can:
- List organizations from Planton Cloud
- Search data from external APIs
- Access public resources

Use the appropriate tools based on what the user is asking for.
"""


def main() -> None:
    """Run the multi-auth MCP configuration example."""
    # Check for required API keys
    planton_token = os.getenv("PLANTON_API_KEY")
    external_key = os.getenv("EXTERNAL_API_KEY")
    
    if not planton_token:
        print("Error: PLANTON_API_KEY environment variable not set")
        print("Get your API key from: https://console.planton.cloud")
        sys.exit(1)
    
    if not external_key:
        print("Warning: EXTERNAL_API_KEY not set, using demo value")
        external_key = "demo-api-key-456"
    
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("Error: Either ANTHROPIC_API_KEY or OPENAI_API_KEY must be set")
        sys.exit(1)
    
    print("Creating agent with multiple MCP servers and auth methods...")
    print("  - Planton Cloud: Bearer token (dynamic)")
    print("  - External API: X-API-Key header (dynamic)")
    print("  - Public API: Hardcoded credentials (static)\n")
    
    # Create agent with multiple MCP servers
    # Mix of static and dynamic authentication
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt=SYSTEM_PROMPT,
        
        # Multiple MCP servers with different authentication methods
        mcp_servers={
            # Server 1: Bearer token authentication (Planton Cloud)
            "planton-cloud": {
                "transport": "streamable_http",
                "url": "https://mcp.planton.ai/",
                "headers": {
                    "Authorization": "Bearer {{PLANTON_TOKEN}}"
                }
            },
            
            # Server 2: API Key authentication (External API)
            "external-api": {
                "transport": "http",
                "url": "https://api.example.com/mcp",
                "headers": {
                    "X-API-Key": "{{EXTERNAL_KEY}}",
                    "X-Client-ID": "graphton-client"
                }
            },
            
            # Server 3: Static credentials (Public API)
            "public-api": {
                "transport": "http",
                "url": "https://public.example.com/mcp",
                "headers": {
                    # Hardcoded - same for all users
                    "X-Public-Token": "public-access-token"
                }
            }
        },
        
        # Tool selection from all servers
        mcp_tools={
            "planton-cloud": [
                "list_organizations",
            ],
            "external-api": [
                "search",
                "fetch_data"
            ],
            "public-api": [
                "get_public_info"
            ]
        }
    )
    
    print("Agent created successfully!")
    print("✅ Configuration mode: DYNAMIC (has template variables)")
    print("   Template variables detected: {{PLANTON_TOKEN}}, {{EXTERNAL_KEY}}")
    print("   Static server (public-api) will be included in dynamic load\n")
    
    print("Invoking agent with multiple services...\n")
    print("-" * 60)
    
    # Invoke agent with multiple authentication tokens
    # Each token is substituted into its respective template variable
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "List my Planton Cloud organizations."
                }
            ]
        },
        config={
            "configurable": {
                # Provide values for all template variables
                "PLANTON_TOKEN": planton_token,
                "EXTERNAL_KEY": external_key,
                # No need to provide value for public-api (static)
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
    
    print("\n✅ Example completed successfully!")
    print("\nKey features demonstrated:")
    print("  - Multiple MCP servers in one agent")
    print("  - Different authentication methods:")
    print("    • Bearer token ({{PLANTON_TOKEN}})")
    print("    • API Key header ({{EXTERNAL_KEY}})")
    print("    • Static credentials (hardcoded)")
    print("  - Per-user dynamic authentication")
    print("  - Template substitution from config['configurable']")
    print("\nArchitecture:")
    print("  - Framework auto-detects dynamic config (has templates)")
    print("  - Tools loaded at invocation time with user-specific auth")
    print("  - Each user gets isolated authentication per request")


if __name__ == "__main__":
    main()














