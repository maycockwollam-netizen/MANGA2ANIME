"""Layer extraction contracts for manga to frame pipeline.

This module defines data contracts for manga page layer extraction.

IMPORTANT: Layer extraction implementation is intentionally not included in this
architecture version. This module only defines the contract boundary.

Architecture:
    tools/manga/  -->  tools/manga_frame/  -->  layer_extraction/  -->  tools/frame/
                                                                    (THIS MODULE)

The contracts define:
- Layer categories (BACKGROUND, CHARACTER, FOREGROUND, EFFECT, UNKNOWN)
- Layer descriptors with metadata
- Input contracts for future extraction implementations
- Output contracts for extraction results
- Status tracking for extraction operations

This module does NOT:
- Load or decode images
- Perform image processing
- Run AI/ML inference
- Access GPU
- Access network
- Generate random values
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

# ============================================================================
# Enums
# ============================================================================


class LayerCategory(StrEnum):
    """Categories for extracted layer types.

    These categories describe the structural type of a layer extracted from
    a manga page. They correspond to the visual role of the layer.

    Note: UNKNOWN is provided for cases where the category cannot be
    determined. Implementations should prefer specific categories when possible.
    """

    BACKGROUND = "background"
    CHARACTER = "character"
    FOREGROUND = "foreground"
    EFFECT = "effect"
    UNKNOWN = "unknown"


class ExtractionStatus(StrEnum):
    """Status of a layer extraction operation.

    These values indicate the state of an extraction operation, allowing
    callers to handle different outcomes appropriately.
    """

    NOT_PROCESSED = "not_processed"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


# ============================================================================
# Metadata Container
# ============================================================================


class LayerMetadata(BaseModel):
    """Immutable metadata container for layer extraction results.

    This is a frozen dataclass-style model that stores arbitrary metadata
    about an extracted layer. All metadata is immutable after construction.

    Note: This is a contract for metadata storage. The actual metadata
    content depends on the specific extraction implementation.
    """

    model_config = {"frozen": True}

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score for the extraction (0.0-1.0)"
    )
    region_bounds: tuple[int, int, int, int] | None = Field(
        default=None,
        description="Bounding box as (x, y, width, height)"
    )
    extra: tuple[tuple[str, str], ...] = Field(
        default_factory=tuple,
        description="Additional key-value metadata as immutable sorted tuple"
    )

    @field_validator("extra", mode="before")
    @classmethod
    def normalize_extra(
        cls,
        v: dict[str, str] | tuple[tuple[str, str], ...] | None
    ) -> tuple[tuple[str, str], ...]:
        """Convert dict to sorted tuple and validate."""
        if v is None:
            return ()
        if isinstance(v, tuple):
            return tuple(sorted(v))
        if isinstance(v, dict):
            return tuple(sorted(v.items()))
        return ()


# ============================================================================
# Layer Descriptor
# ============================================================================


class LayerDescriptor(BaseModel):
    """Represents metadata about one extracted layer.

    This is a data contract that describes a layer extracted from a manga page.
    It does NOT contain image data or pixel buffers.

    The descriptor captures:
    - Layer identification
    - Layer category
    - Layer ordering
    - Source reference
    - Extraction metadata

    Attributes:
        layer_id: Unique identifier for the layer
        category: Structural category of the layer
        layer_index: Z-order index for layer stacking
        source_path: Optional path to the layer source
        metadata: Optional extraction metadata

    Invariants:
        - layer_id must be non-empty after trimming
        - layer_index must be >= 0
        - No duplicate layer_index values in a LayerExtractionResult
    """

    layer_id: str = Field(
        min_length=1,
        description="Unique layer identifier"
    )
    category: LayerCategory = Field(
        default=LayerCategory.UNKNOWN,
        description="Structural category of the layer"
    )
    layer_index: int = Field(
        ge=0,
        description="Z-order index for layer stacking"
    )
    source_path: Path | None = Field(
        default=None,
        description="Path to layer source"
    )
    metadata: LayerMetadata | None = Field(
        default=None,
        description="Extraction metadata"
    )

    @field_validator("layer_id", mode="before")
    @classmethod
    def normalize_layer_id(cls, v: str) -> str:
        """Normalize layer ID to trimmed non-empty string."""
        if not isinstance(v, str):
            raise ValueError(f"layer_id must be string, got {type(v).__name__}")
        stripped = v.strip()
        if not stripped:
            raise ValueError("layer_id cannot be empty or whitespace-only")
        return stripped

    @field_validator("layer_index", mode="before")
    @classmethod
    def validate_layer_index(cls, v: int) -> int:
        """Validate layer index is non-negative integer."""
        if not isinstance(v, int):
            raise ValueError(f"layer_index must be int, got {type(v).__name__}")
        if v < 0:
            raise ValueError("layer_index cannot be negative")
        return v


# ============================================================================
# Extraction Configuration
# ============================================================================


class ExtractionConfig(BaseModel):
    """Configuration for layer extraction operations.

    This contract defines parameters that control how layer extraction
    is performed. The actual behavior depends on the implementation.

    Attributes:
        min_confidence: Minimum confidence threshold (0.0-1.0)
        include_effects: Whether to include effect layers
        max_layers: Maximum number of layers to extract (None = unlimited)
        detect_characters: Whether to detect character regions
    """

    min_confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )
    include_effects: bool = Field(
        default=True,
        description="Whether to include effect layers"
    )
    max_layers: int | None = Field(
        default=None,
        ge=1,
        description="Maximum layers to extract (None = unlimited)"
    )
    detect_characters: bool = Field(
        default=True,
        description="Whether to detect character regions"
    )


# ============================================================================
# Extraction Input
# ============================================================================


class LayerExtractionInput(BaseModel):
    """Input contract for layer extraction operations.

    This contract represents the parameters needed to perform layer extraction
    on a manga page. It contains REFERENCES and CONFIGURATION only.

    IMPORTANT: This contract does NOT load or inspect the actual image.
    Image loading is performed by the extraction implementation.

    Attributes:
        source_path: Path to the manga page image (required)
        page_number: Zero-based page number
        frame_reference: Optional reference to the frame this page maps to
        config: Optional extraction configuration
        sequence_id: Optional sequence identifier for context

    Invariants:
        - source_path must be provided
        - page_number must be >= 0
    """

    source_path: Path = Field(
        description="Path to the manga page image"
    )
    page_number: int = Field(
        ge=0,
        description="Zero-based page number"
    )
    frame_reference: str | None = Field(
        default=None,
        description="Optional frame reference"
    )
    config: ExtractionConfig | None = Field(
        default=None,
        description="Extraction configuration"
    )
    sequence_id: str | None = Field(
        default=None,
        description="Optional sequence identifier for context"
    )

    @field_validator("page_number", mode="before")
    @classmethod
    def validate_page_number(cls, v: int) -> int:
        """Validate page number is non-negative integer."""
        if not isinstance(v, int):
            raise ValueError(f"page_number must be int, got {type(v).__name__}")
        if v < 0:
            raise ValueError("page_number cannot be negative")
        return v


# ============================================================================
# Extraction Result
# ============================================================================


class LayerExtractionResult(BaseModel):
    """Result of a layer extraction operation.

    This contract represents the output of a layer extraction operation,
    containing all extracted layers and metadata about the operation.

    Deep Immutability:
    - This model is frozen/immutable
    - layers is stored as tuple (immutable collection)
    - No caller-owned state can affect the result

    Determinism:
    - Same input produces equivalent output
    - No timestamps, random values, or environment state

    Attributes:
        source_path: Path that was processed
        page_number: Page number that was processed
        layers: Tuple of extracted layer descriptors
        status: Extraction operation status
        frame_reference: Optional frame reference
        metadata: Optional result-level metadata
        sequence_id: Optional sequence identifier

    Invariants:
        - No duplicate layer_index values
        - Layers must be ordered by layer_index
        - layers is immutable tuple
    """

    model_config = {"frozen": True}

    source_path: Path = Field(
        description="Source path that was processed"
    )
    page_number: int = Field(
        ge=0,
        description="Page number that was processed"
    )
    layers: tuple[LayerDescriptor, ...] = Field(
        default_factory=tuple,
        description="Extracted layer descriptors"
    )
    status: ExtractionStatus = Field(
        default=ExtractionStatus.NOT_PROCESSED,
        description="Extraction operation status"
    )
    frame_reference: str | None = Field(
        default=None,
        description="Optional frame reference"
    )
    metadata: LayerMetadata | None = Field(
        default=None,
        description="Optional result-level metadata"
    )
    sequence_id: str | None = Field(
        default=None,
        description="Optional sequence identifier"
    )

    @field_validator("layers", mode="before")
    @classmethod
    def normalize_layers(
        cls,
        v: list[LayerDescriptor] | tuple[LayerDescriptor, ...] | None
    ) -> tuple[LayerDescriptor, ...]:
        """Convert layers list to tuple for immutability."""
        if v is None:
            return ()
        if isinstance(v, tuple):
            return v
        if isinstance(v, list):
            return tuple(v)
        return ()

    @model_validator(mode="after")
    def validate_layer_ordering(self) -> LayerExtractionResult:
        """Validate layers are ordered by layer_index without duplicates.

        Invariant: Layers must be provided in ascending order by layer_index.
        Duplicate layer_index values are rejected to prevent ambiguity.
        """
        if self.layers:
            indices = [layer.layer_index for layer in self.layers]
            if indices != sorted(indices):
                raise ValueError("layers must be ordered by layer_index")
            if len(indices) != len(set(indices)):
                raise ValueError("duplicate layer_index values are not allowed")
        return self

    @property
    def layer_count(self) -> int:
        """Get the number of extracted layers."""
        return len(self.layers)

    def get_layer_by_index(self, layer_index: int) -> LayerDescriptor | None:
        """Get layer descriptor by layer_index.

        Args:
            layer_index: The layer index to search for

        Returns:
            LayerDescriptor if found, None otherwise
        """
        for layer in self.layers:
            if layer.layer_index == layer_index:
                return layer
        return None

    def get_layers_by_category(
        self,
        category: LayerCategory
    ) -> tuple[LayerDescriptor, ...]:
        """Get all layers matching a category.

        Args:
            category: The category to filter by

        Returns:
            Tuple of matching layer descriptors
        """
        return tuple(layer for layer in self.layers if layer.category == category)


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    # Enums
    "LayerCategory",
    "ExtractionStatus",
    # Models
    "LayerMetadata",
    "LayerDescriptor",
    "ExtractionConfig",
    "LayerExtractionInput",
    "LayerExtractionResult",
]
