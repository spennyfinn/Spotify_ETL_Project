"""Unit tests for text_processing_utils (normalization, collaborators, similarity)."""

import pytest
from hypothesis import given, settings
import hypothesis.strategies as st

from src.utils.text_processing_utils import (
    extract_collaborators,
    has_collaborators,
    normalize_song_name,
    similarity_score,
)
from tests.unit.constants import (
    EXTRACT_COLLABORATORS_VALUES,
    EXTRACT_COLLABORATORS_VALUES_IDS,
    HAS_COLLABORATORS_TEST_CASES,
    NORMALIZE_SONG_NAME_VALUES,
    NORMALIZE_SONG_NAME_VALUES_IDS,
    SIMILARITY_SCORE_VALUES,
    SIMILARITY_SCORE_VALUES_IDS,
    WRONG_STRING_PAIRS,
    WRONG_STRING_PAIRS_IDS,
    WRONG_STRING_TYPE,
    WRONG_STRING_TYPE_IDS,
)


class TestTextUtils:
    @pytest.mark.parametrize(
        "input, output", NORMALIZE_SONG_NAME_VALUES, ids=NORMALIZE_SONG_NAME_VALUES_IDS
    )
    def test_normalize_valid_song_name(self, input, output):
        """Table-driven cases: ft/feat stripping, & → and, remix tags, unicode."""
        normalized_song = normalize_song_name(input)
        assert normalized_song == output.strip().lower()

    @pytest.mark.parametrize("type", WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_normalize_wrong_types_song_name(self, type):
        """Non-string inputs raise TypeError for normalize_song_name."""
        with pytest.raises(TypeError, match="string"):
            normalize_song_name(type)

    @given(st.text(min_size=0, max_size=1000))
    def test_normalize_song_name_properties(self, text):
        """Property test: output is lowercase trimmed string without & or feat markers."""
        result = normalize_song_name(text)

        assert type(result) == str
        assert result == result.lower()
        assert not result.endswith("  ")
        assert not result.startswith("  ")
        assert "&" not in result
        assert "feat." or "feat." not in result

    @pytest.mark.parametrize(
        "input, expected_output",
        HAS_COLLABORATORS_TEST_CASES,
        ids=[f"Input:{i} Output:{str(o)}" for i, o in HAS_COLLABORATORS_TEST_CASES],
    )
    def test_has_valid_collaborators(self, input, expected_output):
        """Detects +, feat, ft., featuring patterns in song titles."""
        has_collab = has_collaborators(input)
        assert has_collab == expected_output

    @pytest.mark.parametrize("type", WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_has_collaborators_wrong_types(self, type):
        """Non-string inputs raise TypeError (via normalize path in implementation)."""
        with pytest.raises(TypeError, match="string"):
            normalize_song_name(type)

    @given(st.text(min_size=0, max_size=1000))
    def test_has_collaborators_properties(self, text):
        """If collaborator markers appear in text, has_collaborators is True; case invariant."""
        text = text.lower()
        result = has_collaborators(text)

        patterns = ["+", "feat", "ft.", "featuring"]
        has_pattern = any([pattern in text for pattern in patterns])
        if has_pattern:
            assert result is True

        assert result == has_collaborators(text.upper())
        assert result == has_collaborators(text.lower())

    @pytest.mark.parametrize(
        "input, output", EXTRACT_COLLABORATORS_VALUES, ids=EXTRACT_COLLABORATORS_VALUES_IDS
    )
    def test_extract_collaborators_valid_types(self, input, output):
        """Parses collaborator names from ft/feat/+ syntax into a list."""
        collaborators = extract_collaborators(input)
        assert collaborators == output

    @pytest.mark.parametrize("type", WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_extract_collaborators_wrong_types(self, type):
        """Non-string inputs raise TypeError for extract_collaborators."""
        with pytest.raises(TypeError, match="string"):
            extract_collaborators(type)

    @pytest.mark.parametrize(
        "value1, value2, output", SIMILARITY_SCORE_VALUES, ids=SIMILARITY_SCORE_VALUES_IDS
    )
    def test_similarity_score(self, value1, value2, output):
        """Fuzzy match scores for exact, empty, case, partial, and no match."""
        data = similarity_score(value1, value2)
        assert round(data, 2) == output

    @pytest.mark.parametrize("value1, value2", WRONG_STRING_PAIRS, ids=WRONG_STRING_PAIRS_IDS)
    def test_similarity_score_wrong_types(self, value1, value2):
        """Non-string pairs raise TypeError for similarity_score."""
        with pytest.raises(TypeError, match="string"):
            similarity_score(value1, value2)

    @given(st.text(min_size=0, max_size=200), st.text(min_size=0, max_size=200))
    def test_similarity_score_properties(self, text1, text2):
        """Property test: score in [0,1], symmetric, self-match is 1.0."""
        text1 = text1.lower()
        text2 = text2.lower()
        result = similarity_score(text1, text2)

        assert type(result) == float
        assert 0.0 <= result and result <= 1.0

        assert result == similarity_score(text2, text1)
        assert similarity_score(text1, text1) == 1.0
        assert similarity_score(text2, text2) == 1.0

        assert similarity_score(text1.lower(), text2.lower()) == result
