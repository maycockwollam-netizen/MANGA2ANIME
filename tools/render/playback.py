"""Render sequence playback.

Provides synchronous playback control over an existing RenderPreview abstraction.

This module creates a deterministic playback controller that steps through
frames without threads, async, or caching.

Architecture:
    RenderPreview
        ↓
    RenderPlayback
        ↓
    current frame / seek / step

This module does NOT:
- Use threads or async
- Cache images
- Modify files
- Encode video
- Launch a UI
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from tools.render.preview import RenderPreview


class PlaybackError(Exception):
    """Error controlling render playback.

    Raised when playback operations fail (invalid frame index, invalid state, etc.).
    """

    pass


@dataclass
class RenderPlayback:
    """Synchronous controller for stepping through a RenderPreview.

    Provides deterministic frame-by-frame playback without threads or caching.

    Attributes:
        preview: The underlying RenderPreview being played.
        frame_rate: Frame rate in frames per second (must be positive).
        _current_index: Current position in frame_indices (private).
        _playing: Whether playback is marked as playing (private).

    Note:
        V1 is intentionally synchronous with no real-time timing.
        Use frame_duration for timing calculations externally.
    """

    preview: RenderPreview
    frame_rate: float
    _current_index: int = 0
    _playing: bool = False

    def __post_init__(self) -> None:
        """Validate frame_rate after initialization."""
        if self.frame_rate <= 0:
            raise PlaybackError(
                f"frame_rate must be positive, got {self.frame_rate}"
            )

    @property
    def frame_count(self) -> int:
        """Total number of frames in the sequence."""
        return self.preview.frame_count

    @property
    def frame_duration(self) -> float:
        """Duration of a single frame in seconds (1 / frame_rate)."""
        return 1.0 / self.frame_rate

    @property
    def current_frame_index(self) -> int:
        """Current frame index being played."""
        return self.preview.frame_indices[self._current_index]

    @property
    def current_frame_path(self) -> Path:
        """Path to the current frame's PNG file."""
        return self.preview.frame_paths[self._current_index]

    @property
    def playing(self) -> bool:
        """Whether playback is marked as playing."""
        return self._playing

    def play(self) -> None:
        """Mark playback as playing.

        Does not start a background thread or async behavior.
        V1 only marks the state; timing is external.
        """
        self._playing = True

    def pause(self) -> None:
        """Pause playback and preserve current position."""
        self._playing = False

    def stop(self) -> None:
        """Stop playback and reset to the first frame."""
        self._playing = False
        self._current_index = 0

    def seek(self, frame_index: int) -> None:
        """Move to a specific frame index.

        Args:
            frame_index: The frame index to seek to.

        Raises:
            PlaybackError: If frame_index is not in the sequence.
        """
        if frame_index not in self.preview.frame_indices:
            raise PlaybackError(
                f"Invalid frame index: {frame_index}. "
                f"Available: {self.preview.frame_indices}"
            )

        self._current_index = self.preview.frame_indices.index(frame_index)

    def step_forward(self) -> None:
        """Advance exactly one frame.

        Clamps at the final frame (does not wrap or error).
        """
        if self._current_index < len(self.preview.frame_indices) - 1:
            self._current_index += 1

    def step_backward(self) -> None:
        """Move exactly one frame backward.

        Clamps at the first frame (does not wrap or error).
        """
        if self._current_index > 0:
            self._current_index -= 1

    def current_frame_image(self) -> Image.Image:
        """Get the current frame's image.

        Delegates to RenderPreview.frame_image() with no caching.
        """
        return self.preview.frame_image(self.current_frame_index)
