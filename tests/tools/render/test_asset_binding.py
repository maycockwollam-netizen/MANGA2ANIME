"""Unit tests for tools.render.asset_binding module."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest
from PIL import Image

from tools.frame.models import FrameTransform
from tools.render import RenderFrame, bind_render_frame_assets


class TestBindRenderFrameAssets:
    """Unit tests for bind_render_frame_assets function."""

    @pytest.fixture
    def base_transform(self) -> FrameTransform:
        """Create a base FrameTransform for testing."""
        return FrameTransform(
            position_x=100.0,
            position_y=200.0,
            scale=1.5,
            rotation_deg=45.0,
            opacity=0.8,
            anchor_x=0.25,
            anchor_y=0.75,
        )

    @pytest.fixture
    def base_frame(self, base_transform: FrameTransform) -> RenderFrame:
        """Create a base RenderFrame for testing."""
        return RenderFrame(
            frame_index=5,
            timestamp_seconds=0.5,
            frame_rate=24.0,
            duration_frames=48,
            transforms=MappingProxyType({
                "hero": base_transform,
                "villain": FrameTransform(
                    position_x=500.0,
                    position_y=300.0,
                    scale=1.0,
                    rotation_deg=0.0,
                    opacity=1.0,
                    anchor_x=0.5,
                    anchor_y=0.5,
                ),
            }),
        )

    def test_empty_asset_mapping(self, base_frame: RenderFrame) -> None:
        """Empty asset mapping preserves all transforms unchanged."""
        result = bind_render_frame_assets(base_frame, {})

        # All transforms preserved
        assert len(result.transforms) == 2
        assert "hero" in result.transforms
        assert "villain" in result.transforms

        # Original source_path values preserved (None)
        assert result.transforms["hero"].source_path is None
        assert result.transforms["villain"].source_path is None

        # All transform properties preserved
        assert result.transforms["hero"].position_x == 100.0
        assert result.transforms["hero"].position_y == 200.0
        assert result.transforms["villain"].position_x == 500.0

    def test_one_asset_binding(
        self,
        base_frame: RenderFrame,
        tmp_path: Path,
    ) -> None:
        """One asset binding adds source_path to matching transform."""
        asset_path = tmp_path / "hero.png"

        result = bind_render_frame_assets(
            base_frame,
            {"hero": asset_path},
        )

        # Only hero gets the asset path
        assert result.transforms["hero"].source_path == asset_path
        assert result.transforms["villain"].source_path is None

    def test_multiple_asset_bindings(
        self,
        base_frame: RenderFrame,
        tmp_path: Path,
    ) -> None:
        """Multiple asset bindings add source_path to all matching transforms."""
        hero_path = tmp_path / "hero.png"
        villain_path = tmp_path / "villain.png"

        result = bind_render_frame_assets(
            base_frame,
            {
                "hero": hero_path,
                "villain": villain_path,
            },
        )

        assert result.transforms["hero"].source_path == hero_path
        assert result.transforms["villain"].source_path == villain_path

    def test_unmatched_transform_unchanged(self, base_frame: RenderFrame) -> None:
        """Transform without matching asset mapping remains unchanged."""
        result = bind_render_frame_assets(base_frame, {})

        # villain unchanged
        villain = result.transforms["villain"]
        assert villain.position_x == 500.0
        assert villain.position_y == 300.0
        assert villain.scale == 1.0
        assert villain.source_path is None

    def test_existing_source_path_preserved_when_no_mapping(self) -> None:
        """Existing source_path is preserved when no mapping exists."""
        existing_path = Path("/existing/asset.png")
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=10,
            transforms=MappingProxyType({
                "entity": FrameTransform(
                    position_x=0.0,
                    source_path=existing_path,
                ),
            }),
        )

        result = bind_render_frame_assets(frame, {})

        assert result.transforms["entity"].source_path == existing_path

    def test_explicit_mapping_replaces_source_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Explicit asset mapping replaces existing source_path."""
        existing_path = Path("/existing/asset.png")
        new_path = tmp_path / "new_asset.png"

        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=10,
            transforms=MappingProxyType({
                "entity": FrameTransform(
                    position_x=0.0,
                    source_path=existing_path,
                ),
            }),
        )

        result = bind_render_frame_assets(
            frame,
            {"entity": new_path},
        )

        assert result.transforms["entity"].source_path == new_path
        assert result.transforms["entity"].source_path != existing_path

    def test_all_transform_fields_preserved(
        self,
        base_transform: FrameTransform,
        tmp_path: Path,
    ) -> None:
        """All transform fields are preserved after binding."""
        asset_path = tmp_path / "hero.png"
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=10,
            transforms=MappingProxyType({"hero": base_transform}),
        )

        result = bind_render_frame_assets(frame, {"hero": asset_path})
        bound = result.transforms["hero"]

        assert bound.position_x == base_transform.position_x
        assert bound.position_y == base_transform.position_y
        assert bound.scale == base_transform.scale
        assert bound.rotation_deg == base_transform.rotation_deg
        assert bound.opacity == base_transform.opacity
        assert bound.anchor_x == base_transform.anchor_x
        assert bound.anchor_y == base_transform.anchor_y
        assert bound.source_path == asset_path

    def test_frame_metadata_preserved(
        self,
        base_frame: RenderFrame,
        tmp_path: Path,
    ) -> None:
        """Frame metadata is preserved after binding."""
        asset_path = tmp_path / "hero.png"

        result = bind_render_frame_assets(
            base_frame,
            {"hero": asset_path},
        )

        assert result.frame_index == base_frame.frame_index
        assert result.timestamp_seconds == base_frame.timestamp_seconds
        assert result.frame_rate == base_frame.frame_rate
        assert result.duration_frames == base_frame.duration_frames
        assert result.entity_count == base_frame.entity_count

    def test_input_frame_unchanged(self, base_frame: RenderFrame) -> None:
        """Input RenderFrame is not modified."""
        original_transforms = dict(base_frame.transforms)

        bind_render_frame_assets(base_frame, {})

        # Original frame unchanged
        for clip_id in base_frame.transforms:
            original = original_transforms[clip_id]
            current = base_frame.transforms[clip_id]
            assert current.position_x == original.position_x
            assert current.position_y == original.position_y
            assert current.source_path == original.source_path

    def test_returned_frame_immutable(self, tmp_path: Path) -> None:
        """Returned RenderFrame transforms are immutable."""
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=10,
            transforms=MappingProxyType({
                "entity": FrameTransform(position_x=0.0),
            }),
        )

        result = bind_render_frame_assets(
            frame,
            {"entity": tmp_path / "asset.png"},
        )

        # Result transforms is a MappingProxyType (immutable)
        assert isinstance(result.transforms, MappingProxyType)

    def test_deterministic_repeated_calls(
        self,
        base_frame: RenderFrame,
        tmp_path: Path,
    ) -> None:
        """Repeated calls produce identical results."""
        asset_path = tmp_path / "hero.png"

        result1 = bind_render_frame_assets(
            base_frame,
            {"hero": asset_path},
        )
        result2 = bind_render_frame_assets(
            base_frame,
            {"hero": asset_path},
        )

        # Same transforms
        assert result1.frame_index == result2.frame_index
        assert result1.timestamp_seconds == result2.timestamp_seconds

        # Same bound paths
        assert (
            result1.transforms["hero"].source_path
            == result2.transforms["hero"].source_path
        )
        assert (
            result1.transforms["hero"].position_x
            == result2.transforms["hero"].position_x
        )

    def test_asset_paths_with_str(self, base_frame: RenderFrame) -> None:
        """Asset paths can be specified as str."""
        result = bind_render_frame_assets(
            base_frame,
            {"hero": "/path/to/asset.png"},
        )

        assert result.transforms["hero"].source_path == Path("/path/to/asset.png")
        assert isinstance(result.transforms["hero"].source_path, Path)

    def test_asset_paths_with_path(self, base_frame: RenderFrame, tmp_path: Path) -> None:
        """Asset paths can be specified as Path."""
        asset_path = tmp_path / "asset.png"
        result = bind_render_frame_assets(
            base_frame,
            {"hero": asset_path},
        )

        assert result.transforms["hero"].source_path == asset_path
        assert isinstance(result.transforms["hero"].source_path, Path)

    def test_transform_ordering_preserved(self, tmp_path: Path) -> None:
        """Transform ordering is preserved from input frame."""
        frame = RenderFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            frame_rate=24.0,
            duration_frames=10,
            transforms=MappingProxyType({
                "z_first": FrameTransform(position_x=0.0),
                "a_second": FrameTransform(position_x=0.0),
                "m_middle": FrameTransform(position_x=0.0),
            }),
        )

        result = bind_render_frame_assets(
            frame,
            {
                "a_second": tmp_path / "a.png",
                "m_middle": tmp_path / "m.png",
                "z_first": tmp_path / "z.png",
            },
        )

        # Order preserved
        keys = list(result.transforms.keys())
        assert keys == ["z_first", "a_second", "m_middle"]

    def test_no_image_files_loaded(
        self,
        base_frame: RenderFrame,
        tmp_path: Path,
    ) -> None:
        """No image files are loaded during binding."""
        # Create a non-existent path (would fail if we tried to load it)
        non_existent_path = tmp_path / "non_existent_asset.png"

        # Should not raise - we only bind paths, don't load files
        result = bind_render_frame_assets(
            base_frame,
            {"hero": non_existent_path},
        )

        assert result.transforms["hero"].source_path == non_existent_path

    def test_no_filesystem_mutation(
        self,
        base_frame: RenderFrame,
        tmp_path: Path,
    ) -> None:
        """Binding does not mutate the filesystem."""
        initial_files = set(tmp_path.rglob("*"))
        asset_path = tmp_path / "hero.png"

        bind_render_frame_assets(base_frame, {"hero": asset_path})

        # No files created
        final_files = set(tmp_path.rglob("*"))
        assert initial_files == final_files

    def test_public_api_importable(self) -> None:
        """bind_render_frame_assets is importable from tools.render."""
        from tools.render import bind_render_frame_assets

        assert callable(bind_render_frame_assets)

    def test_invalid_asset_type_raises(self, base_frame: RenderFrame) -> None:
        """Invalid asset path type raises TypeError."""
        with pytest.raises(TypeError, match="must be Path or str"):
            bind_render_frame_assets(
                base_frame,
                {"hero": 123},  # type: ignore
            )

    def test_partial_binding(self, base_frame: RenderFrame, tmp_path: Path) -> None:
        """Partial binding only affects mapped transforms."""
        partial_path = tmp_path / "villain.png"

        result = bind_render_frame_assets(
            base_frame,
            {"villain": partial_path},
        )

        # villain updated
        assert result.transforms["villain"].source_path == partial_path
        # hero unchanged
        assert result.transforms["hero"].source_path is None
        assert result.transforms["hero"].position_x == 100.0

    def test_bound_frame_renders_correctly(
        self,
        base_frame: RenderFrame,
        tmp_path: Path,
    ) -> None:
        """Bound frame can be rendered with ConcreteRenderer."""
        from tools.render import ConcreteRenderer

        asset_path = tmp_path / "hero.png"
        Image.new("RGBA", (50, 50), color=(255, 0, 0, 255)).save(asset_path)

        bound_frame = bind_render_frame_assets(
            base_frame,
            {"hero": asset_path},
        )

        renderer = ConcreteRenderer(canvas_size=(800, 600))
        renderer.render(bound_frame)

        # Get last_output as documented
        result = renderer.last_output
        assert result is not None
        assert result.mode == "RGBA"
        assert result.size == (800, 600)


class TestForbiddenImports:
    """Tests verifying no forbidden imports in production modules."""

    def test_no_forbidden_imports_in_asset_binding(self) -> None:
        """asset_binding module does not import forbidden dependencies."""
        import ast

        module_path = "tools/render/asset_binding.py"

        forbidden = [
            "runtime",
            "AnimationRuntime",
            "AnimationTimeline",
            "AnimationClip",
            "tools.manga_frame",
            "threading",
            "asyncio",
        ]

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
                assert forbid not in imp, (
                    f"Forbidden import '{forbid}' found in {module_path}"
                )
