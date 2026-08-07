"""Renderer exceptions.

Defines the error hierarchy for renderer implementations.
These exceptions provide a public vocabulary for error handling
in concrete renderer implementations.
"""


class RendererError(Exception):
    """Base exception for renderer errors.

    All renderer-specific exceptions inherit from this class.
    Concrete renderer implementations should raise this or subclasses
    to indicate rendering failures.
    """

    pass


class RenderFrameError(RendererError):
    """Error consuming RenderFrame.

    Raised when a renderer encounters invalid or unexpected RenderFrame data.
    """

    pass


class TransformError(RendererError):
    """Error applying a transform.

    Raised when a renderer fails to apply a FrameTransform to an entity.
    """

    pass
