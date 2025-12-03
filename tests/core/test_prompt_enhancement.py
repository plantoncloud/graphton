"""Tests for system prompt enhancement functionality."""

import pytest

from graphton.core.prompt_enhancement import enhance_user_instructions


class TestEnhanceUserInstructions:
    """Test suite for the enhance_user_instructions function."""

    def test_enhancement_preserves_user_instructions(self) -> None:
        """User instructions should be preserved at the beginning."""
        user_text = "You are a helpful research assistant."
        result = enhance_user_instructions(user_text, has_mcp_tools=False)
        
        # User instructions should be at the start
        assert result.startswith(user_text)
        # Enhanced content should be longer
        assert len(result) > len(user_text)

    def test_enhancement_includes_planning_section(self) -> None:
        """Enhancement should include planning system awareness."""
        result = enhance_user_instructions(
            "You help manage tasks.",
            has_mcp_tools=False
        )
        
        # Should mention planning capabilities
        assert "planning" in result.lower() or "todo" in result.lower()
        assert "write_todos" in result or "read_todos" in result

    def test_enhancement_includes_file_system_section(self) -> None:
        """Enhancement should include file system awareness."""
        result = enhance_user_instructions(
            "You are an assistant.",
            has_mcp_tools=False
        )
        
        # Should mention file system capabilities
        assert "file system" in result.lower()
        # Should mention some file tools
        assert any(tool in result for tool in ["ls", "read_file", "write_file", "edit_file"])

    def test_enhancement_includes_mcp_tools_when_configured(self) -> None:
        """Enhancement should mention MCP tools when has_mcp_tools=True."""
        result = enhance_user_instructions(
            "You help with cloud resources.",
            has_mcp_tools=True
        )
        
        assert "mcp" in result.lower()
        assert "tools" in result.lower()

    def test_enhancement_excludes_mcp_tools_when_not_configured(self) -> None:
        """Enhancement should not mention MCP tools when has_mcp_tools=False."""
        result = enhance_user_instructions(
            "You are an assistant.",
            has_mcp_tools=False
        )
        
        # MCP should not be mentioned when not configured
        assert "mcp" not in result.lower()

    def test_enhancement_structure(self) -> None:
        """Enhancement should have proper structure."""
        result = enhance_user_instructions(
            "Original instructions.",
            has_mcp_tools=False
        )
        
        # Should have a capabilities section header
        assert "capabilities" in result.lower()
        # Should have the original text first
        assert result.startswith("Original instructions.")

    def test_empty_instructions_raises_error(self) -> None:
        """Empty user instructions should raise ValueError."""
        with pytest.raises(ValueError, match="user_instructions cannot be empty"):
            enhance_user_instructions("", has_mcp_tools=False)
        
        with pytest.raises(ValueError, match="user_instructions cannot be empty"):
            enhance_user_instructions("   ", has_mcp_tools=False)

    def test_enhancement_is_concise(self) -> None:
        """Enhancement should be minimal, not overwhelming."""
        result = enhance_user_instructions(
            "Simple instructions.",
            has_mcp_tools=True
        )
        
        # Total enhancement (excluding user instructions) should be reasonable
        # Let's say under 800 characters for the added content
        user_instructions = "Simple instructions."
        added_content = result[len(user_instructions):]
        
        # Should be concise but informative
        assert len(added_content) < 1000, "Enhancement should be concise"
        assert len(added_content) > 100, "Enhancement should provide meaningful context"

    def test_multiple_calls_same_result(self) -> None:
        """Multiple calls with same input should produce same result."""
        instructions = "You are a helpful assistant."
        
        result1 = enhance_user_instructions(instructions, has_mcp_tools=False)
        result2 = enhance_user_instructions(instructions, has_mcp_tools=False)
        
        assert result1 == result2

    def test_enhancement_mentions_when_to_use_planning(self) -> None:
        """Enhancement should provide strategic guidance on when to use planning."""
        result = enhance_user_instructions(
            "You help with tasks.",
            has_mcp_tools=False
        )
        
        # Should mention when to use planning (complex/multi-step)
        assert any(word in result.lower() for word in ["complex", "multi-step", "multi step"])

    def test_file_system_path_requirement_mentioned(self) -> None:
        """Enhancement should mention file path requirements."""
        result = enhance_user_instructions(
            "You are an assistant.",
            has_mcp_tools=False
        )
        
        # Should mention the path requirement
        assert "must start with '/'" in result or "start with '/'" in result

    def test_enhancement_with_already_detailed_instructions(self) -> None:
        """Enhancement should work even if user provides detailed instructions."""
        detailed_instructions = """
        You are a research assistant.
        You should use the planning system to break down complex tasks.
        You should use the file system to store your findings.
        """
        
        result = enhance_user_instructions(
            detailed_instructions,
            has_mcp_tools=False
        )
        
        # Should still include user instructions
        assert "research assistant" in result.lower()
        # Should still add capability context (redundancy is acceptable)
        assert "capabilities" in result.lower()

    def test_different_mcp_configurations_produce_different_results(self) -> None:
        """Results should differ based on has_mcp_tools parameter."""
        instructions = "You help manage resources."
        
        result_without_mcp = enhance_user_instructions(instructions, has_mcp_tools=False)
        result_with_mcp = enhance_user_instructions(instructions, has_mcp_tools=True)
        
        # Results should be different
        assert result_without_mcp != result_with_mcp
        # MCP version should be longer
        assert len(result_with_mcp) > len(result_without_mcp)




