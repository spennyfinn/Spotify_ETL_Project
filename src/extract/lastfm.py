import requests
import os
import json

from src.utils.database import get_db
from dotenv import load_dotenv





if __name__ == '__main__':
    load_dotenv()
    conn, cur=get_db()

    cur.execute('SELECT s.song_name, a.artist_name FROM songs AS s JOIN artists AS a ON s.artist_id=a.artist_id WHERE s.engagement_ratio IS NULL')
    res=cur.fetchall()
    print(res)
