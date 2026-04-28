#!/usr/bin/env python3
"""Validate the format of the README.md API entries table.

This script checks that the README.md follows the expected markdown table
format, including proper headers, alphabetical ordering within categories,
and consistent column structure.
"""

import re
import sys
from pathlib import Path

# Expected table header format
TABLE_HEADER = "| API | Description | Auth | HTTPS | CORS |"
TABLE_SEPARATOR = "|---|---|---|---|---|"

# Valid values for specific columns
VALID_AUTH_VALUES = {"", "apiKey", "OAuth", "X-Mashape-Key", "User-Agent", "No"}
VALID_HTTPS_VALUES = {"Yes", "No"}
VALID_CORS_VALUES = {"Yes", "No", "Unknown"}

# Regex for a category header line like "### Category Name"
CATEGORY_HEADER_RE = re.compile(r"^### .+")

# Regex for a table row (starts and ends with |)
TABLE_ROW_RE = re.compile(r"^\|.+\|$")


def find_readme() -> Path:
    """Locate the README.md file relative to this script."""
    script_dir = Path(__file__).resolve().parent
    readme = script_dir.parent / "README.md"
    if not readme.exists():
        print(f"ERROR: README.md not found at {readme}", file=sys.stderr)
        sys.exit(1)
    return readme


def parse_readme(content: str) -> dict:
    """Parse README.md and return a dict mapping category names to their rows.

    Args:
        content: Full text of README.md

    Returns:
        A dict where keys are category names and values are lists of
        raw table data rows (excluding header and separator).
    """
    categories = {}
    current_category = None
    in_table = False

    for line in content.splitlines():
        line = line.strip()

        if CATEGORY_HEADER_RE.match(line):
            current_category = line.lstrip("# ").strip()
            categories[current_category] = []
            in_table = False
            continue

        if current_category is None:
            continue

        if line == TABLE_HEADER:
            in_table = True
            continue

        if in_table and line == TABLE_SEPARATOR:
            continue

        if in_table and TABLE_ROW_RE.match(line):
            categories[current_category].append(line)
        elif in_table and line == "":
            in_table = False

    return categories


def validate_alphabetical_order(category: str, rows: list) -> list:
    """Check that API entries within a category are in alphabetical order.

    Args:
        category: The category name (for error messages).
        rows: List of raw markdown table row strings.

    Returns:
        A list of error message strings (empty if no errors).
    """
    errors = []
    api_names = []

    for row in rows:
        cols = [c.strip() for c in row.split("|")[1:-1]]
        if not cols:
            continue
        # API name may be a markdown link like [Name](url)
        raw_name = cols[0]
        match = re.match(r"\[(.+?)\]", raw_name)
        name = match.group(1) if match else raw_name
        api_names.append(name)

    # Use case-insensitive sort to match how the README is maintained
    sorted_names = sorted(api_names, key=str.casefold)
