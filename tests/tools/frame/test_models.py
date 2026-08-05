"""Tests for frame models V1."""

import pytest

from tools.frame.models import (
    Frame,
    FrameLayer,
    FrameSequence,
    FrameTransform,
    FrameTransition,
    InterpolationType,
    LayerType,
    TransitionType,
)


class TestLayerType:
    """Tests for LayerType enum."""

    def test_layer_type_values(self) -> None:
        """Test LayerType enum values."""
        assert LayerType.BACKGROUND == "background"
        assert LayerType.CHARACTER == "character"
        assert LayerType.FOREGROUND == "foreground"
        assert LayerType.EFFECT == "effect"

    def test_layer_type_is_str_enum(self) -> None:
        """Test LayerType is a string enum."""
        assert isinstance(LayerType.CHARACTER, str)
        assert LayerType.CHARACTER == "character"


class TestTransitionType:
    """Tests for TransitionType enum."""

    def test_transition_type_values(self) -> None:
        """Test TransitionType enum values."""
        assert TransitionType.CUT == "cut"
        assert TransitionType.FADE == "fade"
        assert TransitionType.DISSOLVE == "dissolve"
        assert TransitionType.SLIDE_LEFT == "slide_left"
        assert TransitionType.SLIDE_RIGHT == "slide_right"
        assert TransitionType.ZOOM_IN == "zoom_in"
        assert TransitionType.ZOOM_OUT == "zoom_out"


class TestInterpolationType:
    """Tests for InterpolationType enum."""

    def test_interpolation_type_values(self) -> None:
        """Test InterpolationType enum values."""
        assert InterpolationType.LINEAR == "linear"
        assert InterpolationType.EASE_IN == "ease_in"
        assert InterpolationType.EASE_OUT == "ease_out"
        assert InterpolationType.EASE_IN_OUT == "ease_in_out"


class TestFrameTransform:
    """Tests for FrameTransform model."""

    def test_valid_transform(self) -> None:
        """Test creating a valid transform."""
        transform = FrameTransform(
            position_x=100.0,
            position_y=200.0,
            scale=1.5,
            rotation_deg=45.0,
            opacity=0.8,
        )
        assert transform.position_x == 100.0
        assert transform.position_y == 200.0
        assert transform.scale == 1.5
        assert transform.rotation_deg == 45.0
        assert transform.opacity == 0.8

    def test_default_values(self) -> None:
        """Test default values."""
        transform = FrameTransform()
        assert transform.position_x is None
        assert transform.position_y is None
        assert transform.scale == 1.0
        assert transform.rotation_deg == 0.0
        assert transform.opacity == 1.0
        assert transform.anchor_x == 0.5
        assert transform.anchor_y == 0.5

    def test_opacity_range_validation(self) -> None:
        """Test opacity must be 0-1."""
        with pytest.raises(ValueError):
            FrameTransform(opacity=1.5)
        with pytest.raises(ValueError):
            FrameTransform(opacity=-0.1)

    def test_scale_non_negative(self) -> None:
        """Test scale must be non-negative."""
        with pytest.raises(ValueError):
            FrameTransform(scale=-1.0)

    def test_rotation_range(self) -> None:
        """Test rotation accepts reasonable range."""
        transform = FrameTransform(rotation_deg=360000)
        assert transform.rotation_deg == 360000

        transform = FrameTransform(rotation_deg=-360000)
        assert transform.rotation_deg == -360000


class TestFrameLayer:
    """Tests for FrameLayer model."""

    def test_valid_layer(self) -> None:
        """Test creating a valid layer."""
        layer = FrameLayer(
            layer_id="layer_1",
            layer_type=LayerType.CHARACTER,
            layer_index=0,
        )
        assert layer.layer_id == "layer_1"
        assert layer.layer_type == LayerType.CHARACTER
        assert layer.layer_index == 0
        assert layer.visible is True

    def test_layer_without_id(self) -> None:
        """Test layer without explicit ID."""
        layer = FrameLayer(
            layer_type=LayerType.BACKGROUND,
            layer_index=0,
        )
        assert layer.layer_id is None

    def test_layer_with_transform(self) -> None:
        """Test layer with transform."""
        transform = FrameTransform(position_x=100)
        layer = FrameLayer(
            layer_type=LayerType.EFFECT,
            layer_index=2,
            transform=transform,
        )
        assert layer.transform is not None
        assert layer.transform.position_x == 100

    def test_layer_id_whitespace_rejected(self) -> None:
        """Test whitespace-only layer_id is rejected."""
        with pytest.raises(ValueError):
            FrameLayer(layer_id="   ", layer_type=LayerType.CHARACTER, layer_index=0)

    def test_layer_id_trimmed(self) -> None:
        """Test layer_id is trimmed."""
        layer = FrameLayer(
            layer_id="  layer_1  ",
            layer_type=LayerType.CHARACTER,
            layer_index=0,
        )
        assert layer.layer_id == "layer_1"

    def test_layer_index_non_negative(self) -> None:
        """Test layer_index must be non-negative."""
        with pytest.raises(ValueError):
            FrameLayer(layer_type=LayerType.CHARACTER, layer_index=-1)


class TestFrame:
    """Tests for Frame model."""

    def test_valid_frame(self) -> None:
        """Test creating a valid frame."""
        frame = Frame(
            frame_index=0,
            timestamp_ms=0,
            duration_ms=1000,
        )
        assert frame.frame_index == 0
        assert frame.timestamp_ms == 0
        assert frame.duration_ms == 1000
        assert frame.layers == ()

    def test_frame_with_layers(self) -> None:
        """Test frame with layers."""
        layer1 = FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0)
        layer2 = FrameLayer(layer_type=LayerType.CHARACTER, layer_index=1)
        frame = Frame(frame_index=0, layers=[layer1, layer2])
        assert len(frame.layers) == 2
        # Verify it's a tuple
        assert isinstance(frame.layers, tuple)

    def test_frame_index_non_negative(self) -> None:
        """Test frame_index must be non-negative."""
        with pytest.raises(ValueError):
            Frame(frame_index=-1)

    def test_timing_non_negative(self) -> None:
        """Test timing values must be non-negative."""
        with pytest.raises(ValueError):
            Frame(frame_index=0, timestamp_ms=-1)
        with pytest.raises(ValueError):
            Frame(frame_index=0, duration_ms=-1)

    def test_layer_ordering_validation(self) -> None:
        """Test layers must be ordered by layer_index."""
        layer1 = FrameLayer(layer_type=LayerType.CHARACTER, layer_index=1)
        layer2 = FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0)
        # Out of order
        with pytest.raises(ValueError):
            Frame(frame_index=0, layers=[layer1, layer2])

    def test_duplicate_layer_index_rejected(self) -> None:
        """Test duplicate layer_index values are rejected."""
        layer1 = FrameLayer(layer_type=LayerType.CHARACTER, layer_index=1)
        layer2 = FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=1)
        with pytest.raises(ValueError, match="duplicate layer_index"):
            Frame(frame_index=0, layers=[layer1, layer2])


class TestFrameTransition:
    """Tests for FrameTransition model."""

    def test_valid_transition(self) -> None:
        """Test creating a valid transition."""
        transition = FrameTransition(
            source_frame_index=0,
            target_frame_index=1,
            duration_ms=500,
        )
        assert transition.source_frame_index == 0
        assert transition.target_frame_index == 1
        assert transition.duration_ms == 500
        assert transition.transition_type == "cut"

    def test_transition_with_enum_type(self) -> None:
        """Test transition with TransitionType enum."""
        transition = FrameTransition(
            source_frame_index=0,
            target_frame_index=1,
            duration_ms=500,
            transition_type=TransitionType.FADE,
        )
        assert transition.transition_type == "fade"

    def test_transition_with_interpolation(self) -> None:
        """Test transition with interpolation."""
        transition = FrameTransition(
            source_frame_index=0,
            target_frame_index=1,
            duration_ms=500,
            interpolation=InterpolationType.EASE_IN_OUT,
        )
        assert transition.interpolation == InterpolationType.EASE_IN_OUT

    def test_same_frame_rejected(self) -> None:
        """Test same source and target frame is rejected."""
        with pytest.raises(ValueError):
            FrameTransition(
                source_frame_index=0,
                target_frame_index=0,
                duration_ms=500,
            )

    def test_frame_index_non_negative(self) -> None:
        """Test frame indexes must be non-negative."""
        with pytest.raises(ValueError):
            FrameTransition(source_frame_index=-1, target_frame_index=0, duration_ms=500)
        with pytest.raises(ValueError):
            FrameTransition(source_frame_index=0, target_frame_index=-1, duration_ms=500)


class TestFrameSequence:
    """Tests for FrameSequence model."""

    def test_valid_sequence(self) -> None:
        """Test creating a valid sequence."""
        sequence = FrameSequence(
            sequence_id="seq_1",
            name="Opening Sequence",
            frame_rate=24.0,
        )
        assert sequence.sequence_id == "seq_1"
        assert sequence.name == "Opening Sequence"
        assert sequence.frame_rate == 24.0
        assert sequence.frames == ()
        assert sequence.transitions == ()

    def test_sequence_id_empty_rejected(self) -> None:
        """Test empty sequence_id is rejected."""
        with pytest.raises(ValueError):
            FrameSequence(sequence_id="")

    def test_sequence_id_whitespace_rejected(self) -> None:
        """Test whitespace-only sequence_id is rejected."""
        with pytest.raises(ValueError):
            FrameSequence(sequence_id="   ")

    def test_sequence_id_trimmed(self) -> None:
        """Test sequence_id is trimmed."""
        sequence = FrameSequence(sequence_id="  seq_1  ")
        assert sequence.sequence_id == "seq_1"

    def test_frame_rate_range(self) -> None:
        """Test frame_rate must be in valid range."""
        with pytest.raises(ValueError):
            FrameSequence(sequence_id="seq_1", frame_rate=0)
        with pytest.raises(ValueError):
            FrameSequence(sequence_id="seq_1", frame_rate=121)

    def test_sequence_immutable(self) -> None:
        """Test sequence is immutable/frozen."""
        sequence = FrameSequence(sequence_id="seq_1")
        with pytest.raises(Exception) as exc_info:
            sequence.sequence_id = "new_id"
        assert "frozen" in str(exc_info.value).lower()

    def test_sequence_with_frames(self) -> None:
        """Test sequence with frames."""
        frame1 = Frame(frame_index=0)
        frame2 = Frame(frame_index=1)
        sequence = FrameSequence(
            sequence_id="seq_1",
            frames=[frame1, frame2],
        )
        assert len(sequence.frames) == 2
        # Verify it's a tuple
        assert isinstance(sequence.frames, tuple)

    def test_sequence_with_transitions_and_frames(self) -> None:
        """Test sequence with transitions and valid frame references."""
        frame1 = Frame(frame_index=0)
        frame2 = Frame(frame_index=1)
        transition = FrameTransition(
            source_frame_index=0,
            target_frame_index=1,
            duration_ms=500,
        )
        sequence = FrameSequence(
            sequence_id="seq_1",
            frames=[frame1, frame2],
            transitions=[transition],
        )
        assert len(sequence.transitions) == 1

    def test_transitions_rejected_without_frames(self) -> None:
        """Test transitions cannot exist without frames."""
        transition = FrameTransition(
            source_frame_index=0,
            target_frame_index=1,
            duration_ms=500,
        )
        with pytest.raises(ValueError, match="transitions cannot exist in an empty sequence"):
            FrameSequence(
                sequence_id="seq_1",
                transitions=[transition],
            )

    def test_transition_invalid_frame_index_rejected(self) -> None:
        """Test transition with non-existent frame index is rejected."""
        frame1 = Frame(frame_index=0)
        transition = FrameTransition(
            source_frame_index=0,
            target_frame_index=99,  # Frame 99 doesn't exist
            duration_ms=500,
        )
        with pytest.raises(ValueError, match="target_frame_index 99 does not exist"):
            FrameSequence(
                sequence_id="seq_1",
                frames=[frame1],
                transitions=[transition],
            )


class TestSerialization:
    """Tests for serialization."""

    def test_frame_transform_dump_load(self) -> None:
        """Test FrameTransform serialization."""
        transform = FrameTransform(position_x=100, scale=1.5)
        data = transform.model_dump()
        assert data["position_x"] == 100
        assert data["scale"] == 1.5

    def test_frame_layer_dump_load(self) -> None:
        """Test FrameLayer serialization."""
        layer = FrameLayer(layer_type=LayerType.CHARACTER, layer_index=0)
        data = layer.model_dump()
        assert data["layer_type"] == "character"
        assert data["layer_index"] == 0

    def test_frame_dump_load(self) -> None:
        """Test Frame serialization."""
        frame = Frame(frame_index=0, duration_ms=1000)
        data = frame.model_dump()
        assert data["frame_index"] == 0
        assert data["duration_ms"] == 1000

    def test_round_trip_frame(self) -> None:
        """Test round-trip reconstruction."""
        original = Frame(
            frame_index=0,
            timestamp_ms=0,
            duration_ms=1000,
            layers=[
                FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0),
                FrameLayer(layer_type=LayerType.CHARACTER, layer_index=1),
            ],
        )
        data = original.model_dump()
        reconstructed = Frame(**data)
        assert reconstructed == original

    def test_round_trip_sequence(self) -> None:
        """Test round-trip reconstruction for sequence."""
        original = FrameSequence(
            sequence_id="seq_1",
            name="Test",
            frame_rate=30.0,
            frames=[
                Frame(
                    frame_index=0,
                    layers=[FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0)],
                ),
            ],
        )
        data = original.model_dump()
        reconstructed = FrameSequence(**data)
        assert reconstructed == original


class TestDeepImmutability:
    """Tests for deep immutability guarantees."""

    def test_frame_layers_is_tuple(self) -> None:
        """Test that Frame.layers is stored as tuple."""
        frame = Frame(
            frame_index=0,
            layers=[FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0)],
        )
        assert isinstance(frame.layers, tuple)

    def test_frame_layers_cannot_append(self) -> None:
        """Test that Frame.layers tuple cannot be appended to."""
        frame = Frame(
            frame_index=0,
            layers=[FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0)],
        )
        with pytest.raises(AttributeError):
            frame.layers.append(FrameLayer(layer_type=LayerType.CHARACTER, layer_index=1))

    def test_frame_layers_source_list_modification_protected(self) -> None:
        """Test that modifying source list doesn't affect Frame."""
        original = [FrameLayer(layer_type=LayerType.BACKGROUND, layer_index=0)]
        frame = Frame(frame_index=0, layers=original)

        # Modify original
        original.append(FrameLayer(layer_type=LayerType.CHARACTER, layer_index=1))

        # Frame should be unaffected
        assert len(frame.layers) == 1

    def test_frame_sequence_frames_is_tuple(self) -> None:
        """Test that FrameSequence.frames is stored as tuple."""
        sequence = FrameSequence(
            sequence_id="seq_1",
            frames=[Frame(frame_index=0)],
        )
        assert isinstance(sequence.frames, tuple)

    def test_frame_sequence_transitions_is_tuple(self) -> None:
        """Test that FrameSequence.transitions is stored as tuple."""
        sequence = FrameSequence(
            sequence_id="seq_1",
            frames=[Frame(frame_index=0), Frame(frame_index=1)],
            transitions=[FrameTransition(source_frame_index=0, target_frame_index=1, duration_ms=500)],
        )
        assert isinstance(sequence.transitions, tuple)

    def test_frame_sequence_frames_tuple_cannot_append(self) -> None:
        """Test that FrameSequence.frames tuple cannot be appended to."""
        sequence = FrameSequence(
            sequence_id="seq_1",
            frames=[Frame(frame_index=0)],
        )
        with pytest.raises(AttributeError):
            sequence.frames.append(Frame(frame_index=1))

    def test_nested_mutation_does_not_affect_source(self) -> None:
        """Test that modifying a source list doesn't affect the created model."""
        original_frames = [Frame(frame_index=0)]
        sequence = FrameSequence(sequence_id="seq_1", frames=original_frames)

        # Modify original list
        original_frames.append(Frame(frame_index=1))

        # Sequence should be unaffected
        assert len(sequence.frames) == 1

    def test_nested_frame_mutation_does_not_affect_source(self) -> None:
        """Test that modifying a Frame doesn't affect the one in the tuple."""
        original_frame = Frame(frame_index=0)
        sequence = FrameSequence(
            sequence_id="seq_1",
            frames=[original_frame],
        )

        # Replace in list (should fail because tuple)
        with pytest.raises(TypeError):
            sequence.frames[0] = Frame(frame_index=1)

    def test_sequence_is_frozen(self) -> None:
        """Test that FrameSequence itself is frozen (immutable)."""
        sequence = FrameSequence(sequence_id="seq_1")
        with pytest.raises(Exception):
            sequence.sequence_id = "new_id"
        with pytest.raises(Exception):
            sequence.frame_rate = 30.0


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test same input produces same output."""
        params = {
            "frame_index": 0,
            "timestamp_ms": 0,
            "duration_ms": 1000,
        }
        f1 = Frame(**params)
        f2 = Frame(**params)
        assert f1 == f2
        assert f1.model_dump() == f2.model_dump()

    def test_transform_determinism(self) -> None:
        """Test transform is deterministic."""
        t1 = FrameTransform(position_x=100, scale=2.0)
        t2 = FrameTransform(position_x=100, scale=2.0)
        assert t1 == t2


class TestDependencyRules:
    """Tests for dependency boundary verification."""

    def test_no_forbidden_imports(self) -> None:
        """Verify models has no forbidden imports."""
        import tools.frame.models as models_module
        source = models_module.__file__
        with open(source) as f:
            content = f.read()

        forbidden = [
            "torch", "tensorflow", "cv2", "PIL", "opencv",
            "requests", "httpx", "socket", "ffmpeg", "moviepy",
            "diffusers", "transformers", "stable", "controlnet"
        ]
        for item in forbidden:
            assert item not in content, f"Forbidden import found: {item}"
