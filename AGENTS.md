# AGENTS.md — MANGA2ANIME repository memory

Persistent knowledge for OpenHands agents working in this repo.

## Environment

- Python: `/usr/local/bin/python` (3.13). Deps may need reinstall after env reset:
  `pip install pydantic pytest pillow opencv-python-headless numpy ruff`.
  opencv is installed as `opencv-python-headless` (import as `cv2`).
- Tests: `python -m pytest -q` (2043 tests, ~30s). Config in `pyproject.toml`
  (`pythonpath=["."]`, `testpaths=["tests"]`).
- Lint: `python -m ruff check .` (rules: E,F,W,I,N,UP,B; line-length 100; E501 ignored).
  `--fix` is safe for F401/F541/I001.

## Repo layout

- `tools/<domain>/` — domain modules. Each typically has: contract `__init__.py`
  (Pydantic models + enums), `exceptions.py` (hierarchy), concrete impl files,
  `*_to_frame.py` downstream adapter.
- `tests/tools/<domain>/` — tests mirroring module layout.
- Contracts use Pydantic v2 `BaseModel` + `StrEnum`. Exceptions follow pattern:
  `<Domain>Error(Exception)` base + `<Domain><Specific>Error` subclasses.

## Conventions (observed)

- Contracts in `__init__.py` are IMMUTABLE: do NOT change field names/types of
  existing exported models. Add new exports at the bottom with a comment block.
- Concrete implementations live in sibling files and are re-exported from
  `__init__.py` `__all__`.
- Exception module docstring explicitly lists what the module does NOT do.
- Docstrings: Google/NumPy-ish style with Args/Returns/Raises sections.

## tools/manga_frame/layer_extraction (CV implementation)

- Contract: `LayerCategory = {BACKGROUND, CHARACTER, FOREGROUND, EFFECT, UNKNOWN}`.
  Task required `{panel, speech_bubble, character_bleed}`. Resolution: NO contract
  change. Map sub_category -> existing LayerCategory:
    panel -> BACKGROUND, speech_bubble -> EFFECT, character_bleed -> CHARACTER.
  Sub-category + shape features stored in `LayerMetadata.extra` (dict[str,str]).
- Files:
  - `__init__.py` — contract (unchanged) + re-exports of CV impl.
  - `exceptions.py` — LayerExtractionError hierarchy + `raise_for_input`.
  - `features.py` — `ShapeFeatures` (extent, circularity, aspect_ratio, solidity)
    + `compute_features(contour)`.
  - `shape_classifier.py` — `classify(features, page_area, ...) -> ClassificationResult`.
    Sub-category labels: PANEL/SPEECH_BUBBLE/CHARACTER_BLEED; panel_type
    PANEL_BORDERED/PANEL_BORDERLESS.
  - `cv_detector.py` — `detect_regions(gray)` / `detect_regions_from_path(path)`.
    Panel pass: recursive white-gutter segmentation (`_segment_panels`).
    Bubble/bleed pass: MSER text clustering (`_detect_mser_clusters`).
  - `extractor.py` — `ConcreteLayerExtractor.extract(input) -> LayerExtractionResult`.
  - `manga109_reader.py` — parse Manga109-s annotation XML -> PageGroundTruth.
  - `evaluation.py` — IoU/containment metrics, `evaluate_extraction(pairs)`.
- Tests: `test_cv_layer_extraction.py` (unit, synthetic OpenCV images, 30 tests)
  + `test_manga109_evaluation.py` (integration, SKIPPED unless
  `/tmp/manga109_sample/Manga109s_released_2026_05_21` exists, 13 tests).

## CV performance baseline (Manga109-s, 50 pages across 5 volumes)

Measured with IoU>=0.5 for panels, containment>=0.5 for bubbles/bleed:
- panel:          P=0.67  R=0.25  F1=0.36
- speech_bubble:  P=0.15  R=0.06  F1=0.09
- character_bleed: P=0.00 R=0.00  F1=0.00

Known limitation: character_bleed is NOT reliably detectable with pure CV
heuristics (character art merges with panel ink). Needs ML segmentation (CNN,
e.g. Manga109 character-detection papers). Panel detection via gutter
segmentation works well; speech bubbles via MSER clustering have low precision
(many text/SFX false positives).

## Manga109-s dataset

- License: academic use only. NEVER commit images/annotations to the repo.
- Source: HuggingFace `radii-ai/manga109-s` (or similar). ~3.1GB zip.
- Layout: `images/<book>/<NNN>.jpg` + `annotations.v2020.12.18/<book>.xml`.
- XML: `<page index=.. width=.. height=..>` with `<frame>` (panel),
  `<text>` (speech bubble text bbox), `<body>` (character body bbox),
  `<face>` (face bbox). Each has xmin/ymin/xmax/ymax attrs.
- Note: "Belmondo" is NOT in Manga109-s (only full Manga109). Use
  BakuretsuKungFuGirl as a shoujo sample instead.

## Git

- Remote: https://github.com/maycockwollam-netizen/MANGA2ANIME.git
- Commit style: `feat: <summary>` or `feat: <summary> in tools/<module>`.
- Co-author line: `Co-authored-by: openhands <openhands@all-hands.dev>`.
- Shallow clone — `git fetch --unshallow` if full history needed.
