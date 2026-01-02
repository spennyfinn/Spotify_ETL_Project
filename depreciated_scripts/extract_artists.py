import psycopg2
from dotenv import load_dotenv
import os
import time
import logging
from src.transform.data_transformer import normalize_str
from src.extract.lastfm_extractor import get_artist_data
from src.load.data_loader import insert_artist_query, insert_similar_artist_query
from flatten_json import flatten
from src.utils.database import get_db
from src.utils.artist_utils import load_artist_ids



artist_id_filepath='artists_ids.json'
# -------------------------------
# Environment Configuration
# -------------------------------
load_dotenv()
key  = os.getenv("LAST_FM_KEY")

# -------------------------------
# Logging Configuration
# -------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# -------------------------------
# SQL 
# -------------------------------
def generate_artists_lists(cur):
    # Only get similar artists that don't already exist in the artists table
    cur.execute("""
        SELECT DISTINCT similar_artist_name 
        FROM similar_artists 
        WHERE similar_artist_name NOT IN (SELECT artist_name FROM artists)
    """)
    similar_artists = [artist for(artist,) in cur.fetchall()]
    similar_artists=set(similar_artists)

    cur.execute("SELECT artist_name from artists;")
    artists = [name for (name,) in cur.fetchall()]
    # Create a set of normalized artist names for foreign key checking
    artists_set = {normalize_str(name) for name in artists}

    return similar_artists, artists, artists_set

def insert_similar_artists(similar_artists: list, artist: str, artists_set: set, cur, similar_artist_query):
    """
    Insert similar artist relationships into the database.

    For a given artist, this function iterates through a list of similar artists and inserts
    each pair into the `similar_artists` table using the provided query and database cursor.
    Only inserts relationships if the artist exists in the artists table.

    Args:
        similar_artists (list): List of artist names similar to the given artist.
        artist (str): The main artist name for whom similar artists are being inserted.
        artists_set (set): Set of artist names that exist in the database.
        cur: Database cursor object used to execute SQL commands.
        similar_artist_query (str): SQL query string for inserting into the `similar_artists` table.
    """
    # Normalize the artist name to match database format
    normalized_artist = normalize_str(artist)
    
    # Only insert if the artist exists in the database
    if normalized_artist not in artists_set:
        logging.warning(f"Skipping similar artist relationships for '{artist}' - artist not found in database")
        return
    
    for similar_artist in similar_artists:
        if similar_artist:  # Skip None or empty values
            try:
                cur.execute(similar_artist_query, [normalized_artist, normalize_str(similar_artist)])
            except Exception as e:
                logging.warning(f"Failed to insert similar artist relationship: {normalized_artist} -> {similar_artist}: {e}")




def add_similar_artists(similar_artists:set, artists:list, artists_set:set, cur):
    """
Add and insert similar artists into the database if they do not already exist.

This function iterates over a list of similar artist names, normalizes them, fetches
additional artist data via the API, calculates derived metrics, prepares database rows,
inserts the artist into the artists table, and updates the similar_artists relationships.

Args:
    similar_artists (set): set of artist names considered similar to a main artist.
    artists (list): List of already processed/inserted artist names to avoid duplicates.
    artists_set (set): Set of normalized artist names for foreign key checking.
    cur: Database cursor

Side Effects:
    - Fetches artist data from an external API.
    - Inserts data into the artists and similar_artists tables via the `cur` cursor.
    - Updates the `artists` list and `artists_set` with newly added artists.
"""
    for similar_artist in similar_artists:
        normalized_similar_artist = normalize_str(similar_artist)
        if normalized_similar_artist not in artists_set:
            artist_data={}
            artist_data['artist']={}
            artist_data['artist']['stats']={}
            artist_id_dict = load_artist_ids(artist_id_filepath)
            data=get_artist_data(artist_data, normalized_similar_artist, artist_id_dict, artist_id_filepath )
            if not data:
                continue
            stats_data = data.get('artist',{}).get('stats',{})
            listeners= max(int(stats_data.get('artist_total_listeners',1)),1)
            plays_per_listener= round(int(stats_data.get('artist_total_playcount'))/listeners,5)
            
            artist_row =[value for value in flatten(data).values()]
            similar_artists_list=[artist_row[-1], artist_row[-2],artist_row[-3],artist_row[-4],artist_row[-5]]
            
            artist_row = [artist_row[2], normalized_similar_artist, artist_row[4], artist_row[3], artist_row[1], artist_row[0], plays_per_listener] 
            try:
                cur.execute(insert_artist_query, artist_row)
                # Update artists_set immediately after successful insert
                artists_set.add(normalized_similar_artist)
                # Now insert similar artist relationships
                insert_similar_artists(similar_artists_list, normalized_similar_artist, artists_set, cur, insert_similar_artist_query)
                artists.append(normalized_similar_artist)
            except Exception as e:
                logging.error(f"Failed to insert artist '{normalized_similar_artist}': {e}")
                continue
        else:
            continue



# -------------------------------
# Main Function
# -------------------------------
if __name__ == '__main__':
    fetch_interval = 3600  # Fetch similar artists hourly (1 hour)
    
    logging.info("Starting continuous similar artists fetch process")
    logging.info(f"Will fetch similar artists hourly (every {fetch_interval/3600} hour)")
    
    while True:
        conn, cur = None, None
        try:
            logging.info("Fetching similar artists from database...")
            conn, cur = get_db()
            similar_artists, artists, artists_set = generate_artists_lists(cur)
            
            if not similar_artists:
                logging.info("No similar artists found to process")
            else:
                logging.info(f"Processing {len(similar_artists)} similar artists...")
                add_similar_artists(similar_artists, artists, artists_set, cur)
                logging.info("Similar artists processing complete")
            
            cur.close()
            conn.close()
            
            logging.info(f"Waiting {fetch_interval/3600} hour until next fetch...")
            time.sleep(fetch_interval)
            
        except KeyboardInterrupt:
            logging.info("Shutting down similar artists fetch process...")
            if cur:
                cur.close()
            if conn:
                conn.close()
            break
        except Exception as e:
            logging.error(f"Error in similar artists fetch: {e}", exc_info=True)
            if cur:
                cur.close()
            if conn:
                conn.close()
            logging.info("Retrying in 60 seconds...")
            time.sleep(60)
