"""VFX exceptions.

Defines the error hierarchy for visual effect implementations.
These exceptions provide a public vocabulary for error handling
in concrete VFX effect implementations.
"""


class VfxError(Exception):
    """Base exception for VFX errors.

    All VFX-specific exceptions inherit from this class.
    Concrete VFX effect implementations should raise this or subclasses
    to indicate effect application failures.
    """

    pass


class VfxConfigError(VfxError):
    """Error in VFX effect configuration.

    Raised when a VFX effect receives an invalid or inconsistent configuration
    (e.g. negative line count, out-of-range intensity).
    """

    pass


class VfxRenderError(VfxError):
    """Error applying a VFX effect to an image.

    Raised when a concrete VFX effect fails to render onto its target canvas
    (e.g. invalid image mode, unsupported dimensions).
    """

    pass
