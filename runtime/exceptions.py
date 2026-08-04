"""Runtime-level exceptions."""


class RuntimeError(Exception):
    """Base exception for runtime-related errors."""

    pass


class RuntimeConfigurationError(RuntimeError):
    """Raised when runtime configuration is invalid."""

    pass


class RuntimeExecutionError(RuntimeError):
    """Raised when runtime execution fails."""

    pass


class WorkerError(RuntimeError):
    """Raised when worker operation fails."""

    pass


class SchedulerError(RuntimeError):
    """Raised when scheduler operation fails."""

    pass


class GPUError(RuntimeError):
    """Raised when GPU operation fails."""

    pass


class SandboxError(RuntimeError):
    """Raised when sandbox operation fails."""

    pass
