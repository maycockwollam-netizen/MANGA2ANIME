"""Integration tests for complete render pipeline.

Verifies the full stack from PNG sequence through all layers:
    PNG sequence
        ↓
    RenderSession
        ↓
    RenderArtifact
        ↓
    RenderArtifactManifest
        ↓
    RenderArtifactHandle
        ↓
    Frame access

These tests verify CROSS-LAYER behavior and metadata preservation
across the entire render tooling stack.
"""

import ast
import json
import tempfile
from pathlib import Path

import pytest

from tools.render import (
    RenderFrame,
    create_artifact_manifest,
    create_render_artifact,
    create_render_session,
    export_render_frames,
    get_frame_at_timestamp,
    get_frame_image,
    get_frame_path,
    get_session_info,
    open_render_artifact,
    read_artifact_manifest,
    validate_artifact_manifest,
    validate_render_artifact,
    validate_render_artifact_handle,
    validate_render_session,
    write_artifact_manifest,
)


def create_offset_frames(
    start_index: int,
    count: int,
    frame_rate: float = 24.0,
    duration_frames: int = 48,
) -> list[RenderFrame]:
    """Create a sequence of frames with offset indices.

    Args:
        start_index: First frame index (e.g., 10 for 10-14)
        count: Number of frames
        frame_rate: Frame rate
        duration_frames: Total animation duration in frames

    Returns:
        List of RenderFrame with sequential indices starting from start_index.
    """
    return [
        RenderFrame(
            frame_index=start_index + i,
            timestamp_seconds=(start_index + i) / frame_rate,
            frame_rate=frame_rate,
            duration_frames=duration_frames,
            transforms={},
        )
        for i in range(count)
    ]


class TestPipelineMetadataPreservation:
    """Tests verifying metadata survives all pipeline layers."""

    def test_metadata_preservation_through_session_to_artifact(self) -> None:
        """Verify metadata is preserved from PNG sequence through artifact."""
        frames = create_offset_frames(start_index=10, count=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            # PNG sequence
            export_render_frames(frames, tmpdir)

            # Session layer
            session = create_render_session(tmpdir)
            session_info = get_session_info(session)

            # Artifact layer
            artifact = create_render_artifact(session)

            # Verify metadata matches
            assert artifact.output_dir == Path(tmpdir)
            assert artifact.frame_count == 5
            assert artifact.frame_indices == (10, 11, 12, 13, 14)
            assert artifact.dimensions == (800, 600)
            assert artifact.mode == "RGBA"

            # Session info should match
            assert session_info.frame_count == 5
            assert session_info.first_frame_index == 10
            assert session_info.last_frame_index == 14

    def test_metadata_preservation_through_manifest_serialization(self) -> None:
        """Verify metadata survives manifest write/read cycle."""
        frames = create_offset_frames(start_index=20, count=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Read back
            loaded_manifest = read_artifact_manifest(manifest_path)

            # Verify all fields match
            assert loaded_manifest.output_dir == manifest.output_dir
            assert loaded_manifest.prefix == manifest.prefix
            assert loaded_manifest.frame_count == manifest.frame_count
            assert loaded_manifest.frame_indices == manifest.frame_indices
            assert loaded_manifest.frame_rate == manifest.frame_rate
            assert loaded_manifest.duration_seconds == manifest.duration_seconds
            assert loaded_manifest.dimensions == manifest.dimensions
            assert loaded_manifest.mode == manifest.mode

    def test_metadata_preservation_through_full_pipeline(self) -> None:
        """Verify metadata survives PNG → Handle full pipeline."""
        frames = create_offset_frames(start_index=5, count=4)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Load through full pipeline
            handle = open_render_artifact(manifest_path)

            # Verify handle info matches original
            assert handle.info.frame_count == 4
            assert handle.info.frame_indices == (5, 6, 7, 8)
            assert handle.info.dimensions == (800, 600)
            assert handle.info.mode == "RGBA"


class TestFrameAccessAcrossLayers:
    """Tests verifying frame access works across all layers."""

    def test_frame_access_by_index_at_session_layer(self) -> None:
        """Test frame access by index at session layer."""
        frames = create_offset_frames(start_index=15, count=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)

            # Access each frame by index
            for expected_idx in [15, 16, 17]:
                image = get_frame_image(session, expected_idx)
                path = get_frame_path(session, expected_idx)

                assert image.size == (800, 600)
                assert path.exists()
                assert path.name == f"frame_{expected_idx:06d}.png"

    def test_frame_access_by_index_at_artifact_layer(self) -> None:
        """Test frame access by index through RenderArtifactHandle."""
        frames = create_offset_frames(start_index=25, count=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Open to get RenderArtifactHandle for artifact access
            handle = open_render_artifact(manifest_path)

            # Access each frame by index
            for expected_idx in [25, 26, 27]:
                image = handle.frame_image(expected_idx)
                path = handle.frame_path(expected_idx)

                assert image.size == (800, 600)
                assert path.exists()

    def test_frame_access_by_index_at_handle_layer(self) -> None:
        """Test frame access by index at handle layer."""
        frames = create_offset_frames(start_index=100, count=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            handle = open_render_artifact(manifest_path)

            # Access each frame by index
            for expected_idx in [100, 101, 102]:
                image = handle.frame_image(expected_idx)
                path = handle.frame_path(expected_idx)

                assert image.size == (800, 600)
                assert path.exists()

    def test_timestamp_access_at_session_layer(self) -> None:
        """Test frame access by timestamp at session layer."""
        frames = create_offset_frames(start_index=0, count=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)

            # Access frames by timestamp
            # Frame 2 at timestamp 2/24 = 0.0833...
            image = get_frame_at_timestamp(session, 0.0833)
            assert image.size == (800, 600)

            # Frame 4 at timestamp 4/24 = 0.1666...
            image = get_frame_at_timestamp(session, 0.1666)
            assert image.size == (800, 600)

    def test_timestamp_access_at_artifact_layer(self) -> None:
        """Test frame access by timestamp through RenderArtifactHandle."""
        frames = create_offset_frames(start_index=0, count=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Open to get RenderArtifactHandle for artifact access
            handle = open_render_artifact(manifest_path)

            # Access frames by timestamp
            image = handle.frame_at_timestamp(0.1)
            assert image.size == (800, 600)

    def test_timestamp_access_at_handle_layer(self) -> None:
        """Test frame access by timestamp at handle layer."""
        frames = create_offset_frames(start_index=0, count=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            handle = open_render_artifact(manifest_path)

            # Access frames by timestamp
            image = handle.frame_at_timestamp(0.1)
            assert image.size == (800, 600)


class TestValidationBoundaries:
    """Tests verifying validation at each boundary."""

    def test_session_validation_succeeds(self) -> None:
        """Test session validation passes for valid sequence."""
        frames = create_offset_frames(start_index=1, count=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)

            result = validate_render_session(session)
            assert result.frame_count == 3
            assert result.frame_indices == (1, 2, 3)

    def test_artifact_validation_succeeds(self) -> None:
        """Test artifact validation passes for valid artifact."""
        frames = create_offset_frames(start_index=2, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)

            result = validate_render_artifact(artifact)
            assert result.frame_count == 2

    def test_manifest_validation_succeeds(self) -> None:
        """Test manifest validation passes for valid manifest."""
        frames = create_offset_frames(start_index=3, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

            result = validate_artifact_manifest(artifact, manifest)
            assert result.frame_count == 2

    def test_handle_validation_succeeds(self) -> None:
        """Test handle validation passes for valid handle."""
        frames = create_offset_frames(start_index=4, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            handle = open_render_artifact(manifest_path)
            validate_render_artifact_handle(handle)

    def test_open_with_validation_detects_corruption(self) -> None:
        """Test open with validation detects corrupted PNG."""
        frames = create_offset_frames(start_index=5, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Corrupt PNG
            png_path = Path(tmpdir) / "frame_000005.png"
            png_path.write_bytes(b"not valid png")

            # Should fail
            from tools.render.artifact_integration import ArtifactIntegrationError

            with pytest.raises(ArtifactIntegrationError):
                open_render_artifact(manifest_path)


class TestMalformedArtifacts:
    """Tests verifying clean failures for malformed artifacts."""

    def test_malformed_manifest_json(self) -> None:
        """Test malformed JSON manifest fails cleanly."""
        frames = create_offset_frames(start_index=6, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"

            # Write malformed JSON
            manifest_path.write_text("not valid json {")

            from tools.render.artifact_integration import ArtifactIntegrationError

            with pytest.raises(ArtifactIntegrationError):
                open_render_artifact(manifest_path)

    def test_manifest_artifact_mismatch(self) -> None:
        """Test manifest/artifact mismatch fails cleanly."""
        frames = create_offset_frames(start_index=7, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"

            # Write manifest with wrong frame_count
            manifest_path.write_text(
                '{"output_dir": "%s", "prefix": "%s", "frame_count": 99, '
                '"frame_indices": [0], "frame_rate": 24.0, "duration_seconds": 1.0, '
                '"dimensions": [800, 600], "mode": "RGBA"}'  # noqa: UP031
                % (tmpdir, manifest.prefix)
            )

            from tools.render.artifact_integration import ArtifactIntegrationError

            with pytest.raises(ArtifactIntegrationError):
                open_render_artifact(manifest_path)


class TestNoMutation:
    """Tests verifying no filesystem mutation during operations."""

    def test_png_files_unchanged_after_session_access(self) -> None:
        """Test PNG files are not modified during session access."""
        frames = create_offset_frames(start_index=8, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)

            # Record file contents
            file_hashes = {}
            for png_file in Path(tmpdir).glob("*.png"):
                file_hashes[png_file.name] = png_file.read_bytes()

            session = create_render_session(tmpdir)

            # Access frames multiple times
            for _ in range(3):
                get_frame_image(session, 8)
                get_frame_image(session, 9)

            # Verify no changes
            for png_file in Path(tmpdir).glob("*.png"):
                assert png_file.read_bytes() == file_hashes[png_file.name]

    def test_png_files_unchanged_after_artifact_access(self) -> None:
        """Test PNG files are not modified during artifact access."""
        frames = create_offset_frames(start_index=9, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Open to get RenderArtifactHandle
            handle = open_render_artifact(manifest_path)

            # Record file contents
            file_hashes = {}
            for png_file in Path(tmpdir).glob("*.png"):
                file_hashes[png_file.name] = png_file.read_bytes()

            # Access frames multiple times
            for _ in range(3):
                handle.frame_image(9)
                handle.frame_image(10)

            # Verify no changes
            for png_file in Path(tmpdir).glob("*.png"):
                assert png_file.read_bytes() == file_hashes[png_file.name]

    def test_manifest_unchanged_after_load(self) -> None:
        """Test manifest file is not modified during load."""
        frames = create_offset_frames(start_index=10, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Record manifest content
            original_content = manifest_path.read_bytes()

            # Load artifact
            handle = open_render_artifact(manifest_path)
            _ = handle.info
            _ = handle.frame_image(10)

            # Verify manifest unchanged
            assert manifest_path.read_bytes() == original_content


class TestDeterminism:
    """Tests verifying deterministic behavior."""

    def test_repeated_session_access_returns_identical_data(self) -> None:
        """Test repeated session access returns identical results."""
        frames = create_offset_frames(start_index=11, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)

            # Access same frame multiple times
            img1 = get_frame_image(session, 11)
            img2 = get_frame_image(session, 11)

            # Images should be identical
            assert img1.size == img2.size
            assert list(img1.getdata()) == list(img2.getdata())

    def test_repeated_artifact_access_returns_identical_data(self) -> None:
        """Test repeated artifact access returns identical results."""
        frames = create_offset_frames(start_index=12, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Open to get RenderArtifactHandle
            handle = open_render_artifact(manifest_path)

            # Access same frame multiple times
            img1 = handle.frame_image(12)
            img2 = handle.frame_image(12)

            # Images should be identical
            assert img1.size == img2.size
            assert list(img1.getdata()) == list(img2.getdata())

    def test_repeated_handle_access_returns_identical_data(self) -> None:
        """Test repeated handle access returns identical results."""
        frames = create_offset_frames(start_index=13, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            handle = open_render_artifact(manifest_path)

            # Access same frame multiple times
            img1 = handle.frame_image(13)
            img2 = handle.frame_image(13)

            # Images should be identical
            assert img1.size == img2.size
            assert list(img1.getdata()) == list(img2.getdata())


class TestNoCaching:
    """Tests verifying no caching is performed."""

    def test_no_caching_between_loads(self) -> None:
        """Test each load creates new objects."""
        frames = create_offset_frames(start_index=14, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Load twice
            handle1 = open_render_artifact(manifest_path)
            handle2 = open_render_artifact(manifest_path)

            # Should be different objects
            assert handle1 is not handle2
            assert handle1.loaded is not handle2.loaded
            assert handle1.loaded.artifact is not handle2.loaded.artifact

    def test_no_caching_between_frame_access(self) -> None:
        """Test frame access returns new PIL Image objects."""
        frames = create_offset_frames(start_index=15, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)

            # Access same frame twice
            img1 = get_frame_image(session, 15)
            img2 = get_frame_image(session, 15)

            # Should be different objects
            assert img1 is not img2


class TestFullPipelineWithValidationSkipping:
    """Tests verifying pipeline works with validate=False."""

    def test_open_with_validate_false_works(self) -> None:
        """Test open with validate=False allows corrupted artifact."""
        frames = create_offset_frames(start_index=16, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Corrupt PNG
            png_path = Path(tmpdir) / "frame_000016.png"
            png_path.write_bytes(b"corrupted")

            # Should succeed with validate=False
            handle = open_render_artifact(manifest_path, validate=False)
            assert handle.info.frame_count == 2

    def test_explicit_validation_after_skip(self) -> None:
        """Test explicit validation catches corruption after skip."""
        frames = create_offset_frames(start_index=17, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Open with validate=False
            handle = open_render_artifact(manifest_path, validate=False)

            # Corrupt after opening
            png_path = Path(tmpdir) / "frame_000017.png"
            png_path.write_bytes(b"corrupted")

            # Explicit validation should fail
            from tools.render.artifact_integration import ArtifactIntegrationError

            with pytest.raises(ArtifactIntegrationError):
                validate_render_artifact_handle(handle)


class TestComplexOffsetSequences:
    """Tests with complex offset sequences."""

    def test_offset_frame_indices(self) -> None:
        """Test handling of offset (non-zero start) frame indices."""
        # Create frames starting from offset index 10
        frames = create_offset_frames(start_index=10, count=5)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Verify offset indices
            assert artifact.frame_indices == (10, 11, 12, 13, 14)
            assert artifact.frame_count == 5

            # Load and verify
            handle = open_render_artifact(manifest_path)
            assert handle.info.frame_indices == (10, 11, 12, 13, 14)

            # Access each frame
            for idx in [10, 11, 12, 13, 14]:
                img = handle.frame_image(idx)
                path = handle.frame_path(idx)
                assert img.size == (800, 600)
                assert path.exists()

    def test_high_frame_indices(self) -> None:
        """Test handling of high frame indices."""
        frames = create_offset_frames(
            start_index=10000, count=3, duration_frames=20000
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Verify high indices
            assert artifact.frame_indices == (10000, 10001, 10002)

            # Load and verify
            handle = open_render_artifact(manifest_path)
            assert handle.info.frame_indices == (10000, 10001, 10002)

            # Access frames
            for idx in [10000, 10001, 10002]:
                img = handle.frame_image(idx)
                path = handle.frame_path(idx)
                assert img.size == (800, 600)
                assert path.exists()


class TestManifestSerializationDetails:
    """Tests for manifest serialization details."""

    def test_manifest_json_format(self) -> None:
        """Test manifest is stored as valid JSON."""
        frames = create_offset_frames(start_index=18, count=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Read and parse JSON
            content = manifest_path.read_text()
            data = json.loads(content)

            # Verify required fields
            assert "output_dir" in data
            assert "prefix" in data
            assert "frame_count" in data
            assert "frame_indices" in data
            assert "frame_rate" in data
            assert "duration_seconds" in data
            assert "dimensions" in data
            assert "mode" in data

    def test_manifest_reconstruction_preserves_types(self) -> None:
        """Test manifest round-trip preserves all types."""
        frames = create_offset_frames(start_index=19, count=2, frame_rate=30.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Reconstruct from disk
            loaded_manifest = read_artifact_manifest(manifest_path)

            # Verify types
            assert isinstance(loaded_manifest.output_dir, str)
            assert isinstance(loaded_manifest.prefix, str)
            assert isinstance(loaded_manifest.frame_count, int)
            assert isinstance(loaded_manifest.frame_indices, tuple)
            assert isinstance(loaded_manifest.frame_rate, float)
            assert isinstance(loaded_manifest.duration_seconds, float)
            assert isinstance(loaded_manifest.dimensions, tuple)
            assert isinstance(loaded_manifest.mode, str)


class TestForbiddenImports:
    """Tests verifying no forbidden imports are used."""

    def test_no_forbidden_imports_in_production_code(self) -> None:
        """Test no forbidden imports in render modules."""
        forbidden = [
            "AnimationRuntime",
            "AnimationTimeline",
            "AnimationClip",
            "AnimationOrchestrator",
            "threading",
            "asyncio",
            "FFmpeg",
            "OpenCV",
        ]

        modules_to_check = [
            "tools/render/session_access.py",
            "tools/render/session_validation.py",
            "tools/render/artifact.py",
            "tools/render/artifact_access.py",
            "tools/render/artifact_integration.py",
            "tools/render/artifact_loader.py",
            "tools/render/artifact_manifest.py",
            "tools/render/artifact_manifest_validation.py",
            "tools/render/artifact_validation.py",
        ]

        for module in modules_to_check:
            with open(module) as f:
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
                    assert forbid not in imp, (
                        f"Forbidden import {forbid} found in {module}"
                    )
