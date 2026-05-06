"""
Shared utility functions for the Domain Intelligence App.
Includes domain validation, date parsing, retry logic, and text helpers.
"""

import re
import time
import random
import functools
from datetime import datetime, timezone
from typing import Optional

from utils.logger import get_logger

log = get_logger(__name__)

# ─────────────────────────────────────────────
# Domain Validation
# ─────────────────────────────────────────────
DOMAIN_REGEX = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.[A-Za-z0-9-]{1,63})*"
    r"\.[A-Za-z]{2,63}$"
)


def is_valid_domain(domain: str) -> bool:
    """Validate domain name format."""
    if not domain or len(domain) > 253:
        return False
    return bool(DOMAIN_REGEX.match(domain.strip().lower()))


def extract_tld(domain: str) -> str:
    """Extract TLD from domain name (e.g., 'example.com' → '.com')."""
    domain = domain.strip().lower()
    parts = domain.split(".")
    if len(parts) >= 2:
        return f".{parts[-1]}"
    return ""


def extract_sld(domain: str) -> str:
    """Extract second-level domain (e.g., 'example.com' → 'example')."""
    domain = domain.strip().lower()
    parts = domain.split(".")
    if len(parts) >= 2:
        return parts[-2]
    return domain


# ─────────────────────────────────────────────
# Date Utilities
# ─────────────────────────────────────────────
DATE_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d-%b-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
]


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string into datetime object.
    Tries multiple common formats.
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    log.warning(f"Could not parse date: {date_str}")
    return None


def days_until_expiry(expiry_date: datetime) -> int:
    """Calculate days from now until expiry date."""
    now = datetime.now(timezone.utc)
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    delta = expiry_date - now
    return max(0, delta.days)


def classify_expiry_window(days: int) -> str:
    """Classify domain into expiry window category."""
    if days <= 1:
        return "1 Day"
    elif days <= 7:
        return "7 Days"
    elif days <= 30:
        return "30 Days"
    return "30+ Days"


# ─────────────────────────────────────────────
# Retry Decorator with Exponential Backoff
# ─────────────────────────────────────────────
def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """
    Decorator for retrying a function with exponential backoff + jitter.
    
    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        exceptions: Tuple of exception types to catch.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        log.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.3)
                    sleep_time = delay + jitter
                    log.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {sleep_time:.1f}s..."
                    )
                    time.sleep(sleep_time)
            return None
        return wrapper
    return decorator


# ─────────────────────────────────────────────
# Text Utilities
# ─────────────────────────────────────────────
VOWELS = set("aeiou")
CONSONANTS = set("bcdfghjklmnpqrstvwxyz")


def vowel_ratio(text: str) -> float:
    """Calculate ratio of vowels in text (0.0–1.0)."""
    text = text.lower()
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    vowel_count = sum(1 for c in letters if c in VOWELS)
    return vowel_count / len(letters)


def has_consecutive_consonants(text: str, threshold: int = 4) -> bool:
    """Check if text has awkward consecutive consonant clusters."""
    text = text.lower()
    count = 0
    for c in text:
        if c in CONSONANTS:
            count += 1
            if count >= threshold:
                return True
        else:
            count = 0
    return False


def estimate_syllables(word: str) -> int:
    """Estimate number of syllables in a word (heuristic)."""
    word = word.lower().strip()
    if not word:
        return 0

    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in VOWELS
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    # Adjust for silent 'e'
    if word.endswith("e") and count > 1:
        count -= 1

    return max(1, count)


def clean_domain_name(domain: str) -> str:
    """Normalize domain name to lowercase, stripped."""
    return domain.strip().lower().replace(" ", "")
