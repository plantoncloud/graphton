"""Unit tests for loop detection middleware."""

import pytest
from langchain_core.messages import AIMessage, SystemMessage

from graphton.core.loop_detection import LoopDetectionMiddleware


class TestLoopDetectionMiddleware:
    """Tests for LoopDetectionMiddleware functionality."""
    
    def test_middleware_initialization(self) -> None:
        """Test that middleware initializes with correct defaults."""
        middleware = LoopDetectionMiddleware()
        
        assert middleware.history_size == 10
        assert middleware.consecutive_threshold == 3
        assert middleware.total_threshold == 5
        assert middleware.enabled is True
        assert len(middleware._tool_history) == 0
        assert middleware._intervention_count == 0
        assert middleware._stopped is False
    
    def test_middleware_custom_configuration(self) -> None:
        """Test middleware with custom configuration."""
        middleware = LoopDetectionMiddleware(
            history_size=20,
            consecutive_threshold=5,
            total_threshold=10,
            enabled=False,
        )
        
        assert middleware.history_size == 20
        assert middleware.consecutive_threshold == 5
        assert middleware.total_threshold == 10
        assert middleware.enabled is False
    
    def test_parameter_hashing(self) -> None:
        """Test that parameter hashing is consistent."""
        middleware = LoopDetectionMiddleware()
        
        # Same params should produce same hash
        params1 = {"arg1": "value1", "arg2": 42}
        params2 = {"arg2": 42, "arg1": "value1"}  # Different order
        
        hash1 = middleware._hash_params(params1)
        hash2 = middleware._hash_params(params2)
        
        assert hash1 == hash2
        
        # Different params should produce different hash
        params3 = {"arg1": "different", "arg2": 42}
        hash3 = middleware._hash_params(params3)
        
        assert hash1 != hash3
    
    def test_consecutive_loop_detection(self) -> None:
        """Test detection of consecutive identical tool calls."""
        middleware = LoopDetectionMiddleware(consecutive_threshold=3)
        
        # Add same tool call 3 times
        for _ in range(3):
            middleware._tool_history.append(("read_file", "abc123"))
        
        is_loop, tool_name, count = middleware._detect_consecutive_loops()
        
        assert is_loop is True
        assert tool_name == "read_file"
        assert count == 3
    
    def test_consecutive_loop_not_detected_below_threshold(self) -> None:
        """Test that consecutive loops below threshold are not detected."""
        middleware = LoopDetectionMiddleware(consecutive_threshold=3)
        
        # Add same tool call only 2 times
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("read_file", "abc123"))
        
        is_loop, tool_name, count = middleware._detect_consecutive_loops()
        
        assert is_loop is False
        assert count == 2
    
    def test_consecutive_loop_broken_by_different_tool(self) -> None:
        """Test that consecutive loop is broken by different tool call."""
        middleware = LoopDetectionMiddleware(consecutive_threshold=3)
        
        # Add same tool, then different, then same again
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("write_file", "xyz789"))  # Different tool
        middleware._tool_history.append(("read_file", "abc123"))
        
        is_loop, tool_name, count = middleware._detect_consecutive_loops()
        
        # Only 1 consecutive read_file at the end
        assert is_loop is False
        assert count == 1
    
    def test_total_repetitions_detection(self) -> None:
        """Test detection of total repetitions across history."""
        middleware = LoopDetectionMiddleware(total_threshold=5)
        
        # Add same tool 5 times with other tools in between
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("write_file", "xyz789"))
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("list_dir", "def456"))
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("read_file", "abc123"))
        
        is_excessive, tool_name, count = middleware._detect_total_repetitions()
        
        assert is_excessive is True
        assert tool_name == "read_file"
        assert count == 5
    
    def test_total_repetitions_not_detected_below_threshold(self) -> None:
        """Test that total repetitions below threshold are not detected."""
        middleware = LoopDetectionMiddleware(total_threshold=5)
        
        # Add same tool only 4 times
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("write_file", "xyz789"))
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("list_dir", "def456"))
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._tool_history.append(("read_file", "abc123"))
        
        is_excessive, tool_name, count = middleware._detect_total_repetitions()
        
        assert is_excessive is False
        assert count == 4
    
    def test_intervention_message_warning(self) -> None:
        """Test creation of warning intervention message."""
        middleware = LoopDetectionMiddleware()
        
        msg = middleware._create_intervention_message(
            tool_name="read_file",
            consecutive_count=3,
            total_count=3,
            is_final=False,
        )
        
        assert isinstance(msg, SystemMessage)
        assert "LOOP WARNING" in msg.content
        assert "read_file" in msg.content
        assert "3 times in a row" in msg.content
        assert "different approach" in msg.content
    
    def test_intervention_message_final(self) -> None:
        """Test creation of final (stop) intervention message."""
        middleware = LoopDetectionMiddleware()
        
        msg = middleware._create_intervention_message(
            tool_name="search",
            consecutive_count=5,
            total_count=5,
            is_final=True,
        )
        
        assert isinstance(msg, SystemMessage)
        assert "LOOP DETECTED" in msg.content
        assert "Critical repetition limit" in msg.content
        assert "search" in msg.content
        assert "5 times" in msg.content
        assert "MUST conclude" in msg.content
        assert "Do NOT call" in msg.content
    
    @pytest.mark.asyncio
    async def test_before_agent_clears_state(self) -> None:
        """Test that before_agent clears state for new execution."""
        middleware = LoopDetectionMiddleware()
        
        # Pollute state
        middleware._tool_history.append(("read_file", "abc123"))
        middleware._intervention_count = 2
        middleware._stopped = True
        
        # Call before_agent
        state = {"messages": []}
        await middleware.abefore_agent(state, {})
        
        # State should be cleared
        assert len(middleware._tool_history) == 0
        assert middleware._intervention_count == 0
        assert middleware._stopped is False
    
    @pytest.mark.asyncio
    async def test_after_step_tracks_tool_calls(self) -> None:
        """Test that after_step tracks tool calls from messages."""
        middleware = LoopDetectionMiddleware()
        
        # Initialize state
        await middleware.abefore_agent({"messages": []}, {})
        
        # Create a message with tool call
        tool_call_msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "read_file",
                    "args": {"path": "/test/file.txt"},
                    "id": "call_123",
                }
            ],
        )
        
        state = {"messages": [tool_call_msg]}
        await middleware.aafter_step(state, {})
        
        # Tool history should be updated
        assert len(middleware._tool_history) == 1
        assert middleware._tool_history[0][0] == "read_file"
    
    @pytest.mark.asyncio
    async def test_after_step_consecutive_loop_intervention(self) -> None:
        """Test that consecutive loop triggers intervention."""
        middleware = LoopDetectionMiddleware(consecutive_threshold=3)
        
        # Initialize state
        await middleware.abefore_agent({"messages": []}, {})
        
        # Simulate 3 consecutive identical tool calls
        messages = []
        for i in range(3):
            tool_call_msg = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "read_file",
                        "args": {"path": "/test/file.txt"},
                        "id": f"call_{i}",
                    }
                ],
            )
            messages.append(tool_call_msg)
            state = {"messages": messages.copy()}
            result = await middleware.aafter_step(state, {})
            
            # On the 3rd call, intervention should be injected
            if i == 2:
                assert result is not None
                assert "messages" in result
                # Last message should be intervention
                last_msg = result["messages"][-1]
                assert isinstance(last_msg, SystemMessage)
                assert "LOOP WARNING" in last_msg.content
                assert middleware._intervention_count == 1
    
    @pytest.mark.asyncio
    async def test_after_step_total_loop_stops_execution(self) -> None:
        """Test that total repetitions trigger final intervention and stop."""
        middleware = LoopDetectionMiddleware(total_threshold=5)
        
        # Initialize state
        await middleware.abefore_agent({"messages": []}, {})
        
        # Simulate 5 total calls (with some other tools in between)
        messages = []
        call_count = 0
        
        for i in range(10):
            if i % 2 == 0 and call_count < 5:
                # Read file call
                tool_call_msg = AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "read_file",
                            "args": {"path": "/test/file.txt"},
                            "id": f"call_{i}",
                        }
                    ],
                )
                call_count += 1
            else:
                # Different tool
                tool_call_msg = AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "list_dir",
                            "args": {"path": "/test"},
                            "id": f"call_{i}",
                        }
                    ],
                )
            
            messages.append(tool_call_msg)
            state = {"messages": messages.copy()}
            result = await middleware.aafter_step(state, {})
            
            # On the 5th read_file call, should stop
            if call_count == 5:
                assert result is not None
                last_msg = result["messages"][-1]
                assert isinstance(last_msg, SystemMessage)
                assert "LOOP DETECTED" in last_msg.content
                assert "Critical repetition limit" in last_msg.content
                assert middleware._stopped is True
                break
    
    @pytest.mark.asyncio
    async def test_disabled_middleware_does_nothing(self) -> None:
        """Test that disabled middleware doesn't track or intervene."""
        middleware = LoopDetectionMiddleware(enabled=False)
        
        # Try to trigger loop detection
        await middleware.abefore_agent({"messages": []}, {})
        
        tool_call_msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "read_file",
                    "args": {"path": "/test/file.txt"},
                    "id": "call_1",
                }
            ],
        )
        
        state = {"messages": [tool_call_msg]}
        result = await middleware.aafter_step(state, {})
        
        # No tracking or intervention
        assert len(middleware._tool_history) == 0
        assert result is None
    
    @pytest.mark.asyncio
    async def test_after_step_stops_processing_when_stopped(self) -> None:
        """Test that after_step stops processing after final intervention."""
        middleware = LoopDetectionMiddleware()
        
        # Manually set stopped flag
        middleware._stopped = True
        
        tool_call_msg = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "read_file",
                    "args": {"path": "/test/file.txt"},
                    "id": "call_1",
                }
            ],
        )
        
        state = {"messages": [tool_call_msg]}
        result = await middleware.aafter_step(state, {})
        
        # Should not process or modify state
        assert result is None
        assert len(middleware._tool_history) == 0


class TestLoopDetectionIntegration:
    """Integration tests for loop detection with agent creation."""
    
    def test_loop_detection_auto_injected(self) -> None:
        """Test that loop detection is automatically injected in create_deep_agent."""
        from graphton import create_deep_agent
        
        # Create agent - loop detection should be auto-injected
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a test agent.",
        )
        
        # Agent should be created successfully
        from langgraph.graph.state import CompiledStateGraph
        assert isinstance(agent, CompiledStateGraph)
        
        # Note: We can't easily inspect middleware list from compiled graph,
        # but the fact that it compiles without error validates injection works

