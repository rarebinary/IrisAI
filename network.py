"""
network.py — HTTP client with timeouts, retry, and logging.
Replaces all bare `requests.*` calls across the codebase.
"""

import logging
import requests
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]  # seconds between retries


class NetworkError(RuntimeError):
    """Raised when all retries are exhausted."""
    pass


def make_request(
    method: str,
    url: str,
    timeout: Optional[float] = None,
    max_retries: Optional[int] = None,
    **kwargs: Any,
) -> requests.Response:
    """
    Make an HTTP request with timeout, retry with exponential backoff, and logging.

    Args:
        method: HTTP method (get, post, etc.)
        url: Request URL
        timeout: Request timeout in seconds (default: DEFAULT_TIMEOUT)
        max_retries: Number of retries (default: MAX_RETRIES)
        **kwargs: Passed to requests.request()

    Returns:
        requests.Response

    Raises:
        NetworkError: If all retries are exhausted
    """
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    max_retries = max_retries if max_retries is not None else MAX_RETRIES
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            return response
        except requests.Timeout:
            logger.warning(f"Timeout on {method.upper()} {url} (attempt {attempt}/{max_retries})")
            last_exception = TimeoutError(f"Request timed out after {timeout}s: {method.upper()} {url}")
        except requests.ConnectionError as e:
            logger.warning(f"Connection error on {method.upper()} {url} (attempt {attempt}/{max_retries}): {e}")
            last_exception = e
        except Exception as e:
            logger.error(f"Unexpected error on {method.upper()} {url} (attempt {attempt}/{max_retries}): {e}")
            last_exception = e

        if attempt < max_retries:
            backoff = RETRY_BACKOFF[min(attempt - 1, len(RETRY_BACKOFF) - 1)]
            logger.info(f"Retrying in {backoff}s...")
            time.sleep(backoff)

    raise NetworkError(f"Request failed after {max_retries} retries: {method.upper()} {url}") from last_exception


def get(url: str, timeout: Optional[float] = None, max_retries: Optional[int] = None, **kwargs: Any) -> requests.Response:
    """HTTP GET with timeout and retry."""
    return make_request("GET", url, timeout=timeout, max_retries=max_retries, **kwargs)


def post(url: str, timeout: Optional[float] = None, max_retries: Optional[int] = None, **kwargs: Any) -> requests.Response:
    """HTTP POST with timeout and retry."""
    return make_request("POST", url, timeout=timeout, max_retries=max_retries, **kwargs)
