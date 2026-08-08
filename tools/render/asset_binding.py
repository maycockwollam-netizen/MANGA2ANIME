"""Caller-level asset binding for RenderFrames.

This module provides a minimal utility for binding image asset paths to
animation-generated RenderFrames before rendering.

Architecture:
    AnimationOrchestrator produces RenderFrame with FrameTransform (no source_path)
        ↓
    bind_render_frame_assets() adds source_path to matching transforms
        ↓
    ConcreteRenderer renders with real assets

This is a thin binding utility that:
- Does NOT load image files
- Does NOT validate PNG contents
- Does NOT introduce caching
- Does NOT manage resource lifecycle
- Does NOT add orchestration

The dependency direction remains:
    tools/render/asset_binding
            ↓
    tools/frame/models (FrameTransform, Path)
    tools/render (RenderFrame)

No imports from runtime.animation or tools.manga_frame.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

from tools.frame.models import FrameTransform
from tools.render import RenderFrame


def bind_render_frame_assets(
    frame: RenderFrame,
    assets: Mapping[str, Path | str],
) -> RenderFrame:
    """Bind image asset paths to transforms in a RenderFrame.

    Creates a new RenderFrame with source_path set for transforms whose
    clip/entity IDs appear in the assets mapping. The original frame
    is not modified.

    Args:
        frame: RenderFrame from animation output (may have transforms without source_path)
        assets: Mapping from clip/entity ID to asset path (Path or str)

    Returns:
        New RenderFrame with source_path bound for matched transforms

    Raises:
        TypeError: If assets contains invalid value types

    Example:
        >>> from pathlib import Path
        >>> from tools.render import RenderFrame, bind_render_frame_assets
        >>>
        >>> # Animation produces frame without asset paths
        >>> anim_frame = orchestrator.render_frame()
        >>> # anim_frame.transforms["hero"].source_path is None
        >>>
        >>> # Bind assets
        >>> bound = bind_render_frame_assets(
        ...     anim_frame,
        ...     {"hero": Path("assets/hero.png")}
        ... )
        >>> bound.transforms["hero"].source_path == Path("assets/hero.png")
        True
        >>> anim_frame.transforms["hero"].source_path is None  # Original unchanged
        True
    """
    # Convert str paths to Path objects and validate
    asset_map: dict[str, Path] = {}
    for clip_id, asset_path in assets.items():
        if isinstance(asset_path, str):
            asset_map[clip_id] = Path(asset_path)
        elif isinstance(asset_path, Path):
            asset_map[clip_id] = asset_path
        else:
            raise TypeError(
                f"Asset path for '{clip_id}' must be Path or str, "
                f"got {type(asset_path).__name__}"
            )

    # Build new transforms mapping
    new_transforms: dict[str, FrameTransform] = {}

    # Preserve deterministic ordering by iterating in original order
    for clip_id in frame.transforms:
        original_transform = frame.transforms[clip_id]

        if clip_id in asset_map:
            # Create new transform with source_path from assets mapping
            new_transforms[clip_id] = FrameTransform(
                position_x=original_transform.position_x,
                position_y=original_transform.position_y,
                scale=original_transform.scale,
                rotation_deg=original_transform.rotation_deg,
                opacity=original_transform.opacity,
                anchor_x=original_transform.anchor_x,
                anchor_y=original_transform.anchor_y,
                source_path=asset_map[clip_id],
            )
        else:
            # Preserve original transform (including existing source_path)
            new_transforms[clip_id] = FrameTransform(
                position_x=original_transform.position_x,
                position_y=original_transform.position_y,
                scale=original_transform.scale,
                rotation_deg=original_transform.rotation_deg,
                opacity=original_transform.opacity,
                anchor_x=original_transform.anchor_x,
                anchor_y=original_transform.anchor_y,
                source_path=original_transform.source_path,
            )

    return RenderFrame(
        frame_index=frame.frame_index,
        timestamp_seconds=frame.timestamp_seconds,
        frame_rate=frame.frame_rate,
        duration_frames=frame.duration_frames,
        transforms=MappingProxyType(new_transforms),
    )


__all__ = [
    "bind_render_frame_assets",
]
