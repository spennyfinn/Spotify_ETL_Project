import os
from typing import Dict
from dotenv import load_dotenv
from spotify_preview_finder import finder
import librosa
import requests
import numpy as np
from io import BytesIO
from src.extract.lastfm_extractor import send_through_kafka
from src.utils.database import get_db
from src.utils.kafka_utils import create_producer, flush_kafka_producer
from concurrent.futures import as_completed, TimeoutError, ProcessPoolExecutor
import multiprocessing
import gc


load_dotenv()

def get_songs_and_artists(cur)-> list:
    '''
    Retrieves song name, artist name and song_id from the database

    Args:
        cur (psycopg2.cursor): cursor object 
    Returns
        list: a list of tuples (song_name, artist_name, artist_id, song_id ) or None if the database is empty
    '''
    cur.execute('SELECT s.song_name, a.artist_name, s.song_id '
                'FROM songs s '
                'JOIN artists a ON a.artist_id = s.artist_id '
                'LEFT JOIN song_audio_features af ON af.song_id = s.song_id '
                'WHERE af.song_id IS NULL '
                'LIMIT 10000;'
                )
    result = cur.fetchall()
    return result



def get_audio_features(song_name, artist_name, song_id)-> Dict:
    try:
        
        my_finder = finder
        search_query = f"{song_name} {artist_name}"
        print(f'Song ID:{song_id}')
        # Check what methods are available
        result = my_finder.search_and_get_links(song_name=search_query, client_id=os.getenv('SPOTIFY_CLIENT_ID'), client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"), limit=1)
        #print(result)

        if not result['results']:
            print(f"There was no preview url for {song_name} by {artist_name}")
            return None
        preview_url = result['results'][0]['previewUrl']
        if result['success']!= True:
            print(f"There is not a preview url available for {song_name} by {artist_name}")
            return None

        try:
            resp = requests.get(preview_url)
        except requests.ConnectionError as e:
            print(f"There was a connection error when calling {song_name}")
        except requests.exceptions.RequestException as e:
            print(f"API error for {song_name}: {e}")
            return None

        if resp:
            if len(resp.content)>=10000:
                audio_data = BytesIO(resp.content)
            try:
                y, sr =librosa.load(audio_data)
            except Exception as e:
                print(f"The extraction of audio features for {song_name} was unsuccessful")
                return None

            if len(y) ==0 or sr==0:
                print(f"Invalid audio data for {song_name}")
                return None
            try:
                bpm, beats = librosa.beat.beat_track(y=y, sr=sr)
                if isinstance(bpm, float):
                    bpm = [bpm]
                print(f'BPM: {bpm}')
            except Exception as e:
                print(f"BPM was unable to be extracted for {song_name}: {e}")
                return None
            try:
                rms = librosa.feature.rms(y=y)[0]
                energy = np.mean(rms)
                print(f"Energy: {energy}")
            except Exception as e:
                print(f"Energy was unable to be extracted for {song_name}: {e}")
                return None
            try:
                spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
                centroid_mean = np.mean(spectral_centroid)
                print(f'Brightness: {centroid_mean}')
            except Exception as e:
                print(f"Spectral Centroid was unable to be extracted for {song_name}: {e}")
                return None
            try:
                zcr = librosa.feature.zero_crossing_rate(y)[0]
                zcr_mean= np.mean(zcr)
                print(f"Percussiveness: {zcr_mean}")
            except Exception as e:
                print(f"ZCR was unable to be extracted for {song_name}: {e}")
                return None

            try:
                y_harmonic, y_percussive = librosa.effects.hpss(y)
                harmonic_raw = (sum(abs(y_harmonic)))
                percussive_raw = (sum(abs(y_percussive)))
                total= harmonic_raw + percussive_raw

                if total <=0: 
                    print("The sum of percussive ratio and harmonic ratio should be above 0")
                    return None

                harmonic_ratio = (sum(abs(y_harmonic))/total)
                percussive_ratio = (sum(abs(y_percussive))/total)

                print(f"Harmonic Ratio: {harmonic_ratio}")
                print(f"Percussive Ratio: {percussive_ratio}")
            except Exception as e:
                print(f"Harmonic Ratio and Percussive Ratio were unable to be extracted for {song_name}: {e}")
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
        print(f"There was an error retrieving audio features for {song_name}: {e}")
        return None
            


        
if __name__ == "__main__":
    conn, cur=get_db()
    producer = create_producer('music-streaming-producer')
    song_artists=get_songs_and_artists(cur)
    print(len(song_artists))
    cpu_count = multiprocessing.cpu_count()
    max_workers = min(4, cpu_count)

    with ProcessPoolExecutor(max_workers=max_workers) as w:
        futures= { w.submit(get_audio_features, song, artist, song_id): (song, artist, song_id) for song, artist, song_id in song_artists}

        for future in as_completed(futures):
            try:
                song, artist, song_id = futures[future]
                data= future.result(timeout=120)
                if data:
                    send_through_kafka(data, 'music_audio_features', producer)
                    print(f'{song} by {artist} was processed')
                else:
                    print(f'There was an error processing {song} by {artist}')
            except TimeoutError:
                song, artist, song_id = futures[future]
                print(f"There was a timeout error while processing {song} by {artist}")
            
            except Exception as e:
                song, artist, song_id = futures[future]
                print(f"There was an error while processing {song} by {artist}: {e}")
    flush_kafka_producer(producer)
    print(f'All {len(song_artists)} songs were processed')
