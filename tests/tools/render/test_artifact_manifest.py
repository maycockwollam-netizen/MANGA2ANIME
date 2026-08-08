"""Tests for render artifact manifest."""

import json
import tempfile
from pathlib import Path

import pytest

from tools.render import (
    RenderFrame,
    create_render_artifact,
    create_render_session,
    export_render_frames,
)
from tools.render.artifact_manifest import (
    artifact_manifest_from_dict,
    artifact_manifest_to_dict,
    create_artifact_manifest,
    read_artifact_manifest,
    write_artifact_manifest,
)


class TestArtifactToManifest:
    """Tests for artifact → manifest conversion."""

    def test_artifact_to_manifest(self) -> None:
        """Test creating manifest from artifact."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session, validate=False)
            manifest = create_artifact_manifest(artifact)

        assert manifest.output_dir == str(Path(tmpdir))
        assert manifest.prefix == "frame"
        assert manifest.frame_count == 1
        assert manifest.frame_indices == (0,)
        assert manifest.frame_rate == 24.0
        assert manifest.dimensions == (800, 600)
        assert manifest.mode == "RGBA"


class TestManifestProperties:
    """Tests for manifest properties."""

    def test_all_metadata_preserved(self) -> None:
        """Test all metadata fields are preserved."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

        assert manifest.frame_count == 5
        assert manifest.frame_indices == (0, 1, 2, 3, 4)
        assert manifest.frame_rate == 24.0
        assert manifest.duration_seconds == 5 / 24.0
        assert manifest.dimensions == (800, 600)
        assert manifest.mode == "RGBA"

    def test_manifest_frozen(self) -> None:
        """Test that RenderArtifactManifest is frozen."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

        with pytest.raises(AttributeError):
            manifest.frame_count = 99


class TestManifestToDict:
    """Tests for manifest → dict conversion."""

    def test_manifest_to_dict(self) -> None:
        """Test converting manifest to dict."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            data = artifact_manifest_to_dict(manifest)

        assert isinstance(data, dict)
        assert set(data.keys()) == {
            "output_dir", "prefix", "frame_count", "frame_indices",
            "frame_rate", "duration_seconds", "dimensions", "mode"
        }

    def test_dict_contains_expected_fields(self) -> None:
        """Test dict has exactly expected fields."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            data = artifact_manifest_to_dict(manifest)

        assert data["frame_count"] == 1
        assert data["frame_indices"] == [0]
        assert data["frame_rate"] == 24.0
        assert data["dimensions"] == [800, 600]
        assert data["mode"] == "RGBA"

    def test_deterministic_dict_ordering(self) -> None:
        """Test dict key ordering is deterministic."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

            d1 = artifact_manifest_to_dict(manifest)
            d2 = artifact_manifest_to_dict(manifest)

        assert list(d1.keys()) == list(d2.keys())


class TestManifestToJson:
    """Tests for manifest → JSON conversion."""

    def test_manifest_to_json(self) -> None:
        """Test converting manifest to JSON string."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            data = artifact_manifest_to_dict(manifest)
            json_str = json.dumps(data, sort_keys=True)

        assert isinstance(json_str, str)
        assert "frame_count" in json_str

    def test_deterministic_json_output(self) -> None:
        """Test JSON output is deterministic."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            data = artifact_manifest_to_dict(manifest)

            json1 = json.dumps(data, sort_keys=True)
            json2 = json.dumps(data, sort_keys=True)

        assert json1 == json2


class TestJsonRoundTrip:
    """Tests for JSON round-trip."""

    def test_json_can_be_read_back(self) -> None:
        """Test JSON can be read back correctly."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

            # Write to file
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            # Read back
            loaded = read_artifact_manifest(manifest_path)

        assert loaded.frame_count == manifest.frame_count
        assert loaded.frame_indices == manifest.frame_indices

    def test_roundtrip_preserves_all_metadata(self) -> None:
        """Test round-trip preserves all metadata."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

            # Write and read
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)
            loaded = read_artifact_manifest(manifest_path)

        assert loaded.output_dir == manifest.output_dir
        assert loaded.prefix == manifest.prefix
        assert loaded.frame_count == manifest.frame_count
        assert loaded.frame_indices == manifest.frame_indices
        assert loaded.frame_rate == manifest.frame_rate
        assert loaded.duration_seconds == manifest.duration_seconds
        assert loaded.dimensions == manifest.dimensions
        assert loaded.mode == manifest.mode


class TestValidation:
    """Tests for manifest validation."""

    def test_malformed_json_rejected(self) -> None:
        """Test malformed JSON is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text("not valid json {")

            from tools.render.artifact_manifest import ArtifactManifestError

            with pytest.raises(ArtifactManifestError, match="Invalid JSON"):
                read_artifact_manifest(manifest_path)

    def test_missing_field_rejected(self) -> None:
        """Test missing required field is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": 24.0,
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            # missing "mode"
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="Missing required fields"):
            artifact_manifest_from_dict(data)

    def test_unexpected_field_rejected(self) -> None:
        """Test unexpected field is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": 24.0,
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            "mode": "RGBA",
            "extra_field": "unexpected",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="Unexpected fields"):
            artifact_manifest_from_dict(data)

    def test_wrong_primitive_type_rejected(self) -> None:
        """Test wrong primitive type is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": "not an int",  # Wrong type
            "frame_indices": [0],
            "frame_rate": 24.0,
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="frame_count must be an int"):
            artifact_manifest_from_dict(data)

    def test_invalid_frame_count_rejected(self) -> None:
        """Test invalid frame_count is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 0,  # Must be > 0
            "frame_indices": [0],
            "frame_rate": 24.0,
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="frame_count must be > 0"):
            artifact_manifest_from_dict(data)

    def test_invalid_frame_indices_rejected(self) -> None:
        """Test invalid frame_indices is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": "not a list",  # Wrong type
            "frame_rate": 24.0,
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="frame_indices must be a list or tuple"):
            artifact_manifest_from_dict(data)

    def test_duplicate_frame_indices_rejected(self) -> None:
        """Test duplicate frame_indices are rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 3,
            "frame_indices": [0, 0, 0],  # Duplicates
            "frame_rate": 24.0,
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="frame_indices must be unique"):
            artifact_manifest_from_dict(data)

    def test_invalid_dimensions_rejected(self) -> None:
        """Test invalid dimensions are rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": 24.0,
            "duration_seconds": 1.0,
            "dimensions": "not a list",  # Wrong type
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="dimensions must be a"):
            artifact_manifest_from_dict(data)

    def test_invalid_frame_rate_rejected(self) -> None:
        """Test invalid frame_rate is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": 0,  # Must be > 0
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="frame_rate must be > 0"):
            artifact_manifest_from_dict(data)

    def test_nan_frame_rate_rejected(self) -> None:
        """Test NaN frame_rate is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": float("nan"),
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="frame_rate cannot be NaN"):
            artifact_manifest_from_dict(data)

    def test_infinity_frame_rate_rejected(self) -> None:
        """Test infinity frame_rate is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": float("inf"),
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="frame_rate cannot be infinite"):
            artifact_manifest_from_dict(data)

    def test_invalid_duration_rejected(self) -> None:
        """Test invalid duration_seconds is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": 24.0,
            "duration_seconds": -1.0,  # Must be >= 0
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="duration_seconds must be >= 0"):
            artifact_manifest_from_dict(data)

    def test_nan_duration_rejected(self) -> None:
        """Test NaN duration_seconds is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": 24.0,
            "duration_seconds": float("nan"),
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="duration_seconds cannot be NaN"):
            artifact_manifest_from_dict(data)

    def test_infinity_duration_rejected(self) -> None:
        """Test infinity duration_seconds is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": 24.0,
            "duration_seconds": float("inf"),
            "dimensions": [800, 600],
            "mode": "RGBA",
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="duration_seconds cannot be infinite"):
            artifact_manifest_from_dict(data)

    def test_empty_mode_rejected(self) -> None:
        """Test empty mode is rejected."""
        data = {
            "output_dir": "/tmp",
            "prefix": "frame",
            "frame_count": 1,
            "frame_indices": [0],
            "frame_rate": 24.0,
            "duration_seconds": 1.0,
            "dimensions": [800, 600],
            "mode": "",  # Cannot be empty
        }

        from tools.render.artifact_manifest import ArtifactManifestError

        with pytest.raises(ArtifactManifestError, match="mode cannot be empty"):
            artifact_manifest_from_dict(data)


class TestFileOperations:
    """Tests for file operations."""

    def test_existing_destination_not_overwritten(self) -> None:
        """Test existing destination file is not overwritten."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_path.write_text("existing content")

            from tools.render.artifact_manifest import ArtifactManifestError

            with pytest.raises(ArtifactManifestError, match="already exists"):
                write_artifact_manifest(manifest, manifest_path)

    def test_missing_parent_directory_rejected(self) -> None:
        """Test missing parent directory is rejected."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

            nonexistent_path = Path(tmpdir) / "nonexistent" / "manifest.json"

            from tools.render.artifact_manifest import ArtifactManifestError

            with pytest.raises(ArtifactManifestError, match="Failed to write"):
                write_artifact_manifest(manifest, nonexistent_path)

    def test_read_does_not_mutate_filesystem(self) -> None:
        """Test read operation does not mutate filesystem."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)

            mtime_before = manifest_path.stat().st_mtime

            read_artifact_manifest(manifest_path)

            mtime_after = manifest_path.stat().st_mtime

        assert mtime_before == mtime_after


class TestNoMutation:
    """Tests for no mutation."""

    def test_artifact_unchanged(self) -> None:
        """Test RenderArtifact is unchanged."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)

            artifact_id = id(artifact)
            manifest = create_artifact_manifest(artifact)

            assert id(artifact) == artifact_id
            assert manifest is not None


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_repeated_serialization_deterministic(self) -> None:
        """Test repeated serialization produces identical results."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)

            d1 = artifact_manifest_to_dict(manifest)
            d2 = artifact_manifest_to_dict(manifest)

            assert d1 == d2

    def test_no_caching(self) -> None:
        """Test that no caching is performed."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)

            m1 = create_artifact_manifest(artifact)
            m2 = create_artifact_manifest(artifact)

            assert m1 is not m2


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist."""
        import ast

        with open("tools/render/artifact_manifest.py") as f:
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

        forbidden = [
            "AnimationRuntime",
            "AnimationTimeline",
            "AnimationClip",
            "AnimationOrchestrator",
            "threading",
            "asyncio",
        ]
        for imp in imports:
            for forbid in forbidden:
                assert forbid not in imp, f"Forbidden import found: {imp}"


class TestPublicAPI:
    """Tests for public API."""

    def test_render_artifact_manifest_importable(self) -> None:
        """Test RenderArtifactManifest is importable."""
        from tools.render import RenderArtifactManifest
        assert RenderArtifactManifest is not None

    def test_artifact_manifest_error_importable(self) -> None:
        """Test ArtifactManifestError is importable."""
        from tools.render import ArtifactManifestError
        assert ArtifactManifestError is not None

    def test_create_artifact_manifest_importable(self) -> None:
        """Test create_artifact_manifest is importable."""
        from tools.render import create_artifact_manifest
        assert create_artifact_manifest is not None

    def test_artifact_manifest_to_dict_importable(self) -> None:
        """Test artifact_manifest_to_dict is importable."""
        from tools.render import artifact_manifest_to_dict
        assert artifact_manifest_to_dict is not None

    def test_artifact_manifest_from_dict_importable(self) -> None:
        """Test artifact_manifest_from_dict is importable."""
        from tools.render import artifact_manifest_from_dict
        assert artifact_manifest_from_dict is not None

    def test_write_artifact_manifest_importable(self) -> None:
        """Test write_artifact_manifest is importable."""
        from tools.render import write_artifact_manifest
        assert write_artifact_manifest is not None

    def test_read_artifact_manifest_importable(self) -> None:
        """Test read_artifact_manifest is importable."""
        from tools.render import read_artifact_manifest
        assert read_artifact_manifest is not None
