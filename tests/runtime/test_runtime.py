"""Tests for runtime skeleton."""

import pytest

from runtime import (
    GPUError,
    RuntimeConfigurationError,
    RuntimeError,
    RuntimeExecutionError,
    SandboxError,
    SchedulerError,
    WorkerError,
)


class TestRuntimeExceptions:
    """Tests for runtime exception hierarchy."""

    def test_runtime_error_base(self) -> None:
        """Test RuntimeError is base exception."""
        with pytest.raises(RuntimeError):
            raise RuntimeError("test")

    def test_runtime_configuration_error_inherits(self) -> None:
        """Test RuntimeConfigurationError inherits from RuntimeError."""
        with pytest.raises(RuntimeError):
            raise RuntimeConfigurationError("test")

    def test_runtime_execution_error_inherits(self) -> None:
        """Test RuntimeExecutionError inherits from RuntimeError."""
        with pytest.raises(RuntimeError):
            raise RuntimeExecutionError("test")

    def test_worker_error_inherits(self) -> None:
        """Test WorkerError inherits from RuntimeError."""
        with pytest.raises(RuntimeError):
            raise WorkerError("test")

    def test_scheduler_error_inherits(self) -> None:
        """Test SchedulerError inherits from RuntimeError."""
        with pytest.raises(RuntimeError):
            raise SchedulerError("test")

    def test_gpu_error_inherits(self) -> None:
        """Test GPUError inherits from RuntimeError."""
        with pytest.raises(RuntimeError):
            raise GPUError("test")

    def test_sandbox_error_inherits(self) -> None:
        """Test SandboxError inherits from RuntimeError."""
        with pytest.raises(RuntimeError):
            raise SandboxError("test")


class TestRuntimeImports:
    """Tests for runtime package imports."""

    def test_import_runtime(self) -> None:
        """Test runtime package imports."""
        import runtime
        assert hasattr(runtime, "RuntimeError")

    def test_import_registry(self) -> None:
        """Test runtime.registry package imports."""
        import runtime.registry
        assert runtime.registry is not None

    def test_import_scheduler(self) -> None:
        """Test runtime.scheduler package imports."""
        import runtime.scheduler
        assert runtime.scheduler is not None

    def test_import_workers(self) -> None:
        """Test runtime.workers package imports."""
        import runtime.workers
        assert runtime.workers is not None

    def test_import_gpu(self) -> None:
        """Test runtime.gpu package imports."""
        import runtime.gpu
        assert runtime.gpu is not None

    def test_import_sandbox(self) -> None:
        """Test runtime.sandbox package imports."""
        import runtime.sandbox
        assert runtime.sandbox is not None


class TestDependencyRules:
    """Tests verifying dependency rules."""

    def test_core_does_not_import_runtime(self) -> None:
        """Verify Core modules do not import Runtime."""
        from pathlib import Path

        core_dir = Path("core")
        for py_file in core_dir.rglob("*.py"):
            content = py_file.read_text()
            assert "from runtime" not in content
            assert "import runtime" not in content

    def test_integration_does_not_import_runtime(self) -> None:
        """Verify Integration does not import Runtime."""
        from pathlib import Path

        integration_dir = Path("integration")
        for py_file in integration_dir.rglob("*.py"):
            content = py_file.read_text()
            assert "from runtime" not in content
            assert "import runtime" not in content

    def test_runtime_can_import_integration(self) -> None:
        """Verify Runtime can import Integration (future use)."""
        # This is allowed - runtime will eventually use integration
        import runtime
        assert runtime is not None
