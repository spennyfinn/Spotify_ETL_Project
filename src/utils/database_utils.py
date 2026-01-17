from typing import Any
import psycopg2
import os
import logging
from dotenv import load_dotenv

from tests.unit.constants import AUDIO_FEATURES_REQUIRED_FIELDS

logger = logging.getLogger(__name__)



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




def get_null_artist_popularity(cur):
    try:
        cur.execute('SELECT artist_id, artist_name FROM artists where artist_popularity IS NULL ORDER BY total_playcount DESC ;')
        artist_id_list=cur.fetchall()
    except Exception as e:
        logger.error(f'Error extracting artist IDs from database: {e}')
        return
    if artist_id_list:
        logger.info(f"Found {len(artist_id_list)} artists needing popularity data")
        return artist_id_list


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
                'LIMIT 50000;'
                )
    result = cur.fetchall()
    return result


def export_table_to_csv_copy(table, query, filename):
    conn, cur=get_db()

    try:
        os.makedirs(os.path.dirname(filename), exist_ok= True)

        copy_query = f"COPY ({query}) TO STDOUT WITH CSV HEADER"

        with open(filename, 'w', encoding='utf-8') as f:
            cur.copy_expert(copy_query, f)

    except Exception as e:
        logger.error(f"Error exporting table {table}: {e}")
    finally:
        conn.close()
        cur.close()

#