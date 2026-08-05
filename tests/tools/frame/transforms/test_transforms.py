"""Tests for frame transforms V1."""

import pytest

from tools.frame.models import FrameTransform
from tools.frame.transforms import (
    TransformResult,
    apply_transform,
    compose_transforms,
    identity_transform,
    interpolate_transform,
    lerp_float,
)


class TestTransformResult:
    """Tests for TransformResult."""

    def test_creation(self) -> None:
        """Test creating a TransformResult."""
        result = TransformResult(
            position_x=100.0,
            position_y=200.0,
            scale=1.5,
            rotation_deg=45.0,
            opacity=0.8,
            anchor_x=0.5,
            anchor_y=0.5,
        )
        assert result.position_x == 100.0
        assert result.position_y == 200.0
        assert result.scale == 1.5
        assert result.rotation_deg == 45.0
        assert result.opacity == 0.8

    def test_frozen(self) -> None:
        """Test TransformResult is frozen."""
        result = TransformResult(
            position_x=100.0,
            position_y=200.0,
            scale=1.5,
            rotation_deg=45.0,
            opacity=0.8,
            anchor_x=0.5,
            anchor_y=0.5,
        )
        with pytest.raises(AttributeError):
            result.position_x = 0.0

    def test_model_dump(self) -> None:
        """Test serialization."""
        result = TransformResult(
            position_x=100.0,
            position_y=200.0,
            scale=1.5,
            rotation_deg=45.0,
            opacity=0.8,
            anchor_x=0.5,
            anchor_y=0.5,
        )
        data = result.model_dump()
        assert data["position_x"] == 100.0
        assert data["scale"] == 1.5


class TestApplyTransform:
    """Tests for apply_transform."""

    def test_identity_transform(self) -> None:
        """Test applying identity transform."""
        transform = FrameTransform()
        result = apply_transform(transform)
        assert result.position_x == 0.0
        assert result.position_y == 0.0
        assert result.scale == 1.0
        assert result.rotation_deg == 0.0
        assert result.opacity == 1.0

    def test_translation_only(self) -> None:
        """Test translation only."""
        transform = FrameTransform(position_x=100.0, position_y=50.0)
        result = apply_transform(transform)
        assert result.position_x == 100.0
        assert result.position_y == 50.0

    def test_negative_translation(self) -> None:
        """Test negative translation."""
        transform = FrameTransform(position_x=-50.0, position_y=-100.0)
        result = apply_transform(transform)
        assert result.position_x == -50.0
        assert result.position_y == -100.0

    def test_scale_only(self) -> None:
        """Test scale only."""
        transform = FrameTransform(scale=2.0)
        result = apply_transform(transform)
        assert result.scale == 2.0

    def test_rotation_only(self) -> None:
        """Test rotation only."""
        transform = FrameTransform(rotation_deg=90.0)
        result = apply_transform(transform)
        assert result.rotation_deg == 90.0

    def test_negative_rotation(self) -> None:
        """Test negative rotation."""
        transform = FrameTransform(rotation_deg=-45.0)
        result = apply_transform(transform)
        assert result.rotation_deg == -45.0

    def test_opacity_full(self) -> None:
        """Test full opacity."""
        transform = FrameTransform(opacity=1.0)
        result = apply_transform(transform)
        assert result.opacity == 1.0

    def test_opacity_zero(self) -> None:
        """Test zero opacity."""
        transform = FrameTransform(opacity=0.0)
        result = apply_transform(transform)
        assert result.opacity == 0.0

    def test_opacity_intermediate(self) -> None:
        """Test intermediate opacity."""
        transform = FrameTransform(opacity=0.75)
        result = apply_transform(transform)
        assert result.opacity == 0.75

    def test_anchor_origin(self) -> None:
        """Test origin anchor."""
        transform = FrameTransform(anchor_x=0.0, anchor_y=0.0)
        result = apply_transform(transform)
        assert result.anchor_x == 0.0
        assert result.anchor_y == 0.0

    def test_anchor_center(self) -> None:
        """Test center anchor."""
        transform = FrameTransform(anchor_x=0.5, anchor_y=0.5)
        result = apply_transform(transform)
        assert result.anchor_x == 0.5
        assert result.anchor_y == 0.5

    def test_origin_offset(self) -> None:
        """Test with origin offset."""
        transform = FrameTransform(position_x=100.0)
        result = apply_transform(transform, origin_x=50.0, origin_y=25.0)
        assert result.position_x == 150.0
        assert result.position_y == 25.0

    def test_combined_transform(self) -> None:
        """Test combined transform."""
        transform = FrameTransform(
            position_x=100.0,
            position_y=200.0,
            scale=2.0,
            rotation_deg=90.0,
            opacity=0.5,
        )
        result = apply_transform(transform)
        assert result.position_x == 100.0
        assert result.position_y == 200.0
        assert result.scale == 2.0
        assert result.rotation_deg == 90.0
        assert result.opacity == 0.5

    def test_source_not_mutated(self) -> None:
        """Test source FrameTransform is not mutated."""
        transform = FrameTransform(position_x=100.0, scale=2.0)
        original_x = transform.position_x
        original_scale = transform.scale
        _ = apply_transform(transform)
        assert transform.position_x == original_x
        assert transform.scale == original_scale


class TestComposeTransforms:
    """Tests for compose_transforms."""

    def test_empty_list(self) -> None:
        """Test empty transforms list."""
        result = compose_transforms([])
        assert result.position_x == 0.0
        assert result.position_y == 0.0
        assert result.scale == 1.0
        assert result.rotation_deg == 0.0
        assert result.opacity == 1.0

    def test_single_transform(self) -> None:
        """Test single transform."""
        transform = FrameTransform(position_x=100.0)
        result = compose_transforms([transform])
        assert result.position_x == 100.0

    def test_position_additive(self) -> None:
        """Test position is additive."""
        t1 = FrameTransform(position_x=50.0)
        t2 = FrameTransform(position_x=30.0)
        result = compose_transforms([t1, t2])
        assert result.position_x == 80.0

    def test_scale_multiplicative(self) -> None:
        """Test scale is multiplicative."""
        t1 = FrameTransform(scale=2.0)
        t2 = FrameTransform(scale=3.0)
        result = compose_transforms([t1, t2])
        assert result.scale == 6.0  # 2.0 * 3.0

    def test_rotation_additive(self) -> None:
        """Test rotation is additive."""
        t1 = FrameTransform(rotation_deg=45.0)
        t2 = FrameTransform(rotation_deg=15.0)
        result = compose_transforms([t1, t2])
        assert result.rotation_deg == 60.0

    def test_last_opacity_wins(self) -> None:
        """Test last opacity wins."""
        t1 = FrameTransform(opacity=1.0)
        t2 = FrameTransform(opacity=0.5)
        result = compose_transforms([t1, t2])
        assert result.opacity == 0.5

    def test_last_anchor_wins(self) -> None:
        """Test last anchor wins."""
        t1 = FrameTransform(anchor_x=0.0, anchor_y=0.0)
        t2 = FrameTransform(anchor_x=1.0, anchor_y=1.0)
        result = compose_transforms([t1, t2])
        assert result.anchor_x == 1.0
        assert result.anchor_y == 1.0

    def test_composition_order(self) -> None:
        """Test composition order matters."""
        t1 = FrameTransform(position_x=100.0, scale=2.0)
        t2 = FrameTransform(position_x=50.0, scale=0.5)
        result = compose_transforms([t1, t2])
        assert result.position_x == 150.0  # 100 + 50
        assert result.scale == 1.0  # 2.0 * 0.5

    def test_deterministic(self) -> None:
        """Test composition is deterministic."""
        transforms = [
            FrameTransform(position_x=10.0, scale=2.0),
            FrameTransform(position_y=20.0, rotation_deg=45.0),
        ]
        result1 = compose_transforms(transforms)
        result2 = compose_transforms(transforms)
        assert result1 == result2

    def test_with_origin(self) -> None:
        """Test composition with origin."""
        transform = FrameTransform(position_x=50.0)
        result = compose_transforms([transform], origin_x=100.0)
        assert result.position_x == 150.0


class TestInterpolateTransform:
    """Tests for interpolate_transform."""

    def test_t_zero(self) -> None:
        """Test t=0 returns start."""
        start = FrameTransform(position_x=0.0, scale=1.0)
        end = FrameTransform(position_x=100.0, scale=2.0)
        result = interpolate_transform(start, end, 0.0)
        assert result.position_x == 0.0
        assert result.scale == 1.0

    def test_t_one(self) -> None:
        """Test t=1 returns end."""
        start = FrameTransform(position_x=0.0, scale=1.0)
        end = FrameTransform(position_x=100.0, scale=2.0)
        result = interpolate_transform(start, end, 1.0)
        assert result.position_x == 100.0
        assert result.scale == 2.0

    def test_t_midpoint(self) -> None:
        """Test t=0.5 returns midpoint."""
        start = FrameTransform(position_x=0.0, scale=1.0)
        end = FrameTransform(position_x=100.0, scale=2.0)
        result = interpolate_transform(start, end, 0.5)
        assert result.position_x == 50.0
        assert result.scale == 1.5

    def test_position_interpolation(self) -> None:
        """Test position interpolation."""
        start = FrameTransform(position_x=0.0, position_y=0.0)
        end = FrameTransform(position_x=100.0, position_y=200.0)
        result = interpolate_transform(start, end, 0.25)
        assert result.position_x == 25.0
        assert result.position_y == 50.0

    def test_scale_interpolation(self) -> None:
        """Test scale interpolation."""
        start = FrameTransform(scale=1.0)
        end = FrameTransform(scale=3.0)
        result = interpolate_transform(start, end, 0.5)
        assert result.scale == 2.0

    def test_rotation_interpolation(self) -> None:
        """Test rotation interpolation (direct numeric)."""
        start = FrameTransform(rotation_deg=0.0)
        end = FrameTransform(rotation_deg=180.0)
        result = interpolate_transform(start, end, 0.5)
        assert result.rotation_deg == 90.0

    def test_rotation_direct_interpolation_not_shortest_angle(self) -> None:
        """Test rotation uses direct interpolation, NOT shortest-angle.

        This is a regression test to ensure current behavior is preserved.
        Interpolating 350° to 10° should give 180° (direct), not -20° (shortest).
        """
        start = FrameTransform(rotation_deg=350.0)
        end = FrameTransform(rotation_deg=10.0)
        result = interpolate_transform(start, end, 0.5)
        # Direct: 350 + (10 - 350) * 0.5 = 350 + (-340) * 0.5 = 350 - 170 = 180
        assert result.rotation_deg == 180.0

    def test_opacity_interpolation(self) -> None:
        """Test opacity interpolation."""
        start = FrameTransform(opacity=0.0)
        end = FrameTransform(opacity=1.0)
        result = interpolate_transform(start, end, 0.75)
        assert result.opacity == 0.75

    def test_anchor_interpolation(self) -> None:
        """Test anchor interpolation."""
        start = FrameTransform(anchor_x=0.0, anchor_y=0.0)
        end = FrameTransform(anchor_x=1.0, anchor_y=1.0)
        result = interpolate_transform(start, end, 0.5)
        assert result.anchor_x == 0.5
        assert result.anchor_y == 0.5

    def test_none_defaults(self) -> None:
        """Test None values use defaults."""
        start = FrameTransform()
        end = FrameTransform(position_x=100.0, scale=2.0)
        result = interpolate_transform(start, end, 0.5)
        assert result.position_x == 50.0  # 0 + (100 - 0) * 0.5
        assert result.scale == 1.5  # 1.0 + (2.0 - 1.0) * 0.5

    def test_t_out_of_range_raises(self) -> None:
        """Test t outside [0, 1] raises ValueError."""
        start = FrameTransform()
        end = FrameTransform(position_x=100.0)
        with pytest.raises(ValueError):
            interpolate_transform(start, end, -0.1)
        with pytest.raises(ValueError):
            interpolate_transform(start, end, 1.1)

    def test_deterministic(self) -> None:
        """Test interpolation is deterministic."""
        start = FrameTransform(position_x=0.0, scale=1.0)
        end = FrameTransform(position_x=100.0, scale=2.0)
        result1 = interpolate_transform(start, end, 0.3)
        result2 = interpolate_transform(start, end, 0.3)
        assert result1 == result2

    def test_returns_new_instance(self) -> None:
        """Test interpolation returns new instance."""
        start = FrameTransform(position_x=0.0)
        end = FrameTransform(position_x=100.0)
        result = interpolate_transform(start, end, 0.5)
        assert result is not start
        assert result is not end


class TestLerpFloat:
    """Tests for lerp_float."""

    def test_basic(self) -> None:
        """Test basic linear interpolation."""
        assert lerp_float(0.0, 100.0, 0.0) == 0.0
        assert lerp_float(0.0, 100.0, 1.0) == 100.0
        assert lerp_float(0.0, 100.0, 0.5) == 50.0

    def test_negative_values(self) -> None:
        """Test interpolation with negative values."""
        assert lerp_float(-50.0, 50.0, 0.5) == 0.0

    def test_deterministic(self) -> None:
        """Test lerp is deterministic."""
        result1 = lerp_float(0.0, 100.0, 0.25)
        result2 = lerp_float(0.0, 100.0, 0.25)
        assert result1 == result2


class TestIdentityTransform:
    """Tests for identity_transform."""

    def test_creates_identity(self) -> None:
        """Test creates identity transform."""
        identity = identity_transform()
        assert identity.position_x is None
        assert identity.position_y is None
        assert identity.scale == 1.0
        assert identity.rotation_deg == 0.0
        assert identity.opacity == 1.0

    def test_applies_to_identity(self) -> None:
        """Test applying identity transform."""
        identity = identity_transform()
        result = apply_transform(identity)
        assert result.position_x == 0.0
        assert result.position_y == 0.0
        assert result.scale == 1.0


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test same input always produces same output."""
        transform = FrameTransform(position_x=100.0, scale=2.0)
        for _ in range(10):
            result = apply_transform(transform)
            assert result.position_x == 100.0
            assert result.scale == 2.0

    def test_compose_deterministic(self) -> None:
        """Test composition is deterministic."""
        transforms = [
            FrameTransform(position_x=10.0),
            FrameTransform(position_y=20.0),
            FrameTransform(scale=2.0),
        ]
        for _ in range(10):
            result = compose_transforms(transforms)
            assert result.position_x == 10.0
            assert result.position_y == 20.0
            assert result.scale == 2.0


class TestDependencyRules:
    """Tests for dependency boundary verification."""

    def test_no_forbidden_imports(self) -> None:
        """Verify transforms has no forbidden imports."""
        import tools.frame.transforms as transforms_module
        source = transforms_module.__file__
        with open(source) as f:
            content = f.read()

        forbidden = [
            "torch", "tensorflow", "cv2", "PIL", "opencv",
            "requests", "httpx", "socket", "ffmpeg", "moviepy",
            "diffusers", "transformers", "stable", "controlnet"
        ]
        for item in forbidden:
            assert item not in content, f"Forbidden import found: {item}"
