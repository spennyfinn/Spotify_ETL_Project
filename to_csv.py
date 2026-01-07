import psycopg2
from src.utils.database import get_db
import os
from dotenv import load_dotenv
import csv

load_dotenv()



def export_table_to_csv_copy(table, query, filename):
    conn, cur=get_db()

    try:
        os.makedirs(os.path.dirname(filename), exist_ok= True)

        copy_query = f"COPY ({query}) TO STDOUT WITH CSV HEADER"

        with open(filename, 'w', encoding='utf-8') as f:
            cur.copy_expert(copy_query, f)
        
    except Exception as e:
        print(f"Error exporting {table}: {e}")
    finally:
        conn.close()
        cur.close()

def copy_all_tables():
    artist_query = 'SELECT * from artists ORDER BY artist_name'
    album_query = "SELECT * from albums ORDER BY album_title"
    song_query = 'SELECT * from songs ORDER BY song_name'
    audio_features_query = 'SELECT * from song_audio_features ORDER BY song_id'

    export_table_to_csv_copy('artists', artist_query, 'exports/artist.csv')
    export_table_to_csv_copy('albums', album_query, 'exports/albums.csv')
    export_table_to_csv_copy('songs', song_query, 'exports/songs.csv')
    export_table_to_csv_copy('song_audio_features', audio_features_query, 'exports/song_audio_features.csv')


if __name__ == '__main__':
    copy_all_tables()
    print('Exporting tables is complete')









