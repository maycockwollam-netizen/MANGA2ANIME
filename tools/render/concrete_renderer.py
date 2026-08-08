"""Concrete renderer implementation using Pillow.

V1 implementation that renders RenderFrame to RGBA images using Pillow.

This renderer supports:
- Placeholder colored rectangles for entities without source assets
- Actual image assets when source_path is provided in FrameTransform

This module does NOT:
- Implement GPU rendering
- Access runtime animation internals
- Implement caching or batching
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from tools.frame.models import FrameTransform
from tools.render.exceptions import RendererError, TransformError

if TYPE_CHECKING:
    from tools.render import RenderFrame


# Default placeholder entity size in pixels
DEFAULT_ENTITY_SIZE = 100


class ConcreteRenderer:
    """Concrete renderer using Pillow for RGBA image output.

    V1 supports two rendering modes:
    - Placeholder: Colored rectangles for entities without source assets
    - Asset: Actual image assets when source_path is provided in FrameTransform

    The color for placeholder mode is deterministically derived from clip_id.

    Attributes:
        canvas_size: Output image dimensions as (width, height).
        background: RGBA tuple for background color.

    Example:
        >>> from tools.render import ConcreteRenderer, RenderFrame
        >>> from tools.frame.models import FrameTransform
        >>>
        >>> renderer = ConcreteRenderer()
        >>> # Placeholder rendering
        >>> frame = RenderFrame(
        ...     frame_index=0,
        ...     timestamp_seconds=0.0,
        ...     frame_rate=24.0,
        ...     duration_frames=24,
        ...     transforms={"hero": FrameTransform(position_x=100)},
        ... )
        >>> renderer.render(frame)
        >>>
        >>> # Asset rendering
        >>> asset_frame = RenderFrame(
        ...     frame_index=0,
        ...     timestamp_seconds=0.0,
        ...     frame_rate=24.0,
        ...     duration_frames=24,
        ...     transforms={"hero": FrameTransform(position_x=100, source_path=Path("sprite.png"))},
        ... )
        >>> renderer.render(asset_frame)
    """

    def __init__(
        self,
        canvas_size: tuple[int, int] = (800, 600),
        background: tuple[int, int, int, int] = (255, 255, 255, 255),
    ) -> None:
        """Initialize the concrete renderer.

        Args:
            canvas_size: Output image dimensions as (width, height).
            background: RGBA tuple for background color.

        Raises:
            RendererError: If canvas_size is not positive.
        """
        width, height = canvas_size
        if width <= 0:
            msg = f"canvas width must be positive, got {width}"
            raise RendererError(msg)
        if height <= 0:
            msg = f"canvas height must be positive, got {height}"
            raise RendererError(msg)

        self._canvas_size = canvas_size
        self._background = background
        self._last_output: Image.Image | None = None

    @property
    def canvas_size(self) -> tuple[int, int]:
        """Return the canvas size.

        Returns:
            The (width, height) of the output canvas.
        """
        return self._canvas_size

    @property
    def background(self) -> tuple[int, int, int, int]:
        """Return the background color.

        Returns:
            The RGBA tuple for the background.
        """
        return self._background

    @property
    def last_output(self) -> Image.Image | None:
        """Return the last rendered image.

        Returns:
            The most recently rendered RGBA Image, or None if no frame
            has been rendered yet.
        """
        return self._last_output

    def render(self, frame: RenderFrame) -> None:
        """Render a frame to an image.

        Args:
            frame: The RenderFrame to render.

        Note:
            This method creates a fresh RGBA image for each call.
            The image is stored in last_output and can be retrieved
            via the last_output property.
        """
        # Create fresh RGBA canvas
        image = Image.new("RGBA", self._canvas_size, self._background)

        # Render entities in sorted clip_id order for determinism
        for clip_id in sorted(frame.transforms.keys()):
            transform = frame.transforms[clip_id]
            entity, paste_x, paste_y = self._render_entity_with_position(
                clip_id, transform
            )
            image.paste(entity, (paste_x, paste_y), entity.split()[3])

        self._last_output = image

    def _render_entity_with_position(
        self, clip_id: str, transform: FrameTransform
    ) -> tuple[Image.Image, int, int]:
        """Render a single entity with its transform and return position.

        Args:
            clip_id: The entity identity key.
            transform: The transform to apply.

        Returns:
            Tuple of (entity Image, paste_x, paste_y).

        Raises:
            TransformError: If source_path is invalid or cannot be loaded.
        """
        # Apply defaults for None values
        pos_x = transform.position_x if transform.position_x is not None else 0.0
        pos_y = transform.position_y if transform.position_y is not None else 0.0
        scale = transform.scale if transform.scale is not None else 1.0
        rotation = transform.rotation_deg if transform.rotation_deg is not None else 0.0
        opacity = transform.opacity if transform.opacity is not None else 1.0
        anchor_x = transform.anchor_x if transform.anchor_x is not None else 0.5
        anchor_y = transform.anchor_y if transform.anchor_y is not None else 0.5

        # Load asset or create placeholder
        if transform.source_path is not None:
            entity = self._load_asset(transform.source_path, opacity)
            # Apply scale to assets (assets have natural size)
            if scale != 1.0:
                entity = self._apply_scale(entity, scale)
        else:
            # Create placeholder with scale applied directly to size
            entity = self._create_placeholder(clip_id, opacity, scale)

        # Apply rotation
        width, height = entity.size
        if rotation != 0.0:
            # Pillow rotates counter-clockwise by default
            # FrameTransform specifies clockwise positive
            # So we negate the rotation
            entity = entity.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
            # After rotation with expand=True, size changes
            width, height = entity.size

        # Calculate anchor offset (where in the entity the position maps to)
        anchor_offset_x = width * anchor_x
        anchor_offset_y = height * anchor_y

        # Calculate paste position (entity position minus anchor offset)
        # Pillow paste uses top-left corner
        paste_x = int(pos_x - anchor_offset_x)
        paste_y = int(pos_y - anchor_offset_y)

        return entity, paste_x, paste_y

    def _load_asset(self, source_path: Path, opacity: float) -> Image.Image:
        """Load an image asset from path.

        Args:
            source_path: Path to the image file.
            opacity: Opacity multiplier (0.0-1.0).

        Returns:
            Loaded RGBA Image with opacity applied.

        Raises:
            TransformError: If the file cannot be loaded or is invalid.
        """
        try:
            # Load the image
            image = Image.open(source_path)

            # Convert to RGBA to ensure consistent compositing
            if image.mode != "RGBA":
                image = image.convert("RGBA")

            # Apply opacity if not fully opaque
            if opacity < 1.0:
                # Create a new image with combined opacity
                # We need to copy to avoid mutating the original
                r, g, b, a = image.split()
                new_alpha = a.point(lambda x: int(x * opacity))
                image = Image.merge("RGBA", (r, g, b, new_alpha))

            return image

        except FileNotFoundError as e:
            raise TransformError(
                f"Asset not found: {source_path}"
            ) from e
        except Exception as e:
            raise TransformError(
                f"Failed to load asset '{source_path}': {e}"
            ) from e

    def _create_placeholder(
        self, clip_id: str, opacity: float, scale: float
    ) -> Image.Image:
        """Create a placeholder colored rectangle.

        Args:
            clip_id: The entity identity key.
            opacity: The opacity (0.0-1.0).
            scale: The scale factor (already applied to size).

        Returns:
            Placeholder RGBA Image with size calculated from scale.
        """
        # Calculate effective size using scale
        if scale > 0:
            width = int(DEFAULT_ENTITY_SIZE * scale)
            height = int(DEFAULT_ENTITY_SIZE * scale)
        else:
            # Handle zero scale gracefully
            width = 1
            height = 1

        # Create entity image with deterministic color
        color = self._clip_id_to_color(clip_id, opacity)
        return Image.new("RGBA", (width, height), color)

    def _apply_scale(self, image: Image.Image, scale: float) -> Image.Image:
        """Apply scale transform to an image.

        Args:
            image: The source image.
            scale: Scale factor.

        Returns:
            Scaled image.
        """
        if scale <= 0:
            # Return a 1x1 transparent pixel for zero/negative scale
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        orig_width, orig_height = image.size
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        # Ensure minimum size of 1
        new_width = max(1, new_width)
        new_height = max(1, new_height)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _clip_id_to_color(
        self, clip_id: str, opacity: float
    ) -> tuple[int, int, int, int]:
        """Derive a deterministic RGBA color from clip_id.

        Uses SHA-256 for stable cross-process determinism.
        Does NOT use Python's hash() which has randomization.

        Args:
            clip_id: The entity identity key.
            opacity: The alpha value (0.0-1.0).

        Returns:
            RGBA tuple with deterministic color.
        """
        digest = hashlib.sha256(clip_id.encode("utf-8")).digest()
        r = int(digest[0])  # First byte
        g = int(digest[1])  # Second byte
        b = int(digest[2])  # Third byte
        a = int(opacity * 255)  # Apply opacity
        return (r, g, b, a)
