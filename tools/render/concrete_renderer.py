"""Concrete renderer implementation using Pillow.

V1 implementation that renders RenderFrame to RGBA images using placeholder
rectangles. This is a proof-of-concept renderer that proves the pipeline works.

This module does NOT:
- Load real image assets
- Implement GPU rendering
- Access runtime animation internals
- Implement caching or batching
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from PIL import Image

from tools.frame.models import FrameTransform
from tools.render.exceptions import RendererError

if TYPE_CHECKING:
    from tools.render import RenderFrame


# Default placeholder entity size in pixels
DEFAULT_ENTITY_SIZE = 100


class ConcreteRenderer:
    """Concrete renderer using Pillow for RGBA image output.

    V1 renders placeholder colored rectangles for each clip_id in the frame.
    The color is deterministically derived from the clip_id.

    Attributes:
        canvas_size: Output image dimensions as (width, height).
        background: RGBA tuple for background color.

    Example:
        >>> from tools.render import ConcreteRenderer, RenderFrame
        >>> from tools.frame.models import FrameTransform
        >>>
        >>> renderer = ConcreteRenderer()
        >>> frame = RenderFrame(
        ...     frame_index=0,
        ...     timestamp_seconds=0.0,
        ...     frame_rate=24.0,
        ...     duration_frames=24,
        ...     transforms={"hero": FrameTransform(position_x=100)},
        ... )
        >>> renderer.render(frame)
        >>> image = renderer.last_output
        >>> image.size
        (800, 600)
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
        """
        # Apply defaults for None values
        pos_x = transform.position_x if transform.position_x is not None else 0.0
        pos_y = transform.position_y if transform.position_y is not None else 0.0
        scale = transform.scale if transform.scale is not None else 1.0
        rotation = transform.rotation_deg if transform.rotation_deg is not None else 0.0
        opacity = transform.opacity if transform.opacity is not None else 1.0
        anchor_x = transform.anchor_x if transform.anchor_x is not None else 0.5
        anchor_y = transform.anchor_y if transform.anchor_y is not None else 0.5

        # Calculate effective size
        if scale > 0:
            width = int(DEFAULT_ENTITY_SIZE * scale)
            height = int(DEFAULT_ENTITY_SIZE * scale)
        else:
            # Handle zero scale gracefully
            width = 1
            height = 1

        # Create entity image with deterministic color
        color = self._clip_id_to_color(clip_id, opacity)
        entity = Image.new("RGBA", (width, height), color)

        # Apply rotation if needed (before calculating anchor offset)
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
