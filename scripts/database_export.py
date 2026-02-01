
from dotenv import load_dotenv
from src.utils.database_utils import export_table_to_csv_copy

load_dotenv()


def copy_all_tables():
    artist_query = 'SELECT * from artists ORDER BY artist_name'
    album_query = "SELECT * from albums ORDER BY album_title"
    song_query = 'SELECT * from songs ORDER BY song_name'
    audio_features_query = 'SELECT * from song_audio_features ORDER BY song_id'
    genres_query = 'SELECT * FROM genres ORDER BY genre_id'
    artist_genre_query = 'SELECT * FROM artist_genres ORDER BY artist_id, genre_id'

    export_table_to_csv_copy('artists', artist_query, 'exports/artist.csv')
    export_table_to_csv_copy('albums', album_query, 'exports/albums.csv')
    export_table_to_csv_copy('songs', song_query, 'exports/songs.csv')
    export_table_to_csv_copy('song_audio_features', audio_features_query, 'exports/song_audio_features.csv')
    export_table_to_csv_copy('genres', genres_query, 'exports/genres.csv')
    export_table_to_csv_copy('artist_genres', artist_genre_query, 'exports/artist_genres.csv')


if __name__ == '__main__':
    copy_all_tables()
    print('Exporting tables is complete')









