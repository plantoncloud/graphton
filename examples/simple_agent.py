"""Example: Simple Deep Agent without MCP tools.

This example demonstrates the basic usage of Graphton to create a Deep Agent
with minimal boilerplate. The agent is created with just a model name and
system prompt, eliminating the need for manual model instantiation.

Requirements:
    - ANTHROPIC_API_KEY environment variable set
    - graphton package installed

Usage:
    python examples/simple_agent.py
"""

from graphton import create_deep_agent

# Define the agent's behavior with a system prompt
SYSTEM_PROMPT = """You are a helpful assistant that answers questions concisely.

When answering questions:
- Be direct and to the point
- Provide accurate information
- If you're not sure, say so
- Use clear, simple language
"""

# Create agent with just model and prompt - that's it!
agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt=SYSTEM_PROMPT,
)

# Invoke agent with a message
print("Creating agent and asking a question...")
print("-" * 60)

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ]
})

# Extract and print the response
response = result["messages"][-1]["content"]
print("User: What is the capital of France?")
print(f"Agent: {response}")
print("-" * 60)

# Example 2: Multi-turn conversation
print("\nMulti-turn conversation example:")
print("-" * 60)

# Start a conversation
messages = [
    {"role": "user", "content": "What is 7 times 8?"}
]

result = agent.invoke({"messages": messages})
response = result["messages"][-1]["content"]
print("User: What is 7 times 8?")
print(f"Agent: {response}")

# Continue the conversation
messages = result["messages"]
messages.append({"role": "user", "content": "And what is that plus 10?"})

result = agent.invoke({"messages": messages})
response = result["messages"][-1]["content"]
print("User: And what is that plus 10?")
print(f"Agent: {response}")
print("-" * 60)

# Example 3: Agent with custom parameters
print("\nAgent with custom parameters:")
print("-" * 60)

creative_agent = create_deep_agent(
    model="claude-sonnet-4.5",
    system_prompt="You are a creative writer. Write in a poetic, imaginative style.",
    temperature=0.9,  # Higher temperature for more creativity
    max_tokens=500,
)

result = creative_agent.invoke({
    "messages": [
        {"role": "user", "content": "Describe a sunset in three sentences."}
    ]
})

response = result["messages"][-1]["content"]
print("User: Describe a sunset in three sentences.")
print(f"Creative Agent: {response}")
print("-" * 60)

print("\n✅ Examples completed successfully!")
print("\nKey takeaways:")
print("1. Creating agents is simple - just model name + system prompt")
print("2. No need to manually instantiate ChatAnthropic or manage configs")
print("3. Easy to customize with temperature, max_tokens, etc.")
print("4. Agents maintain conversation context across turns")












