import os
import logging
from typing import Dict
from dotenv import load_dotenv
from spotify_preview_finder import finder
import librosa
import requests
import numpy as np
from io import BytesIO
from src.extract.lastfm_extractor import send_through_kafka
from src.utils.database_utils import get_db, get_songs_and_artists
from src.utils.kafka_utils import create_producer, flush_kafka_producer, safe_batch_send
from concurrent.futures import as_completed, TimeoutError, ProcessPoolExecutor
import multiprocessing
import gc

load_dotenv()

logger = logging.getLogger(__name__)

def get_audio_features(song_name, artist_name, song_id)-> Dict:
    try:
        
        my_finder = finder
        search_query = f"{song_name} {artist_name}"
        logger.debug(f'Processing song ID: {song_id}')
        # Check what methods are available
        result = my_finder.search_and_get_links(song_name=search_query, client_id=os.getenv('SPOTIFY_CLIENT_ID'), client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"), limit=1)
        # Debug: print(result)

        if not result['results']:
            logger.warning(f"No preview URL found for {song_name} by {artist_name}")
            return None
        preview_url = result['results'][0]['previewUrl']
        if result['success']!= True:
            logger.warning(f"Preview URL not available for {song_name} by {artist_name}")
            return None

        try:
            resp = requests.get(preview_url)
        except requests.ConnectionError as e:
            logger.error(f"Connection error when fetching {song_name}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"API error for {song_name}: {e}")
            return None

        if resp:
            if len(resp.content)>=10000:
                audio_data = BytesIO(resp.content)
            try:
                y, sr =librosa.load(audio_data)
            except Exception as e:
                logger.error(f"Audio feature extraction failed for {song_name}: {e}")
                return None

            if len(y) ==0 or sr==0:
                logger.warning(f"Invalid audio data for {song_name}")
                return None
            try:
                bpm, beats = librosa.beat.beat_track(y=y, sr=sr)
                if isinstance(bpm, float):
                    bpm = [bpm]
                logger.debug(f'Extracted BPM: {bpm}')
            except Exception as e:
                logger.error(f"BPM extraction failed for {song_name}: {e}")
                return None
            try:
                rms = librosa.feature.rms(y=y)[0]
                energy = np.mean(rms)
                logger.debug(f"Extracted energy: {energy}")
            except Exception as e:
                logger.error(f"Energy extraction failed for {song_name}: {e}")
                return None
            try:
                spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
                centroid_mean = np.mean(spectral_centroid)
                logger.debug(f'Extracted spectral centroid (brightness): {centroid_mean}')
            except Exception as e:
                logger.error(f"Spectral centroid extraction failed for {song_name}: {e}")
                return None
            try:
                zcr = librosa.feature.zero_crossing_rate(y)[0]
                zcr_mean= np.mean(zcr)
                logger.debug(f"Extracted ZCR (percussiveness): {zcr_mean}")
            except Exception as e:
                logger.error(f"ZCR extraction failed for {song_name}: {e}")
                return None

            try:
                y_harmonic, y_percussive = librosa.effects.hpss(y)
                harmonic_raw = (sum(abs(y_harmonic)))
                percussive_raw = (sum(abs(y_percussive)))
                total= harmonic_raw + percussive_raw

                if total <=0:
                    logger.warning("Invalid harmonic/percussive ratio calculation for {song_name}")
                    return None

                harmonic_ratio = (sum(abs(y_harmonic))/total)
                percussive_ratio = (sum(abs(y_percussive))/total)

                logger.debug(f"Extracted harmonic ratio: {harmonic_ratio}")
                logger.debug(f"Extracted percussive ratio: {percussive_ratio}")
            except Exception as e:
                logger.error(f"Harmonic/percussive ratio extraction failed for {song_name}: {e}")
                return None

            
            
            data={
                    'song_id': song_id,
                    'bpm' : float(bpm[0]),
                    'energy' : float(energy),
                    'spectral_centroid' : float(centroid_mean),
                    'zero_crossing_rate' : float(zcr_mean),
                    'preview_url' : preview_url,
                    'harmonic_ratio': float(harmonic_ratio),
                    'percussive_ratio': float(percussive_ratio),
                    'source': 'preview_url'
                }
            del y,y_harmonic, y_percussive, beats, bpm, rms, zcr, spectral_centroid, sr
            gc.collect()
            return data
    except Exception as e:
        gc.collect()
        logger.error(f"Audio feature retrieval failed for {song_name}: {e}")
        return None
            


        
if __name__ == "__main__":
    conn, cur=get_db()
    producer = create_producer('music-streaming-producer')
    song_artists=get_songs_and_artists(cur)
    logger.info(f"Starting audio feature extraction for {len(song_artists)} songs")
    pending_batch = []
    batch_size = 5
    cpu_count = multiprocessing.cpu_count()
    max_workers = min(8, cpu_count)

    with ProcessPoolExecutor(max_workers=max_workers) as w:
        futures= { w.submit(get_audio_features, song, artist, song_id): (song, artist, song_id) for song, artist, song_id in song_artists}

        for future in as_completed(futures):
            try:
                song, artist, song_id = futures[future]
                data= future.result(timeout=120)
                if data:
                    pending_batch.append(data)
                    if len(pending_batch) >= batch_size:
                        successful, failed = safe_batch_send(pending_batch, 'music_audio_features', producer, batch_size=batch_size)
                        logger.info(f'Batch sent: {successful} success, {failed} failed')
                        pending_batch.clear()
                    logger.debug(f'Processed: {song} by {artist}')
                else:
                    logger.warning(f'Failed to process: {song} by {artist}')
            except TimeoutError:
                song, artist, song_id = futures[future]
                logger.error(f"Timeout processing {song} by {artist}")

            except Exception as e:
                song, artist, song_id = futures[future]
                logger.error(f"Error processing {song} by {artist}: {e}")
    if pending_batch:
        successful, failed = safe_batch_send(pending_batch, 'music_audio_features', producer, batch_size=batch_size)
        logger.info(f'Final batch sent: {successful} success, {failed} failed')
    flush_kafka_producer(producer)
    logger.info(f'Audio feature extraction completed for {len(song_artists)} songs')
