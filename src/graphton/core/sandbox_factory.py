"""Sandbox backend factory for declarative configuration.

This module provides a factory function to create sandbox backend instances
from declarative configuration dictionaries, following the same pattern as
MCP server/tool configuration in Graphton.
"""

from __future__ import annotations

from typing import Any

from deepagents.backends.protocol import BackendProtocol  # type: ignore[import-untyped]


def create_sandbox_backend(config: dict[str, Any]) -> BackendProtocol:
    """Create sandbox backend from declarative configuration.
    
    This factory function instantiates appropriate backend implementations
    based on configuration dictionaries, enabling declarative agent setup
    without manual backend instantiation.
    
    Args:
        config: Sandbox configuration dictionary with required 'type' key.
            Supported types:
            - 'filesystem': Local filesystem with file operations only
            - 'daytona': Daytona cloud sandbox with full execution support
            - 'modal': Modal.com cloud sandbox (future)
            - 'runloop': Runloop cloud sandbox (future)
            - 'harbor': LangGraph Cloud/Harbor (future)
    
    Returns:
        Configured backend instance implementing BackendProtocol.
        For 'filesystem' type, returns FilesystemBackend which provides file
        operations (read, write, edit, ls, glob, grep) but not terminal execution.
        For 'daytona' type, returns DaytonaBackend which implements SandboxBackendProtocol
        and supports full shell command execution via the execute tool.
    
    Raises:
        ValueError: If config is missing 'type' key or type is unsupported.
        ValueError: If required configuration parameters are missing.
    
    Examples:
        Reuse existing Daytona sandbox (recommended for performance):
        
        >>> config = {
        ...     "type": "daytona",
        ...     "sandbox_id": "sandbox-xyz789"  # Reuse existing sandbox
        ... }
        >>> backend = create_sandbox_backend(config)
        >>> # Requires DAYTONA_API_KEY environment variable
        >>> # Instant connection to existing sandbox with skills/state preserved
        
        Create Daytona sandbox backend with pre-built snapshot:
        
        >>> config = {
        ...     "type": "daytona",
        ...     "snapshot_id": "snap-abc123"  # Pre-built with all CLIs
        ... }
        >>> backend = create_sandbox_backend(config)
        >>> # Requires DAYTONA_API_KEY environment variable
        >>> # Instant spin-up from snapshot with all tools pre-installed
        
        Create vanilla Daytona sandbox:
        
        >>> config = {"type": "daytona"}
        >>> backend = create_sandbox_backend(config)
        >>> # Agent will have execute tool enabled for shell commands
        
        Create filesystem backend (file operations only):
        
        >>> config = {"type": "filesystem", "root_dir": "/workspace"}
        >>> backend = create_sandbox_backend(config)
        >>> # execute tool will return error if called
    
    """
    if not isinstance(config, dict):
        raise ValueError(
            f"sandbox_config must be a dictionary, got {type(config).__name__}"
        )
    
    backend_type = config.get("type")
    
    if not backend_type:
        raise ValueError(
            "sandbox_config must include 'type' key. "
            "Supported types: filesystem, modal, runloop, daytona, harbor"
        )
    
    if backend_type == "filesystem":
        # Import only when needed to avoid hard dependencies
        from deepagents.backends import FilesystemBackend  # type: ignore[import-untyped]
        
        root_dir = config.get("root_dir", ".")
        return FilesystemBackend(root_dir=root_dir)
    
    elif backend_type == "daytona":
        # Import Daytona dependencies only when needed
        import os
        import time
        
        try:
            from daytona import Daytona, DaytonaConfig  # type: ignore[import-not-found]
            from daytona.common.daytona import (  # type: ignore[import-not-found]
                CreateSandboxFromSnapshotParams,
            )
            from deepagents_cli.integrations.daytona import (  # type: ignore[import-not-found]
                DaytonaBackend,
            )
        except ImportError as e:
            raise ValueError(
                f"Daytona backend requires 'daytona' package. "
                f"Install with: pip install daytona>=0.113.0\nError: {e}"
            ) from e
        
        # Get API key from config or environment
        api_key = config.get("api_key") or os.environ.get("DAYTONA_API_KEY")
        if not api_key:
            raise ValueError(
                "Daytona API key required. Provide via config['api_key'] or "
                "DAYTONA_API_KEY environment variable."
            )
        
        # Get optional parameters from config
        sandbox_id = config.get("sandbox_id")  # Reuse existing sandbox
        snapshot_id = config.get("snapshot_id")  # Create from snapshot
        
        # Create Daytona client
        daytona = Daytona(DaytonaConfig(api_key=api_key))
        
        # Create or reuse sandbox
        if sandbox_id:
            # Reuse existing sandbox (for skills, persistent state, etc.)
            try:
                sandbox = daytona.get(sandbox_id)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to retrieve existing sandbox {sandbox_id}: {e}"
                ) from e
            
            # Verify sandbox is alive and responsive
            try:
                result = sandbox.process.exec("echo ready", timeout=5)
                if result.exit_code != 0:
                    raise RuntimeError(f"Sandbox {sandbox_id} is not responsive")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to connect to existing sandbox {sandbox_id}: {e}"
                ) from e
        elif snapshot_id:
            # Create from pre-built snapshot for instant spin-up
            params = CreateSandboxFromSnapshotParams(snapshot=snapshot_id)
            sandbox = daytona.create(params=params)
            
            # Poll until sandbox is ready (Daytona requires this)
            for _ in range(90):  # 180s timeout (90 * 2s)
                try:
                    result = sandbox.process.exec("echo ready", timeout=5)
                    if result.exit_code == 0:
                        break
                except Exception:
                    pass
                time.sleep(2)
            else:
                # Cleanup on timeout
                try:
                    sandbox.delete()
                finally:
                    raise RuntimeError(
                        "Daytona sandbox failed to start within 180 seconds"
                    )
        else:
            # Create vanilla sandbox
            sandbox = daytona.create()
            
            # Poll until sandbox is ready (Daytona requires this)
            for _ in range(90):  # 180s timeout (90 * 2s)
                try:
                    result = sandbox.process.exec("echo ready", timeout=5)
                    if result.exit_code == 0:
                        break
                except Exception:
                    pass
                time.sleep(2)
            else:
                # Cleanup on timeout
                try:
                    sandbox.delete()
                finally:
                    raise RuntimeError(
                        "Daytona sandbox failed to start within 180 seconds"
                    )
        
        return DaytonaBackend(sandbox)
    
    elif backend_type == "modal":
        raise ValueError(
            "Modal sandbox support coming soon. "
            "For now, use 'filesystem' type for local execution."
        )
    
    elif backend_type == "runloop":
        raise ValueError(
            "Runloop sandbox support coming soon. "
            "For now, use 'filesystem' type for local execution."
        )
    
    elif backend_type == "harbor":
        raise ValueError(
            "Harbor sandbox support coming soon. "
            "For now, use 'filesystem' type for local execution."
        )
    
    else:
        raise ValueError(
            f"Unsupported sandbox type: {backend_type}. "
            f"Supported types: filesystem, modal, runloop, daytona, harbor"
        )

