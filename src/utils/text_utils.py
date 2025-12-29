import re
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
import time
import requests

def normalize_song_name(name):
    """
    Normalize song name by removing extra formatting for comparison.
    
    Args:
        name (str): Song name to normalize
        
    Returns:
        str: Normalized song name in lowercase
    """
    if type(name) is not str:
        raise TypeError(f'song name must be a string but it is {type(name)}')
    base_name = name.replace('&', 'and')
    base_name = base_name.replace('feat.', 'featuring')
    base_name = base_name.replace('ft.', 'featuring')
    base_name = re.sub(r'\s*\([^)]*\)', '', base_name)
    base_name = re.sub(r'\s*\[[^\]]*\]', '', base_name)
    base_name = re.sub(r'\s*feat\.?\s*.*$', '', base_name, flags=re.IGNORECASE)
    base_name = re.sub(r'\s+\b(?:ft|feat)\.?\s*.*$', '', base_name, flags=re.IGNORECASE)
    base_name = re.sub(r'\s*\+\s*.*$', '', base_name)
    return base_name.strip().lower()

def has_collaborators(name):
    """
    Check if a song name contains collaborator indicators.
    
    Args:
        name (str): Song name to check
        
    Returns:
        bool: True if song has collaborators, False otherwise
    """
    if type(name) is not str:
        raise TypeError(f'song name must be a string but it is {type(name)}')

    name_lower = name.lower()
    return ('+' in name_lower or 
            'feat' in name_lower or 
            'ft.' in name_lower or
            'featuring' in name_lower)

def extract_collaborators(name):
    """
    Extract featured artists or collaborators from song name.
    
    Args:
        name (str): Song name to parse
        
    Returns:
        list: List of collaborator names found in the song name
    """

    if type(name) is not str:
        raise TypeError(f'The input should be a string but it is a(n) {type(name)}')
    
    collaborators = []
    name_lower = name.lower()
    
    if '+' in name:
        parts = name.split('+')
        if len(parts) > 1:
            collaborators.extend([p.strip() for p in parts[1:]])
    
    feat_match = re.search(r'(?:featuring|feat\.?|ft\.?)\s*([^\(\)\[\]]+)', name_lower)
    if feat_match:
        feat_text= feat_match.group(1).strip()
        collaborators.extend([col.strip() for col in feat_text.split(',') if col.strip()])
    
    return collaborators

def similarity_score(str1, str2):
    """
    Calculate similarity score between two strings.
    
    Args:
        str1 (str): First string
        str2 (str): Second string
        
    Returns:
        float: Similarity score between 0 and 1
    """
    if type(str1) is not str:
        raise TypeError(f'{str1} is not a string, rather it is a(n) {type(str1)} ')
    if type(str2) is not str:
        raise TypeError(f'{str2} is not a string, rather it is a(n) {type(str2)} ')
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def get_words_list():
    try:
        words_list=[]
        resp= requests.get('https://www.ef.edu/english-resources/english-vocabulary/top-3000-words/')
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        divs = soup.find('div', class_= 'field-item even')
        words= divs.find('p')
        for word in words:
            print(word.text.lower().strip())
            if word.text.lower().strip() not in words_list and word.text.lower().strip() != '':
                words_list.append(word.text.lower().strip())
        return words_list
    except requests.RequestException as e:
        print(f'There was an error fetching the words list: {e}')
        return None






