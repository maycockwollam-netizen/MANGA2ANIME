"""Tests for render artifact access."""

import tempfile
from pathlib import Path

import pytest

from tools.render import (
    RenderFrame,
    create_artifact_manifest,
    create_render_artifact,
    create_render_session,
    export_render_frames,
    load_render_artifact,
    write_artifact_manifest,
)


class TestValidArtifactAccess:
    """Tests for valid artifact access."""

    def test_valid_single_frame_artifact(self) -> None:
        """Test accessing a valid single-frame artifact."""
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
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_info

            info = get_artifact_info(loaded)

        assert info.frame_count == 1
        assert info.first_frame_index == 0
        assert info.last_frame_index == 0

    def test_valid_multi_frame_artifact(self) -> None:
        """Test accessing a valid multi-frame artifact."""
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
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_info

            info = get_artifact_info(loaded)

        assert info.frame_count == 5
        assert info.first_frame_index == 0
        assert info.last_frame_index == 4


class TestArtifactInfo:
    """Tests for artifact info."""

    def test_artifact_info(self) -> None:
        """Test getting artifact info."""
        frames = [
            RenderFrame(
                frame_index=i,
                timestamp_seconds=i / 24.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={},
            )
            for i in range(3)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)
            session = create_render_session(tmpdir)
            artifact = create_render_artifact(session)
            manifest = create_artifact_manifest(artifact)
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_info

            info = get_artifact_info(loaded)

        assert info.frame_count == 3
        assert info.frame_indices == (0, 1, 2)
        assert info.frame_rate == 24.0
        assert info.dimensions == (800, 600)
        assert info.mode == "RGBA"

    def test_first_last_frame_indices(self) -> None:
        """Test first and last frame indices."""
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
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_info

            info = get_artifact_info(loaded)

        assert info.first_frame_index == 0
        assert info.last_frame_index == 4


class TestFramePathAccess:
    """Tests for frame path access."""

    def test_frame_path_access(self) -> None:
        """Test getting frame path."""
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
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_frame_path

            path = get_artifact_frame_path(loaded, 0)

            assert isinstance(path, Path)
            assert path.name == "frame_000000.png"
            assert path.exists()


class TestFrameImageAccess:
    """Tests for frame image access."""

    def test_frame_image_access(self) -> None:
        """Test getting frame image."""
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
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_frame_image

            image = get_artifact_frame_image(loaded, 0)

        assert image.size == (800, 600)
        assert image.mode == "RGBA"


class TestTimestampAccess:
    """Tests for timestamp-based frame access."""

    def test_timestamp_based_frame_access(self) -> None:
        """Test getting frame at timestamp."""
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
            manifest_path = Path(tmpdir) / "manifest.json"
            write_artifact_manifest(manifest, manifest_path)
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_frame_at_timestamp

            # Get frame at 0.1 seconds (within duration)
            image = get_artifact_frame_at_timestamp(loaded, 0.1)

        assert image.size == (800, 600)


class TestInvalidAccess:
    """Tests for invalid access."""

    def test_invalid_frame_index(self) -> None:
        """Test invalid frame index raises error."""
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
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import (
                ArtifactAccessError,
                get_artifact_frame_path,
            )

            with pytest.raises(ArtifactAccessError, match="Invalid frame_index"):
                get_artifact_frame_path(loaded, 99)

    def test_timestamp_below_zero(self) -> None:
        """Test negative timestamp raises error."""
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
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import (
                ArtifactAccessError,
                get_artifact_frame_at_timestamp,
            )

            with pytest.raises(ArtifactAccessError, match="cannot be negative"):
                get_artifact_frame_at_timestamp(loaded, -0.5)

    def test_timestamp_beyond_duration(self) -> None:
        """Test timestamp beyond duration raises error."""
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
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import (
                ArtifactAccessError,
                get_artifact_frame_at_timestamp,
            )

            with pytest.raises(ArtifactAccessError, match="exceeds duration"):
                get_artifact_frame_at_timestamp(loaded, 100.0)


class TestNoMutation:
    """Tests for no mutation."""

    def test_artifact_unchanged(self) -> None:
        """Test artifact is unchanged after access."""
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
            loaded = load_render_artifact(manifest_path)

            artifact_id = id(loaded.artifact)

            from tools.render.artifact_access import get_artifact_info

            get_artifact_info(loaded)

            assert id(loaded.artifact) == artifact_id

    def test_manifest_unchanged(self) -> None:
        """Test manifest is unchanged after access."""
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
            loaded = load_render_artifact(manifest_path)

            manifest_id = id(loaded.manifest)

            from tools.render.artifact_access import get_artifact_info

            get_artifact_info(loaded)

            assert id(loaded.manifest) == manifest_id

    def test_png_files_unchanged(self) -> None:
        """Test PNG files are unchanged after access."""
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
            loaded = load_render_artifact(manifest_path)

            files_before = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            from tools.render.artifact_access import get_artifact_frame_image

            get_artifact_frame_image(loaded, 0)

            files_after = {
                f.name: f.stat().st_mtime for f in Path(tmpdir).glob("*.png")
            }

            assert files_before == files_after

    def test_no_files_created(self) -> None:
        """Test no files are created during access."""
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
            loaded = load_render_artifact(manifest_path)

            files_before = set(Path(tmpdir).iterdir())

            from tools.render.artifact_access import get_artifact_frame_image

            get_artifact_frame_image(loaded, 0)

            files_after = set(Path(tmpdir).iterdir())

            assert files_before == files_after

    def test_no_files_deleted(self) -> None:
        """Test no files are deleted during access."""
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
            loaded = load_render_artifact(manifest_path)

            png_path = Path(tmpdir) / "frame_000000.png"
            png_content_before = png_path.read_bytes()

            from tools.render.artifact_access import get_artifact_frame_image

            get_artifact_frame_image(loaded, 0)

            png_content_after = png_path.read_bytes()

            assert png_content_before == png_content_after


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_repeated_access_deterministic(self) -> None:
        """Test repeated access produces identical results."""
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
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_info

            i1 = get_artifact_info(loaded)
            i2 = get_artifact_info(loaded)

            assert i1.frame_count == i2.frame_count


class TestNoCaching:
    """Tests for no caching."""

    def test_no_caching(self) -> None:
        """Test no caching is performed."""
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
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_info

            i1 = get_artifact_info(loaded)
            i2 = get_artifact_info(loaded)

            assert i1 is not i2


class TestImmutability:
    """Tests for immutability."""

    def test_result_immutable(self) -> None:
        """Test returned info is immutable."""
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
            loaded = load_render_artifact(manifest_path)

            from tools.render.artifact_access import get_artifact_info

            info = get_artifact_info(loaded)

        with pytest.raises(AttributeError):
            info.frame_count = 99  # type: ignore


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test no forbidden imports."""
        import ast

        with open("tools/render/artifact_access.py") as f:
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

    def test_render_artifact_info_importable(self) -> None:
        """Test RenderArtifactInfo is importable."""
        from tools.render import RenderArtifactInfo
        assert RenderArtifactInfo is not None

    def test_artifact_access_error_importable(self) -> None:
        """Test ArtifactAccessError is importable."""
        from tools.render import ArtifactAccessError
        assert ArtifactAccessError is not None

    def test_get_artifact_info_importable(self) -> None:
        """Test get_artifact_info is importable."""
        from tools.render import get_artifact_info
        assert get_artifact_info is not None

    def test_get_artifact_frame_path_importable(self) -> None:
        """Test get_artifact_frame_path is importable."""
        from tools.render import get_artifact_frame_path
        assert get_artifact_frame_path is not None

    def test_get_artifact_frame_image_importable(self) -> None:
        """Test get_artifact_frame_image is importable."""
        from tools.render import get_artifact_frame_image
        assert get_artifact_frame_image is not None

    def test_get_artifact_frame_at_timestamp_importable(self) -> None:
        """Test get_artifact_frame_at_timestamp is importable."""
        from tools.render import get_artifact_frame_at_timestamp
        assert get_artifact_frame_at_timestamp is not None
