"""
Feature Engineering for the Domain Intelligence App.

Computes numerical features from domain names for ML scoring:
- Length score
- Keyword score
- TLD score
- Pronounceability score
"""

from typing import Dict

from utils.config import (
    PREMIUM_KEYWORDS,
    TLD_SCORES,
    DEFAULT_TLD_SCORE,
)
from utils.helpers import (
    extract_sld,
    extract_tld,
    vowel_ratio,
    has_consecutive_consonants,
    estimate_syllables,
)
from utils.logger import get_logger

log = get_logger(__name__)


def compute_length_score(domain: str) -> float:
    """
    Score domain based on name length (shorter = better).
    
    Scoring curve:
    - 1-4 chars:  95-100 (ultra-premium)
    - 5-7 chars:  80-94  (premium)
    - 8-10 chars: 60-79  (good)
    - 11-15 chars: 30-59 (average)
    - 16+ chars:  0-29   (poor)
    
    Args:
        domain: Full domain name (e.g., 'example.com').
    
    Returns:
        Length score (0-100).
    """
    sld = extract_sld(domain)
    length = len(sld)

    if length <= 2:
        return 100.0
    elif length <= 4:
        return 95.0 + (4 - length) * 1.5
    elif length <= 7:
        return 80.0 + (7 - length) * 5.0
    elif length <= 10:
        return 60.0 + (10 - length) * 7.0
    elif length <= 15:
        return 30.0 + (15 - length) * 6.0
    elif length <= 20:
        return max(5.0, 30.0 - (length - 15) * 5.0)
    else:
        return 2.0


def compute_keyword_score(domain: str) -> float:
    """
    Score domain based on presence of premium keywords.
    
    Premium keywords are industry terms that indicate high commercial value
    (e.g., 'ai', 'cloud', 'crypto', 'pay', 'health').
    
    Scoring:
    - Contains 2+ premium keywords: 85-100
    - Contains 1 premium keyword: 50-84
    - Contains partial keyword match: 20-49
    - No keywords: 0-19
    
    Args:
        domain: Full domain name.
    
    Returns:
        Keyword score (0-100).
    """
    sld = extract_sld(domain).lower()
    score = 0.0

    # Exact keyword matches
    exact_matches = 0
    matched_keywords = []

    for keyword in PREMIUM_KEYWORDS:
        if keyword in sld:
            exact_matches += 1
            matched_keywords.append(keyword)

    if exact_matches >= 3:
        score = 95.0
    elif exact_matches == 2:
        score = 85.0
    elif exact_matches == 1:
        # Score higher for keywords that ARE the domain vs just contained
        kw = matched_keywords[0]
        if sld == kw:
            score = 80.0  # Domain IS the keyword
        elif sld.startswith(kw) or sld.endswith(kw):
            score = 70.0  # Keyword at start/end
        else:
            score = 55.0  # Keyword contained
    else:
        # Partial match: check if domain sounds industry-related
        tech_fragments = ["fy", "ly", "ize", "ify", "tion", "ment"]
        for frag in tech_fragments:
            if frag in sld:
                score += 5.0

        # Check for numeric domains (often less valuable)
        digit_ratio = sum(1 for c in sld if c.isdigit()) / max(len(sld), 1)
        if digit_ratio > 0.3:
            score = max(0, score - 10)

    return min(100.0, max(0.0, score))


def compute_tld_score(domain: str) -> float:
    """
    Score domain based on TLD commercial value.
    
    Uses predefined TLD tier scoring from config.
    
    Args:
        domain: Full domain name.
    
    Returns:
        TLD score (0-100).
    """
    tld = extract_tld(domain)
    return float(TLD_SCORES.get(tld, DEFAULT_TLD_SCORE))


def compute_pronounceability_score(domain: str) -> float:
    """
    Score how pronounceable/memorable a domain name is.
    
    Factors:
    - Vowel/consonant ratio (ideal ~0.35-0.45)
    - No awkward consonant clusters
    - Reasonable syllable count (2-3 ideal)
    - No excessive hyphens or numbers
    
    Args:
        domain: Full domain name.
    
    Returns:
        Pronounceability score (0-100).
    """
    sld = extract_sld(domain).lower()
    score = 50.0  # Start at neutral

    # 1. Vowel ratio (ideal 0.35-0.45)
    vr = vowel_ratio(sld)
    if 0.30 <= vr <= 0.50:
        score += 20.0  # Good ratio
    elif 0.20 <= vr <= 0.60:
        score += 10.0  # Acceptable
    else:
        score -= 15.0  # Poor ratio

    # 2. Consonant clusters
    if has_consecutive_consonants(sld, threshold=4):
        score -= 20.0  # Awkward to pronounce
    elif has_consecutive_consonants(sld, threshold=3):
        score -= 8.0

    # 3. Syllable count (2-3 is ideal for branding)
    syllables = estimate_syllables(sld)
    if syllables == 2:
        score += 20.0
    elif syllables == 3:
        score += 15.0
    elif syllables == 1:
        score += 10.0  # Short but might be cryptic
    elif syllables == 4:
        score += 5.0
    else:
        score -= 10.0  # Too many syllables

    # 4. Penalize numbers and hyphens
    if any(c.isdigit() for c in sld):
        score -= 10.0
    if "-" in sld:
        score -= 15.0

    # 5. Bonus for ending in vowel (often sounds better)
    if sld and sld[-1] in "aeio":
        score += 5.0

    return min(100.0, max(0.0, score))


def compute_all_features(domain: str) -> Dict[str, float]:
    """
    Compute all feature scores for a domain.
    
    Args:
        domain: Full domain name.
    
    Returns:
        Dict of feature name → score (0-100).
    """
    return {
        "length_score": round(compute_length_score(domain), 2),
        "keyword_score": round(compute_keyword_score(domain), 2),
        "tld_score": round(compute_tld_score(domain), 2),
        "pronounceability_score": round(compute_pronounceability_score(domain), 2),
    }


if __name__ == "__main__":
    test_domains = [
        "aicloud.com",
        "nextpay.io",
        "xrqbzm.xyz",
        "healthhub.ai",
        "a.com",
        "my-super-long-domain-name.net",
        "cryptoswap.co",
        "zzzzz.biz",
    ]

    for d in test_domains:
        features = compute_all_features(d)
        print(f"\n{d}:")
        for k, v in features.items():
            print(f"  {k}: {v}")
