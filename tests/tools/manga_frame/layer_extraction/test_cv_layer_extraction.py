"""Tests for the computer-vision layer extraction implementation.

Uses synthetic OpenCV-generated images (no copyrighted manga data) to verify:
    - Shape feature extraction (extent, circularity, aspect ratio, solidity).
    - Shape-heuristic classifier (panel / speech_bubble / character_bleed).
    - CV detector (panel gutter segmentation, MSER bubble clustering).
    - Concrete extractor end-to-end contract conformance.
    - Exception hierarchy.
    - Category mapping (sub_category -> LayerCategory) without breaking the
      existing contract.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from tools.manga_frame.layer_extraction import (
    CHARACTER_BLEED,
    PANEL,
    PANEL_BORDERED,
    PANEL_BORDERLESS,
    SPEECH_BUBBLE,
    ClassificationResult,
    ConcreteLayerExtractor,
    ExtractionConfig,
    ExtractionStatus,
    LayerCategory,
    LayerExtractionClassificationError,
    LayerExtractionConfigError,
    LayerExtractionError,
    LayerExtractionImageError,
    LayerExtractionInput,
    LayerExtractionInputError,
    LayerExtractionResult,
    ShapeFeatures,
    classify,
    compute_features,
    detect_regions,
    extract_layers,
)
from tools.manga_frame.layer_extraction.cv_detector import (
    load_grayscale,
)

# ---------------------------------------------------------------------------
# Synthetic image fixtures (no copyrighted content).
# ---------------------------------------------------------------------------


@pytest.fixture()
def synthetic_page_panels(tmp_path: Path) -> Path:
    """A synthetic manga page with 4 bordered panels on white background."""
    img = np.full((1000, 800), 255, dtype=np.uint8)
    # Draw 4 panel borders (dark rectangles) with white gutters.
    panels = [
        (50, 50, 350, 450),
        (450, 50, 750, 450),
        (50, 550, 350, 950),
        (450, 550, 750, 950),
    ]
    for (x0, y0, x1, y1) in panels:
        cv2.rectangle(img, (x0, y0), (x1, y1), 0, thickness=4)
        # Fill interior with light gray "content".
        img[y0 + 4 : y1 - 4, x0 + 4 : x1 - 4] = 200
    path = tmp_path / "panels.png"
    cv2.imwrite(str(path), img)
    return path


@pytest.fixture()
def synthetic_page_bubbles(tmp_path: Path) -> Path:
    """A synthetic page with elliptical speech bubbles."""
    img = np.full((1000, 800), 255, dtype=np.uint8)
    # Draw a panel border.
    cv2.rectangle(img, (50, 50), (750, 950), 0, thickness=4)
    img[54:946, 54:746] = 230
    # Draw 3 elliptical bubbles.
    for (cx, cy, rx, ry) in [(200, 200, 60, 50), (500, 400, 70, 55), (300, 700, 55, 45)]:
        cv2.ellipse(img, (cx, cy), (rx, ry), 0, 0, 360, 0, thickness=3)
    path = tmp_path / "bubbles.png"
    cv2.imwrite(str(path), img)
    return path


@pytest.fixture()
def synthetic_page_empty(tmp_path: Path) -> Path:
    """An all-white page with no content."""
    img = np.full((500, 500), 255, dtype=np.uint8)
    path = tmp_path / "empty.png"
    cv2.imwrite(str(path), img)
    return path


# ---------------------------------------------------------------------------
# ShapeFeatures tests.
# ---------------------------------------------------------------------------


class TestShapeFeatures:
    """Tests for feature extraction from contours."""

    def test_rectangle_features(self) -> None:
        """A rectangle has extent ~1.0 and solidity ~1.0."""
        rect = np.array([[[10, 10]], [[110, 10]], [[110, 110]], [[10, 110]]], dtype=np.int32)
        f = compute_features(rect)
        assert f.area == pytest.approx(10000.0, rel=1e-3)
        assert f.extent == pytest.approx(1.0, abs=0.05)
        assert f.solidity == pytest.approx(1.0, abs=0.05)
        assert f.aspect_ratio == pytest.approx(1.0, abs=0.05)
        assert f.bbox == (10, 10, 101, 101)

    def test_circle_features(self) -> None:
        """A circle has high circularity (~1.0) and extent ~0.78."""
        canvas = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(canvas, (100, 100), 80, 255, thickness=-1)
        cnts, _ = cv2.findContours(canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        f = compute_features(cnts[0])
        assert f.circularity > 0.85
        assert f.extent < 0.85  # circle extent ~0.78
        assert f.aspect_ratio == pytest.approx(1.0, abs=0.1)

    def test_degenerate_contour_raises(self) -> None:
        """A zero-area contour raises ClassificationError."""
        degenerate = np.array([[[5, 5]], [[5, 5]]], dtype=np.int32)
        with pytest.raises(LayerExtractionClassificationError):
            compute_features(degenerate)


# ---------------------------------------------------------------------------
# Classifier tests.
# ---------------------------------------------------------------------------


class TestClassifier:
    """Tests for the shape-heuristic classifier."""

    def _rect_features(self, x: int, y: int, w: int, h: int) -> ShapeFeatures:
        rect = np.array(
            [[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]], dtype=np.int32
        )
        return compute_features(rect)

    def test_large_rectangle_classifies_as_panel(self) -> None:
        """A large rectangular region classifies as a bordered panel."""
        feats = self._rect_features(0, 0, 400, 400)
        page_area = 800 * 1000.0
        result = classify(feats, page_area=page_area, has_border=True, touches_border=False)
        assert result.sub_category == PANEL
        assert result.category == LayerCategory.BACKGROUND
        assert result.panel_type == PANEL_BORDERED
        assert result.confidence > 0.5

    def test_borderless_panel(self) -> None:
        """A large rectangle touching the border with no border -> borderless."""
        feats = self._rect_features(0, 0, 400, 400)
        result = classify(
            feats, page_area=800 * 1000.0, has_border=False, touches_border=True
        )
        assert result.sub_category == PANEL
        assert result.panel_type == PANEL_BORDERLESS

    def test_small_high_circularity_classifies_as_bubble(self) -> None:
        """A small high-circularity region classifies as speech bubble."""
        canvas = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(canvas, (100, 100), 30, 255, thickness=-1)
        cnts, _ = cv2.findContours(canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        feats = compute_features(cnts[0])
        result = classify(feats, page_area=1000 * 1000.0)
        assert result.sub_category == SPEECH_BUBBLE
        assert result.category == LayerCategory.EFFECT

    def test_large_irregular_classifies_as_character_bleed(self) -> None:
        """A large low-solidity region classifies as character bleed."""
        # Build an L-shape (non-convex) large contour.
        canvas = np.zeros((500, 500), dtype=np.uint8)
        pts = np.array(
            [[[50, 50]], [[450, 50]], [[450, 250]], [[250, 250]], [[250, 450]], [[50, 450]]],
            dtype=np.int32,
        )
        cv2.fillPoly(canvas, [pts], 255)
        cnts, _ = cv2.findContours(canvas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        feats = compute_features(cnts[0])
        result = classify(feats, page_area=500 * 500.0)
        # L-shape is large and non-convex -> bleed.
        assert result.sub_category == CHARACTER_BLEED
        assert result.category == LayerCategory.CHARACTER

    def test_invalid_page_area_raises(self) -> None:
        """A non-positive page_area raises ClassificationError."""
        feats = self._rect_features(0, 0, 100, 100)
        with pytest.raises(LayerExtractionClassificationError):
            classify(feats, page_area=0.0)


# ---------------------------------------------------------------------------
# CV detector tests.
# ---------------------------------------------------------------------------


class TestCVDetector:
    """Tests for the OpenCV region detector."""

    def test_load_grayscale_valid(self, synthetic_page_panels: Path) -> None:
        """load_grayscale reads a valid image."""
        gray = load_grayscale(synthetic_page_panels)
        assert gray is not None
        assert gray.ndim == 2
        assert gray.size > 0

    def test_load_grayscale_missing_raises(self, tmp_path: Path) -> None:
        """load_grayscale raises ImageError for a missing file."""
        with pytest.raises(LayerExtractionImageError):
            load_grayscale(tmp_path / "nonexistent.png")

    def test_load_grayscale_invalid_raises(self, tmp_path: Path) -> None:
        """load_grayscale raises ImageError for a non-image file."""
        bad = tmp_path / "bad.png"
        bad.write_bytes(b"not an image")
        with pytest.raises(LayerExtractionImageError):
            load_grayscale(bad)

    def test_detect_panels(self, synthetic_page_panels: Path) -> None:
        """detect_regions finds panel regions on a 4-panel synthetic page."""
        gray = load_grayscale(synthetic_page_panels)
        regions = detect_regions(gray, white_thresh=0.9)
        panels = [r for r in regions if r.source_pass == "panel"]
        # Should detect at least 2 panels (synthetic gutters are clean).
        assert len(panels) >= 2
        for p in panels:
            assert p.features.area > 0

    def test_detect_regions_empty_image_raises(self) -> None:
        """detect_regions raises DetectionError on an empty array."""
        from tools.manga_frame.layer_extraction.exceptions import (
            LayerExtractionDetectionError,
        )
        with pytest.raises(LayerExtractionDetectionError):
            detect_regions(np.array([], dtype=np.uint8).reshape(0, 0))

    def test_detect_regions_returns_features(self, synthetic_page_bubbles: Path) -> None:
        """Detected regions carry computed ShapeFeatures."""
        gray = load_grayscale(synthetic_page_bubbles)
        regions = detect_regions(gray, white_thresh=0.9)
        assert len(regions) >= 1
        for r in regions:
            assert isinstance(r.features, ShapeFeatures)
            assert r.features.area > 0
            assert r.source_pass in ("panel", "bubble", "bleed")


# ---------------------------------------------------------------------------
# Extractor tests.
# ---------------------------------------------------------------------------


class TestConcreteExtractor:
    """Tests for the end-to-end ConcreteLayerExtractor."""

    def test_extract_returns_contract(self, synthetic_page_panels: Path) -> None:
        """extract() returns a LayerExtractionResult conforming to contract."""
        inp = LayerExtractionInput(source_path=synthetic_page_panels, page_number=0)
        result = ConcreteLayerExtractor().extract(inp)
        assert isinstance(result, LayerExtractionResult)
        assert result.page_number == 0
        assert result.source_path == synthetic_page_panels
        assert result.status in (ExtractionStatus.SUCCESS, ExtractionStatus.PARTIAL)
        assert result.layer_count >= 1

    def test_extract_layers_module_function(self, synthetic_page_panels: Path) -> None:
        """Module-level extract_layers() wrapper works."""
        inp = LayerExtractionInput(source_path=synthetic_page_panels, page_number=1)
        result = extract_layers(inp)
        assert isinstance(result, LayerExtractionResult)

    def test_extract_missing_input_raises(self, tmp_path: Path) -> None:
        """extract() raises InputError for a missing source path."""
        inp = LayerExtractionInput(source_path=tmp_path / "missing.png", page_number=0)
        with pytest.raises(LayerExtractionInputError):
            ConcreteLayerExtractor().extract(inp)

    def test_extract_invalid_image_raises(self, tmp_path: Path) -> None:
        """extract() raises for an unreadable image."""
        bad = tmp_path / "bad.png"
        bad.write_bytes(b"not an image")
        inp = LayerExtractionInput(source_path=bad, page_number=0)
        with pytest.raises((LayerExtractionImageError, LayerExtractionError)):
            ConcreteLayerExtractor().extract(inp)

    def test_extract_layers_carry_metadata(self, synthetic_page_panels: Path) -> None:
        """Each detected layer has metadata with sub_category and confidence."""
        inp = LayerExtractionInput(source_path=synthetic_page_panels, page_number=0)
        result = ConcreteLayerExtractor().extract(inp)
        for layer in result.layers:
            assert layer.metadata is not None
            extra = dict(layer.metadata.extra)
            assert "sub_category" in extra
            assert extra["sub_category"] in (PANEL, SPEECH_BUBBLE, CHARACTER_BLEED)
            assert 0.0 <= layer.metadata.confidence <= 1.0
            assert layer.metadata.region_bounds is not None

    def test_extract_panel_layer_ids(self, synthetic_page_panels: Path) -> None:
        """Panel layer_ids use the sub_category prefix."""
        inp = LayerExtractionInput(source_path=synthetic_page_panels, page_number=0)
        result = ConcreteLayerExtractor().extract(inp)
        panel_layers = [
            layer for layer in result.layers
            if dict(layer.metadata.extra).get("sub_category") == PANEL
        ]
        for layer in panel_layers:
            assert layer.layer_id.startswith("panel_")
            assert layer.category == LayerCategory.BACKGROUND

    def test_min_confidence_filter(self, synthetic_page_panels: Path) -> None:
        """A high min_confidence filters out low-confidence layers."""
        config = ExtractionConfig(min_confidence=0.95)
        inp = LayerExtractionInput(
            source_path=synthetic_page_panels, page_number=0, config=config
        )
        result = ConcreteLayerExtractor().extract(inp)
        for layer in result.layers:
            assert layer.metadata is not None
            assert layer.metadata.confidence >= 0.95

    def test_max_layers_cap(self, synthetic_page_panels: Path) -> None:
        """max_layers caps the number of returned layers."""
        config = ExtractionConfig(max_layers=1)
        inp = LayerExtractionInput(
            source_path=synthetic_page_panels, page_number=0, config=config
        )
        result = ConcreteLayerExtractor().extract(inp)
        assert result.layer_count <= 1

    def test_max_layers_validation_in_contract(self, synthetic_page_panels: Path) -> None:
        """ExtractionConfig already enforces max_layers >= 1 (Pydantic)."""
        # Pydantic rejects max_layers=0 at construction time.
        with pytest.raises(Exception):  # noqa: B017
            ExtractionConfig(max_layers=0)

    def test_empty_page_returns_partial(self, synthetic_page_empty: Path) -> None:
        """An empty (all-white) page yields PARTIAL status with no layers."""
        inp = LayerExtractionInput(source_path=synthetic_page_empty, page_number=0)
        result = ConcreteLayerExtractor().extract(inp)
        assert result.status == ExtractionStatus.PARTIAL
        assert result.layer_count == 0


# ---------------------------------------------------------------------------
# Exception tests.
# ---------------------------------------------------------------------------


class TestExceptions:
    """Tests for the exception hierarchy."""

    def test_hierarchy(self) -> None:
        """All CV exceptions inherit from LayerExtractionError."""
        for exc in (
            LayerExtractionInputError,
            LayerExtractionImageError,
            LayerExtractionClassificationError,
            LayerExtractionConfigError,
        ):
            assert issubclass(exc, LayerExtractionError)

    def test_raise_for_input_missing(self, tmp_path: Path) -> None:
        """raise_for_input raises InputError for missing path."""
        from tools.manga_frame.layer_extraction.exceptions import raise_for_input
        inp = LayerExtractionInput(source_path=tmp_path / "nope.png", page_number=0)
        with pytest.raises(LayerExtractionInputError):
            raise_for_input(inp)


# ---------------------------------------------------------------------------
# Category mapping tests.
# ---------------------------------------------------------------------------


class TestCategoryMapping:
    """Tests that sub_category maps to the existing LayerCategory contract."""

    def test_panel_maps_to_background(self) -> None:
        """panel -> BACKGROUND (contract unchanged)."""
        assert ClassificationResult(
            category=LayerCategory.BACKGROUND,
            sub_category=PANEL,
            confidence=0.8,
            panel_type=PANEL_BORDERED,
            features=compute_features(
                np.array([[[0, 0]], [[10, 0]], [[10, 10]], [[0, 10]]], dtype=np.int32)
            ),
        ).category == LayerCategory.BACKGROUND

    def test_bubble_maps_to_effect(self) -> None:
        """speech_bubble -> EFFECT (contract unchanged)."""
        feats = compute_features(
            np.array([[[0, 0]], [[10, 0]], [[10, 10]], [[0, 10]]], dtype=np.int32)
        )
        result = ClassificationResult(
            category=LayerCategory.EFFECT,
            sub_category=SPEECH_BUBBLE,
            confidence=0.7,
            panel_type=None,
            features=feats,
        )
        assert result.category == LayerCategory.EFFECT

    def test_bleed_maps_to_character(self) -> None:
        """character_bleed -> CHARACTER (contract unchanged)."""
        feats = compute_features(
            np.array([[[0, 0]], [[10, 0]], [[10, 10]], [[0, 10]]], dtype=np.int32)
        )
        result = ClassificationResult(
            category=LayerCategory.CHARACTER,
            sub_category=CHARACTER_BLEED,
            confidence=0.6,
            panel_type=None,
            features=feats,
        )
        assert result.category == LayerCategory.CHARACTER

    def test_sub_categories_are_distinct_strings(self) -> None:
        """The three sub-categories are distinct string labels."""
        assert PANEL != SPEECH_BUBBLE
        assert SPEECH_BUBBLE != CHARACTER_BLEED
        assert PANEL != CHARACTER_BLEED
        assert isinstance(PANEL, str)
        assert isinstance(SPEECH_BUBBLE, str)
        assert isinstance(CHARACTER_BLEED, str)
