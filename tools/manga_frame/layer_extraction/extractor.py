"""Concrete layer extractor (computer-vision implementation).

Combines the OpenCV region detector (cv_detector.py) with the shape-heuristic
classifier (shape_classifier.py) to produce a LayerExtractionResult that
satisfies the existing contract in tools/manga_frame/layer_extraction/__init__.py.

The extractor maps detected regions onto the existing LayerCategory contract
WITHOUT changing any contract field or type:

    sub_category      -> LayerCategory       layer_id prefix
    ---------------------------------------------------------
    panel             -> BACKGROUND          "panel"
    speech_bubble     -> EFFECT              "speech_bubble"
    character_bleed   -> CHARACTER           "character_bleed"

Sub-category and shape features are stored in LayerMetadata.extra as an
immutable sorted tuple of (key, str(value)) pairs, so the downstream
layer_extraction_to_frame.py contract is unchanged.

This module does NOT:
- Define Pydantic contracts (those live in __init__.py)
- Access GPU
- Depend on runtime.manga_frame internals
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from tools.manga_frame.layer_extraction import (
    ExtractionConfig,
    ExtractionStatus,
    LayerCategory,
    LayerDescriptor,
    LayerExtractionInput,
    LayerExtractionResult,
    LayerMetadata,
)
from tools.manga_frame.layer_extraction.cv_detector import (
    detect_regions_from_path,
)
from tools.manga_frame.layer_extraction.exceptions import (
    LayerExtractionConfigError,
    LayerExtractionError,
    LayerExtractionImageError,
    raise_for_input,
)
from tools.manga_frame.layer_extraction.shape_classifier import (
    ClassificationResult,
    classify,
)

if TYPE_CHECKING:
    pass


def _build_metadata(
    result: ClassificationResult,
) -> LayerMetadata:
    """Build LayerMetadata from a classification result.

    Stores confidence, region_bounds, and shape features in extra.
    """
    fx = result.features
    x, y, w, h = fx.bbox
    extra: dict[str, str] = {
        "sub_category": result.sub_category,
        "extent": f"{fx.extent:.4f}",
        "circularity": f"{fx.circularity:.4f}",
        "aspect_ratio": f"{fx.aspect_ratio:.4f}",
        "solidity": f"{fx.solidity:.4f}",
        "area": f"{fx.area:.0f}",
    }
    if result.panel_type is not None:
        extra["panel_type"] = result.panel_type
    return LayerMetadata(
        confidence=result.confidence,
        region_bounds=(x, y, w, h),
        extra=extra,
    )


def _layer_id_for(result: ClassificationResult, index: int) -> str:
    """Generate a semantic layer_id for a classified region.

    Args:
        result: Classification result.
        index: Unique numeric index for uniqueness within the result.

    Returns:
        A layer_id string like "panel_0", "speech_bubble_1".
    """
    return f"{result.sub_category}_{index}"


class ConcreteLayerExtractor:
    """Computer-vision layer extractor.

    Loads a manga page image, detects regions with OpenCV, classifies them
    with shape heuristics, and produces a LayerExtractionResult conforming
    to the existing contract.

    Example:
        >>> from tools.manga_frame.layer_extraction import LayerExtractionInput
        >>> from tools.manga_frame.layer_extraction.extractor import ConcreteLayerExtractor
        >>> # extractor = ConcreteLayerExtractor()
        >>> # result = extractor.extract(LayerExtractionInput(source_path=..., page_number=0))
    """

    def extract(self, input_contract: LayerExtractionInput) -> LayerExtractionResult:
        """Extract layers from a manga page.

        Args:
            input_contract: Input contract with source_path and page_number.

        Returns:
            LayerExtractionResult with detected + classified layers.

        Raises:
            LayerExtractionInputError: If the source path does not exist.
            LayerExtractionImageError: If the image cannot be decoded.
            LayerExtractionConfigError: If the config is invalid.
            LayerExtractionError: For other detection/classification failures.
        """
        raise_for_input(input_contract)

        config = input_contract.config or ExtractionConfig()
        self._validate_config(config)

        try:
            regions = detect_regions_from_path(
                input_contract.source_path,
                min_panel_area_frac=0.05,
                min_bubble_area_frac=0.002,
                white_thresh=0.9,
            )
        except LayerExtractionImageError:
            raise
        except LayerExtractionError:
            raise
        except Exception as e:  # OpenCV/runtime errors.
            raise LayerExtractionError(
                f"region detection failed for {input_contract.source_path}: {e}"
            ) from e

        page_area = self._page_area(input_contract.source_path)

        layers: list[LayerDescriptor] = []
        for idx, region in enumerate(regions):
            classification = classify(
                region.features,
                page_area=page_area,
                touches_border=region.touches_border,
                has_border=region.has_border,
            )

            # Apply min_confidence filter.
            if classification.confidence < config.min_confidence:
                continue

            # Skip effects (speech bubbles) if disabled.
            if (
                classification.category == LayerCategory.EFFECT
                and not config.include_effects
            ):
                continue

            metadata = _build_metadata(classification)
            layer = LayerDescriptor(
                layer_id=_layer_id_for(classification, idx),
                category=classification.category,
                layer_index=idx,
                source_path=None,
                metadata=metadata,
            )
            layers.append(layer)

        # Apply max_layers cap (keep lowest layer_index first).
        if config.max_layers is not None and len(layers) > config.max_layers:
            layers = layers[: config.max_layers]

        status = (
            ExtractionStatus.SUCCESS
            if layers
            else ExtractionStatus.PARTIAL
        )

        return LayerExtractionResult(
            source_path=input_contract.source_path,
            page_number=input_contract.page_number,
            layers=tuple(layers),
            status=status,
            frame_reference=input_contract.frame_reference,
            metadata=None,
            sequence_id=input_contract.sequence_id,
        )

    @staticmethod
    def _validate_config(config: ExtractionConfig) -> None:
        """Validate an ExtractionConfig's CV-relevant parameters.

        Args:
            config: The config to validate.

        Raises:
            LayerExtractionConfigError: If config is internally inconsistent.
        """
        # ExtractionConfig already validates ranges via Pydantic; this hook
        # exists for CV-specific cross-field checks if needed later.
        if config.max_layers is not None and config.max_layers < 1:
            raise LayerExtractionConfigError(
                f"max_layers must be >= 1, got {config.max_layers}"
            )

    @staticmethod
    def _page_area(source_path: Path) -> float:
        """Compute page area (width * height) in pixels.

        Args:
            source_path: Path to the image.

        Returns:
            Page area in pixels.

        Raises:
            LayerExtractionImageError: If the image cannot be decoded.
        """
        from tools.manga_frame.layer_extraction.cv_detector import load_grayscale

        gray = load_grayscale(source_path)
        h, w = gray.shape[:2]
        return float(w * h)


def extract_layers(input_contract: LayerExtractionInput) -> LayerExtractionResult:
    """Module-level convenience wrapper around ConcreteLayerExtractor.extract.

    Args:
        input_contract: Input contract with source_path and page_number.

    Returns:
        LayerExtractionResult.
    """
    return ConcreteLayerExtractor().extract(input_contract)
