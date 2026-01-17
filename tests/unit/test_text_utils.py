import pytest
from src.utils.text_processing_utils import extract_collaborators, has_collaborators, normalize_song_name, similarity_score
import hypothesis.strategies as st
from hypothesis import given, settings
from tests.unit.constants import  NORMALIZE_SONG_NAME_VALUES, NORMALIZE_SONG_NAME_VALUES_IDS, SIMILARITY_SCORE_VALUES, SIMILARITY_SCORE_VALUES_IDS, WRONG_STRING_PAIRS_IDS, WRONG_STRING_PAIRS,EXTRACT_COLLABORATORS_VALUES, EXTRACT_COLLABORATORS_VALUES_IDS, HAS_COLLABORATORS_TEST_CASES, WRONG_STRING_TYPE, WRONG_STRING_TYPE_IDS


class TestTextUtils:

    @pytest.mark.parametrize('input, output', NORMALIZE_SONG_NAME_VALUES, ids=NORMALIZE_SONG_NAME_VALUES_IDS )
    def test_normalize_valid_song_name(self, input, output):
        normalized_song=normalize_song_name(input)
        assert normalized_song==output.strip().lower()
    
    
    @pytest.mark.parametrize('type', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_normalize_wrong_types_song_name(self, type):
        with pytest.raises(TypeError, match='string'):
            normalize_song_name(type)

    
        
    @given(st.text(min_size=0, max_size=1000))
    def test_normalize_song_name_properties(self, text):
        result = normalize_song_name(text)

        assert type(result)==str
        assert result == result.lower()
        assert not result.endswith('  ')
        assert not result.startswith('  ')
        assert '&' not in result
        assert "feat." or 'feat.' not in result

    
    @pytest.mark.parametrize('input, expected_output',HAS_COLLABORATORS_TEST_CASES, ids=[f'Input:{i} Output:{str(o)}' for i,o in HAS_COLLABORATORS_TEST_CASES] )
    def test_has_valid_collaborators(self, input, expected_output):
        has_collab= has_collaborators(input)
        assert has_collab==expected_output

    @pytest.mark.parametrize('type', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_has_collaborators_wrong_types(self, type):
        with pytest.raises(TypeError, match='string'):
            normalize_song_name(type)

    @given(st.text(min_size=0, max_size=1000))
    def test_has_collaborators_properties(self, text):
        text=text.lower()
        result = has_collaborators(text)

        patterns = ['+', 'feat', 'ft.', 'featuring']
        has_pattern = any([pattern in text for pattern in patterns])
        if has_pattern:
            assert result ==True

        assert result == has_collaborators(text.upper())
        assert result == has_collaborators(text.lower())
        

    @pytest.mark.parametrize('input, output', EXTRACT_COLLABORATORS_VALUES, ids=EXTRACT_COLLABORATORS_VALUES_IDS)
    def test_extract_collaborators_valid_types(self, input, output):
        collaborators= extract_collaborators(input)
        assert collaborators==output


    @pytest.mark.parametrize('type', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_extract_collaborators_wrong_types(self, type):
        with pytest.raises(TypeError, match='string'):
            extract_collaborators(type)

    


    @pytest.mark.parametrize('value1, value2, output', SIMILARITY_SCORE_VALUES, ids=SIMILARITY_SCORE_VALUES_IDS )
    def test_similarity_score(self, value1, value2, output):
        data= similarity_score(value1, value2)
        assert round(data,2)==output
        
    
    @pytest.mark.parametrize('value1, value2',WRONG_STRING_PAIRS, ids=WRONG_STRING_PAIRS_IDS )
    def test_similarity_score_wrong_types(self, value1, value2):
        with pytest.raises(TypeError, match='string'):
            similarity_score(value1,value2)


    @given(st.text(min_size=0, max_size=200),st.text(min_size=0, max_size=200))
    def test_extract_collaborators_properties(self, text1, text2):
        text1=text1.lower()
        text2=text2.lower()
        result = similarity_score(text1,text2)

        assert type(result)==float
        assert 0.0<=result and result<=1.0

        assert result == similarity_score(text2, text1)
        assert similarity_score(text1, text1)==1.0
        assert similarity_score(text2, text2)==1.0

        assert similarity_score(text1.lower(), text2.lower())==result


    


    


