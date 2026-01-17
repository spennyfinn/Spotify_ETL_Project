
import pytest
from src.validate.audio_features_validator import AudioFeaturesData
import numpy as np

from tests.unit.constants import  INVALID_0_1_RANGE_VALUES, INVALID_0_1_RANGE_VALUES_IDS, INVALID_ID_IDS, INVALID_IDS, INVALID_SPECTRAL_CENTROID_VALUES, INVALID_SPECTRAL_CENTROID_VALUES_IDS, INVALID_URL_VALUES, INVALID_URL_VALUES_IDS, VALID_0_1_RANGE_VALUES, VALID_0_1_RANGE_VALUES_IDS, VALID_AUDIO_FEATURE_FLOATS, VALID_AUDIO_FEATURE_FLOATS_IDS, VALID_ID_VALUES, VALID_ID_VALUES_IDS, VALID_SPECTRAL_CENTROID_VALUES, VALID_SPECTRAL_CENTROID_VALUES_IDS, VALID_URL_VALUES, VALID_URL_VALUES_IDS, WRONG_FLOAT_TYPE, WRONG_FLOAT_TYPE_IDS, WRONG_STRING_TYPE, WRONG_STRING_TYPE_IDS

class TestAudioFeaturesData():
    # SONG_ID
    @pytest.mark.parametrize('value',VALID_ID_VALUES, ids=VALID_ID_VALUES_IDS)
    def test_valid_song_id(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['song_id'] = value
        validated_data = AudioFeaturesData(**test_data)
        assert validated_data.song_id == value

    @pytest.mark.parametrize('value', INVALID_IDS, ids=INVALID_ID_IDS)
    def test_invalid_song_id(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['song_id'] = value
        with pytest.raises(ValueError, match='song_id'):
            AudioFeaturesData(**test_data)

    @pytest.mark.parametrize('value',WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_song_id(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['song_id'] = value
        with pytest.raises(TypeError, match='song_id'):
            AudioFeaturesData(**test_data)

    # BPM
    @pytest.mark.parametrize('bpm,energy,zcr,danceability', VALID_AUDIO_FEATURE_FLOATS, ids= VALID_AUDIO_FEATURE_FLOATS_IDS)
    def test_valid_bpm(self, valid_audio_features, bpm, energy, zcr, danceability):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = bpm
        test_data['energy'] = energy
        test_data['zero_crossing_rate'] = zcr
        test_data['danceability'] = danceability
        validated_data = AudioFeaturesData(**test_data)
        assert validated_data.bpm == bpm

    @pytest.mark.parametrize('bpm,energy,zcr,danceability', [(-.01, .5, .3, .385),
        (np.nan, .5, .3, .385),
        (np.inf, .5, .3, .385),
        (-100.0, .8, .3, .61),
        (300.1, .6, .77, .754),
        (1001.0, .99, 1.0, .995)])
    def test_invalid_bpm(self, valid_audio_features, bpm, energy, zcr, danceability):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = bpm
        test_data['energy'] = energy
        test_data['zero_crossing_rate'] = zcr
        test_data['danceability'] = danceability
        with pytest.raises(ValueError, match='bpm'):
            AudioFeaturesData(**test_data)

    @pytest.mark.parametrize('value', WRONG_FLOAT_TYPE, ids=WRONG_FLOAT_TYPE_IDS)
    def test_invalid_types_bpm(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = value
        with pytest.raises(TypeError, match='bpm'):
            AudioFeaturesData(**test_data)

    # ENERGY 
    @pytest.mark.parametrize('bpm,energy,zcr,danceability', VALID_AUDIO_FEATURE_FLOATS, ids= VALID_AUDIO_FEATURE_FLOATS_IDS)
    def test_valid_energy(self, valid_audio_features, bpm, energy, zcr, danceability):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = bpm
        test_data['energy'] = energy
        test_data['zero_crossing_rate'] = zcr
        test_data['danceability'] = danceability
        validated_data = AudioFeaturesData(**test_data)
        assert validated_data.energy == energy

    @pytest.mark.parametrize('bpm,energy,zcr,danceability', [(50.0, -.01, .3, .385),
        (50.0, np.nan, .3, .385),
        (50.0, np.inf, .3, .385),
        (50.0, 1.01, .3, .61),
        (50.0, 10.0, .77, .679),
        (50.0, -10.0, 1.0, .995) ])
    def test_invalid_energy(self, valid_audio_features, bpm, energy, zcr, danceability):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = bpm
        test_data['energy'] = energy
        test_data['zero_crossing_rate'] = zcr
        test_data['danceability'] = danceability
        with pytest.raises(ValueError, match='energy'):
            AudioFeaturesData(**test_data)

    @pytest.mark.parametrize('value', WRONG_FLOAT_TYPE, ids=WRONG_FLOAT_TYPE_IDS)
    def test_invalid_types_energy(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['energy'] = value
        with pytest.raises(TypeError, match='energy'):
            AudioFeaturesData(**test_data)

    # SPECTRAL_CENTROID
    @pytest.mark.parametrize('value', VALID_SPECTRAL_CENTROID_VALUES, ids=VALID_SPECTRAL_CENTROID_VALUES_IDS)
    def test_valid_spectral_centroid(self, valid_audio_features, value):
        test_data=valid_audio_features.copy()
        test_data['spectral_centroid']= value
        validated_data = AudioFeaturesData(**test_data)
        assert validated_data.spectral_centroid==value
        
    @pytest.mark.parametrize('value', INVALID_SPECTRAL_CENTROID_VALUES, ids=INVALID_SPECTRAL_CENTROID_VALUES_IDS)
    def test_invalid_spectral_centroid(self, valid_audio_features, value):
        test_data=valid_audio_features.copy()
        test_data['spectral_centroid']= value
        with pytest.raises(ValueError, match='spectral_centroid'):
            AudioFeaturesData(**test_data)
       
    
    @pytest.mark.parametrize('value', WRONG_FLOAT_TYPE, ids=WRONG_FLOAT_TYPE_IDS)
    def test_invalid_types_spectral_centroid(self, valid_audio_features, value):
        test_data=valid_audio_features.copy()
        test_data['spectral_centroid']=value
        with pytest.raises(TypeError, match='spectral_centroid'):
            AudioFeaturesData(**test_data)
        

    # ZERO_CROSSING_RATE 
    @pytest.mark.parametrize('bpm,energy,zcr,danceability', VALID_AUDIO_FEATURE_FLOATS, ids= VALID_AUDIO_FEATURE_FLOATS_IDS)
    def test_valid_zero_crossing_rate(self, valid_audio_features, bpm, energy, zcr, danceability):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = bpm
        test_data['energy'] = energy
        test_data['zero_crossing_rate'] = zcr
        test_data['danceability'] = danceability
        validated_data = AudioFeaturesData(**test_data)
        assert validated_data.zero_crossing_rate == zcr

    @pytest.mark.parametrize('bpm,energy,zcr,danceability', [
        (50.0, .5, -.01, .385),
        (50.0, .5, np.inf, .385),
        (50.0, .5, np.nan, .385),
        (50.0, .5, 1.01, .61),
        (50.0, .5, 10.0, .679),
        (50.0, .5, -10.0, .995)
    ])
    def test_invalid_zero_crossing_rate(self, valid_audio_features, bpm, energy, zcr, danceability):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = bpm
        test_data['energy'] = energy
        test_data['zero_crossing_rate'] = zcr
        test_data['danceability'] = danceability
        with pytest.raises(ValueError, match='zero_crossing_rate'):
            AudioFeaturesData(**test_data)

    @pytest.mark.parametrize('value', WRONG_FLOAT_TYPE, ids=WRONG_FLOAT_TYPE_IDS)
    def test_invalid_types_zero_crossing_rate(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['zero_crossing_rate'] = value
        with pytest.raises(TypeError, match='zero_crossing_rate'):
            AudioFeaturesData(**test_data)

    # DANCEABILITY 
    @pytest.mark.parametrize('bpm,energy,zcr,danceability', VALID_AUDIO_FEATURE_FLOATS, ids= VALID_AUDIO_FEATURE_FLOATS_IDS)
    def test_valid_danceability(self, valid_audio_features, bpm, energy, zcr, danceability):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = bpm
        test_data['energy'] = energy
        test_data['zero_crossing_rate'] = zcr
        test_data['danceability'] = danceability
        validated_data = AudioFeaturesData(**test_data)
        assert validated_data.danceability == danceability

    @pytest.mark.parametrize('bpm,energy,zcr,danceability', [
        (50.0, .5, .3, -.01),
        (50.0, .5, .3, np.nan),
        (50.0, .5, .3, np.inf),
        (50.0, .5, .3, 1.01),
        (50.0, .5, .3, 10.0),
        (50.0, .5, .3, -10.0)
    ])
    def test_invalid_danceability(self, valid_audio_features, bpm, energy, zcr, danceability):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = bpm
        test_data['energy'] = energy
        test_data['zero_crossing_rate'] = zcr
        test_data['danceability'] = danceability
        with pytest.raises(ValueError, match='danceability'):
            AudioFeaturesData(**test_data)

    @pytest.mark.parametrize('value', WRONG_FLOAT_TYPE, ids=WRONG_FLOAT_TYPE_IDS)
    def test_invalid_types_danceability(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['danceability'] = value
        with pytest.raises(TypeError, match='danceability'):
            AudioFeaturesData(**test_data)

    # PREVIEW_URL
    @pytest.mark.parametrize('value', VALID_URL_VALUES, ids=VALID_URL_VALUES_IDS)
    def test_valid_preview_url(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['preview_url'] = value
        validated_data = AudioFeaturesData(**test_data)
        assert validated_data.preview_url == value.strip()

    @pytest.mark.parametrize('value', INVALID_URL_VALUES, ids=INVALID_URL_VALUES_IDS)
    def test_invalid_preview_url(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['preview_url'] = value
        with pytest.raises(ValueError, match='preview_url'):
            AudioFeaturesData(**test_data)
            

    @pytest.mark.parametrize('value', WRONG_STRING_TYPE, ids=WRONG_STRING_TYPE_IDS)
    def test_invalid_types_preview_url(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['preview_url'] = value
        with pytest.raises(TypeError, match='preview_url'):
            AudioFeaturesData(**test_data)

    # HARMONIC_RATIO 
    @pytest.mark.parametrize('value', VALID_0_1_RANGE_VALUES, ids=VALID_0_1_RANGE_VALUES_IDS)
    def test_valid_harmonic_ratio(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['harmonic_ratio'] = value
        validated_data = AudioFeaturesData(**test_data)
        assert validated_data.harmonic_ratio == value


    @pytest.mark.parametrize('value',INVALID_0_1_RANGE_VALUES, ids=INVALID_0_1_RANGE_VALUES_IDS )
    def test_invalid_harmonic_ratio(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['harmonic_ratio'] = value
        with pytest.raises(ValueError, match='harmonic_ratio'):
            AudioFeaturesData(**test_data)

    @pytest.mark.parametrize('value', WRONG_FLOAT_TYPE, ids=WRONG_FLOAT_TYPE_IDS)
    def test_invalid_types_harmonic_ratio(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['harmonic_ratio'] = value
        with pytest.raises(TypeError, match='harmonic_ratio'):
            AudioFeaturesData(**test_data)


    # PERCUSSIVE_RATIO
    @pytest.mark.parametrize('value',VALID_0_1_RANGE_VALUES, ids=VALID_0_1_RANGE_VALUES_IDS)
    def test_valid_percussive_ratio(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['percussive_ratio'] = value
        validated_data = AudioFeaturesData(**test_data)
        assert validated_data.percussive_ratio == value

    @pytest.mark.parametrize('value', INVALID_0_1_RANGE_VALUES, ids=INVALID_0_1_RANGE_VALUES_IDS)
    def test_invalid_percussive_ratio(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['percussive_ratio'] = value
        with pytest.raises(ValueError, match='percussive_ratio'):
            AudioFeaturesData(**test_data)

    @pytest.mark.parametrize('value', WRONG_FLOAT_TYPE, ids=WRONG_FLOAT_TYPE_IDS)
    def test_invalid_types_percussive_ratio(self, valid_audio_features, value):
        test_data = valid_audio_features.copy()
        test_data['percussive_ratio'] = value
        with pytest.raises(TypeError, match='percussive_ratio'):
            AudioFeaturesData(**test_data)

    def test_danceability_calculated_value(self, valid_audio_features):
        test_data = valid_audio_features.copy()
        test_data['bpm'] = 100.0
        test_data['energy'] = .8
        test_data['zero_crossing_rate'] = .3
        test_data['danceability'] = .61

        AudioFeaturesData(**test_data)
        test_data['danceability'] = .99

        with pytest.raises(ValueError, match='calculation mismatch'):
            AudioFeaturesData(**test_data)