
import requests
import json
import time
import random
import logging
from dotenv import load_dotenv
from src.utils.http_utils import safe_requests
from src.utils.spotify_api_utils import extract_spotify_data, get_spotify_token
from src.utils.kafka_utils import create_producer, flush_kafka_producer, safe_batch_send
from src.utils.text_processing_utils import get_words_list

logger = logging.getLogger(__name__)



load_dotenv()



def extract_batch_spotify_data(general_queries):

    all_data=[]
    access_token=get_spotify_token()
    headers={
            'Authorization': f'Bearer {access_token}'
        }

    for query in general_queries:
        logger.info(f"=== Processing query: {query} ===")

        offsets=range(0,200, 50)
        for offset in offsets:
            url = f'https://api.spotify.com/v1/search?q={query}&type=track&limit=50&offset={offset}'


            resp = safe_requests('GET',url, headers=headers, max_retries=5, timeout=5 )

            if resp is None:
                logger.error(f"Failed to get data for query '{query}' offset {offset} after all retries")
                continue

            try:
                data = resp.json()
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for query '{query}' offset {offset}: {e}")
                continue

            data_list = extract_spotify_data(data)
            if data_list:
                all_data.extend(data_list)

            logger.debug(f"{len(data_list)} tracks added from offset {offset}")


            time.sleep(random.uniform(1.0, 3.0))


        time.sleep(random.uniform(5.0, 10.0))

    logger.info(f"Total tracks extracted: {len(all_data)}")
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
            logger.info(f"Processing batch {num//10+1}: words {num-10} to {num-10 + len(batch)}")
            data=extract_batch_spotify_data(words_list[num-10:num])

            # Use batch sending with error handling
            if data:
                successful, failed = safe_batch_send(data, 'music_top_tracks', producer, batch_size=5)
                logger.info(f"Batch results: {successful} successful, {failed} failed")


    flush_kafka_producer(producer)







        
            
            








            
            


            