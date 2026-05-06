"""
Trend Scoring for the Domain Intelligence App.
Evaluates domain keyword relevance to current trends.
"""

from typing import Dict, Optional, List
from utils.config import PREMIUM_KEYWORDS, TRENDING_KEYWORDS
from utils.helpers import extract_sld
from utils.logger import get_logger

log = get_logger(__name__)

STATIC_TREND_SCORES = {
    "ai": 95, "ml": 80, "gpt": 92, "llm": 88, "neural": 75,
    "deep": 70, "gen": 78, "auto": 65, "smart": 60, "bot": 72,
    "quantum": 68, "data": 65, "cloud": 62, "api": 58, "code": 55,
    "crypto": 70, "coin": 55, "nft": 35, "defi": 50, "token": 55,
    "swap": 48, "chain": 52, "block": 50, "wallet": 58, "pay": 62,
    "fin": 55, "bank": 50, "trade": 52, "mint": 45,
    "health": 65, "med": 55, "bio": 60, "care": 50, "fit": 52,
    "well": 48, "vita": 42, "lab": 55,
    "game": 68, "play": 60, "stream": 65, "meta": 55, "pixel": 50,
    "vr": 58, "ar": 48, "esport": 52,
    "hub": 45, "pro": 42, "sync": 50, "flow": 55, "stack": 52,
    "base": 40, "core": 42, "link": 38, "dash": 45, "app": 60,
    "shop": 48, "market": 55, "sell": 42, "grow": 50, "lead": 48,
    "eco": 55, "green": 50, "solar": 58, "clean": 52, "carbon": 60,
    "earth": 45, "tech": 58, "dev": 55, "cyber": 62, "web": 40,
}


class TrendScorer:
    """Scores domain keywords based on trend relevance."""

    def __init__(self, use_pytrends: bool = True):
        self.use_pytrends = use_pytrends
        self._pytrends_available = False
        self._trend_cache: Dict[str, float] = {}
        self._pytrends_client = None
        if use_pytrends:
            self._init_pytrends()

    def _init_pytrends(self):
        try:
            from pytrends.request import TrendReq
            self._pytrends_client = TrendReq(hl="en-US", tz=0, timeout=(10, 25), retries=2, backoff_factor=1.0)
            self._pytrends_available = True
            log.info("pytrends initialized successfully")
        except Exception as e:
            log.warning(f"pytrends unavailable: {e} — using static data")
            self._pytrends_available = False

    def _get_pytrends_score(self, keyword: str) -> Optional[float]:
        if not self._pytrends_available:
            return None
        if keyword in self._trend_cache:
            return self._trend_cache[keyword]
        try:
            self._pytrends_client.build_payload(kw_list=[keyword], timeframe="today 3-m", geo="")
            interest = self._pytrends_client.interest_over_time()
            if interest.empty:
                self._trend_cache[keyword] = 0.0
                return 0.0
            score = min(100.0, float(interest[keyword].mean()))
            self._trend_cache[keyword] = score
            return score
        except Exception as e:
            log.debug(f"pytrends failed for '{keyword}': {e}")
            return None

    def _get_static_score(self, keyword: str) -> float:
        keyword = keyword.lower()
        if keyword in STATIC_TREND_SCORES:
            return float(STATIC_TREND_SCORES[keyword])
        best = 0.0
        for k, v in STATIC_TREND_SCORES.items():
            if k in keyword or keyword in k:
                best = max(best, v * 0.8)
        return best

    def score_domain(self, domain: str) -> float:
        sld = extract_sld(domain).lower()
        if not sld:
            return 0.0
        keywords = self._extract_keywords(sld)
        if not keywords:
            return 5.0
        scores = []
        for kw in keywords:
            if self.use_pytrends and self._pytrends_available:
                ps = self._get_pytrends_score(kw)
                if ps is not None:
                    scores.append(ps)
                    continue
            scores.append(self._get_static_score(kw))
        if not scores:
            return 5.0
        final = max(scores) * 0.7 + (sum(scores) / len(scores)) * 0.3
        return round(min(100.0, max(0.0, final)), 2)

    def _extract_keywords(self, sld: str) -> List[str]:
        keywords = []
        if len(sld) >= 3:
            keywords.append(sld)
        for kw in list(STATIC_TREND_SCORES.keys()) + PREMIUM_KEYWORDS:
            if kw in sld and len(kw) >= 2:
                keywords.append(kw)
        seen = set()
        unique = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)
        return unique[:5]

    def score_batch(self, domains: List[str]) -> Dict[str, float]:
        return {d: self.score_domain(d) for d in domains}
