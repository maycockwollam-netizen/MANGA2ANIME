"""Camera Animation Integration Contract.

Defines the minimal contract for camera animation evaluation. This module
specifies what data a camera animator consumes and produces, without knowing
how interpolation is performed or which rendering backend is used.

This module does NOT:
- Implement interpolation (delegated to concrete_animator.py / interpolation.py)
- Access GPU
- Execute animation logic
- Depend on runtime.animation internals

Architecture:
    tools/animation/models.py (CameraKeyframe, AnimationConfig, EasingType)
            ↓
    tools/animation/interpolation.py (linear / ease_in_out easing, lerp)
            ↓
    tools/animation/protocol.py (CameraAnimator Protocol)
            ↓
    tools/animation/adapter.py (SourceAdapter)
            ↓
    [Concrete Animator Implementations]

Dependency Constraints:
    The CameraAnimator protocol and its models must NOT depend on:
    - runtime.animation (ANY module)
    - AnimationRuntime internals
    - AnimationTimeline / AnimationClip
    - tools.manga_frame
"""

from __future__ import annotations

from tools.animation.adapter import SourceAdapter as SourceAdapter  # noqa: E402
from tools.animation.concrete_animator import (  # noqa: E402
    KeyframeAnimator as KeyframeAnimator,
)
from tools.animation.exceptions import (  # noqa: E402
    AnimationConfigError,
    AnimationError,
    AnimationEvalError,
    AnimationKeyframeError,
)
from tools.animation.interpolation import (  # noqa: E402
    ease_in_out_easing,
    get_easing,
    interpolate_keyframes,
    linear_easing,
    to_frame_transform,
)
from tools.animation.models import (  # noqa: E402
    AnimationConfig,
    CameraKeyframe,
    EasingType,
)
from tools.animation.protocol import CameraAnimator as CameraAnimator  # noqa: E402

__all__ = [
    # Core data contracts
    "CameraKeyframe",
    "AnimationConfig",
    "EasingType",
    # Easing / interpolation
    "linear_easing",
    "ease_in_out_easing",
    "get_easing",
    "interpolate_keyframes",
    "to_frame_transform",
    # Camera animator protocol
    "CameraAnimator",
    # Camera animator adapter
    "SourceAdapter",
    # Concrete camera animator
    "KeyframeAnimator",
    # Animation errors
    "AnimationError",
    "AnimationConfigError",
    "AnimationKeyframeError",
    "AnimationEvalError",
]
