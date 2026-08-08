"""Render session access API.

Provides read-only inspection and access functions for RenderSession.

This module provides high-level read-only access functions that delegate to:
- RenderSession (orchestration)
- RenderPreview (frame access)
- FrameTimeline (time/frame mapping)

Architecture:
    RenderSession
        ↓
    RenderSessionInfo (summary)
    get_frame_image (image access)
    get_frame_path (path access)
    get_frame_at_timestamp (time resolution)

This module does NOT:
- Modify files
- Cache images or data
- Use threads or async
- Encode video
- Launch GUI
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image

    from tools.render.session import RenderSession


class SessionAccessError(Exception):
    """Error accessing render session information.

    Raised when session access operations fail (invalid frame index, timestamp, etc.).
    """

    pass


@dataclass(frozen=True)
class RenderSessionInfo:
    """Immutable summary information for a RenderSession.

    Attributes:
        frame_count: Total number of frames in the sequence.
        frame_rate: Frame rate in frames per second.
        duration_seconds: Total duration in seconds.
        dimensions: Image dimensions as (width, height).
        mode: Image mode (e.g., "RGBA", "RGB").
        first_frame_index: Index of the first frame.
        last_frame_index: Index of the last frame.
    """

    frame_count: int
    frame_rate: float
    duration_seconds: float
    dimensions: tuple[int, int]
    mode: str
    first_frame_index: int
    last_frame_index: int


def get_session_info(session: RenderSession) -> RenderSessionInfo:
    """Return immutable summary information for a RenderSession.

    Args:
        session: The RenderSession to inspect.

    Returns:
        RenderSessionInfo containing session metadata.

    Example:
        >>> info = get_session_info(session)
        >>> print(f"Frames: {info.frame_count}")
        >>> print(f"Duration: {info.duration_seconds}s")
    """
    return RenderSessionInfo(
        frame_count=session.frame_count,
        frame_rate=session.frame_rate,
        duration_seconds=session.duration_seconds,
        dimensions=session.dimensions,
        mode=session.mode,
        first_frame_index=session.manifest.frame_indices[0],
        last_frame_index=session.manifest.frame_indices[-1],
    )


def get_frame_image(
    session: RenderSession,
    frame_index: int,
) -> Image.Image:
    """Return the requested frame image through the existing RenderPreview.

    Args:
        session: The RenderSession containing the frame.
        frame_index: The frame index to load.

    Returns:
        PIL Image for the requested frame.

    Raises:
        SessionAccessError: If frame_index is not in the sequence.

    Note:
        No caching is performed. Each call loads the image fresh.
    """
    try:
        return session.preview.frame_image(frame_index)
    except ValueError as e:
        raise SessionAccessError(
            f"Frame index {frame_index} not found in session. "
            f"Available: {session.preview.frame_indices}"
        ) from e


def get_frame_path(
    session: RenderSession,
    frame_index: int,
) -> Path:
    """Return the requested frame path through the existing RenderPreview.

    Args:
        session: The RenderSession containing the frame.
        frame_index: The frame index to look up.

    Returns:
        Path to the PNG file for the requested frame.

    Raises:
        SessionAccessError: If frame_index is not in the sequence.
    """
    try:
        return session.preview.frame_path(frame_index)
    except ValueError as e:
        raise SessionAccessError(
            f"Frame index {frame_index} not found in session. "
            f"Available: {session.preview.frame_indices}"
        ) from e


def get_frame_at_timestamp(
    session: RenderSession,
    timestamp: float,
) -> Image.Image:
    """Resolve timestamp through FrameTimeline and load that frame.

    Uses the FrameTimeline's frame_for_timestamp() to map the timestamp
    to a frame index, then loads that frame's image.

    Args:
        session: The RenderSession containing the timeline and frames.
        timestamp: Timestamp in seconds from sequence start.

    Returns:
        PIL Image for the frame at the given timestamp.

    Raises:
        SessionAccessError: If timestamp is invalid (negative or beyond duration).

    Note:
        No caching is performed. Each call resolves the timestamp and loads
        the image fresh.
    """
    from tools.render.timeline import TimelineError

    try:
        frame_index = session.timeline.frame_for_timestamp(timestamp)
    except TimelineError as e:
        raise SessionAccessError(
            f"Invalid timestamp {timestamp}: {e}"
        ) from e

    return get_frame_image(session, frame_index)


__all__ = [
    "RenderSessionInfo",
    "SessionAccessError",
    "get_session_info",
    "get_frame_image",
    "get_frame_path",
    "get_frame_at_timestamp",
]
