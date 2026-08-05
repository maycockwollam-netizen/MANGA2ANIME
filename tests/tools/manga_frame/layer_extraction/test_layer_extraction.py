"""Tests for layer extraction contracts."""

from pathlib import Path

import pytest

from tools.manga_frame.layer_extraction import (
    ExtractionConfig,
    ExtractionStatus,
    LayerCategory,
    LayerDescriptor,
    LayerExtractionInput,
    LayerExtractionResult,
    LayerMetadata,
)


class TestLayerCategory:
    """Tests for LayerCategory enum."""

    def test_all_categories_exist(self) -> None:
        """Test all expected categories are defined."""
        assert LayerCategory.BACKGROUND == "background"
        assert LayerCategory.CHARACTER == "character"
        assert LayerCategory.FOREGROUND == "foreground"
        assert LayerCategory.EFFECT == "effect"
        assert LayerCategory.UNKNOWN == "unknown"

    def test_is_str_enum(self) -> None:
        """Test that LayerCategory is a string enum."""
        assert isinstance(LayerCategory.BACKGROUND, str)
        assert LayerCategory.BACKGROUND == "background"


class TestExtractionStatus:
    """Tests for ExtractionStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test all expected statuses are defined."""
        assert ExtractionStatus.NOT_PROCESSED == "not_processed"
        assert ExtractionStatus.SUCCESS == "success"
        assert ExtractionStatus.PARTIAL == "partial"
        assert ExtractionStatus.FAILED == "failed"

    def test_is_str_enum(self) -> None:
        """Test that ExtractionStatus is a string enum."""
        assert isinstance(ExtractionStatus.SUCCESS, str)
        assert ExtractionStatus.SUCCESS == "success"


class TestLayerDescriptor:
    """Tests for LayerDescriptor model."""

    def test_basic_construction(self) -> None:
        """Test basic layer descriptor construction."""
        descriptor = LayerDescriptor(
            layer_id="layer_1",
            layer_index=0,
        )
        assert descriptor.layer_id == "layer_1"
        assert descriptor.layer_index == 0
        assert descriptor.category == LayerCategory.UNKNOWN

    def test_full_construction(self) -> None:
        """Test layer descriptor with all fields."""
        metadata = LayerMetadata(confidence=0.95)
        descriptor = LayerDescriptor(
            layer_id="bg_layer",
            category=LayerCategory.BACKGROUND,
            layer_index=0,
            source_path=Path("/manga/page1.png"),
            metadata=metadata,
        )
        assert descriptor.layer_id == "bg_layer"
        assert descriptor.category == LayerCategory.BACKGROUND
        assert descriptor.layer_index == 0
        assert descriptor.source_path == Path("/manga/page1.png")
        assert descriptor.metadata is not None
        assert descriptor.metadata.confidence == 0.95

    def test_layer_id_normalization(self) -> None:
        """Test that layer_id is trimmed."""
        descriptor = LayerDescriptor(
            layer_id="  layer_id  ",
            layer_index=0,
        )
        assert descriptor.layer_id == "layer_id"

    def test_empty_layer_id_rejected(self) -> None:
        """Test that empty layer_id is rejected."""
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            LayerDescriptor(layer_id="", layer_index=0)

    def test_whitespace_layer_id_rejected(self) -> None:
        """Test that whitespace-only layer_id is rejected."""
        with pytest.raises(ValueError, match="empty or whitespace-only"):
            LayerDescriptor(layer_id="   ", layer_index=0)

    def test_negative_layer_index_rejected(self) -> None:
        """Test that negative layer_index is rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            LayerDescriptor(layer_id="layer", layer_index=-1)

    def test_zero_layer_index_valid(self) -> None:
        """Test that zero layer_index is valid."""
        descriptor = LayerDescriptor(layer_id="layer", layer_index=0)
        assert descriptor.layer_index == 0

    def test_multiple_categories(self) -> None:
        """Test all category values."""
        for category in LayerCategory:
            descriptor = LayerDescriptor(
                layer_id=f"layer_{category.value}",
                category=category,
                layer_index=0,
            )
            assert descriptor.category == category


class TestLayerMetadata:
    """Tests for LayerMetadata model."""

    def test_basic_construction(self) -> None:
        """Test basic metadata construction."""
        metadata = LayerMetadata()
        assert metadata.confidence is None
        assert metadata.region_bounds is None
        assert metadata.extra == ()

    def test_with_confidence(self) -> None:
        """Test metadata with confidence."""
        metadata = LayerMetadata(confidence=0.85)
        assert metadata.confidence == 0.85

    def test_confidence_bounds(self) -> None:
        """Test confidence value bounds."""
        # Valid bounds
        metadata = LayerMetadata(confidence=0.0)
        assert metadata.confidence == 0.0

        metadata = LayerMetadata(confidence=1.0)
        assert metadata.confidence == 1.0

        # Out of bounds
        with pytest.raises(ValueError):
            LayerMetadata(confidence=-0.1)

        with pytest.raises(ValueError):
            LayerMetadata(confidence=1.1)

    def test_region_bounds(self) -> None:
        """Test region bounds."""
        bounds = (100, 200, 50, 75)
        metadata = LayerMetadata(region_bounds=bounds)
        assert metadata.region_bounds == bounds

    def test_extra_from_dict(self) -> None:
        """Test extra metadata from dict."""
        metadata = LayerMetadata(
            extra={"key1": "value1", "key2": "value2"}
        )
        # Should be sorted and converted to tuple
        assert isinstance(metadata.extra, tuple)
        assert ("key1", "value1") in metadata.extra
        assert ("key2", "value2") in metadata.extra

    def test_extra_from_tuple(self) -> None:
        """Test extra metadata from tuple."""
        extra = (("key1", "val1"), ("key2", "val2"))
        metadata = LayerMetadata(extra=extra)
        assert metadata.extra == (("key1", "val1"), ("key2", "val2"))

    def test_metadata_is_frozen(self) -> None:
        """Test that metadata is frozen."""
        metadata = LayerMetadata()
        with pytest.raises((TypeError, ValueError)):
            metadata.confidence = 0.5  # type: ignore[misc]


class TestExtractionConfig:
    """Tests for ExtractionConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ExtractionConfig()
        assert config.min_confidence == 0.5
        assert config.include_effects is True
        assert config.max_layers is None
        assert config.detect_characters is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = ExtractionConfig(
            min_confidence=0.8,
            include_effects=False,
            max_layers=10,
            detect_characters=False,
        )
        assert config.min_confidence == 0.8
        assert config.include_effects is False
        assert config.max_layers == 10
        assert config.detect_characters is False

    def test_confidence_bounds(self) -> None:
        """Test confidence bounds."""
        config = ExtractionConfig(min_confidence=0.0)
        assert config.min_confidence == 0.0

        config = ExtractionConfig(min_confidence=1.0)
        assert config.min_confidence == 1.0

        with pytest.raises(ValueError):
            ExtractionConfig(min_confidence=-0.1)

        with pytest.raises(ValueError):
            ExtractionConfig(min_confidence=1.1)

    def test_max_layers_positive(self) -> None:
        """Test max_layers must be positive."""
        with pytest.raises(ValueError):
            ExtractionConfig(max_layers=0)

        config = ExtractionConfig(max_layers=1)
        assert config.max_layers == 1


class TestLayerExtractionInput:
    """Tests for LayerExtractionInput model."""

    def test_basic_construction(self) -> None:
        """Test basic input construction."""
        inp = LayerExtractionInput(
            source_path=Path("/manga/page1.png"),
            page_number=0,
        )
        assert inp.source_path == Path("/manga/page1.png")
        assert inp.page_number == 0
        assert inp.frame_reference is None
        assert inp.config is None

    def test_with_config(self) -> None:
        """Test input with extraction config."""
        config = ExtractionConfig(min_confidence=0.7)
        inp = LayerExtractionInput(
            source_path=Path("/manga/page2.png"),
            page_number=1,
            config=config,
        )
        assert inp.config is not None
        assert inp.config.min_confidence == 0.7

    def test_with_all_options(self) -> None:
        """Test input with all optional fields."""
        inp = LayerExtractionInput(
            source_path=Path("/manga/page3.png"),
            page_number=2,
            frame_reference="frame_2",
            config=ExtractionConfig(),
            sequence_id="seq_001",
        )
        assert inp.frame_reference == "frame_2"
        assert inp.sequence_id == "seq_001"

    def test_negative_page_number_rejected(self) -> None:
        """Test that negative page_number is rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            LayerExtractionInput(
                source_path=Path("/manga/page.png"),
                page_number=-1,
            )

    def test_zero_page_number_valid(self) -> None:
        """Test that zero page_number is valid."""
        inp = LayerExtractionInput(
            source_path=Path("/manga/page.png"),
            page_number=0,
        )
        assert inp.page_number == 0


class TestLayerExtractionResult:
    """Tests for LayerExtractionResult model."""

    def test_basic_construction(self) -> None:
        """Test basic result construction."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
        )
        assert result.source_path == Path("/manga/page1.png")
        assert result.page_number == 0
        assert result.layers == ()
        assert result.status == ExtractionStatus.NOT_PROCESSED

    def test_with_layers(self) -> None:
        """Test result with extracted layers."""
        layers = (
            LayerDescriptor(layer_id="bg", layer_index=0),
            LayerDescriptor(layer_id="char", layer_index=1),
        )
        result = LayerExtractionResult(
            source_path=Path("/manga/page1.png"),
            page_number=0,
            layers=layers,
            status=ExtractionStatus.SUCCESS,
        )
        assert len(result.layers) == 2
        assert result.status == ExtractionStatus.SUCCESS

    def test_layers_is_tuple(self) -> None:
        """Test that layers is stored as tuple."""
        layers = [LayerDescriptor(layer_id="l1", layer_index=0)]
        result = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
            layers=layers,
        )
        assert isinstance(result.layers, tuple)

    def test_layer_ordering_validated(self) -> None:
        """Test that layer ordering is validated."""
        layers = (
            LayerDescriptor(layer_id="l2", layer_index=2),
            LayerDescriptor(layer_id="l1", layer_index=1),
        )
        with pytest.raises(ValueError, match="must be ordered by layer_index"):
            LayerExtractionResult(
                source_path=Path("/manga/page.png"),
                page_number=0,
                layers=layers,
            )

    def test_duplicate_layer_index_rejected(self) -> None:
        """Test that duplicate layer_index values are rejected."""
        layers = (
            LayerDescriptor(layer_id="l1", layer_index=1),
            LayerDescriptor(layer_id="l1_dup", layer_index=1),
        )
        with pytest.raises(ValueError, match="duplicate layer_index"):
            LayerExtractionResult(
                source_path=Path("/manga/page.png"),
                page_number=0,
                layers=layers,
            )

    def test_result_is_frozen(self) -> None:
        """Test that result is frozen."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
        )
        with pytest.raises((TypeError, ValueError)):
            result.status = ExtractionStatus.SUCCESS  # type: ignore[misc]

    def test_layer_count_property(self) -> None:
        """Test layer_count property."""
        layers = (
            LayerDescriptor(layer_id="l1", layer_index=0),
            LayerDescriptor(layer_id="l2", layer_index=1),
            LayerDescriptor(layer_id="l3", layer_index=2),
        )
        result = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
            layers=layers,
        )
        assert result.layer_count == 3

    def test_get_layer_by_index(self) -> None:
        """Test get_layer_by_index method."""
        layers = (
            LayerDescriptor(layer_id="l1", layer_index=0),
            LayerDescriptor(layer_id="l2", layer_index=1),
        )
        result = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
            layers=layers,
        )
        layer = result.get_layer_by_index(1)
        assert layer is not None
        assert layer.layer_id == "l2"

        missing = result.get_layer_by_index(99)
        assert missing is None

    def test_get_layers_by_category(self) -> None:
        """Test get_layers_by_category method."""
        layers = (
            LayerDescriptor(layer_id="bg", layer_index=0, category=LayerCategory.BACKGROUND),
            LayerDescriptor(layer_id="char", layer_index=1, category=LayerCategory.CHARACTER),
            LayerDescriptor(layer_id="char2", layer_index=2, category=LayerCategory.CHARACTER),
            LayerDescriptor(layer_id="fg", layer_index=3, category=LayerCategory.FOREGROUND),
        )
        result = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
            layers=layers,
        )
        chars = result.get_layers_by_category(LayerCategory.CHARACTER)
        assert len(chars) == 2
        assert chars[0].layer_id == "char"
        assert chars[1].layer_id == "char2"


class TestDeepImmutability:
    """Tests for deep immutability guarantees."""

    def test_layer_descriptor_lists_immutable(self) -> None:
        """Test that layer descriptor doesn't expose mutable lists."""
        descriptor = LayerDescriptor(layer_id="l1", layer_index=0)
        # Should not have append, extend, etc.
        assert not hasattr(descriptor, "append")

    def test_result_layers_cannot_append(self) -> None:
        """Test that result.layers tuple cannot be appended to."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
        )
        with pytest.raises(AttributeError):
            result.layers.append(LayerDescriptor(layer_id="new", layer_index=0))

    def test_caller_list_modification_protected(self) -> None:
        """Test that modifying caller-owned list doesn't affect result."""
        original_layers = [LayerDescriptor(layer_id="l1", layer_index=0)]
        result = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
            layers=original_layers,
        )

        # Modify original list
        original_layers.append(LayerDescriptor(layer_id="l2", layer_index=1))

        # Result should be unaffected
        assert len(result.layers) == 1

    def test_metadata_is_frozen(self) -> None:
        """Test that nested metadata is frozen."""
        metadata = LayerMetadata(confidence=0.5)
        with pytest.raises((TypeError, ValueError)):
            metadata.confidence = 0.9  # type: ignore[misc]

    def test_result_is_frozen(self) -> None:
        """Test that result itself is frozen."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
        )
        with pytest.raises((TypeError, ValueError)):
            result.page_number = 5  # type: ignore[misc]


class TestSerialization:
    """Tests for serialization behavior."""

    def test_layer_descriptor_serialization(self) -> None:
        """Test LayerDescriptor serialization."""
        descriptor = LayerDescriptor(
            layer_id="test_layer",
            layer_index=0,
        )
        data = descriptor.model_dump()
        assert data["layer_id"] == "test_layer"
        assert data["layer_index"] == 0

    def test_result_serialization(self) -> None:
        """Test LayerExtractionResult serialization."""
        result = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
            layers=[LayerDescriptor(layer_id="l1", layer_index=0)],
        )
        data = result.model_dump()
        assert str(data["source_path"]) == "/manga/page.png"
        assert data["page_number"] == 0
        # layers is a collection (tuple in Pydantic v2)
        assert isinstance(data["layers"], (list, tuple))

    def test_serialization_roundtrip(self) -> None:
        """Test that serialization roundtrip preserves equality."""
        original = LayerExtractionResult(
            source_path=Path("/manga/page.png"),
            page_number=0,
            layers=[
                LayerDescriptor(layer_id="l1", layer_index=0),
                LayerDescriptor(layer_id="l2", layer_index=1),
            ],
            status=ExtractionStatus.SUCCESS,
        )

        # Roundtrip
        data = original.model_dump()
        reconstructed = LayerExtractionResult(**data)

        assert reconstructed == original

    def test_metadata_serialization(self) -> None:
        """Test LayerMetadata serialization."""
        metadata = LayerMetadata(
            confidence=0.85,
            region_bounds=(10, 20, 100, 200),
        )
        data = metadata.model_dump()
        assert data["confidence"] == 0.85
        assert data["region_bounds"] == (10, 20, 100, 200)


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test that same input produces same output."""
        input1 = LayerExtractionInput(
            source_path=Path("/manga/page.png"),
            page_number=0,
        )
        input2 = LayerExtractionInput(
            source_path=Path("/manga/page.png"),
            page_number=0,
        )

        # Create equivalent results
        result1 = LayerExtractionResult(
            source_path=input1.source_path,
            page_number=input1.page_number,
        )
        result2 = LayerExtractionResult(
            source_path=input2.source_path,
            page_number=input2.page_number,
        )

        assert result1 == result2
        assert result1.model_dump() == result2.model_dump()


class TestDependencyBoundary:
    """Tests for dependency boundary verification."""

    def test_no_forbidden_imports(self) -> None:
        """Verify no forbidden imports in layer_extraction."""
        import tools.manga_frame.layer_extraction as module
        source_file = module.__file__
        assert source_file is not None

        with open(source_file) as f:
            content = f.read()

        forbidden = [
            "from PIL", "import PIL",
            "from cv2", "import cv2",
            "from numpy", "import numpy",
            "from torch", "import torch",
            "from tensorflow", "import tensorflow",
            "from diffusers", "import diffusers",
            "from transformers", "import transformers",
            "from requests", "import requests",
            "from httpx", "import httpx",
            "from ffmpeg", "import ffmpeg",
            "from moviepy", "import moviepy",
            "import gpu", "import cuda",
            "import potrace",
            "from runtime", "import runtime",
            "from agents", "import agents",
            "from apps", "import apps",
            "from core.", "import core.",
        ]

        for item in forbidden:
            assert item not in content, f"Forbidden import found: {item}"

    def test_allowed_imports(self) -> None:
        """Verify expected allowed imports."""
        import tools.manga_frame.layer_extraction as module
        source_file = module.__file__

        with open(source_file) as f:
            content = f.read()

        # Should have pydantic
        assert "from pydantic" in content

    def test_manga_frame_module_imports_layer_extraction(self) -> None:
        """Verify manga_frame can import layer_extraction."""
        # This should work without errors
        from tools.manga_frame.layer_extraction import (
            LayerCategory,
            LayerDescriptor,
            LayerExtractionResult,
        )
        assert LayerCategory is not None
        assert LayerDescriptor is not None
        assert LayerExtractionResult is not None
