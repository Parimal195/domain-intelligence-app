"""
Seed Data Generator for the Domain Intelligence App.

Generates a realistic dataset of expiring domains across multiple TLDs
with varied naming patterns (brandable, keyword-rich, short, compound).
Used for demo/testing and as a fallback when live sources are unavailable.
"""

import random
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict

from utils.config import SEED_DOMAIN_COUNT, DATA_DIR, PREMIUM_KEYWORDS
from utils.logger import get_logger

log = get_logger(__name__)

# ─────────────────────────────────────────────
# Domain Name Components
# ─────────────────────────────────────────────
PREFIXES = [
    "next", "neo", "hyper", "ultra", "meta", "super", "omni", "flux",
    "nova", "vibe", "apex", "zeno", "lux", "aero", "byte", "digi",
    "turbo", "swift", "pulse", "prime", "zen", "axis", "arc", "ion",
    "pixel", "quantum", "stellar", "fusion", "vertex", "spark",
    "orbit", "blaze", "drift", "echo", "halo", "helix", "neon",
]

SUFFIXES = [
    "hub", "lab", "io", "ly", "ify", "ware", "base", "stack",
    "flow", "sync", "dash", "net", "link", "zone", "box", "pad",
    "spot", "dock", "port", "deck", "forge", "mind", "works",
    "edge", "core", "vault", "nest", "wave", "grid", "pulse",
    "shift", "scope", "craft", "path", "field", "space",
]

WORDS = [
    "cloud", "data", "code", "trade", "pay", "health", "game",
    "stream", "learn", "shop", "build", "grow", "track", "scan",
    "send", "find", "meet", "chat", "book", "hire", "sell",
    "fund", "ship", "farm", "mine", "cook", "ride", "care",
    "plan", "vote", "test", "sign", "clip", "snap", "draw",
    "talk", "host", "rent", "gift", "feed", "lock", "mint",
]

TLDS = [
    (".com", 0.35),   # 35% chance
    (".io", 0.15),
    (".ai", 0.08),
    (".co", 0.10),
    (".net", 0.08),
    (".org", 0.05),
    (".dev", 0.05),
    (".app", 0.04),
    (".xyz", 0.03),
    (".tech", 0.03),
    (".me", 0.02),
    (".gg", 0.02),
]

COUNTRIES = ["US", "UK", "CA", "IN", "DE", "AU", "Unknown"]


def _weighted_tld() -> str:
    """Pick a TLD based on weighted distribution."""
    tlds, weights = zip(*TLDS)
    return random.choices(tlds, weights=weights, k=1)[0]


def _generate_brandable_name() -> str:
    """Generate a brandable-sounding domain name."""
    pattern = random.choice([
        lambda: random.choice(PREFIXES) + random.choice(SUFFIXES),
        lambda: random.choice(PREFIXES) + random.choice(WORDS),
        lambda: random.choice(WORDS) + random.choice(SUFFIXES),
        lambda: random.choice(PREFIXES),
        lambda: random.choice(WORDS) + random.choice(WORDS),
    ])
    return pattern()


def _generate_keyword_name() -> str:
    """Generate a keyword-rich domain name."""
    kw = random.choice(PREMIUM_KEYWORDS)
    pattern = random.choice([
        lambda: kw + random.choice(SUFFIXES),
        lambda: random.choice(PREFIXES) + kw,
        lambda: kw + random.choice(WORDS),
        lambda: "get" + kw,
        lambda: "my" + kw,
        lambda: kw + "pro",
        lambda: kw + "ai",
        lambda: kw + "app",
    ])
    return pattern()


def _generate_short_name() -> str:
    """Generate a short (3-5 char) domain name."""
    length = random.randint(3, 5)
    vowels = "aeiou"
    consonants = "bcdfghjklmnprstvwxyz"
    name = ""
    for i in range(length):
        if i % 2 == 0:
            name += random.choice(consonants)
        else:
            name += random.choice(vowels)
    return name


def _generate_compound_name() -> str:
    """Generate a compound word domain."""
    return random.choice(WORDS) + random.choice(WORDS)


def generate_domain_name() -> str:
    """Generate a random domain name with TLD."""
    generator = random.choices(
        [_generate_brandable_name, _generate_keyword_name,
         _generate_short_name, _generate_compound_name],
        weights=[0.40, 0.30, 0.15, 0.15],
        k=1,
    )[0]

    name = generator()
    tld = _weighted_tld()

    # Clean: remove spaces, ensure lowercase
    name = name.lower().replace(" ", "").replace("-", "")

    # Ensure reasonable length
    if len(name) > 20:
        name = name[:20]

    return f"{name}{tld}"


def generate_expiry_date() -> str:
    """Generate a random expiry date within 1-35 day window."""
    now = datetime.now(timezone.utc)

    # Weighted toward sooner expiry
    window = random.choices(
        [
            (0, 1),     # Expiring today/tomorrow
            (1, 7),     # Expiring within a week
            (7, 30),    # Expiring within a month
            (30, 35),   # Just past 30 days
        ],
        weights=[0.15, 0.30, 0.40, 0.15],
        k=1,
    )[0]

    days_offset = random.randint(window[0], window[1])
    expiry = now + timedelta(days=days_offset, hours=random.randint(0, 23))
    return expiry.strftime("%Y-%m-%d %H:%M:%S")


def generate_seed_data(count: int = SEED_DOMAIN_COUNT) -> List[Dict]:
    """
    Generate a realistic seed dataset of expiring domains.
    
    Args:
        count: Number of domains to generate.
    
    Returns:
        List of domain records as dicts.
    """
    log.info(f"Generating {count} seed domains...")

    domains = set()
    records = []

    attempts = 0
    max_attempts = count * 3  # prevent infinite loop

    while len(records) < count and attempts < max_attempts:
        attempts += 1
        domain = generate_domain_name()

        # Skip duplicates
        if domain in domains:
            continue
        domains.add(domain)

        tld = "." + domain.split(".")[-1]
        sld = domain.split(".")[0]

        record = {
            "domain": domain,
            "expiry_date": generate_expiry_date(),
            "tld": tld,
            "sld": sld,
            "source": "seed",
            "country": random.choice(COUNTRIES),
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        }
        records.append(record)

    log.info(f"Generated {len(records)} seed domains successfully.")
    return records


def save_seed_data(records: List[Dict], filepath: Path = None) -> Path:
    """
    Save seed data to CSV file.
    
    Args:
        records: List of domain records.
        filepath: Optional output path. Defaults to data/domains.csv.
    
    Returns:
        Path to saved file.
    """
    if filepath is None:
        filepath = DATA_DIR / "seed_domains.csv"

    filepath.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["domain", "expiry_date", "tld", "sld", "source", "country", "fetched_at"]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    log.info(f"Seed data saved to {filepath} ({len(records)} records)")
    return filepath


if __name__ == "__main__":
    records = generate_seed_data()
    save_seed_data(records)
