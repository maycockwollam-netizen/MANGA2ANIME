"""Computer-vision region detection for manga pages.

Uses OpenCV to detect candidate regions on a manga page image:

    1. Convert to grayscale + light blur.
    2. Adaptive threshold to binary (ink vs. paper).
    3. Morphological close with a large rectangular kernel to merge panel
       ink into solid blobs separated by white gutters.
    4. Detect white gutter rows/columns to split panels that are stuck
       together (a common failure of pure contour detection).
    5. findContours (RETR_EXTERNAL) -> panel candidates.
    6. Separate pass with morphological open (ellipse kernel) to isolate
       small rounded speech-bubble candidates.
    7. Compute ShapeFeatures for each candidate.

The detector returns raw detected regions (bbox + features + border flag).
Classification into panel / speech_bubble / character_bleed is performed by
shape_classifier.py.

This module does NOT:
- Classify regions (delegated to shape_classifier.py)
- Build LayerExtractionResult contracts (delegated to extractor.py)
- Access GPU
- Depend on runtime.manga_frame internals
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from tools.manga_frame.layer_extraction.exceptions import (
    LayerExtractionDetectionError,
    LayerExtractionImageError,
)
from tools.manga_frame.layer_extraction.features import ShapeFeatures, compute_features

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class DetectedRegion:
    """A raw detected region before classification.

    Attributes:
        features: ShapeFeatures (includes bbox).
        touches_border: True if the region's bbox touches the page edge.
        has_border: True if a detectable enclosing border exists.
        source_pass: Which detection pass produced this region
            ("panel" or "bubble").
    """

    features: ShapeFeatures
    touches_border: bool
    has_border: bool
    source_pass: str


def load_grayscale(source_path: Path) -> np.ndarray:
    """Load an image as a grayscale uint8 array.

    Args:
        source_path: Path to the image file.

    Returns:
        Grayscale image as an HxW uint8 numpy array.

    Raises:
        LayerExtractionImageError: If the image cannot be read or decoded.
    """
    img = cv2.imread(str(source_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise LayerExtractionImageError(f"failed to read image: {source_path}")
    return img


def _binary_ink(gray: np.ndarray) -> np.ndarray:
    """Threshold grayscale into binary ink mask (ink=255, paper=0).

    Uses adaptive thresholding to handle uneven page lighting.
    """
    # Gaussian blur to reduce noise.
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    # Adaptive threshold: ink is darker than local mean.
    bw = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=31,
        C=10,
    )
    return bw


def _white_fraction(gray: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute per-row and per-column fraction of near-white pixels.

    Args:
        gray: Grayscale page image.

    Returns:
        Tuple of (row_white_frac, col_white_frac) as float arrays.
    """
    white = gray > 240
    row_white = np.mean(white, axis=1)
    col_white = np.mean(white, axis=0)
    return row_white, col_white


def _group_seams(frac: np.ndarray, threshold: float) -> list[tuple[int, int]]:
    """Group consecutive indices above threshold into seam ranges.

    Args:
        frac: Per-line white fraction array.
        threshold: Minimum fraction to count as a seam.

    Returns:
        List of (start, end_inclusive) seam ranges.
    """
    above = np.where(frac >= threshold)[0]
    if len(above) == 0:
        return []
    seams: list[tuple[int, int]] = []
    start = int(above[0])
    prev = start
    for i in above[1:]:
        if int(i) - prev > 1:
            if prev - start >= 1:
                seams.append((start, prev))
            start = int(i)
        prev = int(i)
    if prev - start >= 1:
        seams.append((start, prev))
    return seams


def _seam_splits(
    frac: np.ndarray, threshold: float, total: int, min_gap: int = 3
) -> list[int]:
    """Find split positions (boundary lines) from white seams.

    Returns a list of integer positions where the region should be cut
    (each position is the midpoint of a seam).

    Args:
        frac: Per-line white fraction.
        threshold: Seam threshold.
        total: Total length of the axis.
        min_gap: Minimum seam width to count as a split.
    """
    seams = _group_seams(frac, threshold)
    splits: list[int] = []
    for s, e in seams:
        if (e - s) >= min_gap:
            splits.append((s + e) // 2)
    # Boundaries: include 0 and total as implicit splits.
    return splits


def _segment_panels(
    gray: np.ndarray,
    x0: int,
    y0: int,
    w: int,
    h: int,
    white_thresh: float,
    depth: int = 0,
) -> list[tuple[int, int, int, int]]:
    """Recursively segment a page region into panels using white gutters.

    Args:
        gray: Full grayscale page.
        x0, y0: Top-left of the region to segment.
        w, h: Width/height of the region.
        white_thresh: White fraction threshold for gutters.
        depth: Recursion depth guard.

    Returns:
        List of (x, y, w, h) panel bounding boxes.
    """
    if w <= 0 or h <= 0:
        return []
    sub = gray[y0 : y0 + h, x0 : x0 + w]
    if sub.size == 0:
        return []
    row_white = np.mean(sub > 240, axis=1)
    col_white = np.mean(sub > 240, axis=0)

    row_splits = _seam_splits(row_white, white_thresh, h)
    col_splits = _seam_splits(col_white, white_thresh, w)

    if not row_splits and not col_splits:
        # No gutters: this is a leaf panel candidate.
        # Only keep if it has some non-white content.
        if np.count_nonzero(sub <= 240) < (w * h) * 0.01:
            return []
        return [(x0, y0, w, h)]

    if depth > 6:
        return [(x0, y0, w, h)]

    panels: list[tuple[int, int, int, int]] = []
    # Build bands (start, end) from splits.
    if row_splits:
        row_bands = []
        last = 0
        for sp in row_splits:
            if sp - last > 1:
                row_bands.append((last, sp))
            last = sp
        if h - last > 1:
            row_bands.append((last, h))
    else:
        row_bands = [(0, h)]

    if col_splits:
        col_bands = []
        last = 0
        for sp in col_splits:
            if sp - last > 1:
                col_bands.append((last, sp))
            last = sp
        if w - last > 1:
            col_bands.append((last, w))
    else:
        col_bands = [(0, w)]

    for (ry, ry_end) in row_bands:
        rh = ry_end - ry
        for (cx, cx_end) in col_bands:
            cw = cx_end - cx
            panels.extend(
                _segment_panels(
                    gray,
                    x0 + cx,
                    y0 + ry,
                    cw,
                    rh,
                    white_thresh,
                    depth + 1,
                )
            )
    return panels


def _detect_border(
    gray: np.ndarray, x: int, y: int, w: int, h: int
) -> bool:
    """Heuristically detect whether a region has an enclosing border.

    Samples the mean intensity along the region's four edges. A border
    (dark line) makes edge pixels darker than the region interior.

    Args:
        gray: Grayscale page image.
        x, y, w, h: Region bounding box.

    Returns:
        True if a border is detected.
    """
    ph, pw = gray.shape
    # Clamp to page.
    x0 = max(x, 0)
    y0 = max(y, 0)
    x1 = min(x + w, pw)
    y1 = min(y + h, ph)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return False
    # Edge strips (2px).
    top = gray[y0 : y0 + 2, x0:x1]
    bot = gray[y1 - 2 : y1, x0:x1]
    left = gray[y0:y1, x0 : x0 + 2]
    right = gray[y0:y1, x1 - 2 : x1]
    edge_mean = float(
        np.mean([np.mean(top), np.mean(bot), np.mean(left), np.mean(right)])
    )
    # Interior mean (shrink 4px).
    ix0 = min(x0 + 4, x1 - 1)
    iy0 = min(y0 + 4, y1 - 1)
    ix1 = max(x1 - 4, ix0 + 1)
    iy1 = max(y1 - 4, iy0 + 1)
    interior = gray[iy0:iy1, ix0:ix1]
    interior_mean = float(np.mean(interior)) if interior.size > 0 else 255.0
    # A border makes edges darker than the interior.
    return edge_mean < interior_mean - 15.0


def detect_regions(
    gray: np.ndarray,
    *,
    min_panel_area_frac: float = 0.05,
    min_bubble_area_frac: float = 0.002,
    white_thresh: float = 0.95,
) -> list[DetectedRegion]:
    """Detect candidate regions on a manga page.

    Panel detection uses recursive white-gutter segmentation (layout
    analysis): the page is split along fully-white rows/columns, recursively,
    to recover panel boundaries even when panels share content density.

    Speech-bubble and character-bleed detection uses contour analysis on a
    binary ink mask: small high-circularity contours -> speech bubbles;
    large low-solidity contours not matching any panel -> character bleed.

    Args:
        gray: Grayscale page image (HxW uint8).
        min_panel_area_frac: Minimum panel bbox area as a fraction of page
            area.
        min_bubble_area_frac: Minimum bubble area fraction.
        white_thresh: White fraction threshold for gutter detection.

    Returns:
        List of DetectedRegion (panels first, then bubbles/bleeds), with
        ShapeFeatures computed.

    Raises:
        LayerExtractionDetectionError: If detection fails.
    """
    if gray is None or gray.size == 0:
        raise LayerExtractionDetectionError("empty grayscale image")

    page_h, page_w = gray.shape[:2]
    page_area = float(page_w * page_h)
    min_panel_area = page_area * min_panel_area_frac

    regions: list[DetectedRegion] = []

    # --- Panel pass: recursive gutter segmentation ---
    panel_boxes = _segment_panels(gray, 0, 0, page_w, page_h, white_thresh)
    # Filter tiny panels and merge duplicates.
    panel_boxes = _filter_and_merge_boxes(panel_boxes, min_panel_area)

    for (x, y, w, h) in panel_boxes:
        # Build a contour from the panel bbox (rectangular) for features.
        rect = np.array(
            [[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]],
            dtype=np.int32,
        )
        feats = compute_features(rect)
        touches = x <= 1 or y <= 1 or x + w >= page_w - 1 or y + h >= page_h - 1
        has_border = _detect_border(gray, x, y, w, h)
        regions.append(
            DetectedRegion(
                features=feats,
                touches_border=touches,
                has_border=has_border,
                source_pass="panel",
            )
        )

    # --- Bubble / bleed pass via MSER text clustering ---
    # (The earlier morphology-OPEN pass produced many low-precision bubble
    # candidates; MSER-based clustering gives cleaner speech-bubble regions.)
    panel_bboxes = [r.features.bbox for r in regions if r.source_pass == "panel"]
    regions.extend(
        _detect_mser_clusters(gray, panel_bboxes, page_area, page_w, page_h)
    )

    return regions


def _detect_mser_clusters(
    gray: np.ndarray,
    panel_bboxes: list[tuple[int, int, int, int]],
    page_area: float,
    page_w: int,
    page_h: int,
) -> list[DetectedRegion]:
    """Detect speech-bubble / character regions via MSER text clustering.

    Uses MSER to find stroke regions (text/line ink), dilates and groups
    them into connected components. Small compact clusters -> speech bubble;
    large irregular clusters -> character bleed.

    Args:
        gray: Grayscale page image.
        panel_bboxes: Already-detected panel bboxes (to filter artifacts).
        page_area: Page area in pixels.
        page_w: Page width.
        page_h: Page height.

    Returns:
        List of DetectedRegion from MSER clusters.
    """
    mser = cv2.MSER_create()
    mser.setMinArea(50)
    mser.setMaxArea(8000)
    try:
        _, bboxes = mser.detectRegions(gray)
    except cv2.error:
        return []

    if len(bboxes) == 0:
        return []

    # Dilate each MSER bbox into a mask to merge nearby strokes.
    mask = np.zeros((page_h, page_w), np.uint8)
    for (x, y, bw, bh) in bboxes:
        x0 = max(0, x - 4)
        y0 = max(0, y - 4)
        x1 = min(page_w, x + bw + 4)
        y1 = min(page_h, y + bh + 4)
        mask[y0:y1, x0:x1] = 255

    n, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, 8)

    regions: list[DetectedRegion] = []
    for i in range(1, n):
        x, y, w, h, _area = stats[i]
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        box_area = w * h
        if box_area < page_area * 0.0008:
            continue
        if box_area > page_area * 0.35:
            continue

        # Skip if contained in a panel and large (panel border artifact).
        contained = False
        for (px, py, pw, ph) in panel_bboxes:
            if x >= px and y >= py and x + w <= px + pw and y + h <= py + ph:
                if box_area >= (pw * ph) * 0.5:
                    contained = True
                    break
        if contained:
            continue

        # Build a rectangular contour for features.
        rect = np.array(
            [[[x, y]], [[x + w, y]], [[x + w, y + h]], [[x, y + h]]],
            dtype=np.int32,
        )
        feats = compute_features(rect)
        area_frac = feats.area / page_area

        if area_frac >= 0.04 and (feats.extent < 0.82 or feats.solidity < 0.9):
            # Large irregular cluster -> character bleed.
            touches = x <= 1 or y <= 1 or x + w >= page_w - 1 or y + h >= page_h - 1
            regions.append(
                DetectedRegion(
                    features=feats,
                    touches_border=touches,
                    has_border=False,
                    source_pass="bleed",
                )
            )
        elif (
            area_frac < 0.04
            and feats.circularity >= 0.65
            and 0.6 <= feats.aspect_ratio <= 1.7
            and area_frac >= 0.005
        ):
            # Compact near-square text cluster -> speech bubble.
            regions.append(
                DetectedRegion(
                    features=feats,
                    touches_border=False,
                    has_border=False,
                    source_pass="bubble",
                )
            )
    return regions


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    """Compute IoU of two (x, y, w, h) boxes (local, to avoid cross-layer import)."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    inter_x1 = max(ax, bx)
    inter_y1 = max(ay, by)
    inter_x2 = min(ax + aw, bx + bw)
    inter_y2 = min(ay + ah, by + bh)
    inter_w = max(inter_x2 - inter_x1, 0)
    inter_h = max(inter_y2 - inter_y1, 0)
    inter = inter_w * inter_h
    union = aw * ah + bw * bh - inter
    if union <= 0:
        return 0.0
    return inter / union


def _filter_and_merge_boxes(
    boxes: list[tuple[int, int, int, int]],
    min_area: float,
    iou_merge_thresh: float = 0.6,
) -> list[tuple[int, int, int, int]]:
    """Filter tiny boxes and merge near-duplicate / overlapping boxes.

    Args:
        boxes: List of (x, y, w, h).
        min_area: Minimum box area to keep.
        iou_merge_thresh: IoU above which two boxes are merged.

    Returns:
        Filtered + merged list of boxes.
    """
    kept: list[tuple[int, int, int, int]] = []
    for b in boxes:
        x, y, w, h = b
        if w * h < min_area:
            continue
        kept.append(b)

    # Merge overlapping boxes (greedy).
    merged: list[tuple[int, int, int, int]] = []
    for b in kept:
        x, y, w, h = b
        absorbed = False
        for i, m in enumerate(merged):
            if _iou(b, m) >= iou_merge_thresh:
                # Replace with union (min corner / max corner).
                mx, my, mw, mh = m
                nx0 = min(x, mx)
                ny0 = min(y, my)
                nx1 = max(x + w, mx + mw)
                ny1 = max(y + h, my + mh)
                merged[i] = (nx0, ny0, nx1 - nx0, ny1 - ny0)
                absorbed = True
                break
        if not absorbed:
            merged.append(b)
    return merged


def detect_regions_from_path(
    source_path: Path,
    **kwargs,
) -> list[DetectedRegion]:
    """Load an image from path and detect regions.

    Convenience wrapper around load_grayscale + detect_regions.

    Args:
        source_path: Path to the manga page image.
        **kwargs: Forwarded to detect_regions.

    Returns:
        List of DetectedRegion.
    """
    gray = load_grayscale(source_path)
    return detect_regions(gray, **kwargs)
