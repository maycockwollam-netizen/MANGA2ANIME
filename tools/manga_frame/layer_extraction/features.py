"""Shape feature extraction for layer region classification.

Computes geometric features from an OpenCV contour that the shape-heuristic
classifier uses to categorize a region as panel / speech_bubble /
character_bleed.

Features:
    - extent: contour_area / bounding_box_area. Rectangle ~0.9-1.0,
      ellipse ~0.78, irregular shape lower.
    - circularity: 4*pi*area / perimeter^2. Circle ~1.0, jagged/irregular
      lower.
    - aspect_ratio: bounding_box width / height.
    - solidity: contour_area / convex_hull_area. Convex shape ~1.0,
      concave shape lower.

This module does NOT:
- Classify regions (delegated to shape_classifier.py)
- Load or decode images
- Access GPU
- Depend on runtime.manga_frame internals
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class ShapeFeatures:
    """Geometric features extracted from a contour.

    All fields are floats. Bounds and area are also stored for downstream
    contract mapping.

    Attributes:
        extent: contour_area / bbox_area.
        circularity: 4*pi*area / perimeter^2 (0 if perimeter is 0).
        aspect_ratio: bbox width / height (0 if height is 0).
        solidity: contour_area / convex_hull_area (0 if hull area is 0).
        area: contour area in pixels.
        bbox: bounding box as (x, y, width, height) in pixels.
    """

    extent: float
    circularity: float
    aspect_ratio: float
    solidity: float
    area: float
    bbox: tuple[int, int, int, int]


def compute_features(contour: np.ndarray) -> ShapeFeatures:
    """Compute shape features from an OpenCV contour.

    Args:
        contour: An OpenCV contour array (Nx1x2 int32).

    Returns:
        ShapeFeatures for the contour.

    Raises:
        LayerExtractionClassificationError: If the contour is degenerate
            (empty or zero area).
    """
    from tools.manga_frame.layer_extraction.exceptions import (
        LayerExtractionClassificationError,
    )

    area = float(cv2.contourArea(contour))
    if area <= 0.0:
        raise LayerExtractionClassificationError(
            "contour has zero area; cannot compute shape features"
        )

    x, y, w, h = cv2.boundingRect(contour)
    bbox = (int(x), int(y), int(w), int(h))

    bbox_area = float(w * h)
    extent = area / bbox_area if bbox_area > 0 else 0.0

    perimeter = float(cv2.arcLength(contour, True))
    circularity = (4.0 * np.pi * area / (perimeter * perimeter)) if perimeter > 0 else 0.0

    hull = cv2.convexHull(contour)
    hull_area = float(cv2.contourArea(hull))
    solidity = area / hull_area if hull_area > 0 else 0.0

    aspect_ratio = float(w) / float(h) if h > 0 else 0.0

    return ShapeFeatures(
        extent=extent,
        circularity=circularity,
        aspect_ratio=aspect_ratio,
        solidity=solidity,
        area=area,
        bbox=bbox,
    )
