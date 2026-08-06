"""Layer Extraction to Frame integration contracts.

This module defines the integration boundary between layer extraction contracts
and frame data structures.

IMPORTANT: This is a CONTRACT TRANSFORMATION module, not an implementation.
It does not perform actual layer extraction, image processing, or AI/ML inference.

Architecture:
    tools/manga/  -->  tools/manga_frame/
                            ├── layer_extraction/  -->  layer_extraction_to_frame/
                            │                                         ↓
                            ├── character_tracking/  -->  character_frame/  -->  tools/frame/
                            └── manga_frame/                              ↓
                                                                       tools/frame/

The contracts define:
- Input contracts for mapping layer extraction results into frame structures
- Output contracts with conversion metadata
- Explicit handling of LayerCategory.UNKNOWN

This module does NOT:
- Perform layer extraction
- Load or decode images
- Perform image processing
- Run AI/ML inference
- Access GPU
- Access network
- Generate random values
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field, field_validator

from tools.frame.models import Frame, FrameLayer, FrameSequence, LayerType
from tools.manga_frame.layer_extraction import (
    LayerCategory,
    LayerDescriptor,
    LayerExtractionResult,
)

# ============================================================================
# Category Mapping
# ============================================================================

# Mapping from LayerCategory to LayerType
# UNKNOWN has no valid mapping to LayerType
_CATEGORY_TO_TYPE: dict[LayerCategory, LayerType] = {
    LayerCategory.BACKGROUND: LayerType.BACKGROUND,
    LayerCategory.CHARACTER: LayerType.CHARACTER,
    LayerCategory.FOREGROUND: LayerType.FOREGROUND,
    LayerCategory.EFFECT: LayerType.EFFECT,
}


class UnknownLayerCategoryError(ValueError):
    """Raised when LayerCategory.UNKNOWN is encountered during conversion.

    LayerCategory.UNKNOWN cannot be automatically converted to LayerType
    because LayerType does not have an UNKNOWN value.

    This error indicates that the caller must decide how to handle the
    ambiguous/unknown layer category before conversion can proceed.
    """

    def __init__(self, layer_id: str) -> None:
        self.layer_id = layer_id
        super().__init__(
            f"LayerCategory.UNKNOWN cannot be converted to LayerType for layer_id='{layer_id}'. "
            "Either filter out unknown layers before conversion or explicitly map them to a "
            "valid LayerType (e.g., LayerType.BACKGROUND)."
        )


# ============================================================================
# Conversion Metadata
# ============================================================================


class LayerExtractionToFrameMetadata(BaseModel):
    """Metadata for layer extraction to frame conversion.

    This contract stores information about the conversion operation
    without modifying the original LayerExtractionResult structures.

    Attributes:
        pages_converted: Number of pages (LayerExtractionResults) converted to frames
        layers_converted: Total number of layers successfully converted
        layers_filtered: Number of layers filtered out (e.g., due to unknown category)
        pages_failed: Number of pages that failed conversion
    """

    model_config = {"frozen": True}

    pages_converted: int = Field(
        ge=0,
        description="Number of pages converted to frames"
    )
    layers_converted: int = Field(
        ge=0,
        description="Total number of layers successfully converted"
    )
    layers_filtered: int = Field(
        ge=0,
        description="Number of layers filtered out during conversion"
    )
    pages_failed: int = Field(
        ge=0,
        description="Number of pages that failed conversion"
    )


# ============================================================================
# Input Contract
# ============================================================================


class LayerExtractionToFrameInput(BaseModel):
    """Input contract for mapping layer extraction results into frame structures.

    This contract represents the parameters needed to convert layer extraction
    results into a frame sequence.

    Attributes:
        extraction_results: Layer extraction results to convert (one per page)
        sequence_id: Unique identifier for the output FrameSequence
        name: Human-readable name for the sequence (optional)
        frame_rate: Target frame rate in FPS (default: 24.0)
        skip_unknown_categories: If True, skip layers with UNKNOWN category instead of erroring

    Note:
        - One LayerExtractionResult corresponds to one Frame
        - Layers are converted in order from bottom to top
        - The page_number from LayerExtractionResult maps to frame_index
    """

    extraction_results: tuple[LayerExtractionResult, ...] = Field(
        description="Layer extraction results to convert"
    )
    sequence_id: str = Field(
        min_length=1,
        description="Unique identifier for the output sequence"
    )
    name: str | None = Field(
        default=None,
        description="Human-readable sequence name"
    )
    frame_rate: float = Field(
        default=24.0,
        gt=0,
        le=120,
        description="Frame rate in FPS"
    )
    skip_unknown_categories: bool = Field(
        default=False,
        description="If True, skip layers with UNKNOWN category instead of raising error"
    )

    @field_validator("sequence_id", mode="before")
    @classmethod
    def validate_sequence_id(cls, v: str) -> str:
        """Validate sequence ID is non-empty and trimmed."""
        if not isinstance(v, str):
            raise ValueError(f"sequence_id must be string, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("sequence_id cannot be empty or whitespace-only")
        return stripped


# ============================================================================
# Output Contract
# ============================================================================


@dataclass(frozen=True)
class LayerExtractionToFrameOutput:
    """Output of layer extraction to frame conversion.

    Immutable result containing the converted FrameSequence and conversion metadata.

    Attributes:
        sequence: The converted FrameSequence
        metadata: Conversion metadata
        skipped_layers: Tuple of layer IDs that were skipped (due to UNKNOWN category)

    Invariants:
        - All frames are in frame_index order
        - All layers within frames are in layer_index order
        - No duplicate layer_index values within a frame
    """

    sequence: FrameSequence
    metadata: LayerExtractionToFrameMetadata
    skipped_layers: tuple[str, ...]


# ============================================================================
# Validation
# ============================================================================


class DuplicatePageNumberError(ValueError):
    """Raised when duplicate page_number values are detected in extraction results.

    Frame.frame_index must be unique within a FrameSequence.
    """

    def __init__(self, duplicated_pages: tuple[int, ...]) -> None:
        self.duplicated_pages = duplicated_pages
        pages_str = ", ".join(str(p) for p in duplicated_pages)
        super().__init__(
            f"Duplicate page_number values not allowed: [{pages_str}]. "
            "Each LayerExtractionResult must have a unique page_number "
            "to produce unique Frame.frame_index values."
        )


def _validate_unique_page_numbers(
    results: tuple[LayerExtractionResult, ...],
) -> None:
    """Validate that all page_number values are unique.

    Args:
        results: Extraction results to validate

    Raises:
        DuplicatePageNumberError: If any page_number values are duplicated
    """
    page_numbers = [r.page_number for r in results]
    seen: set[int] = set()
    duplicates: list[int] = []

    for page_num in page_numbers:
        if page_num in seen:
            duplicates.append(page_num)
        else:
            seen.add(page_num)

    if duplicates:
        raise DuplicatePageNumberError(tuple(sorted(set(duplicates))))


# ============================================================================
# Conversion Functions
# ============================================================================


def _convert_layer_descriptor(
    descriptor: LayerDescriptor,
    skip_unknown: bool,
) -> tuple[FrameLayer | None, bool]:
    """Convert a single LayerDescriptor to FrameLayer.

    Args:
        descriptor: The layer descriptor to convert
        skip_unknown: If True, skip UNKNOWN categories instead of erroring

    Returns:
        Tuple of (converted FrameLayer or None, was_skipped)
    """
    # Handle UNKNOWN category
    if descriptor.category == LayerCategory.UNKNOWN:
        if skip_unknown:
            return None, True
        raise UnknownLayerCategoryError(descriptor.layer_id)

    # Map category to type
    layer_type = _CATEGORY_TO_TYPE[descriptor.category]

    # Create FrameLayer
    frame_layer = FrameLayer(
        layer_id=descriptor.layer_id,
        layer_type=layer_type,
        layer_index=descriptor.layer_index,
        source_path=descriptor.source_path,
        visible=True,
    )

    return frame_layer, False


def _convert_layer_extraction_result(
    result: LayerExtractionResult,
    frame_index: int,
    skip_unknown: bool,
) -> tuple[Frame, list[str]]:
    """Convert a single LayerExtractionResult to Frame.

    Args:
        result: The layer extraction result to convert
        frame_index: The frame index to use
        skip_unknown: If True, skip UNKNOWN categories instead of erroring

    Returns:
        Tuple of (converted Frame, list of skipped layer IDs)
    """
    frame_layers: list[FrameLayer] = []
    skipped: list[str] = []

    for descriptor in result.layers:
        frame_layer, was_skipped = _convert_layer_descriptor(descriptor, skip_unknown)
        if frame_layer is not None:
            frame_layers.append(frame_layer)
        else:
            skipped.append(descriptor.layer_id)

    return Frame(
        frame_index=frame_index,
        layers=tuple(frame_layers),
        source_path=result.source_path,
    ), skipped


def convert_layer_extraction_to_frames(
    input_contract: LayerExtractionToFrameInput,
) -> LayerExtractionToFrameOutput:
    """Convert layer extraction results to frame sequence.

    This is the primary conversion function for the layer_extraction -> frame boundary.

    Mapping Rules:
    - LayerExtractionResult.page_number -> Frame.frame_index
    - LayerExtractionResult.source_path -> Frame.source_path
    - LayerDescriptor.layer_id -> FrameLayer.layer_id
    - LayerDescriptor.layer_index -> FrameLayer.layer_index
    - LayerDescriptor.category -> FrameLayer.layer_type (if not UNKNOWN)
    - LayerDescriptor.source_path -> FrameLayer.source_path

    UNKNOWN Category Handling:
    - If skip_unknown_categories=True, UNKNOWN layers are skipped
    - If skip_unknown_categories=False (default), raises UnknownLayerCategoryError
    - LayerType has no UNKNOWN value, so silent conversion is not allowed

    Information Preserved:
    - All layer metadata that maps to FrameLayer fields
    - Layer ordering (z-index via layer_index)
    - Source paths for frames and layers

    Information Not Representable:
    - LayerMetadata (confidence, region_bounds, extra)
    - ExtractionStatus
    - Frame reference and sequence ID from LayerExtractionResult

    Immutability:
    - Output FrameSequence is frozen
    - Frame.layers is tuple (immutable)
    - No side effects on input objects

    Determinism:
    - Same input produces same output
    - No random values
    - No timestamps
    - No environment-dependent values
    - Frames are sorted by frame_index

    Args:
        input_contract: Input contract with extraction results and configuration

    Returns:
        LayerExtractionToFrameOutput containing converted FrameSequence

    Raises:
        ValueError: If extraction_results is empty
        DuplicatePageNumberError: If page_number values are not unique
        UnknownLayerCategoryError: If UNKNOWN category encountered and skip is False
    """
    results = input_contract.extraction_results

    # Validate we have results to convert
    if not results:
        raise ValueError("Cannot convert empty extraction_results")

    # Validate unique page numbers
    _validate_unique_page_numbers(results)

    # Convert each result to a frame
    frames: list[Frame] = []
    total_layers = 0
    total_skipped = 0
    all_skipped: list[str] = []

    for result in results:
        # Use page_number as frame_index
        frame_index = result.page_number

        # Convert layers
        frame, skipped = _convert_layer_extraction_result(
            result,
            frame_index,
            input_contract.skip_unknown_categories,
        )
        frames.append(frame)
        total_layers += len(result.layers)
        total_skipped += len(skipped)
        all_skipped.extend(skipped)

    # Sort frames by frame_index for determinism
    frames.sort(key=lambda f: f.frame_index)

    # Create the frozen FrameSequence
    sequence = FrameSequence(
        sequence_id=input_contract.sequence_id,
        name=input_contract.name,
        frame_rate=input_contract.frame_rate,
        frames=tuple(frames),
        transitions=(),  # No transitions for layer extraction conversion
    )

    # Create metadata
    metadata = LayerExtractionToFrameMetadata(
        pages_converted=len(frames),
        layers_converted=total_layers - total_skipped,
        layers_filtered=total_skipped,
        pages_failed=0,
    )

    return LayerExtractionToFrameOutput(
        sequence=sequence,
        metadata=metadata,
        skipped_layers=tuple(all_skipped),
    )


# ============================================================================
# Factory Function
# ============================================================================


def create_frame_sequence_from_layer_extraction(
    extraction_results: tuple[LayerExtractionResult, ...] | list[LayerExtractionResult],
    sequence_id: str,
    *,
    name: str | None = None,
    frame_rate: float = 24.0,
    skip_unknown_categories: bool = False,
) -> FrameSequence:
    """Factory function to convert layer extraction results to frame sequence.

    Convenience wrapper around LayerExtractionToFrameInput + convert_layer_extraction_to_frames.

    Args:
        extraction_results: Layer extraction results to convert
        sequence_id: Unique identifier for the output sequence
        name: Human-readable name (optional)
        frame_rate: Target frame rate in FPS (default: 24.0)
        skip_unknown_categories: If True, skip UNKNOWN layers (default: False)

    Returns:
        Converted FrameSequence

    Raises:
        ValueError: If extraction_results is empty
        UnknownLayerCategoryError: If UNKNOWN category encountered and skip is False

    Example:
        >>> from tools.manga_frame.layer_extraction import LayerExtractionResult, LayerDescriptor, LayerCategory
        >>> result = LayerExtractionResult(
        ...     source_path=Path("/manga/page1.png"),
        ...     page_number=0,
        ...     layers=[
        ...         LayerDescriptor(layer_id="bg", category=LayerCategory.BACKGROUND, layer_index=0),
        ...         LayerDescriptor(layer_id="char", category=LayerCategory.CHARACTER, layer_index=1),
        ...     ],
        ... )
        >>> sequence = create_frame_sequence_from_layer_extraction(
        ...     extraction_results=[result],
        ...     sequence_id="page1_layers",
        ... )
    """
    # Normalize to tuple
    if isinstance(extraction_results, list):
        extraction_results = tuple(extraction_results)

    input_contract = LayerExtractionToFrameInput(
        extraction_results=extraction_results,
        sequence_id=sequence_id,
        name=name,
        frame_rate=frame_rate,
        skip_unknown_categories=skip_unknown_categories,
    )

    output = convert_layer_extraction_to_frames(input_contract)
    return output.sequence


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Models
    "LayerExtractionToFrameInput",
    "LayerExtractionToFrameMetadata",
    "LayerExtractionToFrameOutput",
    # Exceptions
    "DuplicatePageNumberError",
    "UnknownLayerCategoryError",
    # Functions
    "convert_layer_extraction_to_frames",
    "create_frame_sequence_from_layer_extraction",
]
