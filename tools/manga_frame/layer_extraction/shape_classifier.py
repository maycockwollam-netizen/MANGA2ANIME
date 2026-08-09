"""Shape-heuristic region classifier.

Classifies a detected region (via its ShapeFeatures + page context) into one
of three structural sub-categories, then maps it to the existing
LayerCategory contract:

    sub_category      -> LayerCategory       panel/speech_bubble/character_bleed
    --------------------------------------------------------------------
    panel             -> BACKGROUND          (panel_type: bordered|borderless)
    speech_bubble     -> EFFECT
    character_bleed   -> CHARACTER

The sub-category and shape features are stored in LayerMetadata.extra so the
existing downstream contract (layer_extraction_to_frame.py) is NOT changed.

Classification heuristics (V1):
    panel:
        Large region (>= min_panel_area_frac of page area) with a roughly
        rectangular shape (extent >= 0.82). If the contour touches the page
        border or another panel gutter, it is flagged borderless when the
        bounding box has no detectable enclosing border.
    speech_bubble:
        Small-to-medium region (area < panel threshold) with high
        circularity (>= 0.55) and a near-square aspect ratio (0.4 .. 2.5),
        extent in the ellipse range (< 0.92). These match manga speech
        balloons (ellipse/rounded shapes).
    character_bleed:
        A large region that does NOT satisfy panel rectangularity (extent <
        0.82) and/or is highly non-convex (solidity < 0.75), indicating an
        irregular character/object silhouette that spills across panel
        boundaries.

Confidence is a heuristic blend of how strongly the feature vector matches
the chosen category's prototype ranges.

This module does NOT:
- Load or decode images
- Run OpenCV contour detection (features are precomputed by features.py)
- Access GPU
- Depend on runtime.manga_frame internals
"""

from __future__ import annotations

from dataclasses import dataclass

from tools.manga_frame.layer_extraction import LayerCategory
from tools.manga_frame.layer_extraction.features import ShapeFeatures

# ---------------------------------------------------------------------------
# Sub-category labels (stored in LayerMetadata.extra under "sub_category").
# ---------------------------------------------------------------------------

PANEL = "panel"
SPEECH_BUBBLE = "speech_bubble"
CHARACTER_BLEED = "character_bleed"

SUB_CATEGORIES: tuple[str, ...] = (PANEL, SPEECH_BUBBLE, CHARACTER_BLEED)

# Panel type labels (stored in LayerMetadata.extra under "panel_type").
PANEL_BORDERED = "bordered"
PANEL_BORDERLESS = "borderless"

# ---------------------------------------------------------------------------
# Heuristic thresholds (tunable; tuned against Manga109-s validation set).
# ---------------------------------------------------------------------------

# Minimum panel area as a fraction of page area.
MIN_PANEL_AREA_FRAC = 0.05

# Panel rectangularity: extent >= this -> panel candidate.
PANEL_EXTENT_MIN = 0.82

# Speech bubble: circularity >= this.
BUBBLE_CIRCULARITY_MIN = 0.55

# Speech bubble: aspect ratio range.
BUBBLE_ASPECT_MIN = 0.4
BUBBLE_ASPECT_MAX = 2.5

# Speech bubble: extent below this (ellipse ~0.78, not full rectangle).
BUBBLE_EXTENT_MAX = 0.92

# Character bleed: solidity below this (non-convex irregular silhouette).
BLEED_SOLIDITY_MAX = 0.75

# Character bleed: extent below this (irregular shape).
BLEED_EXTENT_MAX = 0.82

# Large-region fraction: above this a region is "large" (panel/bleed scale).
LARGE_AREA_FRAC = 0.04


@dataclass(frozen=True)
class ClassificationResult:
    """Result of classifying a single region.

    Attributes:
        category: The LayerCategory to assign (BACKGROUND/EFFECT/CHARACTER).
        sub_category: One of PANEL / SPEECH_BUBBLE / CHARACTER_BLEED.
        confidence: Heuristic confidence in [0.0, 1.0].
        panel_type: PANEL_BORDERED / PANEL_BORDERLESS if sub_category is
            PANEL, else None.
        features: The ShapeFeatures used for classification.
    """

    category: LayerCategory
    sub_category: str
    confidence: float
    panel_type: str | None
    features: ShapeFeatures


def _clamp01(x: float) -> float:
    """Clamp a float to [0.0, 1.0]."""
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _panel_confidence(features: ShapeFeatures, borderless: bool) -> float:
    """Heuristic confidence for a panel classification.

    Higher extent (closer to 1.0) and larger area increase confidence.
    Borderless panels get a small penalty because the signal is weaker.
    """
    extent_score = _clamp01((features.extent - PANEL_EXTENT_MIN) / (1.0 - PANEL_EXTENT_MIN))
    area_score = _clamp01(features.area / 1.0)  # normalized externally is better; rough
    base = 0.6 + 0.3 * extent_score + 0.1 * _clamp01(area_score)
    if borderless:
        base -= 0.1
    return _clamp01(base)


def _bubble_confidence(features: ShapeFeatures) -> float:
    """Heuristic confidence for a speech-bubble classification.

    Higher circularity (closer to 1.0) and aspect ratio near 1.0 increase
    confidence. MSER text clusters reach circularity ~0.75, which yields a
    solid confidence (~0.76).
    """
    # Map circularity in [0.4, 1.0] -> [0, 1].
    circ_score = _clamp01((features.circularity - 0.4) / (1.0 - 0.4))
    aspect = features.aspect_ratio
    if aspect <= 0:
        aspect_score = 0.0
    else:
        aspect_score = _clamp01(1.0 - min(abs(aspect - 1.0) / 1.5, 1.0))
    return _clamp01(0.4 + 0.45 * circ_score + 0.15 * aspect_score)


def _bleed_confidence(features: ShapeFeatures) -> float:
    """Heuristic confidence for a character-bleed classification.

    Lower solidity and lower extent increase confidence (irregular silhouette).
    """
    solid_score = _clamp01((BLEED_SOLIDITY_MAX - features.solidity) / BLEED_SOLIDITY_MAX)
    extent_score = _clamp01((BLEED_EXTENT_MAX - features.extent) / BLEED_EXTENT_MAX)
    return _clamp01(0.5 + 0.25 * solid_score + 0.25 * extent_score)


def classify(
    features: ShapeFeatures,
    *,
    page_area: float,
    touches_border: bool = False,
    has_border: bool = True,
) -> ClassificationResult:
    """Classify a region into panel / speech_bubble / character_bleed.

    Args:
        features: ShapeFeatures of the contour.
        page_area: Total page area in pixels (width * height) for scale.
        touches_border: True if the contour touches the page edge (used to
            flag borderless panels / bleeds).
        has_border: True if a detectable enclosing border exists around the
            region (False -> borderless panel).

    Returns:
        ClassificationResult with category, sub_category, confidence, and
        panel_type.

    Raises:
        LayerExtractionClassificationError: If page_area is non-positive.
    """
    from tools.manga_frame.layer_extraction.exceptions import (
        LayerExtractionClassificationError,
    )

    if page_area <= 0:
        raise LayerExtractionClassificationError("page_area must be positive")

    area_frac = features.area / page_area
    is_large = area_frac >= LARGE_AREA_FRAC

    # 1. Panel: large + rectangular.
    if is_large and features.extent >= PANEL_EXTENT_MIN:
        borderless = (not has_border) or touches_border
        panel_type = PANEL_BORDERLESS if borderless else PANEL_BORDERED
        return ClassificationResult(
            category=LayerCategory.BACKGROUND,
            sub_category=PANEL,
            confidence=_panel_confidence(features, borderless),
            panel_type=panel_type,
            features=features,
        )

    # 2. Speech bubble: medium/small, high circularity, ellipse-like extent.
    #    Note: MSER text-cluster bboxes are rectangular (extent ~1.0) but
    #    have high circularity (~0.75) because the cluster shape is compact.
    #    Accept either (a) ellipse-like extent (<0.92) OR (b) high
    #    circularity (>=0.6) with near-square aspect.
    is_bubble_shape = (
        features.extent < BUBBLE_EXTENT_MAX
        or (
            features.circularity >= 0.6
            and 0.4 <= features.aspect_ratio <= 2.5
        )
    )
    if (
        is_bubble_shape
        and features.circularity >= 0.4
        and 0.3 <= features.aspect_ratio <= 3.0
        and area_frac < MIN_PANEL_AREA_FRAC
    ):
        return ClassificationResult(
            category=LayerCategory.EFFECT,
            sub_category=SPEECH_BUBBLE,
            confidence=_bubble_confidence(features),
            panel_type=None,
            features=features,
        )

    # 3. Character bleed: large irregular region (low solidity / extent).
    if is_large and (
        features.solidity < BLEED_SOLIDITY_MAX or features.extent < BLEED_EXTENT_MAX
    ):
        return ClassificationResult(
            category=LayerCategory.CHARACTER,
            sub_category=CHARACTER_BLEED,
            confidence=_bleed_confidence(features),
            panel_type=None,
            features=features,
        )

    # Fallback: small irregular blob -> treat as speech bubble candidate
    # (manga often has non-circular bubbles). Low confidence.
    if not is_large:
        return ClassificationResult(
            category=LayerCategory.EFFECT,
            sub_category=SPEECH_BUBBLE,
            confidence=0.35,
            panel_type=None,
            features=features,
        )

    # Large but ambiguous -> character bleed (conservative).
    return ClassificationResult(
        category=LayerCategory.CHARACTER,
        sub_category=CHARACTER_BLEED,
        confidence=0.3,
        panel_type=None,
        features=features,
    )
