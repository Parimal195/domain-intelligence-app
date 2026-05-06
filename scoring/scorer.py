"""
Composite ML Scoring Engine for the Domain Intelligence App.
Combines all feature scores into a final weighted score with value tags.
"""

from typing import Dict
from utils.config import SCORING_WEIGHTS, get_tag
from utils.helpers import extract_sld
from utils.logger import get_logger
from scoring.features import compute_all_features
from scoring.brandability import compute_brandability_score
from scoring.trend_scorer import TrendScorer
from scoring.price_estimator import estimate_price

log = get_logger(__name__)


class DomainScorer:
    """
    Composite scoring engine that combines all sub-scores
    into a final domain intelligence score (0-100).
    """

    def __init__(self, use_pytrends: bool = False):
        self.trend_scorer = TrendScorer(use_pytrends=use_pytrends)
        self.weights = SCORING_WEIGHTS
        log.info(f"DomainScorer initialized (pytrends={'ON' if use_pytrends else 'OFF'})")

    def score_domain(self, domain: str) -> Dict:
        """
        Score a single domain across all dimensions.
        
        Returns dict with all sub-scores, final score, tag, and price.
        """
        # Feature scores
        features = compute_all_features(domain)
        
        # Brandability
        brand_score = compute_brandability_score(domain)
        
        # Trend score
        trend_score = self.trend_scorer.score_domain(domain)
        
        # Weighted final score
        final_score = (
            features["keyword_score"] * self.weights["keyword"]
            + trend_score * self.weights["trend"]
            + features["tld_score"] * self.weights["tld"]
            + brand_score * self.weights["brandability"]
            + features["length_score"] * self.weights["length"]
        )
        final_score = round(min(100.0, max(0.0, final_score)), 2)
        
        # Value tag
        tag = get_tag(final_score)
        
        # Price estimate
        price = estimate_price(domain, score=final_score)
        
        return {
            "domain": domain,
            "sld": extract_sld(domain),
            "score": final_score,
            "tag": tag,
            "estimated_price": price,
            "keyword_score": features["keyword_score"],
            "trend_score": trend_score,
            "tld_score": features["tld_score"],
            "brandability_score": brand_score,
            "length_score": features["length_score"],
            "pronounceability_score": features["pronounceability_score"],
        }

    def score_batch(self, domains: list) -> list:
        """Score a list of domains. Returns list of scored dicts."""
        results = []
        total = len(domains)
        
        for i, domain in enumerate(domains):
            try:
                result = self.score_domain(domain)
                results.append(result)
                if (i + 1) % 100 == 0:
                    log.info(f"Scored {i+1}/{total} domains...")
            except Exception as e:
                log.warning(f"Failed to score {domain}: {e}")
                continue
        
        log.info(f"Scoring complete: {len(results)}/{total} domains scored")
        return results
