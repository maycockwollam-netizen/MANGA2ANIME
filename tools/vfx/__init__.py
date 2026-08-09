"""VFX Integration Contract.

Defines the minimal contract for visual effects applied to rendered frames.
This module specifies what data a VFX effect consumes and produces, without
knowing how the effect is rendered.

This module does NOT:
- Implement effect rendering (delegated to concrete_effect.py)
- Access GPU
- Execute animation logic
- Depend on runtime.animation internals

Architecture:
    tools/vfx/models.py (SpeedLinesConfig, VfxResult)
            ↓
    tools/vfx/protocol.py (VfxEffect Protocol)
            ↓
    tools/vfx/adapter.py (EffectAdapter)
            ↓
    [Concrete Effect Implementations]

Dependency Constraints:
    The VfxEffect protocol and its models must NOT depend on:
    - runtime.animation (ANY module)
    - AnimationRuntime internals
    - AnimationTimeline / AnimationClip
    - tools.manga_frame
"""

from __future__ import annotations

# VFX Effect Adapter - must be imported after protocol
from tools.vfx.adapter import EffectAdapter as EffectAdapter  # noqa: E402

# Concrete VFX Effect - must be imported after protocol
from tools.vfx.concrete_effect import SpeedLinesEffect as SpeedLinesEffect  # noqa: E402

# VFX Exceptions - must be imported after models
from tools.vfx.exceptions import (  # noqa: E402
    VfxConfigError,
    VfxError,
    VfxRenderError,
)

# VFX Models - must be imported first
from tools.vfx.models import (
    SpeedLineDirection,
    SpeedLinesConfig,
    VfxResult,
)

# VFX Effect Protocol - must be imported after models
from tools.vfx.protocol import VfxEffect as VfxEffect  # noqa: E402

__all__ = [
    # Core data contracts
    "SpeedLinesConfig",
    "SpeedLineDirection",
    "VfxResult",
    # VFX effect protocol
    "VfxEffect",
    # VFX effect adapter
    "EffectAdapter",
    # Concrete VFX effect
    "SpeedLinesEffect",
    # VFX errors
    "VfxError",
    "VfxConfigError",
    "VfxRenderError",
]
