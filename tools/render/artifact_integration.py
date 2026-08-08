"""Render artifact integration.

Provides a unified, read-only interface for working with render artifacts.

This module combines the artifact loader and artifact access layers into a single
coherent public API. It acts as a thin facade that delegates to existing
functionality without duplicating logic.

Architecture:
    manifest.json
        ↓
    open_render_artifact()
        ↓
    RenderArtifactHandle
        ├── .loaded
        ├── .info
        ├── .frame_path()
        ├── .frame_image()
        └── .frame_at_timestamp()

This module does NOT:
- Modify files
- Create files
- Delete files
- Cache data
- Use threads or async
- Implement renderer logic
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image as PILImage

    from tools.render.artifact_access import RenderArtifactInfo
    from tools.render.artifact_loader import LoadedRenderArtifact


@dataclass(frozen=True)
class RenderArtifactHandle:
    """Immutable handle for working with a render artifact.

    This class provides a unified interface to access artifact metadata
    and frames without exposing the underlying loaded artifact directly.

    Attributes:
        loaded: The underlying loaded render artifact.

    Example:
        >>> handle = open_render_artifact(Path("output/manifest.json"))
        >>> print(f"Frames: {handle.info.frame_count}")
        >>> image = handle.frame_image(0)
    """

    loaded: LoadedRenderArtifact

    @property
    def info(self) -> RenderArtifactInfo:
        """Get immutable artifact information.

        Returns:
            RenderArtifactInfo with artifact metadata.
        """
        from tools.render.artifact_access import get_artifact_info

        return get_artifact_info(self.loaded)

    def frame_path(self, frame_index: int) -> Path:
        """Get the path to a specific frame.

        Args:
            frame_index: Index of the frame to retrieve.

        Returns:
            Path to the PNG file for the specified frame.

        Raises:
            ArtifactAccessError: If frame_index is invalid.
        """
        from tools.render.artifact_access import get_artifact_frame_path

        return get_artifact_frame_path(self.loaded, frame_index)

    def frame_image(self, frame_index: int) -> PILImage.Image:
        """Get the image data for a specific frame.

        Args:
            frame_index: Index of the frame to retrieve.

        Returns:
            PIL Image for the specified frame.

        Raises:
            ArtifactAccessError: If frame_index is invalid or image cannot be loaded.
        """
        from tools.render.artifact_access import get_artifact_frame_image

        return get_artifact_frame_image(self.loaded, frame_index)

    def frame_at_timestamp(self, timestamp: float) -> PILImage.Image:
        """Get the frame at a specific timestamp.

        Uses the frame rate from the artifact to calculate which frame
        corresponds to the given timestamp.

        Args:
            timestamp: Timestamp in seconds.

        Returns:
            PIL Image for the frame at the specified timestamp.

        Raises:
            ArtifactAccessError: If timestamp is invalid.
        """
        from tools.render.artifact_access import get_artifact_frame_at_timestamp

        return get_artifact_frame_at_timestamp(self.loaded, timestamp)


class ArtifactIntegrationError(Exception):
    """Error working with an integrated render artifact.

    Raised when artifact operations fail due to invalid state or
    missing files.
    """

    pass


def open_render_artifact(
    manifest_path: Path | str,
    *,
    validate: bool = True,
) -> RenderArtifactHandle:
    """Open a render artifact from its manifest file.

    This function loads and optionally validates a render artifact,
    returning an immutable handle for accessing its contents.

    Args:
        manifest_path: Path to the manifest.json file.
        validate: If True, perform full validation. Defaults to True.

    Returns:
        RenderArtifactHandle for accessing artifact contents.

    Raises:
        ArtifactLoadError: If manifest cannot be read or parsed.
        ArtifactValidationError: If validation fails and validate=True.
        ArtifactManifestValidationError: If manifest validation fails.

    Example:
        >>> handle = open_render_artifact(Path("output/manifest.json"))
        >>> print(f"Frames: {handle.info.frame_count}")
    """
    from tools.render.artifact_loader import load_render_artifact

    manifest_path = Path(manifest_path)

    try:
        loaded = load_render_artifact(manifest_path, validate=validate)
    except Exception as e:
        raise ArtifactIntegrationError(
            f"Failed to open render artifact: {e}"
        ) from e

    return RenderArtifactHandle(loaded=loaded)


def validate_render_artifact_handle(
    handle: RenderArtifactHandle,
) -> None:
    """Validate a render artifact handle.

    Performs full validation of the artifact including PNG sequence
    verification and manifest consistency checks.

    Args:
        handle: The render artifact handle to validate.

    Raises:
        ArtifactValidationError: If artifact validation fails.
        ArtifactManifestValidationError: If manifest validation fails.

    Example:
        >>> handle = open_render_artifact(path, validate=False)
        >>> validate_render_artifact_handle(handle)  # Explicit validation
    """
    from tools.render.artifact_manifest_validation import (
        ArtifactManifestValidationError,
        validate_artifact_manifest,
    )
    from tools.render.artifact_validation import (
        ArtifactValidationError,
        validate_render_artifact,
    )

    try:
        validate_render_artifact(handle.loaded.artifact)
    except ArtifactValidationError as e:
        raise ArtifactIntegrationError(
            f"Artifact validation failed: {e}"
        ) from e

    try:
        validate_artifact_manifest(handle.loaded.artifact, handle.loaded.manifest)
    except ArtifactManifestValidationError as e:
        raise ArtifactIntegrationError(
            f"Manifest validation failed: {e}"
        ) from e


__all__ = [
    "RenderArtifactHandle",
    "ArtifactIntegrationError",
    "open_render_artifact",
    "validate_render_artifact_handle",
]
