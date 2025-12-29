
import requests
import json
import os
from dotenv import load_dotenv
from src.utils.spotify_utils import extract_spotify_data, get_spotify_token
from src.utils.kafka_utils import create_producer, flush_kafka_producer, send_through_kafka
from src.utils.text_utils import get_words_list


load_dotenv()



def extract_main_spotify_data(general_queries):
    
    all_data=[]
    access_token=get_spotify_token()
    headers={
            'Authorization': f'Bearer {access_token}'
        }

    for query in general_queries:
        print(f"\n=== Processing query: {query} ===\n")

        offsets=[0,50,100,150,200, 250,300]
        for offset in offsets:
            try:
                resp = requests.get(f'https://api.spotify.com/v1/search?q={query}&type=track&limit=50&offset={offset}',headers=headers, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except ConnectionError as e:
                print(f"Connection error for query '{query}' offset {offset}")
                continue
            except requests.exceptions.Timeout:
                print(f"Timeout for query: {query}")
            except requests.exceptions.RequestException as e:
                 print(f"API error for query '{query}' offset {offset}: {e}")
                 continue
            except json.JSONDecodeError as e:
                print(f"JSON decode error for query '{query}' offset {offset}")
                continue

            
            data_list= extract_spotify_data(data)
            if data_list:
                all_data.extend(data_list)

            print(f"{len(data_list)} were added from offset {offset}")

    print(f"Total Tracks Extracted: {len(all_data)} ")
    return all_data
            


            
if __name__ == '__main__':

    producer=create_producer('music-streaming-producer')

    words_list= get_words_list()
    general_queries=  words_list[:20]
    data=extract_main_spotify_data(general_queries)

    for track in data:
        send_through_kafka(track, 'music_top_tracks', producer)
    
    flush_kafka_producer(producer)







        
            
            








            
            


            