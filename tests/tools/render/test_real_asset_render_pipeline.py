"""End-to-end integration tests for real asset rendering through the complete pipeline.

Tests the full flow:
    PNG asset
        ↓
    FrameTransform(source_path=...)
        ↓
    RenderFrame
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
    load/open artifact
        ↓
    frame access
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from PIL import Image

from tools.frame.models import FrameTransform
from tools.render import (
    RenderArtifact,
    RenderArtifactHandle,
    RenderArtifactInfo,
    RenderArtifactManifest,
    RenderFrame,
    RenderSessionInfo,
    create_artifact_manifest,
    create_render_artifact,
    create_render_session,
    export_render_frames,
    get_frame_image,
    get_session_info,
    open_render_artifact,
    read_artifact_manifest,
    validate_render_artifact,
    validate_render_session,
    write_artifact_manifest,
)


class TestRealAssetRenderPipeline:
    """End-to-end integration tests for real asset rendering pipeline."""

    @pytest.fixture
    def asset_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory for test assets."""
        return tmp_path

    @pytest.fixture
    def red_square_asset(self, asset_dir: Path) -> Path:
        """Create a red square RGBA asset for testing."""
        asset_path = asset_dir / "red_square.png"
        asset = Image.new("RGBA", (50, 50), color=(255, 0, 0, 255))
        asset.save(asset_path)
        return asset_path

    @pytest.fixture
    def blue_circle_asset(self, asset_dir: Path) -> Path:
        """Create a blue circle RGBA asset for testing."""
        asset_path = asset_dir / "blue_circle.png"
        asset = Image.new("RGBA", (40, 40), color=(0, 0, 255, 255))
        asset.save(asset_path)
        return asset_path

    @pytest.fixture
    def green_triangle_asset(self, asset_dir: Path) -> Path:
        """Create a green RGBA asset for testing."""
        asset_path = asset_dir / "green_triangle.png"
        asset = Image.new("RGBA", (30, 30), color=(0, 255, 0, 200))
        asset.save(asset_path)
        return asset_path

    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory for output."""
        out = tmp_path / "output"
        out.mkdir()
        return out

    @pytest.fixture
    def frames_with_asset(self, red_square_asset: Path, green_triangle_asset: Path) -> list[RenderFrame]:
        """Create a sequence of RenderFrames using real assets."""
        return [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=5,
                transforms={
                    "red_entity": FrameTransform(
                        position_x=100,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.5,
                        anchor_y=0.5,
                    ),
                },
            ),
            RenderFrame(
                frame_index=1,
                timestamp_seconds=1.0 / 24.0,
                frame_rate=24.0,
                duration_frames=5,
                transforms={
                    "red_entity": FrameTransform(
                        position_x=150,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.5,
                        anchor_y=0.5,
                    ),
                },
            ),
            RenderFrame(
                frame_index=2,
                timestamp_seconds=2.0 / 24.0,
                frame_rate=24.0,
                duration_frames=5,
                transforms={
                    "red_entity": FrameTransform(
                        position_x=200,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.5,
                        anchor_y=0.5,
                    ),
                    "green_entity": FrameTransform(
                        position_x=100,
                        position_y=200,
                        source_path=green_triangle_asset,
                        anchor_x=0.5,
                        anchor_y=0.5,
                        opacity=0.8,
                    ),
                },
            ),
            RenderFrame(
                frame_index=3,
                timestamp_seconds=3.0 / 24.0,
                frame_rate=24.0,
                duration_frames=5,
                transforms={
                    "red_entity": FrameTransform(
                        position_x=250,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.5,
                        anchor_y=0.5,
                        scale=1.5,
                    ),
                    "green_entity": FrameTransform(
                        position_x=100,
                        position_y=200,
                        source_path=green_triangle_asset,
                        anchor_x=0.5,
                        anchor_y=0.5,
                        opacity=0.8,
                    ),
                },
            ),
            RenderFrame(
                frame_index=4,
                timestamp_seconds=4.0 / 24.0,
                frame_rate=24.0,
                duration_frames=5,
                transforms={},
            ),
        ]

    def test_asset_to_artifact_end_to_end(
        self,
        red_square_asset: Path,
        blue_circle_asset: Path,
        tmp_path: Path,
    ) -> None:
        """Test complete asset → artifact pipeline."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create frames with assets
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms={
                    "entity_a": FrameTransform(
                        position_x=100,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.0,
                        anchor_y=0.0,
                    ),
                    "entity_b": FrameTransform(
                        position_x=200,
                        position_y=150,
                        source_path=blue_circle_asset,
                        anchor_x=0.0,
                        anchor_y=0.0,
                    ),
                },
            ),
            RenderFrame(
                frame_index=1,
                timestamp_seconds=1.0 / 24.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms={
                    "entity_a": FrameTransform(
                        position_x=150,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.0,
                        anchor_y=0.0,
                    ),
                    "entity_b": FrameTransform(
                        position_x=250,
                        position_y=150,
                        source_path=blue_circle_asset,
                        anchor_x=0.0,
                        anchor_y=0.0,
                    ),
                },
            ),
            RenderFrame(
                frame_index=2,
                timestamp_seconds=2.0 / 24.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms={
                    "entity_a": FrameTransform(
                        position_x=200,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.0,
                        anchor_y=0.0,
                        scale=1.5,
                    ),
                },
            ),
        ]

        # Export frames to PNG sequence
        count = export_render_frames(
            frames,
            output_dir,
            prefix="frame",
        )
        assert count == 3

        # Verify PNG files exist (format: frame_XXXXXX.png with 6 digits)
        for i in range(3):
            frame_path = output_dir / f"frame_{i:06d}.png"
            assert frame_path.exists(), f"Frame {i} does not exist: {frame_path}"
            assert frame_path.stat().st_size > 0

        # Create RenderSession
        session = create_render_session(output_dir, prefix="frame", frame_rate=24.0)
        assert session.frame_count == 3

        # Get session info
        session_info = get_session_info(session)
        assert isinstance(session_info, RenderSessionInfo)
        assert session_info.frame_count == 3
        assert session_info.frame_rate == 24.0

        # Create RenderArtifact
        artifact = create_render_artifact(session, validate=True)
        assert isinstance(artifact, RenderArtifact)

        # Create and write manifest
        manifest = create_artifact_manifest(artifact)
        assert isinstance(manifest, RenderArtifactManifest)

        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)
        assert manifest_path.exists()

        # Read manifest back
        loaded_manifest = read_artifact_manifest(manifest_path)
        assert loaded_manifest.frame_count == manifest.frame_count
        assert loaded_manifest.frame_indices == manifest.frame_indices
        assert loaded_manifest.dimensions == manifest.dimensions

        # Open artifact
        handle = open_render_artifact(manifest_path, validate=True)
        assert isinstance(handle, RenderArtifactHandle)

        # Verify handle info
        info = handle.info
        assert isinstance(info, RenderArtifactInfo)
        assert info.frame_count == 3
        assert info.frame_indices == (0, 1, 2)
        assert info.dimensions == (800, 600)  # Default canvas size

    def test_asset_transforms_survive_full_pipeline(
        self,
        red_square_asset: Path,
        tmp_path: Path,
    ) -> None:
        """Test that asset transforms survive the full pipeline."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create frames with scaled asset
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=2,
                transforms={
                    "hero": FrameTransform(
                        position_x=100,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.5,
                        anchor_y=0.5,
                        scale=2.0,  # Scale the 50x50 asset to 100x100
                    ),
                },
            ),
            RenderFrame(
                frame_index=1,
                timestamp_seconds=1.0 / 24.0,
                frame_rate=24.0,
                duration_frames=2,
                transforms={
                    "hero": FrameTransform(
                        position_x=200,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.5,
                        anchor_y=0.5,
                        scale=0.5,  # Scale to 25x25
                    ),
                },
            ),
        ]

        # Export
        export_render_frames(frames, output_dir, prefix="frame")

        # Create session (we just need to verify rendering, not artifact)
        session = create_render_session(output_dir, prefix="frame")

        # Verify asset was rendered at correct positions by checking frame content
        # Frame 0: scaled asset centered at (100, 100) with size 100x100
        # Frame 1: scaled asset centered at (200, 100) with size 25x25
        frame_0 = get_frame_image(session, 0)
        frame_1 = get_frame_image(session, 1)

        assert frame_0.mode == "RGBA"
        assert frame_1.mode == "RGBA"

        # Frame 0 should have red pixels covering a larger area (scaled 2x)
        # Frame 1 should have red pixels covering a smaller area (scaled 0.5x)
        # The center pixel of the scaled asset should be red
        # For frame 0: center at (100, 100), so pixel at (100, 100) should be red
        pixel_0 = frame_0.getpixel((100, 100))
        assert pixel_0[0] > 200  # Red channel should be high

        # For frame 1: center at (200, 100), so pixel at (200, 100) should be red
        pixel_1 = frame_1.getpixel((200, 100))
        assert pixel_1[0] > 200  # Red channel should be high

    def test_artifact_can_be_reloaded_and_accessed(
        self,
        red_square_asset: Path,
        tmp_path: Path,
    ) -> None:
        """Test that artifact can be reloaded and frames accessed."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create and export frames
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms={
                    "hero": FrameTransform(
                        position_x=100 + i * 50,
                        position_y=100,
                        source_path=red_square_asset,
                        anchor_x=0.0,
                        anchor_y=0.0,
                    ),
                },
            )
            for i in range(3)
        ]

        export_render_frames(frames, output_dir, prefix="frame")

        # Create session and artifact
        session = create_render_session(output_dir, prefix="frame")
        artifact = create_render_artifact(session)
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)

        # Open and access
        handle = open_render_artifact(manifest_path)

        # Test frame_path (format: frame_XXXXXX.png with 6 digits)
        for i in range(3):
            path = handle.frame_path(i)
            assert path == output_dir / f"frame_{i:06d}.png"

        # Test frame_image
        for i in range(3):
            image = handle.frame_image(i)
            assert image.mode == "RGBA"
            assert image.size == (800, 600)

        # Test frame_at_timestamp
        for i in range(3):
            timestamp = i / 24.0
            image = handle.frame_at_timestamp(timestamp)
            assert image.mode == "RGBA"

    def test_full_pipeline_validation(
        self,
        red_square_asset: Path,
        blue_circle_asset: Path,
        tmp_path: Path,
    ) -> None:
        """Test that validation works correctly at all pipeline boundaries."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create frames with multiple assets
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=2,
                transforms={
                    "entity_a": FrameTransform(
                        position_x=100,
                        position_y=100,
                        source_path=red_square_asset,
                    ),
                    "entity_b": FrameTransform(
                        position_x=200,
                        position_y=100,
                        source_path=blue_circle_asset,
                    ),
                },
            ),
            RenderFrame(
                frame_index=1,
                timestamp_seconds=1.0 / 24.0,
                frame_rate=24.0,
                duration_frames=2,
                transforms={
                    "entity_a": FrameTransform(
                        position_x=150,
                        position_y=100,
                        source_path=red_square_asset,
                    ),
                },
            ),
        ]

        export_render_frames(frames, output_dir, prefix="frame")

        # Create session and artifact with validation
        session = create_render_session(output_dir, prefix="frame")
        session_valid = validate_render_session(session)
        assert session_valid is not None

        artifact = create_render_artifact(session, validate=True)
        artifact_valid = validate_render_artifact(artifact)
        assert artifact_valid is not None

        # Create manifest
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)

        # Open with validation
        handle = open_render_artifact(manifest_path, validate=True)
        assert handle.info.frame_count == 2

    def test_corrupted_output_is_detected(
        self,
        red_square_asset: Path,
        tmp_path: Path,
    ) -> None:
        """Test that corrupted output is detected by validation."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create and export frames (format uses 6 digits)
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=2,
                transforms={
                    "hero": FrameTransform(
                        position_x=100,
                        position_y=100,
                        source_path=red_square_asset,
                    ),
                },
            )
            for i in range(2)
        ]

        export_render_frames(frames, output_dir, prefix="frame")

        # Create session and artifact
        session = create_render_session(output_dir, prefix="frame")
        artifact = create_render_artifact(session)
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)

        # Corrupt a PNG file (frame_000001.png)
        corrupt_path = output_dir / "frame_000001.png"
        with open(corrupt_path, "r+b") as f:
            f.seek(0)
            f.write(b"CORRUPTED")

        # Validation should detect the corruption
        corruption_detected = False
        try:
            handle = open_render_artifact(manifest_path, validate=True)
            # If we get here without exception, check that frame access fails
            try:
                handle.frame_image(1)
            except Exception:
                corruption_detected = True
        except Exception:
            # Exception during open - corruption detected
            corruption_detected = True

        assert corruption_detected, "Corruption was not detected"

        # Restore and verify validation passes again
        # Re-export
        for f in output_dir.glob("frame_*.png"):
            f.unlink()
        # Remove old manifest
        manifest_path.unlink()

        export_render_frames(frames, output_dir, prefix="frame")
        session = create_render_session(output_dir, prefix="frame")
        artifact = create_render_artifact(session, validate=True)
        manifest = create_artifact_manifest(artifact)
        write_artifact_manifest(manifest, manifest_path)

        # Now validation should pass
        handle = open_render_artifact(manifest_path, validate=True)
        assert handle.frame_image(0) is not None

    def test_pipeline_does_not_mutate_artifact(
        self,
        red_square_asset: Path,
        tmp_path: Path,
    ) -> None:
        """Test that reading/validation does not mutate the artifact."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create and export frames
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=2,
                transforms={
                    "hero": FrameTransform(
                        position_x=100,
                        position_y=100,
                        source_path=red_square_asset,
                    ),
                },
            )
            for i in range(2)
        ]

        export_render_frames(frames, output_dir, prefix="frame")

        # Capture original file hashes
        original_hashes = {}
        for png_file in sorted(output_dir.glob("frame_*.png")):
            with open(png_file, "rb") as f:
                original_hashes[png_file.name] = hashlib.sha256(f.read()).hexdigest()

        # Create manifest
        session = create_render_session(output_dir, prefix="frame")
        artifact = create_render_artifact(session)
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)

        # Capture manifest hash
        with open(manifest_path, "rb") as f:
            original_manifest_hash = hashlib.sha256(f.read()).hexdigest()

        # Load and access multiple times
        handle = open_render_artifact(manifest_path, validate=True)
        for _ in range(3):
            _ = handle.frame_image(0)
            _ = handle.frame_image(1)
            _ = handle.info

        # Validate multiple times
        for _ in range(3):
            _ = validate_render_session(session)
            _ = validate_render_artifact(artifact)

        # Verify files unchanged
        for png_file in sorted(output_dir.glob("frame_*.png")):
            with open(png_file, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            assert current_hash == original_hashes[png_file.name], f"{png_file.name} was mutated"

        with open(manifest_path, "rb") as f:
            current_manifest_hash = hashlib.sha256(f.read()).hexdigest()
        assert current_manifest_hash == original_manifest_hash, "Manifest was mutated"

    def test_pipeline_is_deterministic(
        self,
        red_square_asset: Path,
        blue_circle_asset: Path,
        tmp_path: Path,
    ) -> None:
        """Test that the pipeline produces deterministic results."""
        output_dir_1 = tmp_path / "output1"
        output_dir_2 = tmp_path / "output2"
        output_dir_1.mkdir()
        output_dir_2.mkdir()

        # Same frames for both runs
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms={
                    "entity_a": FrameTransform(
                        position_x=100 + i * 50,
                        position_y=100,
                        source_path=red_square_asset,
                    ),
                    "entity_b": FrameTransform(
                        position_x=200,
                        position_y=150 + i * 25,
                        source_path=blue_circle_asset,
                    ),
                },
            )
            for i in range(3)
        ]

        # Export to both directories
        export_render_frames(frames, output_dir_1, prefix="frame")
        export_render_frames(frames, output_dir_2, prefix="frame")

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
        assert manifest_1.dimensions == manifest_2.dimensions

        # Compare PNG files (format: frame_XXXXXX.png with 6 digits)
        for i in range(3):
            path_1 = output_dir_1 / f"frame_{i:06d}.png"
            path_2 = output_dir_2 / f"frame_{i:06d}.png"

            with open(path_1, "rb") as f:
                hash_1 = hashlib.sha256(f.read()).hexdigest()
            with open(path_2, "rb") as f:
                hash_2 = hashlib.sha256(f.read()).hexdigest()

            assert hash_1 == hash_2, f"Frame {i} differs between runs"

        # Compare frame images from handles
        manifest_path_1 = output_dir_1 / "manifest.json"
        manifest_path_2 = output_dir_2 / "manifest.json"
        write_artifact_manifest(manifest_1, manifest_path_1)
        write_artifact_manifest(manifest_2, manifest_path_2)

        handle_1 = open_render_artifact(manifest_path_1)
        handle_2 = open_render_artifact(manifest_path_2)

        for i in range(3):
            image_1 = handle_1.frame_image(i)
            image_2 = handle_2.frame_image(i)
            assert image_1.tobytes() == image_2.tobytes()

    def test_asset_with_all_transforms_through_pipeline(
        self,
        tmp_path: Path,
    ) -> None:
        """Test asset with all transforms through the complete pipeline."""
        # Create test asset
        asset_path = tmp_path / "test_asset.png"
        asset = Image.new("RGBA", (50, 50), color=(100, 150, 200, 220))
        asset.save(asset_path)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create frames with all transform options
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=1,
                transforms={
                    "hero": FrameTransform(
                        position_x=100,
                        position_y=100,
                        scale=2.0,
                        rotation_deg=45,
                        opacity=0.8,
                        anchor_x=0.5,
                        anchor_y=0.5,
                        source_path=asset_path,
                    ),
                },
            ),
        ]

        # Export
        count = export_render_frames(frames, output_dir, prefix="frame")
        assert count == 1

        # Create session and artifact
        session = create_render_session(output_dir, prefix="frame")
        artifact = create_render_artifact(session)

        # Get frame image
        image = get_frame_image(session, 0)
        assert image.mode == "RGBA"
        assert image.size == (800, 600)

        # Create manifest
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)

        # Open and verify
        handle = open_render_artifact(manifest_path)
        info = handle.info
        assert info.frame_count == 1
        assert info.frame_indices == (0,)

        # Access via handle
        handle_image = handle.frame_image(0)
        assert handle_image.tobytes() == image.tobytes()

    def test_empty_frame_in_sequence(
        self,
        red_square_asset: Path,
        tmp_path: Path,
    ) -> None:
        """Test that empty frames (no assets) work in the pipeline."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms={
                    "hero": FrameTransform(
                        position_x=100,
                        position_y=100,
                        source_path=red_square_asset,
                    ),
                },
            ),
            RenderFrame(
                frame_index=1,
                timestamp_seconds=1.0 / 24.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms={},  # Empty frame
            ),
            RenderFrame(
                frame_index=2,
                timestamp_seconds=2.0 / 24.0,
                frame_rate=24.0,
                duration_frames=3,
                transforms={
                    "hero": FrameTransform(
                        position_x=200,
                        position_y=100,
                        source_path=red_square_asset,
                    ),
                },
            ),
        ]

        # Export
        count = export_render_frames(frames, output_dir, prefix="frame")
        assert count == 3

        # Create session
        session = create_render_session(output_dir, prefix="frame")
        assert session.frame_count == 3

        # Frame 1 should be empty (background only)
        empty_frame = get_frame_image(session, 1)
        assert empty_frame.mode == "RGBA"

        # Create artifact and manifest
        artifact = create_render_artifact(session)
        manifest = create_artifact_manifest(artifact)
        manifest_path = output_dir / "manifest.json"
        write_artifact_manifest(manifest, manifest_path)

        # Open and verify empty frame is accessible
        handle = open_render_artifact(manifest_path)
        empty_handle_frame = handle.frame_image(1)
        assert empty_handle_frame.tobytes() == empty_frame.tobytes()


class TestForbiddenImports:
    """Tests for forbidden imports in render modules."""

    def test_no_forbidden_imports_in_production_render_modules(self) -> None:
        """Verify no forbidden imports exist in render production modules."""
        import ast

        render_modules = [
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
