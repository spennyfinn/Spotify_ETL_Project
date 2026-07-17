"""Spotify artist backfill extractor for the Snowflake ELT pipeline.

Finds artists present on ``stg_spotify__tracks`` that do not yet appear in
``stg_spotify__artists``, calls the Spotify Artist API for followers, popularity,
and genres, and appends results to ``RAW.raw_spotify_artists`` for dbt.

Pipeline position::

    stg_spotify__tracks  -->  Spotify Artist API  -->  raw_spotify_artists
                                                          -->  dbt (stg_spotify__artists+)

Prerequisites:
    - Run ``dbt run --select stg_spotify__tracks`` after loading Spotify seed data.
    - Set ``SPOTIFY_CLIENT_ID`` and ``SPOTIFY_CLIENT_SECRET`` in ``.env``.

Usage::

    python -m src.extract.spotify_artist_extractor

After loading, run ``dbt build --select stg_spotify__artists+`` to refresh marts.
"""

import json
import logging
import os
import uuid

import requests
from dotenv import load_dotenv

from src.load.snowflake_loader import load_raw_records
from src.utils.http_utils import safe_requests
from src.utils.snowflake_utils import fetch_all, snowflake_connection
from src.utils.spotify_api_utils import get_spotify_token

logger = logging.getLogger(__name__)

ARTISTS_NEEDING_SPOTIFY_METRICS_QUERY = """
    SELECT DISTINCT
        t.artist_id,
        t.artist_name
    FROM MUSICDB.STAGING.stg_spotify__tracks AS t
    LEFT JOIN MUSICDB.STAGING.stg_spotify__artists AS a
        ON a.artist_id = t.artist_id
    WHERE t.artist_id IS NOT NULL
        AND t.artist_name IS NOT NULL
        AND a.artist_id IS NULL
    ORDER BY t.artist_name
"""


def extract_spotify_artist_metrics(artist_id: str, artist_name: str) -> dict | None:
    """Fetch Spotify artist metrics for one artist ID.

    Args:
        artist_id: Spotify artist ID from staging tracks.
        artist_name: Display name from staging (fallback if API name missing).

    Returns:
        Payload dict for ``load_raw_records(table='raw_spotify_artists', ...)``,
        or None on API/validation failure.
    """
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    access_token = get_spotify_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = safe_requests(
            "GET",
            url,
            timeout=5,
            headers=headers,
            rate_limit_max_retries=5,
            backoff=1.0,
        )
        if resp is None:
            logger.warning("No response received for artist %s", artist_id)
            return None
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.Timeout as e:
        logger.error("Request timeout for artist %s: %s", artist_id, e)
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error for artist %s: %s", artist_id, e)
        return None
    except requests.HTTPError as e:
        logger.error("HTTP error for artist %s: %s", artist_id, e)
        return None
    except json.JSONDecodeError as e:
        logger.error("JSON decode error for artist %s: %s", artist_id, e)
        return None
    except Exception as e:
        logger.error("Unexpected error for artist %s: %s", artist_id, e)
        return None

    try:
        followers = data.get("followers", {})
        artists = {
            "follower_count": followers.get("total", 0),
            "popularity": data.get("popularity", 0),
            "artist_id": artist_id,
            "genres": data.get("genres", []),
            "source": "Spotify",
        }

        spotify_name = data.get("name")
        if spotify_name and spotify_name != artist_name:
            artists["artist_name"] = spotify_name
        else:
            artists["artist_name"] = artist_name

        required_fields = [
            "artist_id",
            "popularity",
            "follower_count",
            "source",
            "artist_name",
        ]
        if not all(artists.get(field) is not None for field in required_fields):
            logger.warning("Incomplete data for %s", artist_id)
            return None

        return artists
    except KeyError as e:
        logger.error("Key error processing artist data: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error processing artist data: %s", e)
        return None


def main(batch_size: int = 20, run_id: str | None = None) -> None:
    """Backfill Spotify artist metrics for artists missing from staging.

    Queries STAGING for the gap set, fetches artist API data in chunks, and
    loads successful results into ``raw_spotify_artists``.

    Args:
        batch_size: Number of artists to process per Snowflake load batch.
        run_id: Optional run identifier; generated if omitted.
    """
    load_dotenv()

    if not os.getenv("SPOTIFY_CLIENT_ID"):
        raise RuntimeError("Missing SPOTIFY_CLIENT_ID in .env file")
    if not os.getenv("SPOTIFY_CLIENT_SECRET"):
        raise RuntimeError("Missing SPOTIFY_CLIENT_SECRET in .env file")

    logger.info("Querying staging for artists missing Spotify artist enrichment")
    rows = fetch_all(ARTISTS_NEEDING_SPOTIFY_METRICS_QUERY)

    if not rows:
        logger.info("All track artists already have rows in stg_spotify__artists")
        return

    run_id = run_id or str(uuid.uuid4())
    logger.info("Starting artist backfill for %s artists", len(rows))

    for i in range(0, len(rows), batch_size):
        batch_data: list[dict] = []
        chunk = rows[i : i + batch_size]

        for artist_id, artist_name in chunk:
            if not artist_id or not artist_name:
                logger.warning("Skipping row with missing artist_id or artist_name")
                continue

            logger.info("Requesting Spotify artist data for %s (%s)", artist_name, artist_id)
            record = extract_spotify_artist_metrics(artist_id, artist_name)

            if not record:
                logger.warning("No artist metrics returned for %s", artist_id)
                continue

            batch_data.append(record)

        if not batch_data:
            logger.warning("No artist records in this chunk to load")
            continue

        with snowflake_connection() as conn:
            num_rows, error_count = load_raw_records(
                table="raw_spotify_artists",
                records=batch_data,
                id_columns="artist_id",
                run_id=str(run_id),
                conn=conn,
            )

        logger.info(
            "Inserted %s rows into raw_spotify_artists (%s validation errors)",
            num_rows,
            error_count,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(batch_size=20)
