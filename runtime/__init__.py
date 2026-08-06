"""Runtime Layer.

Provides execution infrastructure for Core + Integration systems.
Handles workers, scheduling, GPU resources, sandboxing, and animation runtime.

Dependency direction:
    core → integration → runtime
"""

from runtime.exceptions import (
    GPUError,
    RuntimeConfigurationError,
    RuntimeError,
    RuntimeExecutionError,
    SandboxError,
    SchedulerError,
    WorkerError,
)

__all__ = [
    # Exceptions
    "RuntimeError",
    "RuntimeConfigurationError",
    "RuntimeExecutionError",
    "WorkerError",
    "SchedulerError",
    "GPUError",
    "SandboxError",
]
