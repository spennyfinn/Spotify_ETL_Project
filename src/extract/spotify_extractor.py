
import requests
import json
import time
import random
from dotenv import load_dotenv
from src.utils.spotify_utils import extract_spotify_data, get_spotify_token
from src.utils.kafka_utils import create_producer, flush_kafka_producer, safe_batch_send
from src.utils.text_utils import get_words_list


def make_spotify_request_with_backoff(url, headers, max_retries=5, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                # Rate limited - check for Retry-After header first
                retry_after = e.response.headers.get('Retry-After')
                if retry_after:
                    try:
                        wait_time = int(retry_after)
                        print(f"Rate limited. API suggests waiting {wait_time} seconds (from Retry-After header).")
                    except (ValueError, TypeError):
                        wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.1f} seconds...")
                else:
                    # Fallback to exponential backoff if no Retry-After header
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Rate limited (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.1f} seconds...")

                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Max retries exceeded for rate limiting: {url}")
                    return None
            else:
                # Other HTTP errors - don't retry
                print(f"API error for {url}: {e}")
                return None

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            if attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Connection/timeout error (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                continue
            else:
                print(f"Max retries exceeded for connection error: {url}")
                return None

    return None


load_dotenv()



def extract_batch_spotify_data(general_queries):

    all_data=[]
    access_token=get_spotify_token()
    headers={
            'Authorization': f'Bearer {access_token}'
        }

    for query in general_queries:
        print(f"\n=== Processing query: {query} ===\n")

        offsets=range(0,200, 50) 
        for offset in offsets:
            url = f'https://api.spotify.com/v1/search?q={query}&type=track&limit=50&offset={offset}'

 
            resp = make_spotify_request_with_backoff(url, headers, max_retries=5, base_delay=2.0)

            if resp is None:
                print(f"Failed to get data for query '{query}' offset {offset} after all retries")
                continue

            try:
                data = resp.json()
            except json.JSONDecodeError as e:
                print(f"JSON decode error for query '{query}' offset {offset}: {e}")
                continue

            data_list = extract_spotify_data(data)
            if data_list:
                all_data.extend(data_list)

            print(f"{len(data_list)} tracks added from offset {offset}")

          
            time.sleep(random.uniform(1.0, 3.0))
        
      
        time.sleep(random.uniform(5.0, 10.0))

    print(f"Total Tracks Extracted: {len(all_data)} ")
    return all_data
            


            
if __name__ == '__main__':

    producer=create_producer('music-streaming-producer')
    batch_size=5  

    words_list= get_words_list()
    if words_list:
        for num in range(1420,len(words_list), batch_size):
            batch= words_list[num-10:num]
            if len(batch)>batch_size:
                batch= batch[:batch_size]
            print(f"Processing the batch {num//10+1}: words {num-10} to {num-10 + len(batch)}")
            data=extract_batch_spotify_data(words_list[num-10:num])

            # Use batch sending with error handling
            if data:
                successful, failed = safe_batch_send(data, 'music_top_tracks', producer, batch_size=5)
                print(f"Batch results: {successful} successful, {failed} failed")


    flush_kafka_producer(producer)







        
            
            








            
            


            