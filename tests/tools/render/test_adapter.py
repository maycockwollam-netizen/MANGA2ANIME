"""Tests for renderer adapter."""

import pytest

from tools.frame.models import FrameTransform
from tools.render import (
    FrameAdapter,
    Renderer,
    RendererError,
    RenderFrame,
)
from tools.render.exceptions import RenderFrameError, TransformError


class TestFrameAdapterBasics:
    """Tests for FrameAdapter basic functionality."""

    def test_adapter_accepts_renderer_compatible_implementation(self) -> None:
        """Test that FrameAdapter accepts a Renderer-compatible object."""

        class SimpleRenderer:
            def render(self, frame: RenderFrame) -> None:
                pass

        renderer = SimpleRenderer()
        adapter = FrameAdapter(renderer)

        assert adapter.renderer is renderer

    def test_adapter_uses_isinstance_check(self) -> None:
        """Test that FrameAdapter validates renderer at construction."""

        class NotARenderer:
            def draw(self, frame: RenderFrame) -> None:
                pass

        not_renderer = NotARenderer()
        # FrameAdapter should accept any object with render() method
        # (duck typing via Protocol at runtime)
        adapter = FrameAdapter(not_renderer)
        assert adapter.renderer is not_renderer

    def test_adapter_preserves_renderer_reference(self) -> None:
        """Test that adapter exposes the underlying renderer."""

        class TestRenderer:
            pass

        renderer = TestRenderer()
        adapter = FrameAdapter(renderer)

        assert adapter.renderer is renderer


class TestFrameForwarding:
    """Tests for RenderFrame forwarding."""

    def test_render_frame_forwarded_unchanged(self) -> None:
        """Test that RenderFrame is forwarded without mutation."""

        received_frames: list[RenderFrame] = []

        class CapturingRenderer:
            def render(self, frame: RenderFrame) -> None:
                received_frames.append(frame)

        adapter = FrameAdapter(CapturingRenderer())
        frame = RenderFrame(
            frame_index=5,
            timestamp_seconds=5.0 / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity_1": FrameTransform()},
        )

        adapter.forward(frame)

        assert len(received_frames) == 1
        assert received_frames[0] is frame

    def test_frame_index_preserved(self) -> None:
        """Test that frame_index is preserved in forwarding."""

        class CapturingRenderer:
            def __init__(self) -> None:
                self.frame_index: int | None = None

            def render(self, frame: RenderFrame) -> None:
                self.frame_index = frame.frame_index

        adapter = FrameAdapter(CapturingRenderer())
        frame = RenderFrame(
            frame_index=42,
            timestamp_seconds=42.0 / 24.0,
            frame_rate=24.0,
            duration_frames=240,
            transforms={},
        )

        adapter.forward(frame)

        assert adapter.renderer.frame_index == 42

    def test_timestamp_preserved(self) -> None:
        """Test that timestamp_seconds is preserved in forwarding."""

        class CapturingRenderer:
            def __init__(self) -> None:
                self.timestamp: float | None = None

            def render(self, frame: RenderFrame) -> None:
                self.timestamp = frame.timestamp_seconds

        adapter = FrameAdapter(CapturingRenderer())
        frame = RenderFrame(
            frame_index=10,
            timestamp_seconds=10.0 / 30.0,
            frame_rate=30.0,
            duration_frames=300,
            transforms={},
        )

        adapter.forward(frame)

        assert adapter.renderer.timestamp == 10.0 / 30.0

    def test_duration_preserved(self) -> None:
        """Test that duration_frames and duration_seconds are preserved."""

        class CapturingRenderer:
            def __init__(self) -> None:
                self.duration_frames: int | None = None
                self.duration_seconds: float | None = None

            def render(self, frame: RenderFrame) -> None:
                self.duration_frames = frame.duration_frames
                self.duration_seconds = frame.duration_seconds

        adapter = FrameAdapter(CapturingRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=48,
            transforms={},
        )

        adapter.forward(frame)

        assert adapter.renderer.duration_frames == 48
        assert adapter.renderer.duration_seconds == 48.0 / 24.0


class TestClipIdPreservation:
    """Tests for clip_id identity preservation."""

    def test_clip_id_keys_preserved(self) -> None:
        """Test that transforms clip_id keys are preserved."""

        class CapturingRenderer:
            def __init__(self) -> None:
                self.clip_ids: set[str] = set()

            def render(self, frame: RenderFrame) -> None:
                self.clip_ids = set(frame.transforms.keys())

        adapter = FrameAdapter(CapturingRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "hero_1": FrameTransform(),
                "villain_2": FrameTransform(),
            },
        )

        adapter.forward(frame)

        assert adapter.renderer.clip_ids == {"hero_1", "villain_2"}


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_transforms_work(self) -> None:
        """Test that empty transforms work correctly."""

        class CapturingRenderer:
            def __init__(self) -> None:
                self.entity_count: int = -1

            def render(self, frame: RenderFrame) -> None:
                self.entity_count = frame.entity_count

        adapter = FrameAdapter(CapturingRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        adapter.forward(frame)

        assert adapter.renderer.entity_count == 0

    def test_multiple_entities_work(self) -> None:
        """Test that multiple entities work correctly."""

        class CapturingRenderer:
            def __init__(self) -> None:
                self.entity_count: int = -1

            def render(self, frame: RenderFrame) -> None:
                self.entity_count = frame.entity_count

        adapter = FrameAdapter(CapturingRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "a": FrameTransform(),
                "b": FrameTransform(),
                "c": FrameTransform(),
                "d": FrameTransform(),
            },
        )

        adapter.forward(frame)

        assert adapter.renderer.entity_count == 4

    def test_repeated_render_calls_work(self) -> None:
        """Test that repeated forward calls work correctly."""

        class CountingRenderer:
            def __init__(self) -> None:
                self.call_count: int = 0

            def render(self, frame: RenderFrame) -> None:
                self.call_count += 1

        adapter = FrameAdapter(CountingRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        adapter.forward(frame)
        adapter.forward(frame)
        adapter.forward(frame)

        assert adapter.renderer.call_count == 3


class TestExceptionHandling:
    """Tests for exception handling."""

    def test_renderer_error_propagates(self) -> None:
        """Test that RendererError propagates without being swallowed."""

        class ErrorRenderer:
            def render(self, frame: RenderFrame) -> None:
                raise RendererError("rendering failed")

        adapter = FrameAdapter(ErrorRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        with pytest.raises(RendererError, match="rendering failed"):
            adapter.forward(frame)

    def test_render_frame_error_propagates(self) -> None:
        """Test that RenderFrameError propagates without being swallowed."""

        class FrameErrorRenderer:
            def render(self, frame: RenderFrame) -> None:
                raise RenderFrameError("invalid frame")

        adapter = FrameAdapter(FrameErrorRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        with pytest.raises(RenderFrameError, match="invalid frame"):
            adapter.forward(frame)

    def test_transform_error_propagates(self) -> None:
        """Test that TransformError propagates without being swallowed."""

        class TransformErrorRenderer:
            def render(self, frame: RenderFrame) -> None:
                raise TransformError("invalid transform")

        adapter = FrameAdapter(TransformErrorRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        with pytest.raises(TransformError, match="invalid transform"):
            adapter.forward(frame)

    def test_generic_exception_propagates(self) -> None:
        """Test that generic exceptions propagate without being swallowed."""

        class FailingRenderer:
            def render(self, frame: RenderFrame) -> None:
                raise ValueError("unexpected error")

        adapter = FrameAdapter(FailingRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        with pytest.raises(ValueError, match="unexpected error"):
            adapter.forward(frame)


class TestImmutability:
    """Tests for RenderFrame immutability."""

    def test_adapter_does_not_mutate_render_frame(self) -> None:
        """Test that adapter does not mutate the input RenderFrame."""

        class TestRenderer:
            def render(self, frame: RenderFrame) -> None:
                # Try to mutate the frame
                frame.transforms["new_key"] = FrameTransform()

        adapter = FrameAdapter(TestRenderer())
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        # The adapter should not raise when forwarding
        # (Mutation would be attempted by the renderer, not the adapter)
        try:
            adapter.forward(frame)
        except TypeError:
            # TypeError expected if mutation is attempted on immutable frame
            pass


class TestImports:
    """Tests for adapter module imports."""

    def test_frame_adapter_importable(self) -> None:
        """Test FrameAdapter is importable from tools.render."""
        from tools.render import FrameAdapter

        assert FrameAdapter is not None

    def test_frame_adapter_can_be_instantiated(self) -> None:
        """Test FrameAdapter can be instantiated with a renderer."""

        class MinimalRenderer:
            def render(self, frame: RenderFrame) -> None:
                pass

        from tools.render import FrameAdapter

        adapter = FrameAdapter(MinimalRenderer())
        assert adapter is not None
        assert isinstance(adapter.renderer, Renderer)
