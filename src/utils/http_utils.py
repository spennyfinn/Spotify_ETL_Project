import time
import requests
import logging


logger = logging.getLogger(__name__)

def safe_requests(method, url, max_retries=3, backoff=1.0, **kwargs):
    last_exception = None
    for attempt in range(1, max_retries+1):
        try: 
            resp = requests.request(method, url,timeout = kwargs.pop('timeout',5), **kwargs )
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.warning("HTTP %s to %s failed (attempt %d/%d): %s",
                           method.upper(), url, attempt, max_retries, e)
            last_exception = e
            if attempt < max_retries:
                time.sleep(backoff*(2**(attempt-1)))
    logger.error("All retries failed for %s %s", method.upper(), url)
    if last_exception:
        raise last_exception
            
    