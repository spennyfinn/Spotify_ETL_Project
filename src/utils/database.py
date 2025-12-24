from typing import Any
import psycopg2
import os 
from dotenv import load_dotenv

from tests.unit.constants import AUDIO_FEATURES_REQUIRED_FIELDS



def get_db():
    '''
    Connects to a SQL database using environment variables
    '''
    load_dotenv()
    conn = psycopg2.connect(
        dbname= os.getenv("DB_NAME"),
        user= os.getenv('DB_USER'),
        password= os.getenv('DB_PASSWORD'),
        host= os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    conn.autocommit=True
    cur=conn.cursor()
    return conn,cur


def get_song_needing_spotify_data(cur):
    """
    Get list of songs and artists from database that need Spotify data.
    
    Args:
        cur: Database cursor
        
    Returns:
        list: List of tuples containing (song_name, artist_name)
    """
    song_artist_query=("SELECT DISTINCT s.song_name, a.artist_name FROM songs as s JOIN artists as a on a.artist_id = s.artist_id "
    "JOIN albums as al on al.artist_name=a.artist_name WHERE s.release_date IS NULL and al.album_total_tracks IS NULL;")
    cur.execute(song_artist_query)
    results = cur.fetchall()
    song_artist_list=[]
    for result in results:
        song_artist_list.append((result[0], result[1]))
    return song_artist_list


def get_result_from_db_spotify(song_name, artist_name ):
    song_name = song_name.lower().strip()
    artist_name = artist_name.lower().strip()
    print(song_name, artist_name)
    try:

        conn, cur = get_db()
        query= (f"SELECT s.song_name, s.artist_id, s.duration_ms, s.duration_seconds, s.duration_minutes, s.release_date, s.release_date_precision, s.is_explicit, s.popularity, s.track_number, s.song_id, s.album_id, s.is_playable "
        f"FROM songs as s JOIN artists as a ON a.artist_id = s.artist_id WHERE s.song_name = '{song_name}' AND a.artist_name = '{artist_name}';")
        cur.execute(query)
        song_res= cur.fetchone()
        print(song_res)
        if not song_res:
            raise ValueError(f"There is no song information for the song: {song_name} by {artist_name}")
        cur.execute(f"SELECT album_title, artist_name, album_type, album_total_tracks, album_id FROM albums WHERE album_id = '{song_res[11]}';")
        album_res = cur.fetchone()
        cur.execute(f"SELECT artist_id, artist_name FROM artists WHERE artist_id = '{song_res[1]}';" )
        artist_res = cur.fetchone()
        if not album_res or not artist_res:
            raise ValueError(f'There was an error retrieving information from the database')
        return {
            'song_name':song_res[0], #
            'song_artist_id': song_res[1], #
            'duration_ms': song_res[2],
            'duration_seconds': song_res[3],
            'duration_minutes': song_res[4],
            'release_date': song_res[5],
            'release_date_precision': song_res[6],
            'is_explicit':song_res[7],
            'popularity': song_res[8],
            'track_number': song_res[9],
            'song_id': song_res[10],
            'song_album_id': song_res[11],
            'is_playable': song_res[12],
            'album_title': album_res[0],
            'album_artist_name': album_res[1],  #
            'album_type': album_res[2],
            'album_total_tracks': album_res[3],
            'album_album_id': album_res[4],
            'artist_artist_id': artist_res[0], #
            'artist_artist_name': artist_res[1]  #
        }
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_result_from_db_lastfm(song_name, artist_name):
    song_name = song_name.lower().strip()
    artist_name = artist_name.lower().strip()
    try:
        conn, cur=get_db()

        cur.execute(f"SELECT s.song_name, s.song_id, s.song_listeners, a.artist_id, s.song_url, s.mbid, s.engagement_ratio FROM songs JOIN artists as a ON a.artist_id = s.artist_id WHERE s.song_id = '{song_name}' AND a.artist_name = '{artist_name}'")
        song_res = cur.fetchone()
        if not song_res:
            raise ValueError(f"There was an issue getting info from the database for {song_name} by {artist_name}" )
        cur.execute(f"SELECT artist_name, artist_id, on_tour, total_listeners, total_playcount, plays_per_listener FROM artists WHERE artist_id = '{song_res[3]}'")
        artist_res = cur.fetchone()
        if not artist_res:
            raise ValueError(f"There was an issue getting info for {artist_name}")
        return {
            'song_name': song_res[0],
            'song_id': song_res[1],
            'song_listeners': song_res[2],
            'song_artist_id': song_res[3],
            'song_url': song_res[4],
            'mbid': song_res[5],
            'engagement_ratio': song_res[6],
            'artist_name': artist_res[0],
            'artist_artist_id': artist_res[1],
            'on_tour': artist_res[2],
            'total_listeners': artist_res[3],
            'total_playcount': artist_res[4],
            'plays_per_listener': artist_res[5]
                }
    finally:
        conn.close()
        cur.close()





def get_result_from_db_audio_features(song_name, artist_id):
    song_name=song_name.lower().strip()
    artist_id = artist_id.strip()

    try:
        conn, cur= get_db()
        cur.execute(f"SELECT * from song_audio_features WHERE song_name = '{song_name}' AND artist_id = '{artist_id}'")
        song_res = cur.fetchone()
        return { k:v for k,v in zip(AUDIO_FEATURES_REQUIRED_FIELDS, song_res)}


    finally:
        conn.close()
        cur.close()
    

