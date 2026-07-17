"""Audio feature extractor for the Snowflake ELT pipeline.

Finds a Spotify 30-second preview URL for each song, downloads the clip, and
extracts signal features with Librosa (BPM, energy, spectral centroid, zero
crossing rate, harmonic/percussive ratios). Output is a payload dict suitable
for ``load_raw_records(table='raw_audio_features', ...)``.

Requires ``SPOTIFY_CLIENT_ID`` and ``SPOTIFY_CLIENT_SECRET`` in ``.env`` for
preview URL lookup via ``spotify_preview_finder``.
"""

import gc
import logging
import os
from io import BytesIO
from typing import Dict
import uuid

import librosa
import numpy as np
import requests
from dotenv import load_dotenv
from spotify_preview_finder import finder


from src.load.snowflake_loader import load_raw_records
from src.utils.http_utils import safe_requests
from src.utils.snowflake_utils import fetch_all, snowflake_connection

load_dotenv()

logger = logging.getLogger(__name__)

MIN_PREVIEW_BYTES = 10_000


def _get_preview_url(song_name: str, artist_name: str) -> str | None:
    """Look up a Spotify preview URL for a song.

    Args:
        song_name: Track title from staging.
        artist_name: Artist name from staging.

    Returns:
        Preview URL string, or None if no preview is available.
    """
    search_query = f"{song_name} {artist_name}"[:250]
    result = finder.search_and_get_links(
        song_name=search_query,
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        limit=1,
    )

    if not result["results"]:
        logger.warning("No preview URL found for %s by %s", song_name, artist_name)
        return None

    preview_url = result["results"][0]["previewUrl"]
    if result["success"] is not True or not preview_url:
        logger.warning("Preview URL not available for %s by %s", song_name, artist_name)
        return None

    return preview_url


def _load_preview_audio(preview_url: str, song_name: str) -> tuple[np.ndarray, int] | None:
    """Download a preview clip and decode it into a Librosa waveform.

    Args:
        preview_url: Spotify-hosted MP3 preview URL.
        song_name: Used for logging only.

    Returns:
        Tuple of (waveform array, sample rate), or None on failure.
    """
    try:
        resp = safe_requests("GET", preview_url, timeout=5)
    except requests.ConnectionError as e:
        logger.error("Connection error when fetching %s: %s", song_name, e)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("API error for %s: %s", song_name, e)
        return None

    if not resp:
        return None

    if len(resp.content) >= MIN_PREVIEW_BYTES:
        audio_data = BytesIO(resp.content)
    try:
        y, sr = librosa.load(audio_data)
    except Exception as e:
        logger.error("Audio feature extraction failed for %s: %s", song_name, e)
        return None

    if len(y) == 0 or sr == 0:
        logger.warning("Invalid audio data for %s", song_name)
        return None

    return y, sr


def _extract_bpm(y: np.ndarray, sr: int, song_name: str) -> float | None:
    """Estimate tempo in beats per minute."""
    try:
        bpm, _beats = librosa.beat.beat_track(y=y, sr=sr)
        if isinstance(bpm, float):
            bpm = [bpm]
        logger.debug("Extracted BPM: %s", bpm)
        return float(bpm[0])
    except Exception as e:
        logger.error("BPM extraction failed for %s: %s", song_name, e)
        return None


def _extract_energy(y: np.ndarray, song_name: str) -> float | None:
    """Compute mean RMS energy (loudness proxy)."""
    try:
        rms = librosa.feature.rms(y=y)[0]
        energy = float(np.mean(rms))
        logger.debug("Extracted energy: %s", energy)
        return energy
    except Exception as e:
        logger.error("Energy extraction failed for %s: %s", song_name, e)
        return None


def _extract_spectral_centroid(y: np.ndarray, sr: int, song_name: str) -> float | None:
    """Compute mean spectral centroid (brightness proxy)."""
    try:
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_mean = float(np.mean(spectral_centroid))
        logger.debug("Extracted spectral centroid (brightness): %s", centroid_mean)
        return centroid_mean
    except Exception as e:
        logger.error("Spectral centroid extraction failed for %s: %s", song_name, e)
        return None


def _extract_zero_crossing_rate(y: np.ndarray, song_name: str) -> float | None:
    """Compute mean zero crossing rate (noisiness / percussiveness proxy)."""
    try:
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean = float(np.mean(zcr))
        logger.debug("Extracted ZCR (percussiveness): %s", zcr_mean)
        return zcr_mean
    except Exception as e:
        logger.error("ZCR extraction failed for %s: %s", song_name, e)
        return None


def _extract_harmonic_percussive_ratios(
    y: np.ndarray, song_name: str
) -> tuple[float, float] | None:
    """Split the waveform into harmonic/percussive components and ratio each."""
    try:
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        harmonic_raw = sum(abs(y_harmonic))
        percussive_raw = sum(abs(y_percussive))
        total = harmonic_raw + percussive_raw

        if total <= 0:
            logger.warning("Invalid harmonic/percussive ratio calculation for %s", song_name)
            return None

        harmonic_ratio = sum(abs(y_harmonic)) / total
        percussive_ratio = sum(abs(y_percussive)) / total
        logger.debug("Extracted harmonic ratio: %s", harmonic_ratio)
        logger.debug("Extracted percussive ratio: %s", percussive_ratio)
        return float(harmonic_ratio), float(percussive_ratio)
    except Exception as e:
        logger.error("Harmonic/percussive ratio extraction failed for %s: %s", song_name, e)
        return None


def _build_feature_record(
    song_id: str,
    preview_url: str,
    bpm: float,
    energy: float,
    spectral_centroid: float,
    zero_crossing_rate: float,
    harmonic_ratio: float,
    percussive_ratio: float,
) -> dict:
    """Assemble a payload dict for ``load_raw_records``."""
    return {
        "song_id": str(song_id),
        "bpm": bpm,
        "energy": energy,
        "spectral_centroid": spectral_centroid,
        "zero_crossing_rate": zero_crossing_rate,
        "preview_url": preview_url,
        "harmonic_ratio": harmonic_ratio,
        "percussive_ratio": percussive_ratio,
        "source": "Librosa",
    }


def get_audio_features(song_name, artist_name, song_id) -> Dict | None:
    """Extract Librosa audio features for one song via its Spotify preview.

    Orchestrates preview lookup, download, feature extraction, and payload
    assembly. Returns None when any step fails.

    Args:
        song_name: Track title from staging.
        artist_name: Artist name from staging.
        song_id: Spotify track ID.

    Returns:
        Feature payload dict, or None on failure.
    """
    try:
        logger.debug("Processing song ID: %s", song_id)

        preview_url = _get_preview_url(song_name, artist_name)
        if not preview_url:
            return None

        loaded = _load_preview_audio(preview_url, song_name)
        if not loaded:
            return None
        y, sr = loaded

        bpm = _extract_bpm(y, sr, song_name)
        if bpm is None:
            return None

        energy = _extract_energy(y, song_name)
        if energy is None:
            return None

        spectral_centroid = _extract_spectral_centroid(y, sr, song_name)
        if spectral_centroid is None:
            return None

        zero_crossing_rate = _extract_zero_crossing_rate(y, song_name)
        if zero_crossing_rate is None:
            return None

        ratios = _extract_harmonic_percussive_ratios(y, song_name)
        if ratios is None:
            return None
        harmonic_ratio, percussive_ratio = ratios

        data = _build_feature_record(
            song_id,
            preview_url,
            bpm,
            energy,
            spectral_centroid,
            zero_crossing_rate,
            harmonic_ratio,
            percussive_ratio,
        )
        del y
        gc.collect()
        return data
    except Exception as e:
        gc.collect()
        logger.error("Audio feature retrieval failed for %s: %s", song_name, e)
        return None

def main(batch_size: int, run_id : str):
    """Backfill Librosa audio features for Spotify tracks missing from staging.

    Queries STAGING (not RAW) for songs in ``stg_spotify__tracks`` with no row
    in ``stg_audio__features``, downloads each Spotify preview clip, extracts
    signal features, and loads successful results into ``raw_audio_features``.

    Prerequisites:
        - Run ``dbt run --select stg_spotify__tracks`` so staging is current.
        - Set ``SPOTIFY_CLIENT_ID`` and ``SPOTIFY_CLIENT_SECRET`` in ``.env``.

    After loading, run ``dbt build --select stg_audio__features+`` to refresh
    staging and downstream marts.

    Args:
        batch_size: Number of songs to process per Snowflake load batch.
        run_id: Run identifier for the RAW load; generated if omitted.
    """
    logger.info("Starting Audio Feature Extraction")

    SPOTIFY_CLIENT = os.getenv("SPOTIFY_CLIENT_ID")
    SPOTIFY_ID = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not SPOTIFY_CLIENT:
        raise RuntimeError("Missing SPOTIFY_CLIENT in .env file")
    
    if not SPOTIFY_ID:
        raise RuntimeError("Missing SPOTIFY_ID in .env file")

    #get the songs_and artists get_songs_and_artists function
    SONGS_NEEDING_AUDIO_FEATURES_QUERY = """
        SELECT 
            t.song_name, 
            t.artist_name, 
            t.song_id
        FROM MUSICDB.STAGING.stg_spotify__tracks AS t
        LEFT JOIN MUSICDB.STAGING.stg_audio__features AS a
            ON a.song_id = t.song_id
        WHERE a.song_id IS NULL
            AND t.song_id IS NOT NULL
            AND t.artist_name IS NOT NULL
            AND t.song_name IS NOT NULL
        ORDER BY t._loaded_at DESC
        LIMIT 50000
    """
    rows = fetch_all(SONGS_NEEDING_AUDIO_FEATURES_QUERY)

    if not rows:
        logger.error("There are no songs returned from the database that need audio feature enhancement")
        return

    logger.info(f"Starting audio feature extraction for {len(rows)} songs")

    run_id = run_id or str(uuid.uuid4())

    for i in range(0, len(rows), batch_size):
        pending_batch = []
        stop = batch_size+i if (batch_size+i)<= len(rows) else len(rows)
        chunk = rows[i: stop]

        for song_name, artist_name, song_id in chunk:
            if not song_name:
                logger.warning("Song name is missing")
                continue

            if not artist_name:
                logger.warning("Artist name is missing")
                continue

            if not song_id:
                logger.warning("Song id is missing")
                continue

            audio_data = get_audio_features(song_name, artist_name, song_id)

            if not audio_data:
                logger.warning(f"There was no audio feature data for {song_name} by {artist_name}")
                continue

            pending_batch.append(audio_data)

        if not pending_batch:
            logger.warning("Batched data was empty, moving onto the next batch")
            continue

        with snowflake_connection() as conn:
            n_rows, error_count = load_raw_records(
                table="raw_audio_features",
                records=pending_batch,
                id_columns="song_id",
                run_id=run_id,
                conn=conn,
            )

        logger.info(f'This batch successfully inserted {n_rows} rows into the Raw Audio Features Table')
        logger.info(f'There were {error_count} errenous rows in this batch')
                

        
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    run_id = str(uuid.uuid4())
    main(batch_size=10, run_id= run_id)




       


        


