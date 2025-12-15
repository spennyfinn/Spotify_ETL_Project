"""
ETL Consumer for Music Data Pipeline

This script consumes transformed music track data from a Kafka topic ('music_transformed'),
parses it into relational table structures (songs, artists, albums, tags, similar_artists),
and inserts or updates the data into a PostgreSQL database.

Tech Stack:
- Python, Kafka (confluent_kafka)
- PostgreSQL (psycopg2)
- dotenv for environment variables
"""
import json
from confluent_kafka import Consumer
import psycopg2
import os
from dotenv import load_dotenv
import uuid
import logging
import time

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def consume_message(consumer, topic):
    """
    Continuously poll messages from a Kafka topic and yield them as JSON objects.

    Args:
        consumer (Consumer): Kafka consumer instance
        topic (str): Kafka topic to subscribe to

    Yields:
        dict: Parsed JSON message from Kafka
    """
    consumer.subscribe([topic])
    logging.info(f"Subscribed to topic: {topic}")
    
    while True:
        msg=consumer.poll(1.0)
        if msg == None:
            continue
        if msg.error():
            logging.error(f'Kafka error: {msg.error()}')
            continue
        try:
            encoded_value=msg.value().decode('utf-8')
            yield json.loads(encoded_value)
        except json.JSONDecodeError as e:
            logging.error(f'Failed to parse JSON: {e}')
            try:
                logging.debug(f'Message content: {encoded_value[:200]}...')
            except:
                pass
            continue
        except UnicodeDecodeError as e:
            logging.error(f'Failed to decode value: {e}')
            continue
        except Exception as e:
            logging.error(f'Unexpected error processing message: {e}')
            continue



def parse_insert_message(data):
        """
    Parse a transformed track message into rows for different database tables.

    Args:
        data (dict): Transformed music track data

    Returns:
        Tuple containing:
            song_row (list)
            artist_row (list)
            album_row (list)
            tag_rows (list of lists)
            similar_artist_rows (list of lists)
    """
        # Extract relevant fields into seperate tables 
        song_row=[
            data['song_name'],
            data['song_id'],
            data['rank'],
            data['num_song_listeners'],
            data['duration_seconds'],
            data['duration_minutes'],
            "",
            data['artist_id'],
            data['song_url'],
            data['engagement_ratio']
        ]

        artist_row=[
            data['artist_id'],
            data['artist_name'] ,
            data['artist_url'],
            data['on_tour'] ,
            data['artist_total_listeners'] ,
            data['artist_total_playcount'] ,
            data['plays_per_listener'] 
        ]

        album_row=[
            str(uuid.uuid4()),
            data['album_title'],
            data['artist_name']
        ]


        tag_rows = [[data['song_name'], data['artist_id'], tag] for tag in data['tags']]
        
        similar_artist_rows = [[data['artist_name'], sim] for sim in data['similar_artists']]

        return song_row, artist_row, album_row, tag_rows, similar_artist_rows

def parse_update_message(data):
    print(data)
    song=[
        data['song_name'],
        data['artist_id'],
        data['duration_ms'],
        data['duration_seconds'],
        data['duration_minutes'],
        data['release_date'],
        data['release_date_precision'],
        data['is_explicit'],
        data['popularity'],
        data['track_number']
    ]
    album=[
        data['album_title'],
        data['artist_name'],
        data['album_type'],
        data['album_total_tracks'],
        data['album_id'],
        
    ]

    return song, album
# -------------------------------
# Kafka Consumer Configuration
# -------------------------------
consumer_config= {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'music-streaming-consumer_v2',
    'auto.offset.reset':'earliest',
}
consumer = Consumer(consumer_config)





# -------------------------------
# Database Connection Function
# -------------------------------
def get_db():
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


# -------------------------------
# SQL Queries
# -------------------------------
insert_song_query = ("INSERT INTO songs(song_name, song_id, rank, song_listeners, duration_seconds, duration_minutes, album_id, artist_id, song_url,engagement_ratio) "
                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
                 "ON CONFLICT (song_name, artist_id) DO UPDATE "
                 "SET rank = EXCLUDED.rank, "
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




# -------------------------------
# Main ETL Loop
# -------------------------------
if __name__=='__main__':
    conn,cur=get_db()
    try:
        logging.info("Starting continuous ETL process - loading music data into database")
        
        # Get the maximum rank currently in the database to continue sequential numbering
        cur.execute('SELECT COALESCE(MAX(rank), 0) FROM songs;')
        max_rank_result = cur.fetchone()
        sequential_rank = max_rank_result[0] if max_rank_result else 0
        logging.info(f"Starting sequential rank from: {sequential_rank}")

        # Track statistics
        lastfm_count = 0
        spotify_count = 0
        errors_count = 0
        last_rank_reassign = time.time()
        rank_reassign_interval = 3600  # Reassign ranks every hour
        summary_interval = 300  # Log summary every 5 minutes

        for message in consume_message(consumer, 'music_transformed'):
            if message['source']== 'Lastfm':
                song, artist, album, tags, similar_artists  = parse_insert_message(message)
                song_name = song[0]
                artist_name = artist[1]
                
                try:
                    # Insert artist and album first
                    cur.execute(insert_artist_query, artist)
                    logging.info(f"✓ Artist loaded/updated: {artist_name}")
                    
                    cur.execute(insert_album_query, album)
                    result = cur.fetchone()
                    if result:
                        album_id = result[0]
                        logging.info(f"✓ Album loaded/updated: {album[1]} by {artist_name} (ID: {album_id})")
                    else:
                        cur.execute("SELECT album_id FROM albums WHERE album_title=%s AND artist_name = %s",
                                    (album[1], album[2]))  # album_title is at index 1, artist_name at index 2
                        album_result = cur.fetchone()
                        if not album_result:
                            logging.error(f"✗ Album not found: {album[1]} by {album[2]}")
                            errors_count += 1
                            continue
                        album_id = album_result[0]
                        logging.info(f"✓ Album retrieved: {album[1]} by {artist_name} (ID: {album_id})")
                    song[6]=album_id
                except Exception as e:
                    logging.error(f"✗ Failed to load artist/album for {song_name} by {artist_name}: {e}")
                    errors_count += 1
                    continue
                
                # Check if this song already exists in the database and get its current rank
                cur.execute("SELECT rank FROM songs WHERE song_name = %s AND artist_id = %s",
                           (song[0], song[7]))  # song_name and artist_id
                existing_song = cur.fetchone()
                
                # Get the next sequential rank
                sequential_rank += 1
                new_rank = sequential_rank
                
                # If updating an existing song, check for rank conflicts
                if existing_song:
                    old_rank = existing_song[0]
                    # If the new rank conflicts with another song, temporarily free it
                    if old_rank != new_rank:
                        cur.execute("SELECT song_name, artist_id FROM songs WHERE rank = %s AND (song_name != %s OR artist_id != %s)",
                                   (new_rank, song[0], song[7]))
                        conflict = cur.fetchone()
                        if conflict:
                            # Temporarily set the conflicting song's rank to a high temp value
                            # We'll reassign sequentially at the end
                            cur.execute("UPDATE songs SET rank = 9999999 WHERE rank = %s AND (song_name != %s OR artist_id != %s)",
                                       (new_rank, song[0], song[7]))
                
                # Update rank in song row before insertion
                song[2] = new_rank
                
                # Insert/update the song with the new sequential rank
                try:
                    cur.execute(insert_song_query, song)
                    logging.info(f"✓ Song loaded/updated: {song_name} by {artist_name} (Rank: {new_rank})")
                except psycopg2.IntegrityError as e:
                    # If there's still a rank conflict, handle it
                    if 'rank' in str(e):
                        # Use a temporary high rank, will be reassigned at the end
                        song[2] = 9999999 + sequential_rank
                        cur.execute(insert_song_query, song)
                        logging.warning(f"⚠ Song loaded with temporary rank due to conflict: {song_name} by {artist_name}")
                    else:
                        logging.error(f"✗ Failed to load song {song_name} by {artist_name}: {e}")
                        errors_count += 1
                        raise
                
                # Insert tags
                tags_inserted = 0
                for tag in tags:
                    try:
                        cur.execute(insert_tags_query, tag)
                        tags_inserted += 1
                    except Exception as e:
                        logging.warning(f"⚠ Failed to insert tag '{tag[2]}' for {song_name}: {e}")
                if tags_inserted > 0:
                    logging.info(f"✓ Inserted {tags_inserted} tag(s) for {song_name}")
                
                # Insert similar artists
                similar_inserted = 0
                for similar_artist in similar_artists:
                    try:
                        cur.execute(insert_similar_artist_query, similar_artist)
                        similar_inserted += 1
                    except Exception as e:
                        logging.warning(f"⚠ Failed to insert similar artist '{similar_artist[1]}' for {artist_name}: {e}")
                if similar_inserted > 0:
                    logging.info(f"✓ Inserted {similar_inserted} similar artist(s) for {artist_name}")
                
                lastfm_count += 1
            else:
                song, album = parse_update_message(message)
                song_name = song[0]
                artist_name = album[1]
                
                try:
                    cur.execute(update_song_query, song)
                    logging.info(f"✓ Spotify song data updated: {song_name} by {artist_name}")
                except Exception as e:
                    logging.error(f"✗ Failed to update Spotify song data for {song_name} by {artist_name}: {e}")
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
                        logging.error(f"✗ Failed to update Spotify album data for {album[0]} by {artist_name}: {e}")
                        errors_count += 1
                        raise
                
                spotify_count += 1
            
            # Periodically reassign ranks and log statistics
            current_time = time.time()
            if current_time - last_rank_reassign >= rank_reassign_interval:
                logging.info("Periodic rank reassignment starting...")
                cur.execute("""
                    UPDATE songs
                    SET rank = subquery.new_rank
                    FROM (
                        SELECT song_name, artist_id,
                               ROW_NUMBER() OVER (ORDER BY 
                                   CASE WHEN rank >= 9999999 THEN 9999999 ELSE rank END,
                                   song_name, artist_id
                               ) as new_rank
                        FROM songs
                    ) AS subquery
                    WHERE songs.song_name = subquery.song_name 
                      AND songs.artist_id = subquery.artist_id
                """)
                ranks_updated = cur.rowcount
                logging.info(f"✓ Rank reassignment complete: {ranks_updated} songs updated")
                
                # Summary statistics
                logging.info("=" * 60)
                logging.info("ETL PROCESS STATUS - SUMMARY")
                logging.info("=" * 60)
                logging.info(f"Last.fm records processed: {lastfm_count}")
                logging.info(f"Spotify records processed: {spotify_count}")
                logging.info(f"Total records processed: {lastfm_count + spotify_count}")
                logging.info(f"Errors encountered: {errors_count}")
                logging.info("=" * 60)
                
                last_rank_reassign = current_time
                
    finally:
        cur.close()
        conn.close()
        consumer.close()
        logging.info("Database connections and consumer closed")


