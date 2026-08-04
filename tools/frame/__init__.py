"""Frame tools module.

V0 provides data contracts for frame/motion comic pipeline.
Does NOT implement rendering, animation execution, or AI processing.
"""

from tools.frame.exceptions import (
    FrameToolError,
    FrameTransformError,
    FrameTransitionError,
    FrameValidationError,
)
from tools.frame.models import (
    Frame,
    FrameLayer,
    FrameTransform,
    FrameTransition,
    LayerType,
)

__all__ = [
    # Models
    "Frame",
    "FrameLayer",
    "FrameTransform",
    "FrameTransition",
    "LayerType",
    # Exceptions
    "FrameToolError",
    "FrameValidationError",
    "FrameTransformError",
    "FrameTransitionError",
]
