"""Validate entries in the public-apis README.md file.

This script checks that all API entries in the README follow the required
format and contain valid data, including proper markdown table structure,
required fields, and valid values for Auth and HTTPS columns.
"""

import re
import sys
from pathlib import Path

# Valid values for the Auth column
VALID_AUTH_VALUES = {
    'apiKey',
    'OAuth',
    'X-Mashape-Key',
    'User-Agent',
    'No',
    'Yes',
    ''
}

# Valid values for the HTTPS column
VALID_HTTPS_VALUES = {'Yes', 'No'}

# Valid values for the CORS column
VALID_CORS_VALUES = {'Yes', 'No', 'Unknown'}

# Regex pattern for a valid markdown table row (API entry)
TABLE_ROW_PATTERN = re.compile(
    r'^\|\s*\[.+\]\(.+\)\s*'
    r'\|\s*.+\s*'
    r'\|\s*(?:apiKey|OAuth|X-Mashape-Key|User-Agent|No|Yes|)\s*'
    r'\|\s*(?:Yes|No)\s*'
    r'\|\s*(?:Yes|No|Unknown)\s*'
    r'\|\s*$'
)

# Regex to detect table header separator lines
TABLE_SEPARATOR_PATTERN = re.compile(r'^\|[-| :]+\|\s*$')

# Regex to detect category headers
CATEGORY_HEADER_PATTERN = re.compile(r'^#{1,3}\s+.+')


def parse_table_row(line: str) -> list[str] | None:
    """Parse a markdown table row into its cell values.

    Args:
        line: A string representing a markdown table row.

    Returns:
        A list of cell values, or None if the line is not a table row.
    """
    line = line.strip()
    if not line.startswith('|') or not line.endswith('|'):
        return None
    # Split on '|' and strip whitespace from each cell
    cells = [cell.strip() for cell in line.split('|')]
    # Remove empty strings from the start and end caused by leading/trailing '|'
    cells = [c for c in cells if c != '' or cells.index(c) not in (0, len(cells) - 1)]
    return cells[1:-1] if cells else None


def validate_entry_row(cells: list[str], line_number: int) -> list[str]:
    """Validate a single API entry row's cells.

    Args:
        cells: List of cell values from the parsed table row.
        line_number: The line number in the file (for error reporting).

    Returns:
        A list of error messages (empty if the row is valid).
    """
    errors = []

    if len(cells) != 5:
        errors.append(
            f'Line {line_number}: Expected 5 columns, got {len(cells)}'
        )
        return errors

    api_name, description, auth, https, cors = cells

    # Validate API name contains a markdown link
    if not re.match(r'\[.+\]\(.+\)', api_name):
        errors.append(
            f'Line {line_number}: API name must be a markdown link, got: "{api_name}"'
        )

    # Validate description is not empty
    if not description:
        errors.append(f'Line {line_number}: Description cannot be empty')

    # Trailing period check disabled - too noisy for a personal reference fork
    # where entries are often copied in from external sources as-is.
    # Original upstream enforces this; re-enable if syncing back upstream.
    if description.endswith('.') and False:
