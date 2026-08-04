"""ReferenceResolver for resolving cross-module references."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from integration.context import ProjectContext
from integration.exceptions import DanglingReferenceError, ReferenceResolutionError

if TYPE_CHECKING:
    from core.asset import Asset
    from core.camera import Camera
    from core.character import Character
    from core.scene import Scene, SceneObject
    from core.timeline import Timeline, Track


class ReferenceResolver:
    """Resolves references between Core entities.

    Validates that referenced IDs exist in the ProjectContext
    and returns the corresponding objects when available.
    """

    def __init__(self, context: ProjectContext) -> None:
        """Initialize resolver with a context.

        Args:
            context: ProjectContext to use for resolution.
        """
        self._context = context

    def resolve_scene_reference(self, scene_id: str) -> Scene:
        """Resolve a scene reference.

        Args:
            scene_id: ID of scene to resolve.

        Returns:
            The resolved Scene.

        Raises:
            ReferenceResolutionError: If scene not found.
            DanglingReferenceError: If scene_id is non-empty but not found.
        """
        if not scene_id:
            raise ReferenceResolutionError(
                "Empty scene_id reference",
                reference_id=scene_id,
                reference_type="scene",
            )

        if not self._context.has_scene(scene_id):
            raise DanglingReferenceError(
                f"Scene reference '{scene_id}' not found in context",
                reference_id=scene_id,
                reference_type="scene",
            )

        return self._context.get_scene(scene_id)

    def resolve_character_reference(self, character_id: str) -> Character:
        """Resolve a character reference.

        Args:
            character_id: ID of character to resolve.

        Returns:
            The resolved Character.

        Raises:
            ReferenceResolutionError: If character not found.
            DanglingReferenceError: If character_id is non-empty but not found.
        """
        if not character_id:
            raise ReferenceResolutionError(
                "Empty character_id reference",
                reference_id=character_id,
                reference_type="character",
            )

        if not self._context.has_character(character_id):
            raise DanglingReferenceError(
                f"Character reference '{character_id}' not found in context",
                reference_id=character_id,
                reference_type="character",
            )

        return self._context.get_character(character_id)

    def resolve_camera_reference(self, camera_id: str) -> Camera:
        """Resolve a camera reference.

        Args:
            camera_id: ID of camera to resolve.

        Returns:
            The resolved Camera.

        Raises:
            ReferenceResolutionError: If camera not found.
            DanglingReferenceError: If camera_id is non-empty but not found.
        """
        if not camera_id:
            raise ReferenceResolutionError(
                "Empty camera_id reference",
                reference_id=camera_id,
                reference_type="camera",
            )

        if not self._context.has_camera(camera_id):
            raise DanglingReferenceError(
                f"Camera reference '{camera_id}' not found in context",
                reference_id=camera_id,
                reference_type="camera",
            )

        return self._context.get_camera(camera_id)

    def resolve_timeline_reference(self, timeline_id: str) -> Timeline:
        """Resolve a timeline reference.

        Args:
            timeline_id: ID of timeline to resolve.

        Returns:
            The resolved Timeline.

        Raises:
            ReferenceResolutionError: If timeline not found.
            DanglingReferenceError: If timeline_id is non-empty but not found.
        """
        if not timeline_id:
            raise ReferenceResolutionError(
                "Empty timeline_id reference",
                reference_id=timeline_id,
                reference_type="timeline",
            )

        if not self._context.has_timeline(timeline_id):
            raise DanglingReferenceError(
                f"Timeline reference '{timeline_id}' not found in context",
                reference_id=timeline_id,
                reference_type="timeline",
            )

        return self._context.get_timeline(timeline_id)

    def resolve_asset_reference(self, asset_id: str) -> Asset:
        """Resolve an asset reference.

        Args:
            asset_id: ID of asset to resolve.

        Returns:
            The resolved Asset.

        Raises:
            ReferenceResolutionError: If asset not found.
            DanglingReferenceError: If asset_id is non-empty but not found.
        """
        if not asset_id:
            raise ReferenceResolutionError(
                "Empty asset_id reference",
                reference_id=asset_id,
                reference_type="asset",
            )

        if not self._context.has_asset(asset_id):
            raise DanglingReferenceError(
                f"Asset reference '{asset_id}' not found in context",
                reference_id=asset_id,
                reference_type="asset",
            )

        return self._context.get_asset(asset_id)

    def resolve_object_reference(
        self, scene_id: str, object_id: str
    ) -> SceneObject:
        """Resolve a scene object reference.

        Args:
            scene_id: ID of scene containing the object.
            object_id: ID of object to resolve.

        Returns:
            The resolved SceneObject.

        Raises:
            ReferenceResolutionError: If scene or object not found.
            DanglingReferenceError: If references point to non-existent entities.
        """
        if not scene_id:
            raise ReferenceResolutionError(
                "Empty scene_id for object reference",
                reference_id=scene_id,
                reference_type="scene",
            )

        if not object_id:
            raise ReferenceResolutionError(
                "Empty object_id reference",
                reference_id=object_id,
                reference_type="object",
            )

        scene = self.resolve_scene_reference(scene_id)
        obj = scene.get_object(object_id)
        return obj

    def resolve_track_reference(
        self, timeline_id: str, track_id: str
    ) -> Track:
        """Resolve a timeline track reference.

        Args:
            timeline_id: ID of timeline containing the track.
            track_id: ID of track to resolve.

        Returns:
            The resolved Track.

        Raises:
            ReferenceResolutionError: If timeline or track not found.
            DanglingReferenceError: If references point to non-existent entities.
        """
        if not timeline_id:
            raise ReferenceResolutionError(
                "Empty timeline_id for track reference",
                reference_id=timeline_id,
                reference_type="timeline",
            )

        if not track_id:
            raise ReferenceResolutionError(
                "Empty track_id reference",
                reference_id=track_id,
                reference_type="track",
            )

        timeline = self.resolve_timeline_reference(timeline_id)
        track = timeline.get_track(track_id)
        return track

    def resolve_character_references(self, character: Character) -> dict[str, Any]:
        """Resolve all references for a character.

        Args:
            character: Character with references to resolve.

        Returns:
            Dictionary of resolved references.

        Raises:
            DanglingReferenceError: If any required reference is not found.
        """
        resolved: dict[str, Any] = {}
        refs = character.references

        # Scene reference
        if refs.scene_id:
            resolved["scene"] = self.resolve_scene_reference(refs.scene_id)

        # Object reference
        if refs.object_id:
            resolved["object"] = self.resolve_object_reference(
                refs.scene_id, refs.object_id
            )

        # Track references
        if refs.track_ids:
            resolved["tracks"] = []
            for track_id in refs.track_ids:
                # Track references require timeline_id which is not stored
                # Just validate the ID format for now
                if track_id:
                    resolved["tracks"].append(track_id)

        # Asset references
        if refs.design_asset_id:
            resolved["design_asset"] = self.resolve_asset_reference(
                refs.design_asset_id
            )
        if refs.portrait_asset_id:
            resolved["portrait_asset"] = self.resolve_asset_reference(
                refs.portrait_asset_id
            )
        if refs.model_asset_id:
            resolved["model_asset"] = self.resolve_asset_reference(
                refs.model_asset_id
            )
        if refs.voice_asset_id:
            resolved["voice_asset"] = self.resolve_asset_reference(
                refs.voice_asset_id
            )

        return resolved

    def resolve_camera_references(self, camera: Camera) -> dict[str, Any]:
        """Resolve all references for a camera.

        Args:
            camera: Camera with references to resolve.

        Returns:
            Dictionary of resolved references.

        Raises:
            DanglingReferenceError: If any required reference is not found.
        """
        resolved: dict[str, Any] = {}

        # Scene reference
        if camera.references.scene_id:
            resolved["scene"] = self.resolve_scene_reference(
                camera.references.scene_id
            )

        # Target reference (object in scene)
        if camera.references.target_id and camera.references.scene_id:
            resolved["target"] = self.resolve_object_reference(
                camera.references.scene_id, camera.references.target_id
            )

        return resolved
