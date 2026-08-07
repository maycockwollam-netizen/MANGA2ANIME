"""Tests for renderer protocol contract."""

import pytest

from tools.frame.models import FrameTransform
from tools.render import (
    Renderer,
    RendererError,
    RenderFrame,
    RenderFrameError,
    TransformError,
)


class TestRendererProtocolCompliance:
    """Tests for Renderer protocol structural typing."""

    def test_class_with_render_method_satisfies_protocol(self) -> None:
        """Test that a class with render(frame) method satisfies Renderer protocol."""

        class ValidRenderer:
            def render(self, frame: RenderFrame) -> None:
                pass

        renderer = ValidRenderer()
        assert isinstance(renderer, Renderer)

    def test_class_without_render_method_does_not_satisfy_protocol(self) -> None:
        """Test that a class without render method does not satisfy Renderer."""

        class InvalidRenderer:
            def draw(self, frame: RenderFrame) -> None:
                pass

        renderer = InvalidRenderer()
        assert not isinstance(renderer, Renderer)

    def test_renderer_is_runtime_checkable_protocol(self) -> None:
        """Test that Renderer is a runtime-checkable protocol.

        This verifies that isinstance() works at runtime to check
        structural protocol compliance.
        """

        class MinimalRenderer:
            def render(self, frame: RenderFrame) -> None:
                pass

        # isinstance works with runtime-checkable Protocol
        assert isinstance(MinimalRenderer(), Renderer)

        # Non-renderer objects are correctly rejected
        assert not isinstance("not a renderer", Renderer)
        assert not isinstance(123, Renderer)
        assert not isinstance(None, Renderer)

    def test_renderer_protocol_is_type(self) -> None:
        """Test that Renderer itself is a type/class."""
        assert isinstance(Renderer, type)


class TestRendererRenderMethod:
    """Tests for Renderer.render() contract."""

    def test_renderer_accepts_render_frame(self) -> None:
        """Test renderer can receive and consume RenderFrame."""

        class CapturingRenderer:
            def __init__(self) -> None:
                self.received_frames: list[RenderFrame] = []

            def render(self, frame: RenderFrame) -> None:
                self.received_frames.append(frame)

        renderer = CapturingRenderer()
        frame = RenderFrame(
            frame_index=12,
            timestamp_seconds=0.5,
            frame_rate=24.0,
            duration_frames=240,
            transforms={"hero_1": FrameTransform(position_x=100)},
        )

        renderer.render(frame)

        assert len(renderer.received_frames) == 1
        assert renderer.received_frames[0].frame_index == 12
        assert renderer.received_frames[0].timestamp_seconds == 0.5

    def test_renderer_consumes_clip_id_identity(self) -> None:
        """Test renderer receives transforms keyed by clip_id."""

        class CapturingRenderer:
            def __init__(self) -> None:
                self.received_transforms: dict[str, FrameTransform] = {}

            def render(self, frame: RenderFrame) -> None:
                self.received_transforms = dict(frame.transforms.items())

        renderer = CapturingRenderer()
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "hero_1": FrameTransform(position_x=100),
                "villain_2": FrameTransform(position_y=200),
            },
        )

        renderer.render(frame)

        assert "hero_1" in renderer.received_transforms
        assert "villain_2" in renderer.received_transforms
        assert renderer.received_transforms["hero_1"].position_x == 100
        assert renderer.received_transforms["villain_2"].position_y == 200

    def test_renderer_handles_empty_frame(self) -> None:
        """Test renderer handles frame with no entities."""

        class TestRenderer:
            def render(self, frame: RenderFrame) -> None:
                assert frame.entity_count == 0
                assert len(frame.transforms) == 0

        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        TestRenderer().render(frame)

    def test_renderer_handles_multiple_entities(self) -> None:
        """Test renderer handles frame with multiple entities."""

        class TestRenderer:
            def __init__(self) -> None:
                self.entities_seen: set[str] = set()

            def render(self, frame: RenderFrame) -> None:
                self.entities_seen.update(frame.transforms.keys())
                assert frame.entity_count == 3

        renderer = TestRenderer()
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity_a": FrameTransform(),
                "entity_b": FrameTransform(),
                "entity_c": FrameTransform(),
            },
        )

        renderer.render(frame)
        assert renderer.entities_seen == {"entity_a", "entity_b", "entity_c"}

    def test_renderer_deterministic_repeated_calls(self) -> None:
        """Test renderer produces deterministic results for same frame."""

        class CountingRenderer:
            def __init__(self) -> None:
                self.render_count = 0

            def render(self, frame: RenderFrame) -> None:
                self.render_count += 1

        renderer = CountingRenderer()
        frame = RenderFrame(
            frame_index=5,
            timestamp_seconds=5.0 / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )

        renderer.render(frame)
        renderer.render(frame)
        renderer.render(frame)

        assert renderer.render_count == 3

    def test_renderer_receives_immutable_frame(self) -> None:
        """Test that renderer receives an immutable RenderFrame.

        The RenderFrame is frozen and its transforms mapping should be
        wrapped in MappingProxyType when produced by AnimationOrchestrator.
        The renderer contract expects immutable input.
        """

        class TestRenderer:
            def __init__(self) -> None:
                self.received_frame: RenderFrame | None = None

            def render(self, frame: RenderFrame) -> None:
                self.received_frame = frame

        from types import MappingProxyType

        renderer = TestRenderer()

        # Simulate what AnimationOrchestrator.render_frame() produces:
        # transforms wrapped in MappingProxyType
        wrapped_transforms = MappingProxyType({"test": FrameTransform()})

        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms=wrapped_transforms,
        )

        renderer.render(frame)

        # Verify renderer received the frame
        assert renderer.received_frame is not None
        assert renderer.received_frame.frame_index == 0

        # Verify transforms mapping is immutable (MappingProxyType)
        # Adding keys should raise TypeError
        with pytest.raises(TypeError):
            renderer.received_frame.transforms["new_key"] = FrameTransform()

        # Verify original transforms are preserved
        assert "test" in renderer.received_frame.transforms


class TestRendererEntityLifecycle:
    """Tests for entity lifecycle semantics in renderer."""

    def test_entity_disappearance_implicit_in_transforms(self) -> None:
        """Test that entity disappearance is handled by checking transforms."""

        class TrackingRenderer:
            def __init__(self) -> None:
                self.present_entities: set[str] = set()

            def render(self, frame: RenderFrame) -> None:
                self.present_entities = set(frame.transforms.keys())

        renderer = TrackingRenderer()

        # Frame with entity
        frame1 = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity_a": FrameTransform()},
        )
        renderer.render(frame1)
        assert "entity_a" in renderer.present_entities

        # Frame without entity
        frame2 = RenderFrame(
            frame_index=1,
            timestamp_seconds=1.0 / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={},
        )
        renderer.render(frame2)
        assert "entity_a" not in renderer.present_entities

    def test_entity_appearance_implicit_in_transforms(self) -> None:
        """Test that entity appearance is handled by checking transforms."""

        class TrackingRenderer:
            def __init__(self) -> None:
                self.present_entities: set[str] = set()

            def render(self, frame: RenderFrame) -> None:
                self.present_entities = set(frame.transforms.keys())

        renderer = TrackingRenderer()

        # Frame without new entity
        frame1 = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={"entity_a": FrameTransform()},
        )
        renderer.render(frame1)
        assert "entity_b" not in renderer.present_entities

        # Frame with new entity appearing
        frame2 = RenderFrame(
            frame_index=10,
            timestamp_seconds=10.0 / 24.0,
            frame_rate=24.0,
            duration_frames=24,
            transforms={
                "entity_a": FrameTransform(),
                "entity_b": FrameTransform(),
            },
        )
        renderer.render(frame2)
        assert "entity_b" in renderer.present_entities


class TestRendererImports:
    """Tests for renderer module imports."""

    def test_render_frame_importable(self) -> None:
        """Test RenderFrame is importable from tools.render."""
        from tools.render import RenderFrame

        assert RenderFrame is not None

    def test_renderer_importable(self) -> None:
        """Test Renderer is importable from tools.render."""
        from tools.render import Renderer

        assert Renderer is not None

    def test_renderer_is_protocol(self) -> None:
        """Test Renderer is a Protocol type."""
        from typing import Protocol

        assert issubclass(Renderer, Protocol)

    def test_renderer_error_importable(self) -> None:
        """Test RendererError hierarchy is importable."""
        from tools.render import RendererError, RenderFrameError, TransformError

        assert RendererError is not None
        assert issubclass(RenderFrameError, RendererError)
        assert issubclass(TransformError, RendererError)

    def test_renderer_error_can_be_raised(self) -> None:
        """Test RendererError can be raised."""
        with pytest.raises(RendererError):
            raise RendererError("test error")

    def test_render_frame_error_can_be_raised(self) -> None:
        """Test RenderFrameError can be raised."""
        with pytest.raises(RenderFrameError):
            raise RenderFrameError("test frame error")

    def test_transform_error_can_be_raised(self) -> None:
        """Test TransformError can be raised."""
        with pytest.raises(TransformError):
            raise TransformError("test transform error")
