"""
PLATO Room: modelexperiment
Tile: **2. Generated Code & Comparison**
Domain: modelexperiment
"""

import re

def validate_email(email: str) -> tuple[bool, str]:
    """
    Validates an email address format.
    Returns (is_valid: bool, reason: str).
    """
    if not email or not isinstance(email, str):
        return False, "Email must be a non-empty string."
    
    # Basic length check
    if len(email) > 254:
        return False, "Email exceeds maximum length (254 chars)."
    
    # RFC 5322 simplified regex (common practice)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(pattern, email):
        return True, "Email format is valid."
    else:
        return False, "Email format is invalid."

import re

def validate_email(email):
    """
    Validate an email address.
    Returns a tuple (bool, str) where bool indicates validity and str provides a reason.
    """
    if not isinstance(email, str):
        return False, "Input must be a string"
    
    email = email.strip()
    if len(email) == 0:
        return False, "Email cannot be empty"
    
    # Regular expression for basic email validation
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(regex, email):
        return True, "Valid email address"
    else:
        return False, "Invalid email format"

from typing import Dict, Any

def merge_dicts_safe(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges multiple dictionaries, handling key conflicts by appending
    numerical suffixes (_1, _2, etc.) to duplicate keys.
    """
    result = {}
    key_count = {}
    
    for d in dicts:
        if not isinstance(d, dict):
            continue  # skip non-dict args
        for key, value in d.items():
            if key not in result:
                result[key] = value
                key_count[key] = 1
            else:
                new_key = f"{key}_{key_count[key]}"
                key_count[key] += 1
                result[new_key] = value
    return result

