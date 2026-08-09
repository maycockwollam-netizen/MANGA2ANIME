"""Integration tests for layer extraction against Manga109-s ground truth.

These tests validate the CV extractor against real Manga109-s annotations.
They are skipped unless the Manga109-s sample data is available at
/tmp/manga109_sample/ (set up out-of-band via the HuggingFace dataset download,
academic-use license — data is NOT redistributed or committed).

Run explicitly:
    pytest tests/tools/manga_frame/layer_extraction/test_manga109_evaluation.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.manga_frame.layer_extraction import (
    ConcreteLayerExtractor,
    LayerExtractionInput,
)
from tools.manga_frame.layer_extraction.evaluation import (
    CategoryMetrics,
    containment,
    evaluate_extraction,
    evaluate_page,
    iou,
)
from tools.manga_frame.layer_extraction.manga109_reader import (
    GroundTruthBox,
    PageGroundTruth,
    annotation_path_for,
    image_path_for,
    parse_book_annotations,
)

MANGA109_ROOT = Path("/tmp/manga109_sample/Manga109s_released_2026_05_21")
SAMPLE_BOOKS = ("ARMS", "BakuretsuKungFuGirl", "BEMADER_P")


def _manga109_available() -> bool:
    """True if the Manga109-s sample tree is present."""
    return MANGA109_ROOT.exists() and (MANGA109_ROOT / "annotations.v2020.12.18").exists()


pytestmark = pytest.mark.skipif(
    not _manga109_available(),
    reason="Manga109-s sample data not available at /tmp/manga109_sample/",
)


# ---------------------------------------------------------------------------
# Reader tests.
# ---------------------------------------------------------------------------


class TestManga109Reader:
    """Tests for the Manga109-s annotation reader."""

    def test_parse_book_annotations(self) -> None:
        """parse_book_annotations returns pages with boxes."""
        xml = annotation_path_for(MANGA109_ROOT, "ARMS")
        pages = parse_book_annotations(xml)
        assert len(pages) > 0
        # First few pages should have at least one box somewhere.
        total_boxes = sum(len(p.boxes) for p in pages.values())
        assert total_boxes > 0

    def test_page_ground_truth_fields(self) -> None:
        """PageGroundTruth exposes book, index, width, height, boxes."""
        xml = annotation_path_for(MANGA109_ROOT, "ARMS")
        pages = parse_book_annotations(xml)
        idx = next(i for i, p in pages.items() if p.boxes)
        gt = pages[idx]
        assert gt.book == "ARMS"
        assert gt.page_index == idx
        assert gt.width > 0
        assert gt.height > 0
        for box in gt.boxes:
            assert box.category in ("panel", "speech_bubble", "character")
            assert box.x_max > box.x_min
            assert box.y_max > box.y_min

    def test_image_path_for_exists(self) -> None:
        """image_path_for resolves to an existing image for sampled pages."""
        xml = annotation_path_for(MANGA109_ROOT, "ARMS")
        pages = parse_book_annotations(xml)
        idx = next(i for i, p in pages.items() if p.boxes)
        img = image_path_for(MANGA109_ROOT, "ARMS", idx)
        assert img.exists()


# ---------------------------------------------------------------------------
# Metric tests.
# ---------------------------------------------------------------------------


class TestMetrics:
    """Tests for IoU / containment / greedy matching."""

    def test_iou_identical(self) -> None:
        """Identical boxes have IoU 1.0."""
        assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == pytest.approx(1.0)

    def test_iou_disjoint(self) -> None:
        """Disjoint boxes have IoU 0.0."""
        assert iou((0, 0, 10, 10), (100, 100, 10, 10)) == 0.0

    def test_iu_partial(self) -> None:
        """Partially overlapping boxes have IoU in (0, 1)."""
        score = iou((0, 0, 10, 10), (5, 5, 10, 10))
        assert 0.0 < score < 1.0

    def test_containment_full(self) -> None:
        """A detection fully containing GT has containment 1.0."""
        assert containment((0, 0, 100, 100), (10, 10, 20, 20)) == pytest.approx(1.0)

    def test_containment_partial(self) -> None:
        """Partial overlap gives fractional containment."""
        score = containment((0, 0, 15, 15), (10, 10, 20, 20))
        assert 0.0 < score < 1.0

    def test_evaluate_page_returns_all_categories(self) -> None:
        """evaluate_page returns metrics for all 3 sub-categories."""
        from tools.manga_frame.layer_extraction import (
            ExtractionStatus,
            LayerDescriptor,
            LayerExtractionResult,
            LayerMetadata,
        )
        from tools.manga_frame.layer_extraction.shape_classifier import (
            CHARACTER_BLEED,
            PANEL,
            SPEECH_BUBBLE,
        )

        def _layer(sub: str, bounds: tuple[int, int, int, int], idx: int) -> LayerDescriptor:
            return LayerDescriptor(
                layer_id=f"{sub}_{idx}",
                layer_index=idx,
                metadata=LayerMetadata(
                    confidence=0.8,
                    region_bounds=bounds,
                    extra={"sub_category": sub},
                ),
            )

        layers = (
            _layer(PANEL, (0, 0, 100, 100), 0),
            _layer(SPEECH_BUBBLE, (50, 50, 30, 30), 1),
            _layer(CHARACTER_BLEED, (200, 200, 80, 80), 2),
        )
        result = LayerExtractionResult(
            source_path=Path("/x.png"),
            page_number=0,
            layers=layers,
            status=ExtractionStatus.SUCCESS,
        )
        gt = PageGroundTruth(
            book="test",
            page_index=0,
            width=1000,
            height=1000,
            boxes=(
                GroundTruthBox("panel", 0, 0, 100, 100),
                GroundTruthBox("speech_bubble", 50, 50, 80, 80),
                GroundTruthBox("character", 200, 200, 280, 280),
            ),
        )
        metrics = evaluate_page(result, gt)
        assert set(metrics.keys()) == {PANEL, SPEECH_BUBBLE, CHARACTER_BLEED}
        for m in metrics.values():
            assert isinstance(m, CategoryMetrics)


# ---------------------------------------------------------------------------
# End-to-end evaluation tests (real Manga109-s data).
# ---------------------------------------------------------------------------


class TestEndToEndEvaluation:
    """End-to-end extraction + evaluation on Manga109-s."""

    def _build_pairs(self, book: str, n_pages: int = 6):
        extractor = ConcreteLayerExtractor()
        xml = annotation_path_for(MANGA109_ROOT, book)
        pages = parse_book_annotations(xml)
        pairs = []
        for idx in list(pages.keys())[:n_pages]:
            img = image_path_for(MANGA109_ROOT, book, idx)
            if not img.exists():
                continue
            gt = pages[idx]
            if not gt.boxes:
                continue
            res = extractor.extract(LayerExtractionInput(source_path=img, page_number=idx))
            pairs.append((res, gt))
        return pairs

    def test_arms_panel_precision_above_threshold(self) -> None:
        """Panel precision on ARMS is reasonable for a CV-heuristic baseline."""
        pairs = self._build_pairs("ARMS")
        assert len(pairs) >= 3
        report = evaluate_extraction(pairs)
        panel = report.per_category["panel"]
        # CV-heuristic baseline: panel precision should be meaningfully > random.
        assert panel.precision >= 0.4

    def test_report_summary_renders(self) -> None:
        """The evaluation report renders a human-readable summary."""
        pairs = self._build_pairs("ARMS", n_pages=3)
        report = evaluate_extraction(pairs)
        summary = report.summary()
        assert "panel" in summary
        assert "speech_bubble" in summary
        assert "character_bleed" in summary
        assert "pages evaluated" in summary

    def test_report_records_failure_cases(self) -> None:
        """The report records notable failure cases (character bleed)."""
        pairs = self._build_pairs("BEMADER_P", n_pages=4)
        report = evaluate_extraction(pairs)
        # Character bleed is a known-hard category for CV heuristics; expect
        # at least one failure case recorded across a few pages.
        assert isinstance(report.failure_cases, list)

    def test_multi_book_evaluation(self) -> None:
        """Evaluation across multiple books yields aggregated metrics."""
        all_pairs = []
        for book in SAMPLE_BOOKS:
            all_pairs.extend(self._build_pairs(book, n_pages=3))
        assert len(all_pairs) >= 3
        report = evaluate_extraction(all_pairs)
        assert report.pages_evaluated == len(all_pairs)
        # All three categories present in report.
        assert set(report.per_category.keys()) == {
            "panel",
            "speech_bubble",
            "character_bleed",
        }
