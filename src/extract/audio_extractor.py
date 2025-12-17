import os
from dotenv import load_dotenv
from spotify_preview_finder import finder
import librosa
import requests
import numpy as np
from io import BytesIO
from lastfm_extractor import send_through_kafka
from src.utils.database import get_db


load_dotenv()

def get_songs_and_artists(cur):
    cur.execute('SELECT song_name, artist_name, s.artist_id, s.song_id '  
                'FROM songs AS s JOIN artists AS a ' 
                'ON a.artist_id = s.artist_id '
                )
    result = cur.fetchall()
    return result



def get_audio_features(song_name, artist_name, artist_id, song_id):
    my_finder = finder
    search_query = f"{song_name} {artist_name}"
    print(f'song IDDDDD:{song_id}')
    # Check what methods are available
    result = my_finder.search_and_get_links(song_name=search_query, client_id=os.getenv('SPOTIFY_CLIENT_ID'), client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"), limit=1)
    preview_url = result['results'][0]['previewUrl']
    print(result)
    if result['success']== True:
        resp = requests.get(preview_url)
        audio_data = BytesIO(resp.content)
        
        y, sr =librosa.load(audio_data)
        bpm, beats = librosa.beat.beat_track(y=y, sr=sr)
        print(f'BPM: {bpm}')

        rms = librosa.feature.rms(y=y)[0]
        energy = np.mean(rms)
        print(f"Energy: {energy}")

        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        centroid_mean = np.mean(spectral_centroid)
        print(f'Brightness: {centroid_mean}')

        zcr = librosa.feature.zero_crossing_rate(y)[0]
        zcr_mean= np.mean(zcr)
        print(f"Percussiveness: {zcr_mean}")

        y_harmonic, y_percussive = librosa.effects.hpss(y)
        harmonic_ratio = (sum(abs(y_harmonic))/ np.sum(np.abs(y)))
        percussive_ratio = (sum(abs(y_percussive))/np.sum(np.abs(y)))
        print(f"Harmonic Ratio: {harmonic_ratio}")
        print(f"Percussive Ratio: {percussive_ratio}")

       
       
        data={
                'name': song_name,
                'song_id': song_id,
                'artist_id' : artist_id,
                'bpm' : float(bpm[0]),
                'energy' : float(energy),
                'spectral_centroid' : float(centroid_mean),
                'zero_crossing_rate' : float(zcr_mean),
                'preview_url' : preview_url,
                'harmonic_ratio': float(harmonic_ratio),
                'percussive_ratio': float(percussive_ratio),
                'source': 'preview_url'
            }

        return data
            

    else:
        print(f"There is not a preview url available for {song_name} by {artist_name}")
        return

if __name__ == "__main__":
    conn, cur=get_db()
    song_artists=get_songs_and_artists(cur)
    counter=0
    for song, artist, artist_id, song_id in song_artists:
        data=get_audio_features(song, artist, artist_id, song_id)
        send_through_kafka(data)
        counter+=1
        if counter>0:
            break