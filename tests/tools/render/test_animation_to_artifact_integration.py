"""Integration tests for Animation → Render → Artifact pipeline.

Tests the integration between the animation system and the asset-backed
render pipeline, verifying that real animation output can flow through
the existing render architecture.

Pipeline under test:
    AnimationOrchestrator
        ↓
    RenderFrame (animation-produced transforms)
        ↓
    Caller-level integration (adds source_path)
        ↓
    RenderFrame (with source_path)
        ↓
    ConcreteRenderer
        ↓
    PNG sequence
        ↓
    RenderSession
        ↓
    RenderArtifact
        ↓
    ArtifactManifest
        ↓
    open_render_artifact()
        ↓
    RenderArtifactHandle

Note on Architecture:
    The animation system produces FrameTransform objects without source_path.
    The render system expects source_path for asset-backed rendering.
    A caller/integration layer bridges these by adding source_path to transforms
    before rendering. This is the correct architectural separation:
    - Animation knows HOW to transform (position, scale, rotation, etc.)
    - Rendering knows WHAT to render (asset paths)
    - The caller layer connects them

    This test demonstrates the caller-level integration pattern without
    modifying the animation or render systems.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import MappingProxyType

import pytest
from PIL import Image

from runtime.animation.consumer import AnimationOrchestrator
from tools.frame.models import FrameTransform
from tools.manga_frame.character_animation import (
    CharacterAnimationBinding,
    CharacterAnimationMetadata,
    CharacterAnimationOutput,
    CharacterAnimationTarget,
    CharacterTransformInput,
    CharacterTransformInputSet,
)
from tools.render import (
    RenderFrame,
    bind_render_frame_assets,
    create_artifact_manifest,
    create_render_artifact,
    create_render_session,
    export_render_frames,
    get_session_info,
    open_render_artifact,
    read_artifact_manifest,
    validate_render_artifact,
    validate_render_session,
    write_artifact_manifest,
)


def create_animation_data(
    character_id: str,
    clip_id: str,
    start_frame: int,
    end_frame: int,
    start_x: float,
    end_x: float,
    sequence_id: str = "test_sequence",
) -> tuple[CharacterAnimationOutput, CharacterTransformInputSet]:
    """Create animation data for testing.

    This helper creates the minimal animation contract needed for testing.
    It demonstrates how the animation system produces transform data.

    Args:
        character_id: Character identifier
        clip_id: Clip identifier (used for reference, not part of contract)
        start_frame: Starting frame
        end_frame: Ending frame
        start_x: Starting X position
        end_x: Ending X position
        sequence_id: Sequence identifier

    Returns:
        Tuple of (CharacterAnimationOutput, CharacterTransformInputSet)
    """
    # Create bindings for all frames in the range
    # Each binding creates an appearance at a specific frame
    bindings = tuple(
        CharacterAnimationBinding(
            target=CharacterAnimationTarget(
                character_id=character_id,
                layer_id="main",
                sequence_id=sequence_id,
            ),
            frame_index=frame,
            palette_id=None,
        )
        for frame in range(start_frame, end_frame + 1)
    )

    output = CharacterAnimationOutput(
        sequence_id=sequence_id,
        bindings=bindings,
        metadata=CharacterAnimationMetadata(
            bindings_created=len(bindings),
            characters_bound=1,
            palettes_available=0,
            palettes_missing=1,
        ),
    )

    # Create transform inputs - defines HOW to transform
    # Linear interpolation from start to end
    keyframe_0_transform = FrameTransform(
        position_x=start_x,
        position_y=100.0,
        scale=1.0,
    )
    keyframe_end_transform = FrameTransform(
        position_x=end_x,
        position_y=100.0,
        scale=1.0,
    )

    transforms = (
        CharacterTransformInput(
            character_id=character_id,
            frame_index=start_frame,
            transform=keyframe_0_transform,
        ),
        CharacterTransformInput(
            character_id=character_id,
            frame_index=end_frame,
            transform=keyframe_end_transform,
        ),
    )

    transform_set = CharacterTransformInputSet(transforms=transforms)

    return output, transform_set


class TestAnimationToArtifactPipeline:
    """Integration tests for animation-to-artifact pipeline."""

    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create temporary output directory."""
        out = tmp_path / "output"
        out.mkdir()
        return out

    @pytest.fixture
    def asset_path(self, tmp_path: Path) -> Path:
        """Create a test asset (red square)."""
        asset = tmp_path / "test_asset.png"
        Image.new("RGBA", (50, 50), color=(255, 0, 0, 255)).save(asset)
        return asset

    @pytest.fixture
    def blue_asset_path(self, tmp_path: Path) -> Path:
        """Create a test asset (blue square)."""
        asset = tmp_path / "blue_asset.png"
        Image.new("RGBA", (40, 40), color=(0, 0, 255, 255)).save(asset)
        return asset

    def test_animation_produces_render_frames(
        self,
        asset_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test that animation system produces real RenderFrame objects."""
        # Create animation data
        anim_output, transform_set = create_animation_data(
            character_id="hero",
            clip_id="hero_main",
            start_frame=0,
            end_frame=5,
            start_x=100.0,
            end_x=300.0,
        )

        # Create orchestrator and load animation
        orchestrator = AnimationOrchestrator(frame_rate=24.0)
        clips = orchestrator.load(anim_output, transform_set)

        # Verify clips were created
        assert len(clips) == 1
        assert clips[0].clip_id == "hero_main"

        # Verify render_frame() produces RenderFrame with transforms
        frame = orchestrator.render_frame()

        assert isinstance(frame, RenderFrame)
        assert frame.frame_index == 0
        assert frame.frame_rate == 24.0
        # Duration is the last valid frame index (end_frame)
        assert frame.duration_frames == clips[0].end_frame

        # Verify transforms exist (without source_path - this is the animation output)
        assert "hero_main" in frame.transforms
        transform = frame.transforms["hero_main"]
        assert isinstance(transform, FrameTransform)
        assert transform.position_x == 100.0
        assert transform.position_y == 100.0

        # Note: source_path is None here - animation doesn't know about assets
        assert transform.source_path is None

    def test_animation_frame_renders_real_asset(
        self,
        asset_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test that animation frame with source_path can render real asset.

        This demonstrates the caller-level integration pattern:
        Animation produces transforms → Caller adds source_path → Renderer renders.
        """
        # Create animation
        anim_output, transform_set = create_animation_data(
            character_id="hero",
            clip_id="hero_main",
            start_frame=0,
            end_frame=2,
            start_x=100.0,
            end_x=200.0,
        )

        orchestrator = AnimationOrchestrator(frame_rate=24.0)
        orchestrator.load(anim_output, transform_set)

        # Get animation frame
        anim_frame = orchestrator.render_frame()

        # Caller-level integration: Create RenderFrame with source_path
        # This is the bridge between animation and rendering
        transforms_with_assets: dict[str, FrameTransform] = {}
        for clip_id, transform in anim_frame.transforms.items():
            # Create new transform with source_path added
            asset_transform = FrameTransform(
                position_x=transform.position_x,
                position_y=transform.position_y,
                scale=transform.scale,
                rotation_deg=transform.rotation_deg,
                opacity=transform.opacity,
                anchor_x=transform.anchor_x,
                anchor_y=transform.anchor_y,
                source_path=asset_path,  # Add asset path
            )
            transforms_with_assets[clip_id] = asset_transform

        # Create render frame with asset paths
        render_frame = RenderFrame(
            frame_index=anim_frame.frame_index,
            timestamp_seconds=anim_frame.timestamp_seconds,
            frame_rate=anim_frame.frame_rate,
            duration_frames=anim_frame.duration_frames,
            transforms=MappingProxyType(transforms_with_assets),
        )

        # Verify source_path is now set
        assert render_frame.transforms["hero_main"].source_path == asset_path

    def test_animation_sequence_exports_to_png(
        self,
        asset_path: Path,
        blue_asset_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test that animation sequence with assets exports to PNG sequence."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create animation with two characters
        anim_output_1, transform_set_1 = create_animation_data(
            character_id="hero",
            clip_id="hero_main",
            start_frame=0,
            end_frame=4,
            start_x=100.0,
            end_x=300.0,
        )

        anim_output_2, transform_set_2 = create_animation_data(
            character_id="villain",
            clip_id="villain_main",
            start_frame=0,
            end_frame=4,
            start_x=500.0,
            end_x=300.0,
        )

        # Combine animations
        # Note: In practice, a caller would manage multiple orchestrators
        # For this test, we'll create the frames manually

        # Create frames with caller-level integration
        frames: list[RenderFrame] = []
        for i in range(5):
            transforms: dict[str, FrameTransform] = {
                "hero_main": FrameTransform(
                    position_x=100.0 + i * 50,
                    position_y=100.0,
                    source_path=asset_path,
                ),
                "villain_main": FrameTransform(
                    position_x=500.0 - i * 50,
                    position_y=100.0,
                    source_path=blue_asset_path,
                ),
            }

            frame = RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=5,
                transforms=MappingProxyType(transforms),
            )
            frames.append(frame)

        # Export to PNG sequence
        count = export_render_frames(frames, output_dir, prefix="frame")
        assert count == 5

        # Verify PNG files exist
        for i in range(5):
            frame_path = output_dir / f"frame_{i:06d}.png"
            assert frame_path.exists()
            assert frame_path.stat().st_size > 0

            # Verify PNG is valid
            img = Image.open(frame_path)
            assert img.mode == "RGBA"
            assert img.size == (800, 600)

    def test_animation_sequence_creates_valid_session(
        self,
        asset_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test that animation sequence creates valid RenderSession."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create animation frames with assets
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms=MappingProxyType({
                    "entity": FrameTransform(
                        position_x=100.0 + i * 50,
                        position_y=100.0,
                        source_path=asset_path,
                    ),
                }),
            )
            for i in range(3)
        ]

        export_render_frames(frames, output_dir, prefix="frame")

        # Create session
        session = create_render_session(output_dir, prefix="frame", frame_rate=24.0)

        # Verify session metadata
        assert session.frame_count == 3
        assert session.duration_seconds == 3 / 24.0

        # Get session info
        info = get_session_info(session)
        assert info.frame_count == 3
        assert info.frame_rate == 24.0
        assert info.dimensions == (800, 600)
        assert info.mode == "RGBA"
        assert info.first_frame_index == 0
        assert info.last_frame_index == 2

    def test_animation_output_creates_reloadable_artifact(
        self,
        asset_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test that animation output creates reloadable RenderArtifact."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create and export frames
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms=MappingProxyType({
                    "hero": FrameTransform(
                        position_x=100.0 + i * 50,
                        position_y=100.0,
                        source_path=asset_path,
                    ),
                }),
            )
            for i in range(3)
        ]

        export_render_frames(frames, output_dir, prefix="frame")

        # Create session
        session = create_render_session(output_dir, prefix="frame")

        # Create artifact
        artifact = create_render_artifact(session, validate=True)
        assert artifact is not None

        # Create manifest
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)

        # Verify manifest
        assert manifest.frame_count == 3
        assert manifest.frame_indices == (0, 1, 2)
        assert manifest.dimensions == (800, 600)

        # Reload artifact
        loaded_manifest = read_artifact_manifest(manifest_path)
        assert loaded_manifest.frame_count == manifest.frame_count

        # Open handle
        handle = open_render_artifact(manifest_path, validate=True)

        # Verify handle
        info = handle.info
        assert info.frame_count == 3
        assert info.frame_indices == (0, 1, 2)
        assert info.dimensions == (800, 600)

        # Verify frame access
        for i in range(3):
            path = handle.frame_path(i)
            assert path == output_dir / f"frame_{i:06d}.png"

            image = handle.frame_image(i)
            assert image.mode == "RGBA"
            assert image.size == (800, 600)

            timestamp = i / 24.0
            image_at_ts = handle.frame_at_timestamp(timestamp)
            assert image_at_ts.mode == "RGBA"

    def test_animation_artifact_validation(
        self,
        asset_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test validation chain for animation-generated artifact."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create and export frames
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=2,
                transforms=MappingProxyType({
                    "hero": FrameTransform(
                        position_x=100.0 + i * 100,
                        position_y=100.0,
                        source_path=asset_path,
                    ),
                }),
            )
            for i in range(2)
        ]

        export_render_frames(frames, output_dir, prefix="frame")

        # Create session and validate
        session = create_render_session(output_dir, prefix="frame")
        session_validation = validate_render_session(session)
        assert session_validation is not None

        # Create artifact and validate
        artifact = create_render_artifact(session, validate=True)
        artifact_validation = validate_render_artifact(artifact)
        assert artifact_validation is not None

        # Create manifest
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)

        # Open with validation
        handle = open_render_artifact(manifest_path, validate=True)
        assert handle.info.frame_count == 2

    def test_corrupted_animation_artifact_detected(
        self,
        asset_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test that corrupted animation artifact is detected."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create and export frames
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=2,
                transforms=MappingProxyType({
                    "hero": FrameTransform(
                        position_x=100.0 + i * 100,
                        position_y=100.0,
                        source_path=asset_path,
                    ),
                }),
            )
            for i in range(2)
        ]

        export_render_frames(frames, output_dir, prefix="frame")

        # Create artifact
        session = create_render_session(output_dir, prefix="frame")
        artifact = create_render_artifact(session)
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)

        # Corrupt a PNG file
        corrupt_path = output_dir / "frame_000001.png"
        with open(corrupt_path, "r+b") as f:
            f.seek(0)
            f.write(b"CORRUPTED")

        # Corruption should be detected
        corruption_detected = False
        try:
            handle = open_render_artifact(manifest_path, validate=True)
            try:
                handle.frame_image(1)
            except Exception:
                corruption_detected = True
        except Exception:
            corruption_detected = True

        assert corruption_detected, "Corruption was not detected"

    def test_animation_render_pipeline_is_deterministic(
        self,
        asset_path: Path,
        blue_asset_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test that animation render pipeline produces deterministic results."""
        output_dir_1 = tmp_path / "output1"
        output_dir_2 = tmp_path / "output2"
        output_dir_1.mkdir()
        output_dir_2.mkdir()

        # Create identical frames for both runs
        def create_frames() -> list[RenderFrame]:
            return [
                RenderFrame(
                    frame_index=i,
                    timestamp_seconds=i / 24.0,
                    frame_rate=24.0,
                    duration_frames=3,
                    transforms=MappingProxyType({
                        "hero": FrameTransform(
                            position_x=100.0 + i * 50,
                            position_y=100.0,
                            source_path=asset_path,
                        ),
                        "villain": FrameTransform(
                            position_x=500.0 - i * 50,
                            position_y=100.0,
                            source_path=blue_asset_path,
                        ),
                    }),
                )
                for i in range(3)
            ]

        # Export to both directories
        frames_1 = create_frames()
        frames_2 = create_frames()

        export_render_frames(frames_1, output_dir_1, prefix="frame")
        export_render_frames(frames_2, output_dir_2, prefix="frame")

        # Create sessions and artifacts
        session_1 = create_render_session(output_dir_1, prefix="frame")
        session_2 = create_render_session(output_dir_2, prefix="frame")

        artifact_1 = create_render_artifact(session_1)
        artifact_2 = create_render_artifact(session_2)

        # Compare session info
        info_1 = get_session_info(session_1)
        info_2 = get_session_info(session_2)
        assert info_1.frame_count == info_2.frame_count
        assert info_1.frame_rate == info_2.frame_rate
        assert info_1.dimensions == info_2.dimensions

        # Compare artifacts
        manifest_1 = create_artifact_manifest(artifact_1)
        manifest_2 = create_artifact_manifest(artifact_2)
        assert manifest_1.frame_count == manifest_2.frame_count
        assert manifest_1.frame_indices == manifest_2.frame_indices

        # Compare PNG files
        for i in range(3):
            path_1 = output_dir_1 / f"frame_{i:06d}.png"
            path_2 = output_dir_2 / f"frame_{i:06d}.png"

            with open(path_1, "rb") as f:
                hash_1 = hashlib.sha256(f.read()).hexdigest()
            with open(path_2, "rb") as f:
                hash_2 = hashlib.sha256(f.read()).hexdigest()

            assert hash_1 == hash_2, f"Frame {i} differs between runs"

    def test_animation_to_artifact_with_bind_render_frame_assets(
        self,
        asset_path: Path,
        blue_asset_path: Path,
        tmp_path: Path,
    ) -> None:
        """Test full pipeline: AnimationOrchestrator → bind_render_frame_assets → Artifact.

        This test proves the complete integration:
            AnimationOrchestrator
                ↓
            RenderFrame (animation-produced transforms)
                ↓
            bind_render_frame_assets()  ← New utility
                ↓
            RenderFrame (with source_path)
                ↓
            ConcreteRenderer
                ↓
            PNG sequence
                ↓
            RenderSession
                ↓
            RenderArtifact
                ↓
            Manifest
                ↓
            open_render_artifact()
                ↓
            RenderArtifactHandle
        """
        # Step 1: Create animation data
        anim_output, transform_set = create_animation_data(
            character_id="hero",
            clip_id="hero_main",
            start_frame=0,
            end_frame=4,
            start_x=100.0,
            end_x=300.0,
        )

        # Step 2: Create orchestrator and load animation
        orchestrator = AnimationOrchestrator(frame_rate=24.0)
        orchestrator.load(anim_output, transform_set)

        # Step 3: Get animation frame (without source_path)
        anim_frame = orchestrator.render_frame()
        assert anim_frame.transforms["hero_main"].source_path is None

        # Step 4: Create bound frames for the full sequence using bind_render_frame_assets
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        frames: list[RenderFrame] = []
        for i in range(5):
            # Advance orchestrator to each frame
            orchestrator.seek(i)
            anim_frame = orchestrator.render_frame()

            # Use bind_render_frame_assets to add asset paths
            bound_frame = bind_render_frame_assets(
                anim_frame,
                {"hero_main": asset_path},
            )

            # Create new frame with explicit metadata (bind_render_frame_assets preserves timing)
            frame = RenderFrame(
                frame_index=bound_frame.frame_index,
                timestamp_seconds=bound_frame.timestamp_seconds,
                frame_rate=bound_frame.frame_rate,
                duration_frames=bound_frame.duration_frames,
                transforms=bound_frame.transforms,
            )
            frames.append(frame)

        # Step 5: Export to PNG sequence
        count = export_render_frames(frames, output_dir, prefix="frame")
        assert count == 5

        # Verify PNG files exist
        for i in range(5):
            frame_path = output_dir / f"frame_{i:06d}.png"
            assert frame_path.exists()
            img = Image.open(frame_path)
            assert img.mode == "RGBA"
            assert img.size == (800, 600)

        # Step 6: Create RenderSession
        session = create_render_session(output_dir, prefix="frame")
        assert session.frame_count == 5

        # Step 7: Create RenderArtifact
        artifact = create_render_artifact(session, validate=True)
        assert artifact is not None

        # Step 8: Create and write manifest
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)
        assert manifest_path.exists()

        # Step 9: Reload manifest and open artifact
        loaded_manifest = read_artifact_manifest(manifest_path)
        assert loaded_manifest.frame_count == 5
        assert loaded_manifest.frame_indices == (0, 1, 2, 3, 4)

        # Step 10: Open handle
        handle = open_render_artifact(manifest_path, validate=True)
        assert handle.info.frame_count == 5
        assert handle.info.frame_indices == (0, 1, 2, 3, 4)

        # Step 11: Verify frame access works
        for i in range(5):
            path = handle.frame_path(i)
            assert path == output_dir / f"frame_{i:06d}.png"

            image = handle.frame_image(i)
            assert image.mode == "RGBA"
            assert image.size == (800, 600)

            timestamp = i / 24.0
            image_at_ts = handle.frame_at_timestamp(timestamp)
            assert image_at_ts.mode == "RGBA"

        # Step 12: Verify original orchestrator frame was not mutated
        orchestrator.seek(0)
        original_frame = orchestrator.render_frame()
        assert original_frame.transforms["hero_main"].source_path is None

    def test_no_forbidden_imports_in_render(
        self,
        tmp_path: Path,
    ) -> None:
        """Verify render modules don't import forbidden dependencies."""
        import ast

        render_modules = [
            "tools/render/__init__.py",
            "tools/render/concrete_renderer.py",
            "tools/render/protocol.py",
            "tools/render/exceptions.py",
        ]

        forbidden = [
            "runtime",
            "AnimationRuntime",
            "AnimationTimeline",
            "AnimationClip",
            "tools.manga_frame",
        ]

        for module_path in render_modules:
            with open(module_path) as f:
                source = f.read()

            tree = ast.parse(source)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            for imp in imports:
                for forbid in forbidden:
                    assert forbid not in imp, f"Forbidden import '{forbid}' found in {module_path}"
