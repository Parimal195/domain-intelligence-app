"""
Brandability Scoring for the Domain Intelligence App.

Evaluates how "brandable" a domain name is using:
- Word segmentation (does it contain real words?)
- Phonetic appeal (how it sounds)
- Memorability heuristics
- Brand pattern matching
"""

import re
from typing import List, Tuple

from utils.helpers import (
    extract_sld,
    vowel_ratio,
    has_consecutive_consonants,
    estimate_syllables,
    VOWELS,
    CONSONANTS,
)
from utils.logger import get_logger

log = get_logger(__name__)

# ─────────────────────────────────────────────
# Common English words for word segmentation
# (lightweight — no external dependency required)
# ─────────────────────────────────────────────
COMMON_WORDS = {
    # 2-letter
    "ai", "go", "up", "my", "do", "no", "we", "be", "it", "on",
    # 3-letter
    "the", "and", "for", "are", "but", "not", "you", "all", "can",
    "app", "web", "net", "hub", "pay", "buy", "get", "top", "new",
    "big", "hot", "pro", "win", "run", "set", "box", "lab", "bit",
    "now", "one", "two", "try", "use", "way", "day", "fin", "bio",
    "eco", "zen", "fit", "fix", "fly", "pop", "mix", "max", "key",
    # 4-letter
    "data", "tech", "code", "game", "play", "shop", "find", "link",
    "chat", "book", "hire", "sell", "send", "grow", "flow", "sync",
    "dash", "base", "core", "mind", "wave", "buzz", "edge", "volt",
    "mint", "peak", "pure", "leap", "bold", "fast", "flux", "glow",
    "hive", "loop", "nest", "vibe", "zone", "beta", "byte", "coin",
    "dock", "fuel", "grid", "quad", "snap", "spark", "true", "work",
    "fund", "farm", "mine", "cook", "ride", "care", "plan", "vote",
    "test", "sign", "clip", "draw", "talk", "host", "rent", "gift",
    "feed", "lock", "swap", "bank", "auto", "deep", "next", "meta",
    "star", "fire", "blue", "real", "open", "free", "safe", "easy",
    # 5-letter
    "cloud", "smart", "trade", "block", "chain", "cyber", "pixel",
    "ultra", "prime", "boost", "share", "stack", "track", "learn",
    "build", "solar", "green", "earth", "clean", "fresh", "power",
    "money", "scale", "shift", "swift", "scope", "forge", "craft",
    "pulse", "spark", "light", "rapid", "super", "turbo", "hyper",
    "space", "orbit", "blaze", "dream", "voice", "royal", "noble",
    "alpha", "omega", "delta", "sigma", "logic", "nexus", "atlas",
    # 6+ letter
    "health", "market", "stream", "studio", "design", "launch",
    "master", "rocket", "fusion", "genius", "global", "mobile",
    "crypto", "fintech", "gaming", "social", "carbon", "quantum",
    "neural", "vision", "motion", "impact", "bridge", "summit",
    "harbor", "beacon", "venture", "digital", "stellar", "pioneer",
    "dynamic", "evolve",
}


def segment_words(text: str) -> List[str]:
    """
    Attempt to segment a concatenated string into known words.
    Uses greedy longest-match approach.
    
    Args:
        text: Input text (typically SLD of domain).
    
    Returns:
        List of found words. Empty segments are included as single chars.
    """
    text = text.lower()
    words = []
    i = 0

    while i < len(text):
        best_match = ""
        # Try longest match first (up to 10 chars)
        for length in range(min(10, len(text) - i), 1, -1):
            candidate = text[i:i + length]
            if candidate in COMMON_WORDS:
                best_match = candidate
                break

        if best_match:
            words.append(best_match)
            i += len(best_match)
        else:
            # No word found — advance by 1
            words.append(text[i])
            i += 1

    return words


def compute_brandability_score(domain: str) -> float:
    """
    Compute overall brandability score for a domain.
    
    Factors:
    1. Word composition (40%): Does it contain real words?
    2. Phonetic appeal (25%): Is it pleasant to say?
    3. Memorability (20%): Is it easy to remember?
    4. Brand pattern (15%): Does it follow common brand naming patterns?
    
    Args:
        domain: Full domain name.
    
    Returns:
        Brandability score (0-100).
    """
    sld = extract_sld(domain).lower()

    if not sld:
        return 0.0

    # ── 1. Word Composition Score (0-100) ──
    word_score = _word_composition_score(sld)

    # ── 2. Phonetic Appeal Score (0-100) ──
    phonetic_score = _phonetic_appeal_score(sld)

    # ── 3. Memorability Score (0-100) ──
    memorability_score = _memorability_score(sld)

    # ── 4. Brand Pattern Score (0-100) ──
    pattern_score = _brand_pattern_score(sld)

    # Weighted combination
    final = (
        word_score * 0.40
        + phonetic_score * 0.25
        + memorability_score * 0.20
        + pattern_score * 0.15
    )

    return round(min(100.0, max(0.0, final)), 2)


def _word_composition_score(sld: str) -> float:
    """Score based on how much of the domain is made of real words."""
    words = segment_words(sld)

    # Calculate coverage: what fraction of chars are in recognized words
    word_chars = sum(len(w) for w in words if w in COMMON_WORDS)
    coverage = word_chars / max(len(sld), 1)

    if coverage >= 0.9:
        return 95.0
    elif coverage >= 0.7:
        return 80.0
    elif coverage >= 0.5:
        return 65.0
    elif coverage >= 0.3:
        return 45.0
    else:
        # Even non-word domains can be brandable if they sound good
        return 25.0


def _phonetic_appeal_score(sld: str) -> float:
    """Score based on phonetic qualities."""
    score = 50.0

    # Good vowel ratio
    vr = vowel_ratio(sld)
    if 0.30 <= vr <= 0.50:
        score += 20.0
    elif 0.25 <= vr <= 0.55:
        score += 10.0
    else:
        score -= 10.0

    # No harsh consonant clusters
    if has_consecutive_consonants(sld, threshold=4):
        score -= 25.0
    elif has_consecutive_consonants(sld, threshold=3):
        score -= 10.0

    # Ends pleasantly
    if sld[-1:] in "aeiouy":
        score += 10.0
    elif sld[-2:] in ("ly", "er", "le", "al", "ty", "fy"):
        score += 8.0

    # Starts with a clean consonant
    if sld and sld[0] in "bdfgklmnprstvw":
        score += 5.0

    return min(100.0, max(0.0, score))


def _memorability_score(sld: str) -> float:
    """Score based on memorability heuristics."""
    score = 50.0

    length = len(sld)

    # Ideal length for memorability
    if 4 <= length <= 8:
        score += 25.0
    elif 3 <= length <= 10:
        score += 15.0
    elif length <= 12:
        score += 5.0
    else:
        score -= 15.0

    # Syllable count
    syllables = estimate_syllables(sld)
    if syllables <= 3:
        score += 15.0
    elif syllables <= 4:
        score += 5.0
    else:
        score -= 10.0

    # Penalize numbers and special chars
    if any(c.isdigit() for c in sld):
        score -= 15.0
    if "-" in sld:
        score -= 10.0

    # Bonus for alliteration
    if len(sld) >= 4 and sld[0] == sld[len(sld) // 2]:
        score += 5.0

    return min(100.0, max(0.0, score))


def _brand_pattern_score(sld: str) -> float:
    """Score based on similarity to known brand naming patterns."""
    score = 40.0

    # Pattern: Prefix + common suffix (Spotify, Shopify, Amplify)
    brand_suffixes = ["ify", "ly", "io", "eo", "ia", "ium", "ize", "fy", "er", "le"]
    for suffix in brand_suffixes:
        if sld.endswith(suffix) and len(sld) > len(suffix) + 2:
            score += 25.0
            break

    # Pattern: Two-syllable compound (Facebook, YouTube, TikTok)
    syllables = estimate_syllables(sld)
    if syllables == 2 and 5 <= len(sld) <= 8:
        score += 20.0

    # Pattern: Portmanteau (Pinterest = pin + interest)
    words = segment_words(sld)
    real_words = [w for w in words if w in COMMON_WORDS and len(w) >= 3]
    if len(real_words) == 2:
        score += 15.0
    elif len(real_words) == 1 and len(sld) <= 8:
        score += 10.0

    # Penalize generic patterns
    if re.match(r"^(get|my|the|best|top|free)\w+$", sld):
        score -= 10.0

    return min(100.0, max(0.0, score))


if __name__ == "__main__":
    test_domains = [
        "shopify.com",
        "nextcloud.io",
        "xrqbzm.xyz",
        "healthhub.ai",
        "a.com",
        "spotify.com",
        "cryptoswap.co",
        "get-my-stuff.net",
        "zenflow.dev",
        "buzzpay.app",
    ]

    for d in test_domains:
        score = compute_brandability_score(d)
        sld = extract_sld(d)
        words = segment_words(sld)
        print(f"{d:30s} → {score:5.1f}  words: {words}")
