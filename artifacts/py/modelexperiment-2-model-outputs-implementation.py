"""
PLATO Room: modelexperiment
Tile: **2. Model Outputs & Implementation**
Domain: modelexperiment
"""

import re
from typing import List, Tuple

def clean_and_validate_email_list(email_list: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validates a list of email addresses, deduplicates valid ones, and categorizes them.

    Args:
        email_list: A list of email address strings.

    Returns:
        A tuple containing:
        - List of unique, lowercased valid email addresses.
        - List of invalid email addresses.
    """
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    email_regex = re.compile(pattern)

    valid_set = set()
    invalid_emails = []

    for email in email_list:
        if not isinstance(email, str):
            invalid_emails.append(str(email))
            continue

        email = email.strip()
        if email_regex.match(email):
            # Normalize to lowercase for deduplication
            valid_set.add(email.lower())
        else:
            invalid_emails.append(email)

    valid_emails = list(valid_set)
    return valid_emails, invalid_emails

import re
from typing import List, Tuple

def clean_and_validate_email_list(email_list: List[str]) -> Tuple[List[str], List[str]]:
    """
    Clean and validate a list of email addresses.

    Parameters:
    email_list (List[str]): List of email addresses.

    Returns:
    Tuple[List[str], List[str]]: A tuple containing:
        - List of valid, unique email addresses (lowercased).
        - List of invalid email addresses.
    """
    if not email_list:
        return [], []

    # Regular expression for basic email validation
    email_pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

    valid_emails_set = set()
    invalid_emails = []

    for email in email_list:
        # Ensure it's a string
        if not isinstance(email, str):
            invalid_emails.append(str(email))
            continue

        email = email.strip()

        # Check if email matches pattern
        if email_pattern.match(email):
            valid_emails_set.add(email.lower())
        else:
            invalid_emails.append(email)

    # Convert set to list for output
    valid_emails = list(valid_emails_set)

    return valid_emails, invalid_emails

