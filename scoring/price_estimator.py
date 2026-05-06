"""
Price Estimator for the Domain Intelligence App.
Estimates domain buy price based on TLD, length, and keyword presence.
"""

from utils.config import TLD_PRICE_RANGES, DEFAULT_PRICE_RANGE, PREMIUM_KEYWORDS
from utils.helpers import extract_tld, extract_sld
from utils.logger import get_logger

log = get_logger(__name__)


def estimate_price(domain: str, score: float = 50.0) -> float:
    """
    Estimate domain registration/buy price in USD.
    
    Args:
        domain: Full domain name.
        score: Domain's composite score (0-100) for premium adjustment.
    
    Returns:
        Estimated price in USD.
    """
    tld = extract_tld(domain)
    sld = extract_sld(domain).lower()
    
    # Base price from TLD
    low, high = TLD_PRICE_RANGES.get(tld, DEFAULT_PRICE_RANGE)
    base_price = (low + high) / 2.0
    
    # Length multiplier: shorter domains cost more
    length = len(sld)
    if length <= 3:
        length_mult = 3.0
    elif length <= 5:
        length_mult = 2.0
    elif length <= 7:
        length_mult = 1.5
    elif length <= 10:
        length_mult = 1.2
    else:
        length_mult = 1.0
    
    # Keyword multiplier
    keyword_mult = 1.0
    for kw in PREMIUM_KEYWORDS:
        if kw in sld:
            keyword_mult = max(keyword_mult, 1.5)
            if sld == kw or sld.startswith(kw) or sld.endswith(kw):
                keyword_mult = max(keyword_mult, 2.0)
            break
    
    # Score-based adjustment
    if score >= 80:
        score_mult = 2.5
    elif score >= 70:
        score_mult = 1.8
    elif score >= 50:
        score_mult = 1.3
    else:
        score_mult = 1.0
    
    estimated = base_price * length_mult * keyword_mult * score_mult
    return round(estimated, 2)


def get_price_display(price: float) -> str:
    """Format price for display."""
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 100:
        return f"${price:.0f}"
    else:
        return f"${price:.2f}"
