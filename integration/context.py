"""ProjectContext - central container for Core entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from integration.registry import Registry

if TYPE_CHECKING:
    from core.asset import Asset
    from core.camera import Camera
    from core.character import Character
    from core.project import Project
    from core.scene import Scene
    from core.timeline import Timeline


class ProjectContext:
    """Central context for holding Core entities.

    Provides organized access to all Core entities through separate registries.
    Does not duplicate Core domain models - uses existing Core objects directly.
    """

    def __init__(self) -> None:
        """Initialize an empty context."""
        self._project: Project | None = None
        self._scenes: Registry[Scene] = Registry()
        self._characters: Registry[Character] = Registry()
        self._cameras: Registry[Camera] = Registry()
        self._timelines: Registry[Timeline] = Registry()
        self._assets: Registry[Asset] = Registry()

    # Project management

    def set_project(self, project: Project) -> Project:
        """Set the project.

        Args:
            project: Project to set.

        Returns:
            The project.
        """
        self._project = project
        return project

    def get_project(self) -> Project | None:
        """Get the project.

        Returns:
            The project or None if not set.
        """
        return self._project

    def has_project(self) -> bool:
        """Check if project is set.

        Returns:
            True if project is set.
        """
        return self._project is not None

    # Scene management

    def register_scene(self, scene: Scene) -> Scene:
        """Register a scene.

        Args:
            scene: Scene to register.

        Returns:
            The registered scene.
        """
        return self._scenes.register(scene)

    def unregister_scene(self, scene_id: str) -> Scene:
        """Unregister a scene.

        Args:
            scene_id: ID of scene to unregister.

        Returns:
            The unregistered scene.
        """
        return self._scenes.unregister(scene_id)

    def get_scene(self, scene_id: str) -> Scene:
        """Get a scene by ID.

        Args:
            scene_id: ID of scene to get.

        Returns:
            The scene.
        """
        return self._scenes.get(scene_id)

    def has_scene(self, scene_id: str) -> bool:
        """Check if scene exists.

        Args:
            scene_id: ID to check.

        Returns:
            True if scene exists.
        """
        return self._scenes.exists(scene_id)

    def list_scenes(self) -> list[Scene]:
        """List all scenes.

        Returns:
            List of scenes sorted by ID.
        """
        return self._scenes.list()

    def scene_count(self) -> int:
        """Get the number of scenes.

        Returns:
            Number of scenes.
        """
        return self._scenes.count()

    # Character management

    def register_character(self, character: Character) -> Character:
        """Register a character.

        Args:
            character: Character to register.

        Returns:
            The registered character.
        """
        return self._characters.register(character)

    def unregister_character(self, character_id: str) -> Character:
        """Unregister a character.

        Args:
            character_id: ID of character to unregister.

        Returns:
            The unregistered character.
        """
        return self._characters.unregister(character_id)

    def get_character(self, character_id: str) -> Character:
        """Get a character by ID.

        Args:
            character_id: ID of character to get.

        Returns:
            The character.
        """
        return self._characters.get(character_id)

    def has_character(self, character_id: str) -> bool:
        """Check if character exists.

        Args:
            character_id: ID to check.

        Returns:
            True if character exists.
        """
        return self._characters.exists(character_id)

    def list_characters(self) -> list[Character]:
        """List all characters.

        Returns:
            List of characters sorted by ID.
        """
        return self._characters.list()

    def character_count(self) -> int:
        """Get the number of characters.

        Returns:
            Number of characters.
        """
        return self._characters.count()

    # Camera management

    def register_camera(self, camera: Camera) -> Camera:
        """Register a camera.

        Args:
            camera: Camera to register.

        Returns:
            The registered camera.
        """
        return self._cameras.register(camera)

    def unregister_camera(self, camera_id: str) -> Camera:
        """Unregister a camera.

        Args:
            camera_id: ID of camera to unregister.

        Returns:
            The unregistered camera.
        """
        return self._cameras.unregister(camera_id)

    def get_camera(self, camera_id: str) -> Camera:
        """Get a camera by ID.

        Args:
            camera_id: ID of camera to get.

        Returns:
            The camera.
        """
        return self._cameras.get(camera_id)

    def has_camera(self, camera_id: str) -> bool:
        """Check if camera exists.

        Args:
            camera_id: ID to check.

        Returns:
            True if camera exists.
        """
        return self._cameras.exists(camera_id)

    def list_cameras(self) -> list[Camera]:
        """List all cameras.

        Returns:
            List of cameras sorted by ID.
        """
        return self._cameras.list()

    def camera_count(self) -> int:
        """Get the number of cameras.

        Returns:
            Number of cameras.
        """
        return self._cameras.count()

    # Timeline management

    def register_timeline(self, timeline: Timeline) -> Timeline:
        """Register a timeline.

        Args:
            timeline: Timeline to register.

        Returns:
            The registered timeline.
        """
        return self._timelines.register(timeline)

    def unregister_timeline(self, timeline_id: str) -> Timeline:
        """Unregister a timeline.

        Args:
            timeline_id: ID of timeline to unregister.

        Returns:
            The unregistered timeline.
        """
        return self._timelines.unregister(timeline_id)

    def get_timeline(self, timeline_id: str) -> Timeline:
        """Get a timeline by ID.

        Args:
            timeline_id: ID of timeline to get.

        Returns:
            The timeline.
        """
        return self._timelines.get(timeline_id)

    def has_timeline(self, timeline_id: str) -> bool:
        """Check if timeline exists.

        Args:
            timeline_id: ID to check.

        Returns:
            True if timeline exists.
        """
        return self._timelines.exists(timeline_id)

    def list_timelines(self) -> list[Timeline]:
        """List all timelines.

        Returns:
            List of timelines sorted by ID.
        """
        return self._timelines.list()

    def timeline_count(self) -> int:
        """Get the number of timelines.

        Returns:
            Number of timelines.
        """
        return self._timelines.count()

    # Asset management

    def register_asset(self, asset: Asset) -> Asset:
        """Register an asset.

        Args:
            asset: Asset to register.

        Returns:
            The registered asset.
        """
        return self._assets.register(asset)

    def unregister_asset(self, asset_id: str) -> Asset:
        """Unregister an asset.

        Args:
            asset_id: ID of asset to unregister.

        Returns:
            The unregistered asset.
        """
        return self._assets.unregister(asset_id)

    def get_asset(self, asset_id: str) -> Asset:
        """Get an asset by ID.

        Args:
            asset_id: ID of asset to get.

        Returns:
            The asset.
        """
        return self._assets.get(asset_id)

    def has_asset(self, asset_id: str) -> bool:
        """Check if asset exists.

        Args:
            asset_id: ID to check.

        Returns:
            True if asset exists.
        """
        return self._assets.exists(asset_id)

    def list_assets(self) -> list[Asset]:
        """List all assets.

        Returns:
            List of assets sorted by ID.
        """
        return self._assets.list()

    def asset_count(self) -> int:
        """Get the number of assets.

        Returns:
            Number of assets.
        """
        return self._assets.count()

    # Bulk operations

    def clear(self) -> None:
        """Clear all entities from the context."""
        self._project = None
        self._scenes.clear()
        self._characters.clear()
        self._cameras.clear()
        self._timelines.clear()
        self._assets.clear()

    def total_count(self) -> int:
        """Get total count of all entities.

        Returns:
            Total number of entities.
        """
        return (
            (1 if self._project else 0)
            + self._scenes.count()
            + self._characters.count()
            + self._cameras.count()
            + self._timelines.count()
            + self._assets.count()
        )
