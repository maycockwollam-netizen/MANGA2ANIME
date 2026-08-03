"""Asset properties - type-specific asset metadata."""

from typing import Any

from pydantic import BaseModel, Field


class AssetProperties(BaseModel):
    """Extensible properties for an asset.

    Different asset types have different properties.
    Use optional fields to handle this variation.
    """

    # Image/video properties
    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)

    # Time-based properties
    duration: float | None = Field(default=None, ge=0.0)
    frame_count: int | None = Field(default=None, ge=0)

    # Audio properties
    sample_rate: int | None = Field(default=None, ge=0)
    channels: int | None = Field(default=None, ge=0)
    bit_rate: int | None = Field(default=None, ge=0)

    # Format properties
    format: str = Field(default="", max_length=100)
    codec: str = Field(default="", max_length=100)
    color_space: str = Field(default="", max_length=50)

    # Custom properties
    custom_attributes: dict[str, Any] = Field(default_factory=dict)

    def validate(self) -> list[str]:
        """Validate asset properties.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if self.width is not None and self.width < 0:
            errors.append("Width must be non-negative")
        if self.height is not None and self.height < 0:
            errors.append("Height must be non-negative")
        if self.duration is not None and self.duration < 0:
            errors.append("Duration must be non-negative")
        if self.frame_count is not None and self.frame_count < 0:
            errors.append("Frame count must be non-negative")
        if self.sample_rate is not None and self.sample_rate < 0:
            errors.append("Sample rate must be non-negative")
        if self.channels is not None and self.channels < 0:
            errors.append("Channels must be non-negative")
        if self.bit_rate is not None and self.bit_rate < 0:
            errors.append("Bit rate must be non-negative")
        if len(self.format) > 100:
            errors.append("Format must be 100 characters or less")
        if len(self.codec) > 100:
            errors.append("Codec must be 100 characters or less")
        if len(self.color_space) > 50:
            errors.append("Color space must be 50 characters or less")

        return errors

    def get_dimensions(self) -> tuple[int, int] | None:
        """Get dimensions if available.

        Returns:
            Tuple of (width, height) or None if not set.
        """
        if self.width is not None and self.height is not None:
            return (self.width, self.height)
        return None

    def get_aspect_ratio(self) -> float | None:
        """Calculate aspect ratio if dimensions available.

        Returns:
            Aspect ratio or None if dimensions not set.
        """
        dims = self.get_dimensions()
        if dims and dims[1] > 0:
            return dims[0] / dims[1]
        return None

    def is_image_like(self) -> bool:
        """Check if properties suggest an image-like asset.

        Returns:
            True if width and height are set.
        """
        return self.width is not None and self.height is not None

    def is_audio_like(self) -> bool:
        """Check if properties suggest an audio-like asset.

        Returns:
            True if duration is set.
        """
        return self.duration is not None

    def is_video_like(self) -> bool:
        """Check if properties suggest a video-like asset.

        Returns:
            True if dimensions and duration are set.
        """
        return (
            self.width is not None
            and self.height is not None
            and self.duration is not None
        )
