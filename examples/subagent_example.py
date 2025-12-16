"""Example demonstrating sub-agent usage in Graphton.

This example shows how to use sub-agents for task delegation with specialized
agents for research and code review.

Requirements:
    - Set ANTHROPIC_API_KEY environment variable

Usage:
    python examples/subagent_example.py
"""

import os

from graphton import create_deep_agent


def main() -> None:
    """Demonstrate sub-agent usage with research and code review specialists."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY=your-key-here")
        return
    
    print("=" * 80)
    print("Graphton Sub-agent Example")
    print("=" * 80)
    print()
    
    # Create agent with specialized sub-agents
    print("Creating agent with specialized sub-agents...")
    print()
    
    agent = create_deep_agent(
        model="claude-sonnet-4.5",
        system_prompt="""You are a research and development coordinator.
        
Your role is to:
- Coordinate research tasks by delegating to the deep-researcher sub-agent
- Coordinate code review tasks by delegating to the code-reviewer sub-agent
- Use the general-purpose sub-agent for other complex tasks
- Synthesize results from sub-agents into comprehensive responses

When you receive a request:
1. Identify which sub-agent(s) are best suited for the task
2. Delegate work to appropriate sub-agents using the task tool
3. Synthesize their results into a coherent response
4. Provide clear, actionable information to the user
""",
        
        # Define specialized sub-agents
        subagents=[
            {
                "name": "deep-researcher",
                "description": "Conducts thorough research on complex topics with comprehensive analysis",
                "system_prompt": """You are a research specialist.

Your capabilities:
- Conduct comprehensive research on assigned topics
- Analyze information from multiple perspectives
- Cite sources and evidence
- Provide detailed, well-organized findings

When researching:
1. Break down the topic into key aspects
2. Gather relevant information systematically
3. Analyze and synthesize findings
4. Present results in a clear, structured format
5. Include key insights and implications
""",
            },
            {
                "name": "code-reviewer",
                "description": "Reviews code for quality, security, best practices, and potential issues",
                "system_prompt": """You are a code review expert.

Your capabilities:
- Analyze code for bugs and logical errors
- Identify security vulnerabilities
- Suggest performance improvements
- Recommend best practices and design patterns
- Assess code readability and maintainability

When reviewing code:
1. Examine the code structure and logic
2. Identify potential issues (bugs, security, performance)
3. Suggest specific improvements with examples
4. Prioritize findings by severity
5. Provide constructive, actionable feedback
""",
            }
        ],
        
        # Include general-purpose sub-agent for other tasks
        general_purpose_agent=True,
        
        # Optional: Configure agent behavior
        recursion_limit=150,
        temperature=0.3,
        max_tokens=10000,
    )
    
    print("✓ Agent created with 3 sub-agents:")
    print("  1. deep-researcher (research specialist)")
    print("  2. code-reviewer (code quality specialist)")
    print("  3. general-purpose (context isolation)")
    print()
    
    # Example 1: Research task
    print("-" * 80)
    print("Example 1: Research Task")
    print("-" * 80)
    print()
    
    research_query = "What are the key benefits of using sub-agents in AI systems?"
    print(f"Query: {research_query}")
    print()
    print("Processing... (agent will delegate to deep-researcher sub-agent)")
    print()
    
    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": research_query}]
        })
        
        print("Response:")
        print("-" * 40)
        # Get the last message content
        if result and "messages" in result:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                print(last_message.content)
            else:
                print(last_message)
        print()
        
    except Exception as e:
        print(f"Error during research task: {e}")
        print()
    
    # Example 2: Code review task
    print("-" * 80)
    print("Example 2: Code Review Task")
    print("-" * 80)
    print()
    
    code_to_review = """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item['price'] * item['quantity']
    return total
"""
    
    review_query = f"Please review this Python code:\n{code_to_review}"
    print("Query: Review code for calculating order totals")
    print()
    print("Processing... (agent will delegate to code-reviewer sub-agent)")
    print()
    
    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": review_query}]
        })
        
        print("Response:")
        print("-" * 40)
        if result and "messages" in result:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                print(last_message.content)
            else:
                print(last_message)
        print()
        
    except Exception as e:
        print(f"Error during code review task: {e}")
        print()
    
    # Example 3: Mixed task (uses multiple sub-agents)
    print("-" * 80)
    print("Example 3: Mixed Task (Multiple Sub-agents)")
    print("-" * 80)
    print()
    
    mixed_query = """Research the concept of 'context isolation' in AI agents, 
and then review the following code that attempts to implement it:

class ContextIsolation:
    def __init__(self):
        self.contexts = {}
    
    def create_context(self, task_id):
        self.contexts[task_id] = {"messages": []}
    
    def get_context(self, task_id):
        return self.contexts.get(task_id, {})
"""
    
    print("Query: Research context isolation AND review implementation code")
    print()
    print("Processing... (agent will delegate to both sub-agents)")
    print()
    
    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": mixed_query}]
        })
        
        print("Response:")
        print("-" * 40)
        if result and "messages" in result:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                print(last_message.content)
            else:
                print(last_message)
        print()
        
    except Exception as e:
        print(f"Error during mixed task: {e}")
        print()
    
    print("=" * 80)
    print("Example Complete")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("- Main agent coordinates and delegates to specialized sub-agents")
    print("- Each sub-agent has isolated context and focused expertise")
    print("- Sub-agents return concise summaries to main agent")
    print("- Main agent synthesizes results into comprehensive responses")
    print()
    print("Benefits:")
    print("- Context isolation: Each sub-agent works independently")
    print("- Token efficiency: Main agent only sees summaries")
    print("- Parallel execution: Multiple sub-agents can work simultaneously")
    print("- Specialization: Different sub-agents for different domains")


if __name__ == "__main__":
    main()
