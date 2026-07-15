from src.extract.spotify_track_extractor import extract_batch_spotify_data
from src.load.snowflake_loader import load_raw_records
import uuid
from dotenv import load_dotenv


from src.utils.text_processing_utils import get_words_list
from src.utils.snowflake_utils import snowflake_connection
import logging


load_dotenv()

logger = logging.getLogger(__name__)


def main(batch_size: int = 5, start_idx: int = 0, run_id: str | None = None) -> None:
    batch_size = batch_size
    # get a list of words to query the Spotify API
    words_list = get_words_list()
    if not words_list:
        raise RuntimeError("No words list, cannot query the API")

    if start_idx < 0 or start_idx >= len(words_list):
        raise ValueError(
            f"start_idx must be a positive value and longer than words list: "
            f"{len(words_list)}, but start_idx was: {start_idx}"
        )

    run_id = run_id or str(uuid.uuid4())

    start_idx = (start_idx // batch_size) * batch_size

    for num in range(start_idx, len(words_list), batch_size):
        batch = words_list[num : num + batch_size]
        logger.info(f"Processing batch from {batch[0]} to {batch[-1]} ")
        data = extract_batch_spotify_data(batch)

        if not data:
            logger.warning("There was an error in extracting Spotify track data, no data returned")
            continue

        with snowflake_connection() as conn:
            successful, error = load_raw_records(
                table="raw_spotify_tracks",
                records=data,
                id_columns="song_id",
                run_id=run_id,
                conn=conn,
            )

        logger.info(f"Number of successful Spotify Tracks loaded: {successful}")
        logger.info(f"Number of Spotify Tracks that were not loaded: {error}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(start_idx=5, batch_size=1)
