# Runtime Layer

## Purpose

The Runtime Layer provides execution infrastructure for Core + Integration systems. It handles workers, scheduling, GPU resources, and sandboxing.

## Architecture Direction

```
core
  │
  ▼
integration
  │
  ▼
runtime
 ├── Registry
 ├── Scheduler
 ├── Workers
 ├── GPU
 └── Sandbox
```

## Dependency Direction

```
core → integration → runtime
```

**Rules:**
- Core MUST NOT depend on Runtime
- Integration MUST NOT depend on Runtime
- Runtime MAY depend on Core and Integration

## What Runtime Owns

| Package | Responsibility |
|---------|----------------|
| `runtime/registry` | Resource registration, worker registration, execution resource lookup |
| `runtime/scheduler` | Job scheduling, priority management, dependency resolution, execution ordering |
| `runtime/workers` | Worker lifecycle, worker state, execution worker pools |
| `runtime/gpu` | GPU discovery, GPU resources, memory tracking |
| `runtime/sandbox` | Isolated execution, process/container boundaries, security restrictions |

## What Runtime Does NOT Own

| Concern | Belongs To |
|---------|------------|
| Data models | `core/` |
| Cross-domain validation | `integration/` |
| Manga parsing | `tools/manga/` |
| Image processing | `tools/image/` |
| Audio processing | `tools/audio/` |
| AI/LLM | `agents/` |
| API endpoints | `apps/` |
| UI | `apps/frontend/` |

## Package Boundaries

### runtime/registry

**Future responsibility:**
- Runtime resource registration
- Worker registration
- Execution resource lookup

**Current status:** Architecture skeleton only.

### runtime/scheduler

**Future responsibility:**
- Job scheduling
- Priority management
- Dependency resolution
- Execution ordering

**Current status:** Architecture skeleton only.

### runtime/workers

**Future responsibility:**
- Worker lifecycle management
- Worker state tracking
- Execution worker pools

**Current status:** Architecture skeleton only.

### runtime/gpu

**Future responsibility:**
- GPU device discovery
- GPU resource management
- Memory tracking

**Current status:** Architecture skeleton only.

### runtime/sandbox

**Future responsibility:**
- Isolated execution environments
- Process/container boundaries
- Security restrictions

**Current status:** Architecture skeleton only.

## Exception Hierarchy

```
RuntimeError
├── RuntimeConfigurationError
├── RuntimeExecutionError
├── WorkerError
├── SchedulerError
├── GPUError
└── SandboxError
```

## Public API

```python
# Exceptions
from runtime import (
    RuntimeError,
    RuntimeConfigurationError,
    RuntimeExecutionError,
    WorkerError,
    SchedulerError,
    GPUError,
    SandboxError,
)
```

## Future Extension Points

1. **Worker pools**: Process/thread-based execution
2. **GPU allocation**: CUDA/ROCm/Metal device management
3. **Sandboxing**: Container/process isolation
4. **Scheduling**: Priority queues, dependency graphs
5. **Monitoring**: Resource usage, execution metrics

## Known Limitations

1. **No execution logic**: Skeleton only, no actual workers
2. **No GPU support**: No CUDA/ROCm/Metal integration
3. **No sandboxing**: No process/container isolation
4. **No scheduling**: No job queue implementation

## Implementation Status

| Package | Status |
|---------|--------|
| `runtime/registry` | ✅ Skeleton |
| `runtime/scheduler` | ✅ Skeleton |
| `runtime/workers` | ✅ Skeleton |
| `runtime/gpu` | ✅ Skeleton |
| `runtime/sandbox` | ✅ Skeleton |
| Exception hierarchy | ✅ Implemented |
| Tests | ✅ Basic tests |
| Documentation | ✅ This document |
