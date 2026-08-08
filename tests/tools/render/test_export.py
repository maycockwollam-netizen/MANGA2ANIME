"""Tests for end-to-end render sequence export entry point."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from tools.frame.models import FrameTransform
from tools.render import RenderFrame, export_render_frames


class TestExportRenderFramesBasics:
    """Tests for basic export_render_frames functionality."""

    def test_import_export_render_frames(self) -> None:
        """Test that export_render_frames is importable."""
        from tools.render import export_render_frames

        assert export_render_frames is not None

    def test_accepts_iterable_of_render_frames(self) -> None:
        """Test that function accepts an Iterable[RenderFrame]."""
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
        # Verify it's accepted as Iterable[RenderFrame]
        result = export_render_frames(frames, tempfile.mkdtemp())
        assert result == 3

    def test_empty_iterable_works(self) -> None:
        """Test that empty iterable works."""
        result = export_render_frames([], tempfile.mkdtemp())
        assert result == 0

    def test_one_frame_exports_correctly(self) -> None:
        """Test that one frame exports correctly."""
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
            count = export_render_frames(frames, tmpdir)
            assert count == 1

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 1
            assert png_files[0].name == "frame_000000.png"

    def test_multiple_frames_export_correctly(self) -> None:
        """Test that multiple frames export correctly."""
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
            count = export_render_frames(frames, tmpdir)
            assert count == 5

            png_files = sorted(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 5


class TestDelegationToRenderFramesToPng:
    """Tests verifying delegation to render_frames_to_png."""

    def test_exact_render_frame_objects_reach_underlying_exporter(self) -> None:
        """Test that exact RenderFrame objects reach the underlying exporter."""
        captured_frames: list[RenderFrame] = []

        class CapturingRenderer:
            last_output = None

            def render(self, f: RenderFrame) -> None:
                captured_frames.append(f)
                # Set last_output to satisfy integration check
                self.last_output = Image.new("RGBA", (1, 1))

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
            export_render_frames(frames, tmpdir, renderer=CapturingRenderer())

        assert len(captured_frames) == 3
        assert captured_frames[0] is frames[0]
        assert captured_frames[1] is frames[1]
        assert captured_frames[2] is frames[2]

    def test_frame_index_preserved(self) -> None:
        """Test that frame_index is preserved."""
        frames = [
            RenderFrame(
                frame_index=42,
                timestamp_seconds=42.0 / 24.0,
                frame_rate=24.0,
                duration_frames=48,
                transforms={},
            )
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames(frames, tmpdir)

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            assert len(png_files) == 1
            assert "000042" in png_files[0].name

    def test_timestamp_unchanged(self) -> None:
        """Test that timestamp_seconds is unchanged."""
        frame = RenderFrame(
            frame_index=5,
            timestamp_seconds=5.0 / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        captured_timestamp = None

        class TimestampCapturingRenderer:
            last_output = None

            def render(self, f: RenderFrame) -> None:
                nonlocal captured_timestamp
                captured_timestamp = f.timestamp_seconds
                self.last_output = Image.new("RGBA", (1, 1))

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames([frame], tmpdir, renderer=TimestampCapturingRenderer())

        assert captured_timestamp == 5.0 / 24.0

    def test_duration_metadata_unchanged(self) -> None:
        """Test that duration_frames/duration_seconds remain unchanged."""
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=48,
            transforms={},
        )

        captured_duration = None

        class DurationCapturingRenderer:
            last_output = None

            def render(self, f: RenderFrame) -> None:
                nonlocal captured_duration
                captured_duration = f.duration_frames
                self.last_output = Image.new("RGBA", (1, 1))

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames([frame], tmpdir, renderer=DurationCapturingRenderer())

        assert captured_duration == 48

    def test_clip_id_keys_unchanged(self) -> None:
        """Test that clip_id keys remain unchanged."""
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity_a": FrameTransform(), "entity_b": FrameTransform()},
        )

        captured_keys: set[str] = set()

        class KeysCapturingRenderer:
            last_output = None

            def render(self, f: RenderFrame) -> None:
                captured_keys.update(f.transforms.keys())
                self.last_output = Image.new("RGBA", (1, 1))

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames([frame], tmpdir, renderer=KeysCapturingRenderer())

        assert "entity_a" in captured_keys
        assert "entity_b" in captured_keys

    def test_empty_transforms_work(self) -> None:
        """Test that empty transforms work."""
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
            count = export_render_frames(frames, tmpdir)
            assert count == 1

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])
            assert image.format == "PNG"
            assert image.mode == "RGBA"

    def test_multiple_entities_work(self) -> None:
        """Test that multiple entities work."""
        frames = [
            RenderFrame(
                frame_index=0,
                timestamp_seconds=0.0,
                frame_rate=24.0,
                duration_frames=24,
                transforms={
                    "hero": FrameTransform(position_x=100, position_y=100),
                    "villain": FrameTransform(position_x=300, position_y=200),
                },
            )
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            count = export_render_frames(frames, tmpdir)
            assert count == 1

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])

            # Check both entities are visible
            pixel1 = image.getpixel((100, 100))
            pixel2 = image.getpixel((300, 200))
            assert pixel1 != (255, 255, 255, 255)
            assert pixel2 != (255, 255, 255, 255)


class TestParameterForwarding:
    """Tests for parameter forwarding to underlying implementation."""

    def test_supplied_renderer_forwarded(self) -> None:
        """Test that supplied Renderer is forwarded."""
        render_count = 0

        class CountingRenderer:
            last_output = None

            def render(self, f: RenderFrame) -> None:
                nonlocal render_count
                render_count += 1
                self.last_output = Image.new("RGBA", (1, 1))

        renderer = CountingRenderer()
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
            export_render_frames(frames, tmpdir, renderer=renderer)

        assert render_count == 3

    def test_canvas_size_forwarded(self) -> None:
        """Test that canvas_size is forwarded."""
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
            export_render_frames(frames, tmpdir, canvas_size=(640, 480))

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])
            assert image.size == (640, 480)

    def test_background_forwarded(self) -> None:
        """Test that background is forwarded."""
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
            # Black background
            export_render_frames(frames, tmpdir, background=(0, 0, 0, 255))

            png_files = list(Path(tmpdir).glob("frame_*.png"))
            image = Image.open(png_files[0])

            # Check background color (RGBA)
            corner_pixel = image.getpixel((0, 0))
            assert corner_pixel == (0, 0, 0, 255)

    def test_prefix_forwarded(self) -> None:
        """Test that prefix is forwarded."""
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
            export_render_frames(frames, tmpdir, prefix="img")

            png_files = list(Path(tmpdir).glob("img_*.png"))
            assert len(png_files) == 1
            assert png_files[0].name == "img_000000.png"


class TestErrorHandling:
    """Tests for error handling."""

    def test_renderer_exception_propagates(self) -> None:
        """Test that renderer exceptions propagate unchanged."""

        class FailingRenderer:
            def render(self, f: RenderFrame) -> None:
                msg = "Export test error"
                raise RuntimeError(msg)

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
            with pytest.raises(RuntimeError, match="Export test error"):
                export_render_frames(frames, tmpdir, renderer=FailingRenderer())


class TestImmutability:
    """Tests for RenderFrame immutability."""

    def test_render_frame_not_mutated(self) -> None:
        """Test that RenderFrame is not mutated."""
        frame = RenderFrame(
            frame_index=5,
            timestamp_seconds=5.0 / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity": FrameTransform()},
        )

        original_frame_index = frame.frame_index
        original_timestamp = frame.timestamp_seconds
        original_keys = set(frame.transforms.keys())

        with tempfile.TemporaryDirectory() as tmpdir:
            export_render_frames([frame], tmpdir)

        assert frame.frame_index == original_frame_index
        assert frame.timestamp_seconds == original_timestamp
        assert set(frame.transforms.keys()) == original_keys


class TestImports:
    """Tests for module imports."""

    def test_no_forbidden_imports(self) -> None:
        """Test that no forbidden imports exist in export module."""
        import ast

        with open("tools/render/export.py") as f:
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

        # Check for forbidden imports
        forbidden = [
            "AnimationRuntime",
            "AnimationTimeline",
            "AnimationClip",
            "AnimationOrchestrator",
        ]
        for imp in imports:
            for forbid in forbidden:
                assert forbid not in imp, f"Forbidden import found: {imp}"
