"""Layer extraction CV exceptions.

Defines the error hierarchy for the computer-vision layer extraction
implementation. These exceptions provide a public vocabulary for error
handling in concrete extraction implementations.

This module does NOT:
- Define Pydantic contracts (those live in tools/manga_frame/layer_extraction/__init__.py)
- Load or decode images
- Perform image processing
"""

from __future__ import annotations

from tools.manga_frame.layer_extraction import LayerExtractionInput


class LayerExtractionError(Exception):
    """Base exception for layer extraction errors.

    All extraction-specific exceptions inherit from this class. Concrete
    extraction implementations should raise this or subclasses to indicate
    detection/classification failures.
    """

    pass


class LayerExtractionInputError(LayerExtractionError):
    """Error in extraction input.

    Raised when an extraction input is invalid (e.g. source path does not
    exist, page number inconsistent, unsupported image format).
    """

    pass


class LayerExtractionImageError(LayerExtractionError):
    """Error loading or decoding an image.

    Raised when the source image cannot be read or decoded (e.g. corrupt
    file, unsupported format, unreadable path).
    """

    pass


class LayerExtractionDetectionError(LayerExtractionError):
    """Error during region detection.

    Raised when the computer-vision detection pass fails (e.g. OpenCV
    contour detection fails, morphology operation fails).
    """

    pass


class LayerExtractionClassificationError(LayerExtractionError):
    """Error during region classification.

    Raised when the shape-heuristic classifier cannot assign a category to
    a detected region (e.g. degenerate contour with zero area).
    """

    pass


class LayerExtractionConfigError(LayerExtractionError):
    """Error in extraction configuration.

    Raised when an ExtractionConfig contains invalid or inconsistent
    parameters (e.g. min_confidence out of range, max_layers <= 0).
    """

    pass


def raise_for_input(input_contract: LayerExtractionInput) -> None:
    """Validate an extraction input's source path existence.

    Args:
        input_contract: The extraction input to validate.

    Raises:
        LayerExtractionInputError: If the source path does not exist.
    """
    if not input_contract.source_path.exists():
        raise LayerExtractionInputError(
            f"source image not found: {input_contract.source_path}"
        )
