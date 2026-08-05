"""Tests for frame palette."""

import pytest

from tools.frame.palette import CharacterColorPalette


class TestConstruction:
    """Tests for palette construction."""

    def test_valid_palette(self) -> None:
        """Test creating a valid palette."""
        palette = CharacterColorPalette(
            character_id="naruto",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )

        assert palette.character_id == "naruto"
        assert palette.hair == "#FF9900"
        assert palette.skin == "#FFCC99"
        assert palette.eyes == "#4477EE"
        assert palette.outfit == "#FFCC00"

    def test_minimal_palette(self) -> None:
        """Test minimal palette with only required fields."""
        palette = CharacterColorPalette(
            character_id="character1",
            hair="#000000",
            skin="#FFFFFF",
            eyes="#000000",
            outfit="#FFFFFF",
        )

        assert palette.character_id == "character1"
        assert palette.accessories is None
        assert palette.custom_colors == ()

    def test_optional_accessories(self) -> None:
        """Test palette with optional accessories."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            accessories="#333333",
        )

        assert palette.accessories == "#333333"

    def test_custom_colors(self) -> None:
        """Test palette with custom colors as tuple."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            custom_colors={"cape": "#FF0000", "sword": "#AAAAAA"},
        )

        # custom_colors is now a tuple of tuples, sorted by key
        assert isinstance(palette.custom_colors, tuple)
        assert len(palette.custom_colors) == 2
        # Sorted alphabetically by key
        assert palette.custom_colors[0] == ("cape", "#FF0000")
        assert palette.custom_colors[1] == ("sword", "#AAAAAA")


class TestCharacterID:
    """Tests for character ID validation."""

    def test_valid_character_id(self) -> None:
        """Test valid character ID."""
        palette = CharacterColorPalette(
            character_id="valid_id_123",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
        assert palette.character_id == "valid_id_123"

    def test_empty_character_id_rejected(self) -> None:
        """Test empty character ID is rejected."""
        with pytest.raises(ValueError):
            CharacterColorPalette(
                character_id="",
                hair="#FF9900",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )

    def test_whitespace_only_id_rejected(self) -> None:
        """Test whitespace-only character ID is rejected."""
        with pytest.raises(ValueError):
            CharacterColorPalette(
                character_id="   ",
                hair="#FF9900",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )


class TestHexValidation:
    """Tests for HEX color validation."""

    def test_valid_uppercase_hex(self) -> None:
        """Test valid uppercase HEX color."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
        assert palette.hair == "#FF9900"

    def test_valid_lowercase_hex_normalized(self) -> None:
        """Test lowercase HEX is normalized to uppercase."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#ff9900",
            skin="#ffcc99",
            eyes="#4477ee",
            outfit="#ffcc00",
        )
        assert palette.hair == "#FF9900"
        assert palette.skin == "#FFCC99"
        assert palette.eyes == "#4477EE"
        assert palette.outfit == "#FFCC00"

    def test_malformed_hex_too_short(self) -> None:
        """Test malformed HEX (too short) is rejected."""
        with pytest.raises(ValueError, match="Invalid HEX color format"):
            CharacterColorPalette(
                character_id="test",
                hair="#FF99",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )

    def test_malformed_hex_missing_hash(self) -> None:
        """Test malformed HEX (missing #) is rejected."""
        with pytest.raises(ValueError, match="Invalid HEX color format"):
            CharacterColorPalette(
                character_id="test",
                hair="FF9900",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )

    def test_malformed_hex_double_hash(self) -> None:
        """Test malformed HEX (double #) is rejected."""
        with pytest.raises(ValueError, match="Invalid HEX color format"):
            CharacterColorPalette(
                character_id="test",
                hair="##FF9900",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )

    def test_malformed_hex_invalid_chars(self) -> None:
        """Test malformed HEX with invalid characters is rejected."""
        with pytest.raises(ValueError, match="Invalid HEX color format"):
            CharacterColorPalette(
                character_id="test",
                hair="#GGGGGG",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )

    def test_malformed_hex_wrong_length(self) -> None:
        """Test malformed HEX (wrong length) is rejected."""
        with pytest.raises(ValueError, match="Invalid HEX color format"):
            CharacterColorPalette(
                character_id="test",
                hair="#12345",
                skin="#FFCC99",
                eyes="#4477EE",
                outfit="#FFCC00",
            )


class TestNormalization:
    """Tests for color normalization."""

    def test_canonical_hex_output(self) -> None:
        """Test canonical uppercase HEX output."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#aabbcc",
            skin="#DDEEFF",
            eyes="#123456",
            outfit="#ABCDEF",
        )
        # All should be normalized to uppercase
        assert palette.hair == "#AABBCC"
        assert palette.skin == "#DDEEFF"
        assert palette.eyes == "#123456"
        assert palette.outfit == "#ABCDEF"

    def test_deterministic_normalization(self) -> None:
        """Test normalization is deterministic."""
        def create_palette():
            return CharacterColorPalette(
                character_id="test",
                hair="#ff9900",
                skin="#ffcc99",
                eyes="#4477ee",
                outfit="#ffcc00",
            )

        p1 = create_palette()
        p2 = create_palette()

        assert p1.hair == p2.hair
        assert p1.skin == p2.skin
        assert p1.eyes == p2.eyes
        assert p1.outfit == p2.outfit


class TestImmutability:
    """Tests for palette immutability."""

    def test_direct_mutation_rejected(self) -> None:
        """Test direct field mutation is rejected."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )

        with pytest.raises(Exception) as exc_info:
            palette.hair = "#00FF00"
        assert "frozen" in str(exc_info.value).lower()

    def test_custom_colors_attribute_reassignment_rejected(self) -> None:
        """Test reassigning custom_colors attribute is rejected."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )

        # Reassigning the custom_colors attribute should fail
        with pytest.raises(Exception) as exc_info:
            palette.custom_colors = [("new_key", "#FFFFFF")]
        assert "frozen" in str(exc_info.value).lower()

    def test_custom_colors_is_tuple(self) -> None:
        """Test that custom_colors is stored as tuple."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            custom_colors={"cape": "#FF0000"},
        )
        assert isinstance(palette.custom_colors, tuple)

    def test_custom_colors_cannot_append(self) -> None:
        """Test that custom_colors tuple cannot be appended to."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            custom_colors={"cape": "#FF0000"},
        )
        with pytest.raises(AttributeError):
            palette.custom_colors.append(("sword", "#AAAAAA"))

    def test_custom_colors_nested_mutation_protected(self) -> None:
        """Test that nested tuples cannot be modified."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            custom_colors={"cape": "#FF0000"},
        )
        # Get the first tuple
        first_entry = palette.custom_colors[0]
        # Try to modify it (tuples are immutable)
        with pytest.raises(TypeError):
            first_entry[0] = "new_key"

    def test_source_dict_modification_does_not_affect_palette(self) -> None:
        """Test that modifying source dict doesn't affect palette."""
        source_dict = {"cape": "#FF0000"}
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            custom_colors=source_dict,
        )

        # Modify source
        source_dict["sword"] = "#AAAAAA"

        # Palette should be unaffected
        assert len(palette.custom_colors) == 1

    def test_deterministic_ordering(self) -> None:
        """Test that custom_colors is always sorted for determinism."""
        # Pass in reverse order
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            custom_colors={"zulu": "#111111", "alpha": "#AAAAAA"},
        )

        # Should be sorted alphabetically
        assert palette.custom_colors[0][0] == "alpha"
        assert palette.custom_colors[1][0] == "zulu"


class TestSerialization:
    """Tests for palette serialization."""

    def test_model_dump(self) -> None:
        """Test model_dump serialization."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
        data = palette.model_dump()

        assert data["character_id"] == "test"
        assert data["hair"] == "#FF9900"
        assert data["skin"] == "#FFCC99"
        assert data["eyes"] == "#4477EE"
        assert data["outfit"] == "#FFCC00"
        assert data["accessories"] is None
        # custom_colors is now a tuple
        assert data["custom_colors"] == ()

    def test_model_dump_json(self) -> None:
        """Test model_dump_json serialization."""
        palette = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
        json_str = palette.model_dump_json()

        assert '"character_id":"test"' in json_str
        assert '"hair":"#FF9900"' in json_str

    def test_round_trip_reconstruction(self) -> None:
        """Test round-trip reconstruction."""
        original = CharacterColorPalette(
            character_id="test",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
            accessories="#333333",
            custom_colors={"cape": "#FF0000"},
        )

        data = original.model_dump()
        reconstructed = CharacterColorPalette(**data)

        assert reconstructed == original
        assert reconstructed.character_id == original.character_id
        assert reconstructed.hair == original.hair


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self) -> None:
        """Test same input produces same output."""
        params = {
            "character_id": "test",
            "hair": "#FF9900",
            "skin": "#FFCC99",
            "eyes": "#4477EE",
            "outfit": "#FFCC00",
        }

        p1 = CharacterColorPalette(**params)
        p2 = CharacterColorPalette(**params)

        assert p1 == p2
        assert p1.model_dump() == p2.model_dump()

    def test_different_inputs_different_outputs(self) -> None:
        """Test different inputs produce different outputs."""
        p1 = CharacterColorPalette(
            character_id="char1",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )
        p2 = CharacterColorPalette(
            character_id="char2",
            hair="#FF9900",
            skin="#FFCC99",
            eyes="#4477EE",
            outfit="#FFCC00",
        )

        assert p1 != p2
        assert p1.character_id != p2.character_id


class TestDependencyRules:
    """Tests for dependency boundary verification."""

    def test_no_forbidden_imports(self) -> None:
        """Verify palette has no forbidden imports."""
        import tools.frame.palette
        source = tools.frame.palette.__file__
        with open(source) as f:
            content = f.read()

        forbidden = [
            "torch", "tensorflow", "cv2", "PIL", "opencv",
            "requests", "httpx", "socket", "ffmpeg", "moviepy",
            "diffusers", "transformers", "stable", "controlnet"
        ]
        for item in forbidden:
            assert item not in content, f"Forbidden import found: {item}"
