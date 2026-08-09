"""Manga109-s annotation reader for validation.

Parses Manga109-s annotation XML files to extract ground-truth bounding
boxes for:

    - panels       (<frame> elements)
    - speech text  (<text> elements; used as speech-bubble ground truth)
    - character    (<body> elements; used as character-bleed ground truth)

The reader is used ONLY for evaluation/testing against the Manga109-s
dataset (academic-use license, not redistributed). It is not part of the
runtime extraction pipeline.

Annotation XML format (per Manga109):

    <book title="...">
      <characters> <character id="..." name="..."/> ... </characters>
      <pages>
        <page index="0" width="1654" height="1170">
          <text   id="..." xmin=".." ymin=".." xmax=".." ymax="..">..</text>
          <body   id="..." xmin=".." ymin=".." xmax=".." ymax=".." character=".."/>
          <face   id="..." xmin=".." ymin=".." xmax=".." ymax=".." character=".."/>
          <frame  id="..." xmin=".." ymin=".." xmax=".." ymax=".."/>
        </page>
        ...
      </pages>
    </book>

This module does NOT:
- Load or decode images
- Perform detection
- Access GPU
- Redistribute Manga109-s data
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GroundTruthBox:
    """A single ground-truth bounding box.

    Attributes:
        category: One of "panel", "speech_bubble", "character".
        x_min, y_min, x_max, y_max: Bounding box in pixel coordinates.
    """

    category: str
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    @property
    def width(self) -> int:
        """Box width."""
        return self.x_max - self.x_min

    @property
    def height(self) -> int:
        """Box height."""
        return self.y_max - self.y_min

    @property
    def area(self) -> int:
        """Box area in pixels."""
        return max(self.width, 0) * max(self.height, 0)


@dataclass(frozen=True)
class PageGroundTruth:
    """Ground truth for a single page.

    Attributes:
        book: Book title.
        page_index: Page index.
        width: Page width in pixels.
        height: Page height in pixels.
        boxes: Tuple of GroundTruthBox.
    """

    book: str
    page_index: int
    width: int
    height: int
    boxes: tuple[GroundTruthBox, ...]


def _box(elem: ET.Element, category: str) -> GroundTruthBox:
    """Build a GroundTruthBox from an XML element with xmin/ymin/xmax/ymax."""
    return GroundTruthBox(
        category=category,
        x_min=int(elem.get("xmin", 0)),
        y_min=int(elem.get("ymin", 0)),
        x_max=int(elem.get("xmax", 0)),
        y_max=int(elem.get("ymax", 0)),
    )


def parse_book_annotations(xml_path: Path) -> dict[int, PageGroundTruth]:
    """Parse a Manga109-s book annotation XML.

    Args:
        xml_path: Path to the book annotation XML file.

    Returns:
        Dict mapping page index -> PageGroundTruth. Pages with no annotated
        boxes are still included (with empty boxes) if they appear in the
        XML with a width/height.

    Raises:
        FileNotFoundError: If xml_path does not exist.
        ET.ParseError: If the XML is malformed.
    """
    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    book_title = root.get("title", xml_path.stem)

    result: dict[int, PageGroundTruth] = {}
    pages_elem = root.find("pages")
    if pages_elem is None:
        return result

    for page in pages_elem.findall("page"):
        idx = int(page.get("index", 0))
        width = int(page.get("width", 0))
        height = int(page.get("height", 0))
        boxes: list[GroundTruthBox] = []
        for frame in page.findall("frame"):
            boxes.append(_box(frame, "panel"))
        for text in page.findall("text"):
            boxes.append(_box(text, "speech_bubble"))
        for body in page.findall("body"):
            boxes.append(_box(body, "character"))
        result[idx] = PageGroundTruth(
            book=book_title,
            page_index=idx,
            width=width,
            height=height,
            boxes=tuple(boxes),
        )
    return result


def image_path_for(
    manga109_root: Path, book: str, page_index: int
) -> Path:
    """Resolve the image path for a book/page in a Manga109-s tree.

    Manga109-s images are stored as:
        <root>/images/<book>/<page_index:03d>.jpg

    Args:
        manga109_root: Root directory of the extracted Manga109-s dataset.
        book: Book title (folder name).
        page_index: Zero-based page index.

    Returns:
        Path to the image file (existence not guaranteed).
    """
    return manga109_root / "images" / book / f"{page_index:03d}.jpg"


def annotation_path_for(manga109_root: Path, book: str) -> Path:
    """Resolve the annotation XML path for a book.

    Manga109-s annotations are stored as:
        <root>/annotations.v2020.12.18/<book>.xml

    Args:
        manga109_root: Root directory of the extracted Manga109-s dataset.
        book: Book title.

    Returns:
        Path to the annotation XML file.
    """
    return manga109_root / "annotations.v2020.12.18" / f"{book}.xml"
