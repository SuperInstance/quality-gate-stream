"""
PLATO Room: modelexperiment
Tile: **2. Prompt & Generated Code**
Domain: modelexperiment
"""

import re
from typing import List, Tuple

def clean_and_validate_email_list(email_list: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validates a list of email addresses, returning separate lists for valid and invalid entries.
    Strips whitespace from each entry before validation.

    Args:
        email_list: A list of strings representing potential email addresses.

    Returns:
        A tuple containing:
            - List of valid email addresses (strings).
            - List of invalid entries (strings).
    """
    # RFC 5322 compliant regex (simplified practical version)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    valid_emails = []
    invalid_entries = []

    for entry in email_list:
        if not isinstance(entry, str):
            invalid_entries.append(str(entry))
            continue

        cleaned = entry.strip()
        if not cleaned:  # Handle empty strings after stripping
            invalid_entries.append(entry)
            continue

        if re.match(pattern, cleaned):
            valid_emails.append(cleaned)
        else:
            invalid_entries.append(entry)

    return valid_emails, invalid_entries

from typing import List, Tuple
import re

def clean_and_validate_email_list(email_list: List[str]) -> Tuple[List[str], List[str]]:
    """
    Separates valid and invalid email addresses from a list.

    Parameters:
    email_list (List[str]): Input list of email address strings.

    Returns:
    Tuple[List[str], List[str]]: Two lists: valid emails, invalid entries.
    """
    valid = []
    invalid = []

    # Email validation regex pattern
    email_regex = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

    for email in email_list:
        # Check if input is string
        if not isinstance(email, str):
            invalid.append(str(email))
            continue

        # Strip whitespace
        email_clean = email.strip()

        # Check for empty string after strip
        if email_clean == '':
            invalid.append(email)
            continue

        # Validate with regex
        if email_regex.match(email_clean):
            valid.append(email_clean)
        else:
            invalid.append(email)

    return valid, invalid

