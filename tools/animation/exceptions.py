"""Animation exceptions.

Defines the error hierarchy for camera animation implementations.
These exceptions provide a public vocabulary for error handling
in concrete camera animator implementations.
"""


class AnimationError(Exception):
    """Base exception for animation errors.

    All animation-specific exceptions inherit from this class. Concrete
    animator implementations should raise this or subclasses to indicate
    evaluation failures.
    """

    pass


class AnimationConfigError(AnimationError):
    """Error in animation configuration.

    Raised when an animator receives an invalid or inconsistent configuration
    (e.g. keyframes out of order, invalid easing type).
    """

    pass


class AnimationKeyframeError(AnimationError):
    """Error interpreting a keyframe.

    Raised when a keyframe's timestamp is negative, out of order, or its
    parameters are inconsistent with the animation range.
    """

    pass


class AnimationEvalError(AnimationError):
    """Error during interpolation evaluation.

    Raised when the interpolation pass fails (e.g. evaluating a time outside
    the keyframe range, unsupported easing).
    """

    pass
