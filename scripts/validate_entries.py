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

    # Validate Auth value
    if auth not in VALID_AUTH_VALUES:
        errors.append(
            f'Line {line_number}: Invalid Auth value "{auth}". '
            f'Must be one of: {sorted(VALID_AUTH_VALUES)}'
        )

    # Validate HTTPS value
    if https not in VALID_HTTPS_VALUES:
        errors.append(
            f'Line {line_number}: Invalid HTTPS value "{https}". '
            f'Must be one of: {sorted(VALID_HTTPS_VALUES)}'
        )

    # Validate CORS value
    if cors not in VALID_CORS_VALUES:
        errors.append(
            f'Line {line_number}: Invalid CORS value "{cors}". '
            f'Must be one of: {sorted(VALID_CORS_VALUES)}'
        )

    return errors


def validate_entries(readme_path: str = 'README.md') -> bool:
    """Validate all API entries in the README file.

    Args:
        readme_path: Path to the README.md file.

    Returns:
        True if all entries are valid, False otherwise.
    """
    path = Path(readme_path)
    if not path.exists():
        print(f'Error: File not found: {readme_path}')
        return False

    content = path.read_text(encoding='utf-8')
    lines = content.splitlines()

    all_errors = []
    in_table = False
    header_seen = False

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Detect table header separator (marks start of data rows)
        if TABLE_SEPARATOR_PATTERN.match(stripped):
            in_table = True
            header_seen = True
            continue

        # Detect category headers — reset table state
        if CATEGORY_HEADER_PATTERN.match(stripped):
            in_table = False
            header_seen = False
            continue

        # Skip non-table lines
        if not stripped.startswith('|'):
            in_table = False
            continue

        # Skip the column header row itself
        if stripped.startswith('|') and not header_seen:
            continue

        # Validate data rows
        if in_table and header_seen:
            cells = parse_table_row(line)
            if cells:
                errors = validate_entry_row(cells, line_number)
                all_errors.extend(errors)

    if all_errors:
        print(f'Found {len(all_errors)} validation error(s):\n')
        for error in all_errors:
            print(f'  ✗ {error}')
        return False

    print('All entries are valid.')
    return True


if __name__ == '__main__':
    readme = sys.argv[1] if len(sys.argv) > 1 else 'README.md'
    success = validate_entries(readme)
    sys.exit(0 if success else 1)
