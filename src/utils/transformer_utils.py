

import logging

logger = logging.getLogger(__name__)

def safe_int(value, default=None):
    '''Safely convert to int'''
    if not value or value=='':
        return default
    try:
        return int(float(value))
    except(ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    '''Safely convert to float'''
    if not value or value =='':
        return default
    try:
        return float(value)
    except(ValueError, TypeError):
        return default

def safe_string(value, default=None, lowercase=False):
    '''Safely convert to string'''
    if not value:
        return None
    if isinstance(value, str):
        stripped= value.strip()
        if not stripped:
            return default
        result = stripped.lower() if lowercase else stripped
        return result
    try:
        result = str(value).strip()
        if not result:
            return default
        return result.lower() if lowercase else result
    except Exception:
        return default


def determine_missing_fields(data):
    missing = [k for k,v in data.items() if v is None]
    if missing:
        logger.debug(f'Missing fields: {', '.join(missing)}')
        return
    logger.debug('No missing fields')