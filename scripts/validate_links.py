#!/usr/bin/env python3
"""Script to validate links in the README.md file.

This script checks all URLs found in the README.md to ensure they are
accessible and return valid HTTP status codes.
"""

import re
import sys
import time
import argparse
from typing import Optional

import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects


README_PATH = "README.md"
URL_PATTERN = re.compile(r'https?://[^\s\)\]\>"]+', re.IGNORECASE)
DEFAULT_TIMEOUT = 15  # seconds - increased from 10 to reduce false positives on slow APIs
RETRY_DELAY = 2  # seconds between retries
MAX_RETRIES = 2

# HTTP status codes considered as valid
VALID_STATUS_CODES = {200, 201, 204, 301, 302, 307, 308}

# Known URLs to skip validation (e.g., require auth or block bots)
SKIP_URLS = {
    "https://www.linkedin.com",
    "https://twitter.com",
    "https://x.com",
    "https://www.facebook.com",  # also blocks bots consistently
}


def extract_urls(filepath: str) -> list[str]:
    """Extract all URLs from a markdown file."""
    urls = []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    matches = URL_PATTERN.findall(content)
    # Deduplicate while preserving order
    seen = set()
    for url in matches:
        # Strip trailing punctuation that may have been captured
        url = url.rstrip(".,;:!?'\"")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def should_skip(url: str) -> bool:
    """Determine if a URL should be skipped during validation."""
    return any(url.startswith(skip) for skip in SKIP_URLS)


def check_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[bool, Optional[int], str]:
    """Check if a URL is accessible.

    Returns:
        Tuple of (is_valid, status_code, error_message)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; public-apis-link-checker/1.0)"
    }
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.head(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
            )
            if response.status_code == 405:
                # HEAD not allowed, fall back to GET
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=True,
                    stream=True,
                )
            if response.status_code in VALID_STATUS_CODES:
                return True, response.status_code, ""
            return False, response.status_code, f"HTTP {response.status_code}"
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return False, None, str(e)
        except Exception as e:  # noqa: BLE001
            return False, None, f"Unexpected error: {e}"
    return False, None, "Max retries exceeded"


def validate_links(filepath: str, verbose: bool = False) -> int:
    """Validate
