"""Last.fm backfill extractor for the Snowflake ELT pipeline.

Finds Spotify tracks in STAGING that do not yet have Last.fm enrichment, calls
the Last.fm API to resolve listener counts and artist stats, and appends
results to ``RAW.raw_lastfm`` for dbt to promote into ``stg_lastfm``.

Pipeline position::

    stg_spotify__tracks  -->  Last.fm API  -->  raw_lastfm  -->  dbt (stg_lastfm+)

Prerequisites:
    - Run ``dbt run --select stg_spotify__tracks`` after loading Spotify seed data
      so STAGING reflects current RAW rows.
    - Set ``LAST_FM_KEY`` in ``.env``.

Usage::

    python -m src.extract.lastfm_extractor

After loading, run ``dbt build --select stg_lastfm+`` to refresh staging and marts.

Matching strategy:
    1. ``track.getInfo`` using Spotify song + artist names (primary).
    2. ``track.search`` with separate track/artist params (fallback).
    3. ``artist.getInfo`` to attach mbid, tour status, and artist-level stats.

Rows that fail similarity checks or return no API match are skipped (not loaded).
"""

import json
import logging
import os
import random
import time
import uuid

import requests
from dotenv import load_dotenv

from src.load.snowflake_loader import load_raw_records
from src.utils.snowflake_utils import fetch_all, snowflake_connection
from src.utils.text_processing_utils import normalize_song_name, similarity_score

LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"

logger = logging.getLogger(__name__)


def _lastfm_get(params: dict, key: str) -> dict | None:
    """Call the Last.fm API and return JSON, or None on error / not found."""
    try:
        resp = requests.get(
            LASTFM_API_URL,
            params={**params, "api_key": key, "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except json.JSONDecodeError as e:
        logger.error("JSON decode error from Last.fm: %s", e)
        return None
    except requests.exceptions.Timeout as e:
        logger.error("Last.fm timeout: %s", e)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Last.fm request error: %s", e)
        return None

    if data.get("error"):
        logger.debug("Last.fm API: %s", data.get("message"))
        return None
    return data


def _build_track_match(
    song_name: str,
    artist_name: str,
    song_id: str,
    artist_id: str,
    track_name: str,
    matched_artist_name: str,
    listeners: int,
) -> dict:
    """Build a normalized match dict ready for ``load_raw_records``."""
    return {
        "song_name": normalize_song_name(track_name).lower(),
        "artist_name": normalize_song_name(matched_artist_name).lower(),
        "listeners": listeners,
        "original_song_name": song_name,
        "original_artist_name": artist_name,
        "artist_id": artist_id,
        "song_id": song_id,
    }


def _is_valid_match(
    song_name_normalized: str,
    artist_name_normalized: str,
    track_name: str,
    matched_artist_name: str,
    listeners: int,
) -> bool:
    """Return True when a Last.fm candidate passes name and listener thresholds."""
    if not track_name or not matched_artist_name or listeners < 10:
        return False
    if normalize_song_name(matched_artist_name).lower() in ("unknown", "<unknown>", ""):
        return False

    song_score = similarity_score(song_name_normalized, normalize_song_name(track_name))
    artist_score = similarity_score(artist_name_normalized, normalize_song_name(matched_artist_name))
    if song_score < 0.8 or artist_score < 0.7:
        logger.debug(
            "Match rejected: %s by %s (song=%.2f, artist=%.2f)",
            track_name,
            matched_artist_name,
            song_score,
            artist_score,
        )
        return False
    return True


def _get_track_from_get_info(
    song_name: str,
    artist_name: str,
    song_id: str,
    artist_id: str,
    key: str,
    song_name_normalized: str,
    artist_name_normalized: str,
) -> dict | None:
    """Direct lookup when Spotify already provides artist + track names."""
    data = _lastfm_get(
        {"method": "track.getInfo", "track": song_name, "artist": artist_name},
        key,
    )
    if not data or "track" not in data:
        return None

    track = data["track"]
    listeners = int(track.get("listeners") or 0)
    track_name = track.get("name") or song_name

    artist_block = track.get("artist", {})
    if isinstance(artist_block, dict):
        matched_artist_name = artist_block.get("name") or artist_name
    else:
        matched_artist_name = artist_name

    if not _is_valid_match(
        song_name_normalized,
        artist_name_normalized,
        track_name,
        matched_artist_name,
        listeners,
    ):
        return None

    logger.info(
        "track.getInfo match: %s by %s (%s listeners)",
        track_name,
        matched_artist_name,
        listeners,
    )
    return _build_track_match(
        song_name, artist_name, song_id, artist_id, track_name, matched_artist_name, listeners
    )


def _get_track_from_search(
    song_name: str,
    artist_name: str,
    song_id: str,
    artist_id: str,
    key: str,
    song_name_normalized: str,
    artist_name_normalized: str,
) -> dict | None:
    """Fallback fuzzy search with separate track and artist params."""
    data = _lastfm_get(
        {
            "method": "track.search",
            "track": song_name_normalized,
            "artist": artist_name_normalized,
            "limit": 10,
        },
        key,
    )
    if not data:
        return None

    tracks = data.get("results", {}).get("trackmatches", {}).get("track", [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    if not tracks:
        logger.warning("No tracks found for %s by %s", song_name, artist_name)
        return None

    best_match = None
    best_score = 0.0

    for track in tracks:
        track_name = track.get("name") or ""
        matched_artist_name = track.get("artist") or ""
        listeners = int(track.get("listeners") or 0)

        if not _is_valid_match(
            song_name_normalized,
            artist_name_normalized,
            track_name,
            matched_artist_name,
            listeners,
        ):
            continue

        song_score = similarity_score(song_name_normalized, normalize_song_name(track_name))
        artist_score = similarity_score(
            artist_name_normalized, normalize_song_name(matched_artist_name)
        )
        total_score = (song_score * 0.5) + (artist_score * 0.5)

        if total_score > best_score:
            best_score = total_score
            best_match = _build_track_match(
                song_name,
                artist_name,
                song_id,
                artist_id,
                track_name,
                matched_artist_name,
                listeners,
            )
        elif total_score == best_score and best_match and listeners > best_match["listeners"]:
            best_match = _build_track_match(
                song_name,
                artist_name,
                song_id,
                artist_id,
                track_name,
                matched_artist_name,
                listeners,
            )

        time.sleep(random.uniform(0.5, 1))

    if best_match and best_score >= 0.75:
        logger.info(
            "track.search match: %s by %s (score: %.2f)",
            best_match["song_name"],
            best_match["artist_name"],
            best_score,
        )
        return best_match

    logger.warning("No strong matches found for %s by %s", song_name, artist_name)
    return None


def get_track_from_lastfm(
    song_name: str, artist_name: str, song_id: str, artist_id: str, key: str
) -> dict | None:
    """Resolve a Spotify song to Last.fm track listener counts.

    Tries ``track.getInfo`` first, then falls back to ``track.search`` if the
    direct lookup fails or does not pass similarity checks.

    Args:
        song_name: Track title from Spotify staging.
        artist_name: Primary artist name from Spotify staging.
        song_id: Spotify track ID.
        artist_id: Spotify artist ID.
        key: Last.fm API key.

    Returns:
        Match dict with listener count and original Spotify identifiers, or None.
    """
    song_name_normalized = normalize_song_name(song_name)
    artist_name_normalized = normalize_song_name(artist_name)

    match = _get_track_from_get_info(
        song_name,
        artist_name,
        song_id,
        artist_id,
        key,
        song_name_normalized,
        artist_name_normalized,
    )
    if match:
        return match

    return _get_track_from_search(
        song_name,
        artist_name,
        song_id,
        artist_id,
        key,
        song_name_normalized,
        artist_name_normalized,
    )




def match_artists_from_lastfm(track_data: dict, key: str) -> dict | None:
    """Enrich a track match with Last.fm artist-level stats.

    Calls ``artist.getInfo`` using the original Spotify artist name (not the
    Last.fm matched name) and adds ``mbid``, ``on_tour``, ``artist_listeners``,
    and ``artist_playcount`` to the payload.

    Args:
        track_data: Output from ``get_track_from_lastfm``.
        key: Last.fm API key.

    Returns:
        Updated track_data dict, or None if artist lookup fails validation.
    """
    spotify_artist_name = track_data.get("original_artist_name") or track_data.get("artist_name")
    if not spotify_artist_name:
        return None

    data = _lastfm_get({"method": "artist.getInfo", "artist": spotify_artist_name}, key)
    if not data or "artist" not in data:
        return None

    artist = data["artist"]
    stats = artist.get("stats", {})
    if not artist:
        return None

    lastfm_artist_name = (artist.get("name") or "").lower().strip()
    spotify_artist_normalized = spotify_artist_name.lower().strip()
    artist_score = similarity_score(lastfm_artist_name, spotify_artist_normalized)

    if artist_score < 0.9:
        return None

    track_data["mbid"] = artist.get("mbid") or track_data.get("mbid")
    track_data["on_tour"] = artist.get("ontour", artist.get("on_tour", 0))
    track_data["artist_listeners"] = int(stats.get("listeners") or 0)
    track_data["artist_playcount"] = int(stats.get("playcount") or 0)
    track_data["source"] = "Lastfm"

    logger.debug("Processed track data: %s", track_data)
    return track_data

def process_last_fm_data(
    song_name: str, artist_name: str, song_id: str, artist_id: str, key: str
) -> dict | None:
    """Fetch and merge track + artist Last.fm data for one Spotify song.

    Args:
        song_name: Track title from Spotify staging.
        artist_name: Primary artist name from Spotify staging.
        song_id: Spotify track ID.
        artist_id: Spotify artist ID.
        key: Last.fm API key.

    Returns:
        Complete record dict for ``load_raw_records``, or None on failure.
    """
    try:

        match_data = get_track_from_lastfm(song_name, artist_name, song_id, artist_id, key)
        if not match_data:
            logger.warning(f"No track data found for: {song_name} by {artist_name}")
            return None


        complete_data = match_artists_from_lastfm(match_data, key)
        if not complete_data:
            logger.warning(f"Artist matching failed for: {song_name} by {artist_name}")
            return None
        return complete_data

    except Exception as e:
        logger.error(f"Error processing {song_name} by {artist_name}: {e}")
        return None
    

# Songs in staging that have no matching row in stg_lastfm yet.
SONGS_NEEDING_LASTFM_QUERY = """
    SELECT
        t.artist_id, t.song_id, t.song_name, t.artist_name
    FROM MUSICDB.STAGING.stg_spotify__tracks t
    LEFT JOIN MUSICDB.STAGING.stg_lastfm a
        ON a.song_id = t.song_id
    WHERE t.artist_id IS NOT NULL
        AND t.song_id IS NOT NULL
        AND a.song_id IS NULL
        AND t.song_name IS NOT NULL
        AND t.artist_name IS NOT NULL
    ORDER BY t._loaded_at DESC
"""


def main(batch_size: int = 5, run_id: str | None = None) -> None:
    """Backfill Last.fm enrichment for Spotify tracks missing from staging.

    Queries STAGING (not RAW) for the gap set, processes songs in chunks,
    and loads successful matches into ``raw_lastfm``.

    Args:
        batch_size: Number of songs to process per Snowflake load batch.
        run_id: Optional run identifier; generated if omitted.
    """
    load_dotenv()
    key = os.getenv("LAST_FM_KEY")

    if not key:
        raise RuntimeError("LAST_FM_KEY is not set")

    logger.info("Querying staging for songs missing Last.fm enrichment")
    rows = fetch_all(SONGS_NEEDING_LASTFM_QUERY)

    if not rows:
        logger.error("All of the Spotify track data is enhanced by LastFm")
        return
    
    run_id = run_id or str(uuid.uuid4())

    for i in range(0, len(rows), batch_size):
        batch_data=[]
        stop = i+ batch_size if (i+batch_size)<= len(rows) else len(rows)
        chunk = rows[i: stop]
        for artist_id, song_id, song_name, artist_name  in chunk:

            if not song_name or not artist_id or not song_id or not artist_name:
                logger.warning("Skipping row with missing artist or song data")
                continue

            logger.info(f"Requesting LastFm data for {song_name} by {artist_name}")

            complete_data = process_last_fm_data(song_name, artist_name, song_id, artist_id, key)

            if not complete_data: 
                logger.warning(f'There was no LastFm artist data for song: {song_name} by artist: {artist_name}')
                continue

            batch_data.append(complete_data)

        if not batch_data:
            logger.warning("No Last.fm matches in this chunk to load")
            continue

        with snowflake_connection() as conn:
            num_rows, error_count = load_raw_records(
                table="raw_lastfm",
                records=batch_data,
                id_columns="song_id",
                run_id=str(run_id),
                conn=conn,
            )

        logger.info(f'This batch successfully inserted {num_rows} rows into the Raw LastFm database')
        logger.info(f'There were {error_count} errenous rows in this batch')

        

    
    



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_id = str(uuid.uuid4())
    main(batch_size=500, run_id=run_id)
    