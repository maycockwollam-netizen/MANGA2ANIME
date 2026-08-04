"""Frame tools module V1.

Provides data contracts for the frame/animation pipeline.
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
    FrameSequence,
    FrameTransform,
    FrameTransition,
    InterpolationType,
    LayerType,
    TransitionType,
)

__all__ = [
    # Models
    "Frame",
    "FrameLayer",
    "FrameSequence",
    "FrameTransform",
    "FrameTransition",
    # Enums
    "InterpolationType",
    "LayerType",
    "TransitionType",
    # Exceptions
    "FrameToolError",
    "FrameValidationError",
    "FrameTransformError",
    "FrameTransitionError",
]
