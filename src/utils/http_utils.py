import logging
import time

import requests

logger = logging.getLogger(__name__)


def _retry_after_seconds(response: requests.Response, backoff: float, attempt: int) -> float:
    """Seconds to wait before retrying; honors Spotify ``Retry-After`` when present."""
    retry_after = response.headers.get("Retry-After")
    if retry_after is not None:
        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            pass
    return backoff * (2 ** (attempt - 1))


def safe_requests(
    method,
    url,
    max_retries=3,
    backoff=1.0,
    rate_limit_max_retries=5,
    **kwargs,
):
    """HTTP request with retries on failure and dedicated 429 exponential backoff.

    On HTTP 429, retries up to ``rate_limit_max_retries`` times (exponential
    ``backoff``, or ``Retry-After`` when the server sends it) without consuming
    the generic ``max_retries`` budget. Other errors use ``max_retries`` with
    the same backoff pattern.
    """
    timeout = kwargs.pop("timeout", 5)
    last_exception = None
    rate_limit_attempts = 0

    for attempt in range(1, max_retries + 1):
        try:
            while True:
                resp = requests.request(method, url, timeout=timeout, **kwargs)

                if resp.status_code == 429:
                    rate_limit_attempts += 1
                    if rate_limit_attempts > rate_limit_max_retries:
                        logger.error(
                            "Rate limited (429) on %s %s after %d retries",
                            method.upper(),
                            url,
                            rate_limit_max_retries,
                        )
                        resp.raise_for_status()

                    wait = _retry_after_seconds(resp, backoff, rate_limit_attempts)
                    logger.warning(
                        "Rate limited (429) on %s %s (retry %d/%d), sleeping %.1fs",
                        method.upper(),
                        url,
                        rate_limit_attempts,
                        rate_limit_max_retries,
                        wait,
                    )
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp

        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                raise
            logger.warning(
                "HTTP %s to %s failed (attempt %d/%d): %s",
                method.upper(),
                url,
                attempt,
                max_retries,
                e,
            )
            last_exception = e
            if attempt < max_retries:
                time.sleep(backoff * (2 ** (attempt - 1)))
        except requests.RequestException as e:
            logger.warning(
                "HTTP %s to %s failed (attempt %d/%d): %s",
                method.upper(),
                url,
                attempt,
                max_retries,
                e,
            )
            last_exception = e
            if attempt < max_retries:
                time.sleep(backoff * (2 ** (attempt - 1)))

    logger.error("All retries failed for %s %s", method.upper(), url)
    if last_exception:
        raise last_exception
