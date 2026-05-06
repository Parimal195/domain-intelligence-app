"""
Central configuration for the Domain Intelligence App.
All tunable parameters, file paths, scoring weights, and keyword lists.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_FILE = DATA_DIR / "domains.csv"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# Scoring Weights (must sum to 1.0)
# ─────────────────────────────────────────────
SCORING_WEIGHTS = {
    "keyword": 0.30,
    "trend": 0.25,
    "tld": 0.15,
    "brandability": 0.20,
    "length": 0.10,
}

# ─────────────────────────────────────────────
# TLD Tier Scoring (0–100)
# ─────────────────────────────────────────────
TLD_SCORES = {
    ".com": 100,
    ".ai": 92,
    ".io": 85,
    ".co": 78,
    ".app": 76,
    ".dev": 74,
    ".net": 70,
    ".org": 68,
    ".xyz": 55,
    ".tech": 60,
    ".online": 45,
    ".info": 40,
    ".biz": 35,
    ".club": 30,
    ".site": 42,
    ".store": 48,
    ".me": 65,
    ".gg": 72,
    ".so": 58,
    ".cc": 50,
}
DEFAULT_TLD_SCORE = 30

# ─────────────────────────────────────────────
# TLD Price Estimates (USD) — registration cost range
# ─────────────────────────────────────────────
TLD_PRICE_RANGES = {
    ".com": (8, 15),
    ".ai": (50, 90),
    ".io": (30, 55),
    ".co": (10, 30),
    ".app": (12, 20),
    ".dev": (12, 18),
    ".net": (10, 15),
    ".org": (10, 14),
    ".xyz": (2, 10),
    ".tech": (5, 50),
    ".online": (2, 8),
    ".info": (3, 12),
    ".biz": (5, 15),
    ".club": (3, 10),
    ".site": (2, 8),
    ".store": (3, 15),
    ".me": (8, 20),
    ".gg": (40, 80),
    ".so": (15, 40),
    ".cc": (10, 25),
}
DEFAULT_PRICE_RANGE = (5, 20)

# ─────────────────────────────────────────────
# Premium Keywords (boost scoring)
# ─────────────────────────────────────────────
PREMIUM_KEYWORDS = [
    # Tech / AI
    "ai", "ml", "data", "cloud", "api", "dev", "code", "tech", "bot",
    "cyber", "quantum", "neural", "auto", "smart", "deep", "gen",
    # Fintech / Crypto
    "pay", "fin", "bank", "crypto", "coin", "nft", "defi", "token",
    "swap", "trade", "wallet", "chain", "block", "mint",
    # Health
    "health", "med", "bio", "care", "fit", "vita", "well", "lab",
    # Gaming / Entertainment
    "game", "play", "stream", "meta", "pixel", "vr", "ar", "esport",
    # Business
    "hub", "pro", "sync", "flow", "stack", "base", "core", "link",
    "net", "dash", "app", "shop", "market", "sell", "grow", "lead",
    # Sustainability
    "eco", "green", "solar", "clean", "earth", "carbon",
]

# ─────────────────────────────────────────────
# Trending Categories (fallback when pytrends fails)
# ─────────────────────────────────────────────
TRENDING_KEYWORDS = [
    "artificial intelligence", "machine learning", "chatgpt", "generative ai",
    "cryptocurrency", "bitcoin", "ethereum", "defi",
    "fintech", "neobank", "digital payments",
    "gaming", "esports", "cloud gaming", "metaverse",
    "streaming", "content creation",
    "sustainability", "climate tech", "renewable energy",
    "healthtech", "telemedicine", "biotech",
    "cybersecurity", "zero trust", "quantum computing",
    "saas", "no-code", "low-code", "api-first",
    "remote work", "productivity", "collaboration",
]

# ─────────────────────────────────────────────
# RDAP Configuration
# ─────────────────────────────────────────────
RDAP_BASE_URL = "https://rdap.org/domain/"
RDAP_RATE_LIMIT_SECONDS = 1.2  # seconds between requests
RDAP_MAX_RETRIES = 3
RDAP_TIMEOUT_SECONDS = 10

# ─────────────────────────────────────────────
# Pipeline Configuration
# ─────────────────────────────────────────────
MAX_DOMAINS_PER_RUN = 2000  # cap to stay within free tier
SEED_DOMAIN_COUNT = 500
EXPIRY_WINDOWS = {
    "1_day": 1,
    "7_days": 7,
    "30_days": 30,
}

# ─────────────────────────────────────────────
# Value Tags
# ─────────────────────────────────────────────
HIGH_VALUE_THRESHOLD = 70
MEDIUM_VALUE_THRESHOLD = 40

def get_tag(score: float) -> str:
    """Return value tag based on score."""
    if score >= HIGH_VALUE_THRESHOLD:
        return "High Value"
    elif score >= MEDIUM_VALUE_THRESHOLD:
        return "Medium Value"
    return "Low Value"
