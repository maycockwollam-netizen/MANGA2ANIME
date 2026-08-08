"""Render artifact loader.

Provides read-only loading of an existing render artifact from its JSON manifest.

This module loads and validates an existing artifact without modifying any files.

Architecture:
    manifest.json
        ↓
    read_artifact_manifest()
        ↓
    RenderArtifactManifest
        ↓
    load_render_artifact()
        ↓
    LoadedRenderArtifact (or exception)

This module does NOT:
- Modify files
- Create files
- Delete files
- Render anything
- Use threads or async
- Cache data
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.render.artifact import RenderArtifact
    from tools.render.artifact_manifest import RenderArtifactManifest


@dataclass(frozen=True)
class LoadedRenderArtifact:
    """Immutable loaded artifact with its manifest.

    Attributes:
        artifact: The reconstructed RenderArtifact.
        manifest: The loaded RenderArtifactManifest.
    """

    artifact: RenderArtifact
    manifest: RenderArtifactManifest


class ArtifactLoadError(Exception):
    """Error loading a render artifact.

    Raised when artifact loading fails due to missing files, invalid manifest,
    or validation errors.
    """

    pass


def load_render_artifact(
    manifest_path: Path | str,
    *,
    validate: bool = True,
) -> LoadedRenderArtifact:
    """Load an existing render artifact from its manifest.

    Reads the manifest JSON, reconstructs the RenderArtifact metadata,
    and optionally validates against the PNG sequence.

    Args:
        manifest_path: Path to the manifest JSON file.
        validate: If True, validate the artifact and manifest against
            the PNG sequence. Default is True.

    Returns:
        LoadedRenderArtifact containing the artifact and manifest.

    Raises:
        ArtifactLoadError: If loading or validation fails.

    Example:
        >>> loaded = load_render_artifact("output/manifest.json")
        >>> print(f"Frames: {loaded.artifact.frame_count}")
    """
    from tools.render.artifact import RenderArtifact
    from tools.render.artifact_manifest import (
        ArtifactManifestError,
        read_artifact_manifest,
    )
    from tools.render.artifact_manifest_validation import (
        ArtifactManifestValidationError,
        validate_artifact_manifest,
    )
    from tools.render.artifact_validation import (
        ArtifactValidationError,
        validate_render_artifact,
    )

    manifest_path = Path(manifest_path)

    # Step 1: Read the manifest
    try:
        manifest: RenderArtifactManifest = read_artifact_manifest(manifest_path)
    except ArtifactManifestError as e:
        raise ArtifactLoadError(
            f"Failed to read manifest: {e}"
        ) from e

    # Step 2: Reconstruct RenderArtifact from manifest metadata
    try:
        artifact: RenderArtifact = RenderArtifact(
            output_dir=Path(manifest.output_dir),
            prefix=manifest.prefix,
            frame_count=manifest.frame_count,
            frame_indices=manifest.frame_indices,
            frame_rate=manifest.frame_rate,
            duration_seconds=manifest.duration_seconds,
            dimensions=manifest.dimensions,
            mode=manifest.mode,
        )
    except Exception as e:
        raise ArtifactLoadError(
            f"Failed to reconstruct artifact: {e}"
        ) from e

    # Step 3: Optionally validate
    if validate:
        # Validate artifact
        try:
            validate_render_artifact(artifact)
        except ArtifactValidationError as e:
            raise ArtifactLoadError(
                f"Artifact validation failed: {e}"
            ) from e

        # Validate manifest against artifact
        try:
            validate_artifact_manifest(artifact, manifest)
        except ArtifactManifestValidationError as e:
            raise ArtifactLoadError(
                f"Manifest validation failed: {e}"
            ) from e

    return LoadedRenderArtifact(
        artifact=artifact,
        manifest=manifest,
    )


__all__ = [
    "LoadedRenderArtifact",
    "ArtifactLoadError",
    "load_render_artifact",
]
