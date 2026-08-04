"""IntegrationValidator for validating ProjectContext integrity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from integration.context import ProjectContext
from integration.exceptions import IntegrationValidationError

if TYPE_CHECKING:
    pass


class IntegrationValidator:
    """Validates the integrity of a ProjectContext.

    Checks for:
    - duplicate IDs across registries
    - missing referenced objects
    - dangling references
    - invalid cross-module relationships
    """

    def __init__(self, context: ProjectContext) -> None:
        """Initialize validator with a context.

        Args:
            context: ProjectContext to validate.
        """
        self._context = context

    def validate(self) -> list[str]:
        """Validate the entire context.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        errors.extend(self._check_duplicate_ids())
        errors.extend(self._check_character_scene_references())
        errors.extend(self._check_character_object_references())
        errors.extend(self._check_camera_scene_references())
        errors.extend(self._check_camera_target_references())
        errors.extend(self._check_asset_references())

        return errors

    def validate_or_raise(self) -> None:
        """Validate the context and raise if invalid.

        Raises:
            IntegrationValidationError: If validation fails.
        """
        errors = self.validate()
        if errors:
            raise IntegrationValidationError("Integration validation failed", errors=errors)

    def _check_duplicate_ids(self) -> list[str]:
        """Check for duplicate IDs across registries.

        Returns:
            List of error messages.
        """
        errors: list[str] = []
        seen_ids: dict[str, str] = {}

        # Check scenes
        for scene in self._context.list_scenes():
            if scene.id in seen_ids:
                errors.append(
                    f"Duplicate ID '{scene.id}' found in scenes and {seen_ids[scene.id]}"
                )
            else:
                seen_ids[scene.id] = "scenes"

        # Check characters
        for character in self._context.list_characters():
            if character.id in seen_ids:
                errors.append(
                    f"Duplicate ID '{character.id}' found in characters and {seen_ids[character.id]}"
                )
            else:
                seen_ids[character.id] = "characters"

        # Check cameras
        for camera in self._context.list_cameras():
            if camera.id in seen_ids:
                errors.append(
                    f"Duplicate ID '{camera.id}' found in cameras and {seen_ids[camera.id]}"
                )
            else:
                seen_ids[camera.id] = "cameras"

        # Check timelines
        for timeline in self._context.list_timelines():
            if timeline.id in seen_ids:
                errors.append(
                    f"Duplicate ID '{timeline.id}' found in timelines and {seen_ids[timeline.id]}"
                )
            else:
                seen_ids[timeline.id] = "timelines"

        # Check assets
        for asset in self._context.list_assets():
            if asset.id in seen_ids:
                errors.append(
                    f"Duplicate ID '{asset.id}' found in assets and {seen_ids[asset.id]}"
                )
            else:
                seen_ids[asset.id] = "assets"

        return errors

    def _check_character_scene_references(self) -> list[str]:
        """Check character scene references.

        Returns:
            List of error messages.
        """
        errors: list[str] = []

        for character in self._context.list_characters():
            scene_id = character.references.scene_id
            if scene_id and not self._context.has_scene(scene_id):
                errors.append(
                    f"Character '{character.id}' references non-existent scene '{scene_id}'"
                )

        return errors

    def _check_character_object_references(self) -> list[str]:
        """Check character object references.

        Returns:
            List of error messages.
        """
        errors: list[str] = []

        for character in self._context.list_characters():
            refs = character.references
            if refs.object_id:
                if not refs.scene_id:
                    errors.append(
                        f"Character '{character.id}' has object_id but no scene_id"
                    )
                elif self._context.has_scene(refs.scene_id):
                    scene = self._context.get_scene(refs.scene_id)
                    if refs.object_id not in scene.objects:
                        errors.append(
                            f"Character '{character.id}' references non-existent object '{refs.object_id}' in scene '{refs.scene_id}'"
                        )

        return errors

    def _check_camera_scene_references(self) -> list[str]:
        """Check camera scene references.

        Returns:
            List of error messages.
        """
        errors: list[str] = []

        for camera in self._context.list_cameras():
            refs = camera.references
            if refs.scene_id and not self._context.has_scene(refs.scene_id):
                errors.append(
                    f"Camera '{camera.id}' references non-existent scene '{refs.scene_id}'"
                )

        return errors

    def _check_camera_target_references(self) -> list[str]:
        """Check camera target references.

        Returns:
            List of error messages.
        """
        errors: list[str] = []

        for camera in self._context.list_cameras():
            refs = camera.references
            if refs.target_id:
                if not refs.scene_id:
                    errors.append(
                        f"Camera '{camera.id}' has target_id but no scene_id"
                    )
                elif self._context.has_scene(refs.scene_id):
                    scene = self._context.get_scene(refs.scene_id)
                    if refs.target_id not in scene.objects:
                        errors.append(
                            f"Camera '{camera.id}' references non-existent object '{refs.target_id}' in scene '{refs.scene_id}'"
                        )

        return errors

    def _check_asset_references(self) -> list[str]:
        """Check asset references in characters.

        Returns:
            List of error messages.
        """
        errors: list[str] = []

        for character in self._context.list_characters():
            refs = character.references
            if refs.design_asset_id and not self._context.has_asset(
                refs.design_asset_id
            ):
                errors.append(
                    f"Character '{character.id}' references non-existent design asset '{refs.design_asset_id}'"
                )

            if refs.portrait_asset_id and not self._context.has_asset(
                refs.portrait_asset_id
            ):
                errors.append(
                    f"Character '{character.id}' references non-existent portrait asset '{refs.portrait_asset_id}'"
                )

            if refs.model_asset_id and not self._context.has_asset(
                refs.model_asset_id
            ):
                errors.append(
                    f"Character '{character.id}' references non-existent model asset '{refs.model_asset_id}'"
                )

            if refs.voice_asset_id and not self._context.has_asset(
                refs.voice_asset_id
            ):
                errors.append(
                    f"Character '{character.id}' references non-existent voice asset '{refs.voice_asset_id}'"
                )

        return errors
