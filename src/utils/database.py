import psycopg2
import os 



def get_db():
    '''
    Connects to a SQL database using environment variables
    '''
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