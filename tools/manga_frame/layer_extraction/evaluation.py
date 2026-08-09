"""Evaluation metrics for layer extraction on Manga109-s.

Computes IoU-based precision/recall/F1 per category (panel, speech_bubble,
character_bleed) by comparing the extractor's output against Manga109-s
ground-truth annotations.

A detection is a true positive if it has IoU >= iou_threshold with a
ground-truth box of the same category, and neither box was already matched
(greedy one-to-one matching by descending IoU).

Character-bleed mapping note:
    Ground truth <body> boxes are character bodies. The extractor flags a
    region as character_bleed when it is a large irregular contour that does
    not satisfy panel rectangularity. The evaluation therefore compares
    detected character_bleed regions against GT <body> boxes (a proxy for
    character presence), which is an approximate measure of bleed detection.

This module does NOT:
- Load or decode images (it consumes already-extracted results)
- Perform detection
- Access GPU
- Redistribute Manga109-s data
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tools.manga_frame.layer_extraction import (
    LayerExtractionResult,
)
from tools.manga_frame.layer_extraction.manga109_reader import (
    GroundTruthBox,
    PageGroundTruth,
)
from tools.manga_frame.layer_extraction.shape_classifier import (
    CHARACTER_BLEED,
    PANEL,
    SPEECH_BUBBLE,
)

if TYPE_CHECKING:
    pass

# Mapping from sub_category (stored in metadata.extra) to GT category.
_SUBCAT_TO_GT: dict[str, str] = {
    PANEL: "panel",
    SPEECH_BUBBLE: "speech_bubble",
    CHARACTER_BLEED: "character",
}


@dataclass(frozen=True)
class CategoryMetrics:
    """Precision/recall/F1 for a single category.

    Attributes:
        category: Category name (panel / speech_bubble / character_bleed).
        true_positives: Number of TP detections.
        false_positives: Number of FP detections.
        false_negatives: Number of FN ground-truth boxes.
        precision: TP / (TP + FP), or 0.0 if denominator is 0.
        recall: TP / (TP + FN), or 0.0 if denominator is 0.
        f1: Harmonic mean of precision and recall, or 0.0 if undefined.
    """

    category: str
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float


@dataclass
class EvaluationReport:
    """Full evaluation report across all categories and pages.

    Attributes:
        per_category: Dict of category -> CategoryMetrics.
        pages_evaluated: Number of pages evaluated.
        iou_threshold: IoU threshold used for matching.
        failure_cases: List of human-readable descriptions of notable
            classification failures (e.g., borderless panel misclassified as
            character_bleed). Each entry is a (page_label, description) tuple.
    """

    per_category: dict[str, CategoryMetrics] = field(default_factory=dict)
    pages_evaluated: int = 0
    iou_threshold: float = 0.5
    failure_cases: list[tuple[str, str]] = field(default_factory=list)

    def summary(self) -> str:
        """Render a human-readable summary of the report."""
        lines = [
            "Manga109-s layer extraction evaluation",
            f"  pages evaluated: {self.pages_evaluated}",
            f"  IoU threshold:   {self.iou_threshold}",
            "",
            f"  {'category':<16} {'precision':>10} {'recall':>10} {'f1':>8}  {'TP':>4} {'FP':>4} {'FN':>4}",
        ]
        for cat in (PANEL, SPEECH_BUBBLE, CHARACTER_BLEED):
            m = self.per_category.get(cat)
            if m is None:
                lines.append(f"  {cat:<16} {'n/a':>10}")
                continue
            lines.append(
                f"  {cat:<16} {m.precision:>10.3f} {m.recall:>10.3f} "
                f"{m.f1:>8.3f}  {m.true_positives:>4} {m.false_positives:>4} "
                f"{m.false_negatives:>4}"
            )
        if self.failure_cases:
            lines.append("")
            lines.append("  Notable failure cases:")
            for label, desc in self.failure_cases[:20]:
                lines.append(f"    [{label}] {desc}")
        return "\n".join(lines)


def iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    """Compute Intersection-over-Union of two (x, y, w, h) boxes.

    Args:
        a: First box (x, y, w, h).
        b: Second box (x, y, w, h).

    Returns:
        IoU in [0.0, 1.0].
    """
    return _iou_xywh(a, b)


def _iou_xywh(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    """IoU for (x, y, w, h) boxes."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2 = ax + aw
    ay2 = ay + ah
    bx2 = bx + bw
    by2 = by + bh

    inter_x1 = max(ax, bx)
    inter_y1 = max(ay, by)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(inter_x2 - inter_x1, 0)
    inter_h = max(inter_y2 - inter_y1, 0)
    inter = inter_w * inter_h
    union = aw * ah + bw * bh - inter
    if union <= 0:
        return 0.0
    return inter / union


def containment(det: tuple[int, int, int, int], gt: tuple[int, int, int, int]) -> float:
    """Compute containment of GT inside a detection.

    Containment = intersection_area / gt_area.

    Used for speech_bubble / character detection where the detected cluster
    (text ink + outline) is larger than the ground-truth text/body bbox, so
    IoU is a poor match metric. Containment measures how much of the GT box
    is covered by the detection.

    Args:
        det: Detection box (x, y, w, h).
        gt: Ground-truth box (x, y, w, h).

    Returns:
        Containment fraction in [0.0, 1.0].
    """
    dx, dy, dw, dh = det
    gx, gy, gw, gh = gt
    ix1 = max(dx, gx)
    iy1 = max(dy, gy)
    ix2 = min(dx + dw, gx + gw)
    iy2 = min(dy + dh, gy + gh)
    iw = max(ix2 - ix1, 0)
    ih = max(iy2 - iy1, 0)
    inter = iw * ih
    gt_area = gw * gh
    if gt_area <= 0:
        return 0.0
    return inter / gt_area


def _match_score(
    det: tuple[int, int, int, int],
    gt_box: GroundTruthBox,
    mode: str,
) -> float:
    """Compute the match score for a detection/GT pair given a mode.

    Args:
        det: Detection (x, y, w, h).
        gt_box: Ground-truth box.
        mode: "iou" or "containment".

    Returns:
        Match score in [0.0, 1.0].
    """
    gt_xywh = (gt_box.x_min, gt_box.y_min, gt_box.width, gt_box.height)
    if mode == "containment":
        return containment(det, gt_xywh)
    return _iou_xywh(det, gt_xywh)


def _detected_category(layer_meta_extra: dict[str, str]) -> str | None:
    """Map a detected layer's sub_category to a GT category.

    Args:
        layer_meta_extra: The extra metadata dict of a LayerDescriptor.

    Returns:
        GT category string ("panel"/"speech_bubble"/"character") or None.
    """
    sub = layer_meta_extra.get("sub_category")
    if sub is None:
        return None
    return _SUBCAT_TO_GT.get(sub)


def _greedy_match(
    detections: list[tuple[str, tuple[int, int, int, int]]],
    ground_truth: list[GroundTruthBox],
    iou_threshold: float,
    *,
    match_mode: str = "iou",
) -> tuple[int, int, int, list[tuple[int, int, float]]]:
    """Greedy one-to-one matching of detections to GT by descending score.

    Args:
        detections: List of (category, (x,y,w,h)) detections.
        ground_truth: List of GroundTruthBox.
        iou_threshold: Minimum score for a match.
        match_mode: "iou" or "containment".

    Returns:
        Tuple of (true_positives, false_positives, false_negatives, matches)
        where matches is a list of (det_idx, gt_idx, score).
    """
    # Build all candidate pairs with score >= threshold, same category.
    pairs: list[tuple[float, int, int]] = []
    for di, (dcat, dbox) in enumerate(detections):
        for gi, gbox in enumerate(ground_truth):
            if gbox.category != dcat:
                continue
            score = _match_score(dbox, gbox, match_mode)
            if score >= iou_threshold:
                pairs.append((score, di, gi))
    # Sort by descending score.
    pairs.sort(key=lambda p: p[0], reverse=True)

    matched_det: set[int] = set()
    matched_gt: set[int] = set()
    matches: list[tuple[int, int, float]] = []
    for score, di, gi in pairs:
        if di in matched_det or gi in matched_gt:
            continue
        matched_det.add(di)
        matched_gt.add(gi)
        matches.append((di, gi, score))

    tp = len(matched_det)
    fp = len(detections) - tp
    fn = len(ground_truth) - len(matched_gt)
    return tp, fp, fn, matches


def _safe_prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    """Compute precision/recall/F1 with zero-denominator guards."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return precision, recall, f1


def evaluate_page(
    result: LayerExtractionResult,
    gt: PageGroundTruth,
    *,
    iou_threshold: float = 0.5,
    match_modes: dict[str, str] | None = None,
) -> dict[str, CategoryMetrics]:
    """Evaluate a single page's extraction result against ground truth.

    Args:
        result: The LayerExtractionResult from the extractor.
        gt: The PageGroundTruth from Manga109-s.
        iou_threshold: Threshold for matching.
        match_modes: Optional dict mapping sub_category -> "iou" or
            "containment". Defaults to IoU for panels and containment for
            speech_bubble / character_bleed.

    Returns:
        Dict mapping sub_category -> CategoryMetrics for this page.
    """
    if match_modes is None:
        match_modes = {
            PANEL: "iou",
            SPEECH_BUBBLE: "containment",
            CHARACTER_BLEED: "containment",
        }

    # Group detections by GT category.
    detections_by_cat: dict[str, list[tuple[int, int, int, int]]] = {
        "panel": [],
        "speech_bubble": [],
        "character": [],
    }
    for layer in result.layers:
        if layer.metadata is None:
            continue
        extra = dict(layer.metadata.extra)
        gt_cat = _detected_category(extra)
        if gt_cat is None:
            continue
        bounds = layer.metadata.region_bounds
        if bounds is None:
            continue
        detections_by_cat[gt_cat].append(bounds)

    gt_by_cat: dict[str, list[GroundTruthBox]] = {
        "panel": [],
        "speech_bubble": [],
        "character": [],
    }
    for box in gt.boxes:
        if box.category in gt_by_cat:
            gt_by_cat[box.category].append(box)

    metrics: dict[str, CategoryMetrics] = {}
    sub_to_gt = {
        PANEL: "panel",
        SPEECH_BUBBLE: "speech_bubble",
        CHARACTER_BLEED: "character",
    }
    for sub_cat, gt_cat in sub_to_gt.items():
        dets = detections_by_cat.get(gt_cat, [])
        gts = gt_by_cat.get(gt_cat, [])
        mode = match_modes.get(sub_cat, "iou")
        tp, fp, fn, _ = _greedy_match(
            [(gt_cat, d) for d in dets], gts, iou_threshold, match_mode=mode
        )
        p, r, f1 = _safe_prf(tp, fp, fn)
        metrics[sub_cat] = CategoryMetrics(
            category=sub_cat,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=p,
            recall=r,
            f1=f1,
        )
    return metrics


def _merge_metrics(
    accumulator: dict[str, list[int]],
    page_metrics: dict[str, CategoryMetrics],
) -> None:
    """Accumulate TP/FP/FN counts across pages."""
    for sub_cat, m in page_metrics.items():
        acc = accumulator.setdefault(sub_cat, [0, 0, 0])
        acc[0] += m.true_positives
        acc[1] += m.false_positives
        acc[2] += m.false_negatives


def evaluate_extraction(
    results: list[tuple[LayerExtractionResult, PageGroundTruth]],
    *,
    iou_threshold: float = 0.5,
    match_modes: dict[str, str] | None = None,
) -> EvaluationReport:
    """Evaluate a batch of extraction results against Manga109-s ground truth.

    Args:
        results: List of (LayerExtractionResult, PageGroundTruth) pairs.
        iou_threshold: Threshold for matching.
        match_modes: Optional dict mapping sub_category -> "iou" or
            "containment". Defaults to IoU for panels and containment for
            speech_bubble / character_bleed.

    Returns:
        EvaluationReport with per-category precision/recall/F1 and notable
        failure cases.
    """
    if match_modes is None:
        match_modes = {
            PANEL: "iou",
            SPEECH_BUBBLE: "containment",
            CHARACTER_BLEED: "containment",
        }

    acc: dict[str, list[int]] = {}
    report = EvaluationReport(iou_threshold=iou_threshold)

    for result, gt in results:
        page_metrics = evaluate_page(
            result, gt, iou_threshold=iou_threshold, match_modes=match_modes
        )
        _merge_metrics(acc, page_metrics)
        report.pages_evaluated += 1

        # Record notable failure cases.
        _record_failures(report, result, gt, page_metrics, iou_threshold)

    for sub_cat, (tp, fp, fn) in acc.items():
        p, r, f1 = _safe_prf(tp, fp, fn)
        report.per_category[sub_cat] = CategoryMetrics(
            category=sub_cat,
            true_positives=tp,
            false_positives=fp,
            false_negatives=fn,
            precision=p,
            recall=r,
            f1=f1,
        )
    return report


def _record_failures(
    report: EvaluationReport,
    result: LayerExtractionResult,
    gt: PageGroundTruth,
    page_metrics: dict[str, CategoryMetrics],
    iou_threshold: float,
) -> None:
    """Record notable failure cases for a page.

    Detects:
        - Borderless panels misclassified as character_bleed (panel GT present
          but panel recall is 0 while character_bleed has FPs).
        - Panels with no GT match (panel FPs).
        - Character_bleed recall failures (character FN > 0).
    """
    label = f"{gt.book}#{gt.page_index}"

    panel_m = page_metrics.get(PANEL)
    bleed_m = page_metrics.get(CHARACTER_BLEED)

    # Borderless panel misclassified as character_bleed: panel has FNs and
    # bleed has FPs on the same page.
    if (
        panel_m
        and bleed_m
        and panel_m.false_negatives > 0
        and bleed_m.false_positives > 0
    ):
        report.failure_cases.append(
            (
                label,
                "possible borderless panel misclassified as character_bleed "
                f"(panel FN={panel_m.false_negatives}, bleed FP={bleed_m.false_positives})",
            )
        )

    # Large panel FP burst.
    if panel_m and panel_m.false_positives >= 3:
        report.failure_cases.append(
            (label, f"high panel false positives ({panel_m.false_positives})")
        )

    # Character bleed recall failure.
    if bleed_m and bleed_m.false_negatives > 0 and bleed_m.true_positives == 0:
        report.failure_cases.append(
            (label, f"character_bleed undetected (FN={bleed_m.false_negatives})")
        )
