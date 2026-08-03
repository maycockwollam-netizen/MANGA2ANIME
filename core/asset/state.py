"""Asset state."""

from typing import Any

from pydantic import BaseModel, Field


class AssetState(BaseModel):
    """Basic asset state representation."""

    enabled: bool = Field(default=True)
    available: bool = Field(default=True)
    verified: bool = Field(default=False)
    custom_state: dict[str, Any] = Field(default_factory=dict)

    def validate(self) -> list[str]:
        """Validate asset state.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        # No constraints currently
        return errors
