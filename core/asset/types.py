"""Asset type definitions."""

from enum import StrEnum


class AssetType(StrEnum):
    """Asset type classification.

    Represents the category of an asset in the Manga2Anime system.
    """

    # Image assets
    IMAGE = "image"
    MANGA_PAGE = "manga_page"
    CHARACTER_REFERENCE = "character_reference"
    BACKGROUND = "background"
    SPRITE = "sprite"
    TEXTURE = "texture"

    # Audio assets
    AUDIO = "audio"
    VOICE = "voice"
    MUSIC = "music"
    SFX = "sfx"

    # Media assets
    VIDEO = "video"
    ANIMATION = "animation"

    # Document/text assets
    FONT = "font"
    TEXTURE_ATLAS = "texture_atlas"

    # Data assets
    DATA = "data"
    CONFIG = "config"

    # Other
    OTHER = "other"

    @classmethod
    def is_image(cls, asset_type: "AssetType") -> bool:
        """Check if asset type is an image type.

        Args:
            asset_type: Asset type to check.

        Returns:
            True if image type.
        """
        return asset_type in {
            cls.IMAGE,
            cls.MANGA_PAGE,
            cls.CHARACTER_REFERENCE,
            cls.BACKGROUND,
            cls.SPRITE,
            cls.TEXTURE,
        }

    @classmethod
    def is_audio(cls, asset_type: "AssetType") -> bool:
        """Check if asset type is an audio type.

        Args:
            asset_type: Asset type to check.

        Returns:
            True if audio type.
        """
        return asset_type in {cls.AUDIO, cls.VOICE, cls.MUSIC, cls.SFX}

    @classmethod
    def is_video(cls, asset_type: "AssetType") -> bool:
        """Check if asset type is a video type.

        Args:
            asset_type: Asset type to check.

        Returns:
            True if video type.
        """
        return asset_type in {cls.VIDEO, cls.ANIMATION}
