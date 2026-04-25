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
DEFAULT_TIMEOUT = 10  # seconds
RETRY_DELAY = 2  # seconds between retries
MAX_RETRIES = 2

# HTTP status codes considered as valid
VALID_STATUS_CODES = {200, 201, 204, 301, 302, 307, 308}

# Known URLs to skip validation (e.g., require auth or block bots)
SKIP_URLS = {
    "https://www.linkedin.com",
    "https://twitter.com",
    "https://x.com",
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
    """Validate all links in the given file.

    Returns:
        Number of broken links found.
    """
    urls = extract_urls(filepath)
    print(f"Found {len(urls)} unique URLs in '{filepath}'")

    broken = []
    for i, url in enumerate(urls, 1):
        if should_skip(url):
            if verbose:
                print(f"  [{i}/{len(urls)}] SKIP  {url}")
            continue

        is_valid, status_code, error = check_url(url)
        status_label = str(status_code) if status_code else "N/A"

        if is_valid:
            if verbose:
                print(f"  [{i}/{len(urls)}] OK    ({status_label}) {url}")
        else:
            print(f"  [{i}/{len(urls)}] FAIL  ({status_label}) {url} — {error}")
            broken.append((url, status_label, error))

    print(f"\nResults: {len(urls)} checked, {len(broken)} broken")
    if broken:
        print("\nBroken links:")
        for url, code, err in broken:
            print(f"  [{code}] {url} — {err}")
    return len(broken)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate links in README.md")
    parser.add_argument(
        "--file",
        default=README_PATH,
        help="Path to the markdown file to validate (default: README.md)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show status for all URLs, not just broken ones",
    )
    args = parser.parse_args()

    broken_count = validate_links(args.file, verbose=args.verbose)
    sys.exit(1 if broken_count > 0 else 0)


if __name__ == "__main__":
    main()
