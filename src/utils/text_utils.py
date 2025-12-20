import re
from difflib import SequenceMatcher


def normalize_song_name(name:str):
    """
    Normalize song name by removing extra formatting for comparison.
    
    Args:
        name (str): Song name to normalize
        
    Returns:
        str: Normalized song name in lowercase
    """
    if not name:
        return ""
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
    collaborators = []
    name_lower = name.lower()
    
    if '+' in name:
        parts = name.split('+')
        if len(parts) > 1:
            collaborators.extend([p.strip() for p in parts[1:]])
    
    feat_match = re.search(r'(?:feat\.?|ft\.?|featuring)\s*([^\(\)\[\]]+)', name_lower)
    if feat_match:
        collaborators.append(feat_match.group(1).strip())
    
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
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


