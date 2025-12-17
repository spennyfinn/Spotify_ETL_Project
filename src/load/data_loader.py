import json
from confluent_kafka import Consumer
import psycopg2
from dotenv import load_dotenv
import uuid
import logging
from src.utils.database import get_db
from src.utils.kafka_utils import consume_message, create_consumer
from parsers import parse_audio_features_data, parse_insert_message, parse_update_message


load_dotenv()


# -------------------------------
# Logging Configs
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# -------------------------------
# SQL Queries
# -------------------------------
insert_song_query = ("INSERT INTO songs(song_name, song_id, song_listeners, album_id, artist_id, song_url,engagement_ratio) "
                 "VALUES (%s, %s, %s, %s, %s, %s, %s) "
                 "ON CONFLICT (song_name, artist_id) DO UPDATE "
                 "song_listeners = EXCLUDED.song_listeners,"
                 "engagement_ratio = EXCLUDED.engagement_ratio;")
                 
insert_artist_query = ("INSERT INTO artists(artist_id,artist_name, artist_url, on_tour, total_listeners, total_playcount, plays_per_listener) "
            "VALUES (%s,%s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (artist_id) DO UPDATE "
            "SET on_tour = EXCLUDED.on_tour, "
            "total_listeners = EXCLUDED.total_listeners,"
            "total_playcount = EXCLUDED.total_playcount,"
            "plays_per_listener=EXCLUDED.plays_per_listener;")
insert_album_query = ("INSERT INTO albums(album_id, album_title, artist_name) "
            "VALUES (%s,%s, %s) "
            "ON CONFLICT (album_title, artist_name) DO UPDATE "
            "SET album_id = EXCLUDED.album_id " \
            "RETURNING album_id; "
            )
insert_tags_query = ("INSERT INTO tags(song_name,artist_id,tag) "
            "VALUES (%s,%s, %s) "
            "ON CONFLICT (song_name, artist_id,tag) DO NOTHING; "
            )
insert_similar_artist_query =("INSERT INTO similar_artists(artist_name, similar_artist_name) "
            "VALUES (%s, %s) "
            "ON CONFLICT (artist_name, similar_artist_name) DO NOTHING ;"
            )

update_song_query=('INSERT INTO songs(song_name, artist_id, duration_ms, duration_seconds, duration_minutes, release_date, release_date_precision, is_explicit, popularity, track_number) '
                   'VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ' \
                   'ON CONFLICT (song_name, artist_id) '
                   'DO UPDATE ' \
                    'SET duration_seconds = EXCLUDED.duration_seconds,' \
                    'duration_minutes = EXCLUDED.duration_minutes,' \
                    'duration_ms= EXCLUDED.duration_ms,' \
                    'release_date = EXCLUDED.release_date,' \
                    'release_date_precision=EXCLUDED.release_date_precision,' \
                    'is_explicit=EXCLUDED.is_explicit,' \
                    'popularity= EXCLUDED.popularity,' \
                    'track_number= EXCLUDED.track_number;'
                   )
update_album_query=('INSERT INTO albums(album_title, artist_name, album_type, album_total_tracks, album_id) '
                    'VALUES(%s,%s,%s,%s,%s) '
                    'ON CONFLICT (album_title, artist_name) DO UPDATE '
                    'SET album_type = EXCLUDED.album_type,'
                    'album_total_tracks = EXCLUDED.album_total_tracks')


insert_audio_features_query= ('INSERT INTO song_audio_features(song_name, artist_id, bpm, energy, spectral_centroid, zero_crossing_rate, danceability, preview_url, harmonic_ratio, percussive_ratio) '
                              'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) '
                              'ON CONFLICT (song_name, artist_id) DO UPDATE SET '
                              'bpm = EXCLUDED.bpm, '
                              'energy = EXCLUDED.energy, '
                              'spectral_centroid = EXCLUDED.spectral_centroid, '
                              'zero_crossing_rate = EXCLUDED.zero_crossing_rate, '
                              'danceability = EXCLUDED.danceability, '
                              'preview_url = EXCLUDED.preview_url, '
                              'harmonic_ratio = EXCLUDED.harmonic_ratio, '
                              'percussive_ratio = EXCLUDED.percussive_ratio;'
)


# -------------------------------
# Main ETL Loop
# -------------------------------
if __name__=='__main__':
    conn,cur=get_db()
    consumer = create_consumer('music-streaming-consumer_v2')
    try:
        logging.info("Starting continuous ETL process - loading music data into database")

        lastfm_count=0
        spotify_count=0
        audio_features_count=0
        success_count=0
        errors_count = 0

        for message in consume_message(consumer, 'music_transformed'):
            if message['source']== 'Lastfm':
                song, artist, album, tags, similar_artists  = parse_insert_message(message)
                song_name = song[0]
                artist_name = artist[1]
                
                try:
                    # Insert artist and album first
                    cur.execute(insert_artist_query, artist)
                    logging.info(f"Artist loaded/updated: {artist_name}")
                    
                    cur.execute(insert_album_query, album)
                    result = cur.fetchone()
                    if result:
                        album_id = result[0]
                        logging.info(f"sAlbum loaded/updated: {album[1]} by {artist_name} (ID: {album_id})")
                    else:
                        cur.execute("SELECT album_id FROM albums WHERE album_title=%s AND artist_name = %s",
                                    (album[1], album[2]))  # album_title is at index 1, artist_name at index 2
                        album_result = cur.fetchone()
                        if not album_result:
                            logging.error(f"Album not found: {album[1]} by {album[2]}")
                            errors_count += 1
                            continue
                        album_id = album_result[0]
                        logging.info(f"Album retrieved: {album[1]} by {artist_name} (ID: {album_id})")
                    song[6]=album_id
                except Exception as e:
                    logging.error(f"Failed to load artist/album for {song_name} by {artist_name}: {e}")
                    errors_count += 1
                    continue
                
                # Insert the song 
                try:
                    cur.execute(insert_song_query, song)
                    logging.info(f"Song loaded/updated: {song_name} by {artist_name}")
                except psycopg2.IntegrityError as e:
                        logging.error(f"Failed to load song {song_name} by {artist_name}: {e}")
                        errors_count += 1
                        raise
                
                # Insert tags
                tags_inserted = 0
                for tag in tags:
                    try:
                        cur.execute(insert_tags_query, tag)
                        tags_inserted += 1
                    except Exception as e:
                        logging.warning(f"Failed to insert tag '{tag[2]}' for {song_name}: {e}")
                if tags_inserted > 0:
                    logging.info(f"Inserted {tags_inserted} tag(s) for {song_name}")
                
                # Insert similar artists
                similar_inserted = 0
                for similar_artist in similar_artists:
                    try:
                        cur.execute(insert_similar_artist_query, similar_artist)
                        similar_inserted += 1
                    except Exception as e:
                        logging.warning(f"Failed to insert similar artist '{similar_artist[1]}' for {artist_name}: {e}")
                if similar_inserted > 0:
                    logging.info(f"Inserted {similar_inserted} similar artist(s) for {artist_name}")
                
                lastfm_count += 1


            elif message['source']=='Spotify':
                song, album = parse_update_message(message)
                song_name = song[0]
                artist_name = album[1]
                
                try:
                    cur.execute(update_song_query, song)
                    logging.info(f"Spotify song data updated: {song_name} by {artist_name}")
                except Exception as e:
                    logging.error(f"Failed to update Spotify song data for {song_name} by {artist_name}: {e}")
                    errors_count += 1
                    continue
                
                # Try to insert/update album, handling potential album_id conflicts
                try:
                    cur.execute(update_album_query, album)
                    logging.info(f"✓ Spotify album data updated: {album[0]} by {artist_name}")
                except psycopg2.IntegrityError as e:
                    if 'albums_pkey' in str(e) or 'album_id' in str(e):
                        # Album_id already exists - update by title/artist without changing album_id
                        cur.execute("""
                            UPDATE albums 
                            SET album_type = %s, album_total_tracks = %s
                            WHERE album_title = %s AND artist_name = %s
                        """, (album[2], album[3], album[0], album[1]))
                        logging.info(f"✓ Spotify album data updated (conflict resolved): {album[0]} by {artist_name}")
                    else:
                        logging.error(f"Failed to update Spotify album data for {album[0]} by {artist_name}: {e}")
                        errors_count += 1
                        raise
                
                spotify_count += 1
            elif message['source']=='preview_url':
                try:
                    audio_features = parse_audio_features_data(message)
                    cur.execute(insert_audio_features_query, audio_features)
                    logging.info(f"Audio features loaded for: {message.get('song_name', 'Unknown')}")
                    audio_features_count+=1
                except Exception as e:
                    logging.error(f"Failed to load audio features: {e}")
                    errors_count+=1
                    continue



            

                
                # Summary statistics
                logging.info("=" * 60)
                logging.info("ETL PROCESS STATUS - SUMMARY")
                logging.info("=" * 60)
                logging.info(f"Last.fm records processed: {lastfm_count}")
                logging.info(f"Spotify records processed: {spotify_count}")
                logging.info(f"Audio Feature records processed: {audio_features_count}")
                logging.info(f"Total records processed: {lastfm_count + spotify_count + audio_features_count}")
                logging.info(f"Errors encountered: {errors_count}")
                logging.info("=" * 60)
                
                
    finally:
        cur.close()
        conn.close()
        consumer.close()
        logging.info("Database connections and consumer closed")


