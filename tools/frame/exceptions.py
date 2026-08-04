"""Frame tools exceptions."""


class FrameToolError(Exception):
    """Base exception for frame tool errors."""

    pass


class FrameValidationError(FrameToolError):
    """Raised when frame validation fails."""

    pass


class FrameTransformError(FrameToolError):
    """Raised when frame transform operations fail."""

    pass


class FrameTransitionError(FrameToolError):
    """Raised when frame transition operations fail."""

    pass


class FramePaletteError(FrameToolError):
    """Raised when frame palette operations fail."""

    pass
