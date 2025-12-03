"""Unit tests for sandbox configuration and backend creation."""

import pytest
from langgraph.graph.state import CompiledStateGraph

from graphton import create_deep_agent
from graphton.core.sandbox_factory import create_sandbox_backend


class TestSandboxBackendFactory:
    """Tests for sandbox backend factory function."""
    
    def test_create_filesystem_backend_default_root(self) -> None:
        """Test creating filesystem backend with default root directory."""
        config = {"type": "filesystem"}
        backend = create_sandbox_backend(config)
        
        # Verify backend was created (should be FilesystemBackend)
        assert backend is not None
        assert hasattr(backend, "read")
        assert hasattr(backend, "write")
        # Note: FilesystemBackend provides file ops but not execute (terminal commands)
    
    def test_create_filesystem_backend_custom_root(self) -> None:
        """Test creating filesystem backend with custom root directory."""
        config = {"type": "filesystem", "root_dir": "/tmp/test"}
        backend = create_sandbox_backend(config)
        
        assert backend is not None
        assert hasattr(backend, "read")
        assert hasattr(backend, "write")
        # Note: FilesystemBackend provides file ops but not execute (terminal commands)
    
    def test_missing_type_raises_error(self) -> None:
        """Test that missing 'type' key raises ValueError."""
        config = {"root_dir": "/workspace"}
        
        with pytest.raises(ValueError, match="must include 'type' key"):
            create_sandbox_backend(config)
    
    def test_empty_config_raises_error(self) -> None:
        """Test that empty config dict raises ValueError."""
        config = {}
        
        with pytest.raises(ValueError, match="must include 'type' key"):
            create_sandbox_backend(config)
    
    def test_invalid_config_type_raises_error(self) -> None:
        """Test that non-dict config raises ValueError."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            create_sandbox_backend("filesystem")  # type: ignore[arg-type]
    
    def test_unsupported_sandbox_type_raises_error(self) -> None:
        """Test that unsupported sandbox type raises ValueError."""
        config = {"type": "docker"}
        
        with pytest.raises(ValueError, match="Unsupported sandbox type: docker"):
            create_sandbox_backend(config)
    
    def test_modal_not_yet_supported(self) -> None:
        """Test that modal type returns helpful error message."""
        config = {"type": "modal"}
        
        with pytest.raises(ValueError, match="Modal sandbox support coming soon"):
            create_sandbox_backend(config)
    
    def test_runloop_not_yet_supported(self) -> None:
        """Test that runloop type returns helpful error message."""
        config = {"type": "runloop"}
        
        with pytest.raises(ValueError, match="Runloop sandbox support coming soon"):
            create_sandbox_backend(config)
    
    def test_daytona_requires_package(self) -> None:
        """Test that daytona type requires daytona package to be installed."""
        config = {"type": "daytona"}
        
        with pytest.raises(ValueError, match="Daytona backend requires 'daytona' package"):
            create_sandbox_backend(config)
    
    def test_harbor_not_yet_supported(self) -> None:
        """Test that harbor type returns helpful error message."""
        config = {"type": "harbor"}
        
        with pytest.raises(ValueError, match="Harbor sandbox support coming soon"):
            create_sandbox_backend(config)


class TestAgentWithSandboxConfig:
    """Tests for creating agents with sandbox configuration."""
    
    def test_create_agent_with_filesystem_sandbox(self) -> None:
        """Test creating agent with filesystem sandbox configuration."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a DevOps assistant.",
            sandbox_config={"type": "filesystem", "root_dir": "."}
        )
        
        assert isinstance(agent, CompiledStateGraph)
    
    def test_create_agent_without_sandbox(self) -> None:
        """Test creating agent without sandbox (backward compatibility)."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a documentation assistant."
            # No sandbox_config - should work fine
        )
        
        assert isinstance(agent, CompiledStateGraph)
    
    def test_create_agent_with_none_sandbox(self) -> None:
        """Test creating agent with explicitly None sandbox_config."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            sandbox_config=None
        )
        
        assert isinstance(agent, CompiledStateGraph)
    
    def test_invalid_sandbox_config_raises_error(self) -> None:
        """Test that invalid sandbox config raises ValueError during validation."""
        with pytest.raises(ValueError, match="Configuration validation failed"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                sandbox_config="filesystem"  # type: ignore[arg-type]
            )
    
    def test_empty_sandbox_config_raises_error(self) -> None:
        """Test that empty sandbox config raises ValueError."""
        with pytest.raises(ValueError, match="sandbox_config cannot be empty"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                sandbox_config={}
            )
    
    def test_sandbox_config_missing_type_raises_error(self) -> None:
        """Test that sandbox config without 'type' raises ValueError."""
        with pytest.raises(ValueError, match="must include 'type' key"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                sandbox_config={"root_dir": "/workspace"}
            )
    
    def test_unsupported_sandbox_type_in_agent_raises_error(self) -> None:
        """Test that unsupported sandbox type in agent creation raises error."""
        with pytest.raises(ValueError, match="Unsupported sandbox type"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                sandbox_config={"type": "unknown"}
            )


class TestSandboxConfigValidation:
    """Tests for sandbox config validation in AgentConfig."""
    
    def test_valid_filesystem_config_passes_validation(self) -> None:
        """Test that valid filesystem config passes validation."""
        # This should not raise any errors
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            sandbox_config={"type": "filesystem"}
        )
        assert isinstance(agent, CompiledStateGraph)
    
    def test_all_supported_types_pass_validation(self) -> None:
        """Test that all supported sandbox types pass config validation."""
        supported_types = ["filesystem", "modal", "runloop", "daytona", "harbor"]
        
        for sandbox_type in supported_types:
            config = {"type": sandbox_type}
            
            # Should pass validation (may fail at backend creation for unsupported types)
            # but validation itself should succeed
            if sandbox_type == "filesystem":
                # Only filesystem actually works without additional dependencies
                agent = create_deep_agent(
                    model="claude-sonnet-4.5",
                    system_prompt="You are a helpful assistant.",
                    sandbox_config=config
                )
                assert isinstance(agent, CompiledStateGraph)
            elif sandbox_type == "daytona":
                # Daytona is implemented but requires the daytona package
                with pytest.raises(ValueError, match="Daytona backend requires 'daytona' package"):
                    create_deep_agent(
                        model="claude-sonnet-4.5",
                        system_prompt="You are a helpful assistant.",
                        sandbox_config=config
                    )
            else:
                # Others should fail at backend creation with "coming soon" message
                with pytest.raises(ValueError, match="support coming soon"):
                    create_deep_agent(
                        model="claude-sonnet-4.5",
                        system_prompt="You are a helpful assistant.",
                        sandbox_config=config
                    )
    
    def test_non_string_type_raises_error(self) -> None:
        """Test that non-string type value raises validation error."""
        with pytest.raises(ValueError, match="'type' must be a string"):
            create_deep_agent(
                model="claude-sonnet-4.5",
                system_prompt="You are a helpful assistant.",
                sandbox_config={"type": 123}  # type: ignore[dict-item]
            )


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing code."""
    
    def test_agent_without_sandbox_still_works(self) -> None:
        """Test that agents can still be created without any sandbox config."""
        # This is the existing usage pattern - should continue to work
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant."
        )
        
        assert isinstance(agent, CompiledStateGraph)
    
    def test_agent_with_other_params_no_sandbox(self) -> None:
        """Test agent creation with various params but no sandbox."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a helpful assistant.",
            recursion_limit=50,
            max_tokens=5000,
            temperature=0.7
        )
        
        assert isinstance(agent, CompiledStateGraph)
    
    def test_combining_sandbox_with_other_features(self) -> None:
        """Test that sandbox config works alongside other features."""
        agent = create_deep_agent(
            model="claude-sonnet-4.5",
            system_prompt="You are a DevOps assistant.",
            sandbox_config={"type": "filesystem"},
            recursion_limit=75,
            max_tokens=10000,
            temperature=0.5
        )
        
        assert isinstance(agent, CompiledStateGraph)

